#include "dli.h"
#include <thrust/device_vector.h>
#include <thrust/transform.h>
#include <thrust/for_each.h>
#include <thrust/iterator/zip_iterator.h>
#include <thrust/iterator/transform_iterator.h>
#include <thrust/iterator/counting_iterator.h>
#include <cub/block/block_reduce.cuh>

struct DiffOp {
    __host__ __device__ float operator()(float x, float y) const { return x - y; }
};

struct HXFinalOp {
    float dt, dy;
    HXFinalOp(float _dt, float _dy) : dt(_dt), dy(_dy) {}
    __host__ __device__ float operator()(float h, float cex) const {
        return h - dli::C0 * dt / 1.3f * cex / dy;
    }
};

struct HYFinalOp {
    float dt, dx;
    HYFinalOp(float _dt, float _dx) : dt(_dt), dx(_dx) {}
    __host__ __device__ float operator()(float h, float cey) const {
        return h - dli::C0 * dt / 1.3f * cey / dx;
    }
};

struct DZStepOp {
    int n; float dx, dy, dt;
    float *hx, *hy, *dz;
    DZStepOp(int _n, float _dx, float _dy, float _dt, float* _hx, float* _hy, float* _dz) 
        : n(_n), dx(_dx), dy(_dy), dt(_dt), hx(_hx), hy(_hy), dz(_dz) {}
    
    __host__ __device__ void operator()(int cell_id) const {
        if (cell_id > n) {
            float hx_diff = hx[cell_id - n] - hx[cell_id];
            float hy_diff = hy[cell_id] - hy[cell_id - 1];
            dz[cell_id] += dli::C0 * dt * (hx_diff / dx + hy_diff / dy);
        }
    }
};

struct EZUpdateOp {
    __host__ __device__ float operator()(float d) const { return d / 1.3f; }
};

void update_hx(int n, float dx, float dy, float dt, thrust::device_vector<float> &hx,
               thrust::device_vector<float> &ez, thrust::device_vector<float> &buffer) {
    thrust::transform(thrust::device, ez.begin() + n, ez.end(), ez.begin(), buffer.begin(), DiffOp());
    thrust::transform(thrust::device, hx.begin(), hx.end() - n, buffer.begin(), hx.begin(), HXFinalOp(dt, dy));
}

void update_hy(int n, float dx, float dy, float dt, thrust::device_vector<float> &hy,
               thrust::device_vector<float> &ez, thrust::device_vector<float> &buffer) {
    thrust::transform(thrust::device, ez.begin(), ez.end() - 1, ez.begin() + 1, buffer.begin(), DiffOp());
    thrust::transform(thrust::device, hy.begin(), hy.end() - 1, buffer.begin(), hy.begin(), HYFinalOp(dt, dx));
}

void update_dz(int n, float dx, float dy, float dt, thrust::device_vector<float> &hx_vec,
               thrust::device_vector<float> &hy_vec, thrust::device_vector<float> &dz_vec,
               thrust::device_vector<int> &cell_ids) {
    float* hx = thrust::raw_pointer_cast(hx_vec.data());
    float* hy = thrust::raw_pointer_cast(hy_vec.data());
    float* dz = thrust::raw_pointer_cast(dz_vec.data());

    thrust::for_each(thrust::device, cell_ids.begin(), cell_ids.end(), 
                     DZStepOp(n, dx, dy, dt, hx, hy, dz));
}

void update_ez(thrust::device_vector<float> &ez, thrust::device_vector<float> &dz) {
    thrust::transform(thrust::device, dz.begin(), dz.end(), ez.begin(), EZUpdateOp());
}

void simulate(int cells_along_dimension, float dx, float dy, float dt,
              thrust::device_vector<float> &d_hx,
              thrust::device_vector<float> &d_hy,
              thrust::device_vector<float> &d_dz,
              thrust::device_vector<float> &d_ez) {
    
    int cells = cells_along_dimension * cells_along_dimension;
    
    std::vector<int> cell_ids_h(cells);
    for (int i = 0; i < cells; i++) { cell_ids_h[i] = i; }
    thrust::device_vector<int> d_cell_ids = cell_ids_h; // Move once to device for use in kernel

    thrust::device_vector<float> d_buffer(cells); // Intermediate GPU buffer

    for (int step = 0; step < dli::steps; step++) {
        update_hx(cells_along_dimension, dx, dy, dt, d_hx, d_ez, d_buffer);
        update_hy(cells_along_dimension, dx, dy, dt, d_hy, d_ez, d_buffer);
        update_dz(cells_along_dimension, dx, dy, dt, d_hx, d_hy, d_dz, d_cell_ids);
        update_ez(d_ez, d_dz);
    }
}










struct HXUpdateOp {
    float dt, dy;
    HXUpdateOp(float _dt, float _dy) : dt(_dt), dy(_dy) {}
    __host__ __device__ float operator()(thrust::tuple<float, float, float> t) const {
        float h = thrust::get<0>(t);
        float ez_next = thrust::get<1>(t);
        float ez_curr = thrust::get<2>(t);
        return h - dli::C0 * dt / 1.3f * (ez_next - ez_curr) / dy;
    }
};

struct HYUpdateOp {
    float dt, dx;
    HYUpdateOp(float _dt, float _dx) : dt(_dt), dx(_dx) {}
    __host__ __device__ float operator()(thrust::tuple<float, float, float> t) const {
        float h = thrust::get<0>(t);
        float ez_curr = thrust::get<1>(t);
        float ez_next = thrust::get<2>(t);
        return h - dli::C0 * dt / 1.3f * (ez_curr - ez_next) / dx;
    }
};

struct DZUpdateOp {
    int n; float dx, dy, dt;
    const float *hx, *hy;
    float *dz;
    DZUpdateOp(int _n, float _dx, float _dy, float _dt, const float* _hx, const float* _hy, float* _dz) 
        : n(_n), dx(_dx), dy(_dy), dt(_dt), hx(_hx), hy(_hy), dz(_dz) {}
    
    __host__ __device__ void operator()(int id) const {
        if (id > n) {
            float hx_diff = hx[id - n] - hx[id];
            float hy_diff = hy[id] - hy[id - 1];
            dz[id] += dli::C0 * dt * (hx_diff / dx + hy_diff / dy);
        }
    }
};

void update_hx(int n, float dx, float dy, float dt, thrust::device_vector<float> &hx,
               thrust::device_vector<float> &ez) {

    auto begin = thrust::make_zip_iterator(thrust::make_tuple(hx.begin(), ez.begin() + n, ez.begin()));
    auto end = thrust::make_zip_iterator(thrust::make_tuple(hx.end() - n, ez.end(), ez.begin() + (hx.size() - n)));
    
    thrust::transform(thrust::device, begin, end, hx.begin(), HXUpdateOp(dt, dy));
}

void update_hy(int n, float dx, float dy, float dt, thrust::device_vector<float> &hy,
               thrust::device_vector<float> &ez) {

    auto begin = thrust::make_zip_iterator(thrust::make_tuple(hy.begin(), ez.begin(), ez.begin() + 1));
    auto end = thrust::make_zip_iterator(thrust::make_tuple(hy.end() - 1, ez.end() - 1, ez.end()));
    
    thrust::transform(thrust::device, begin, end, hy.begin(), HYUpdateOp(dt, dx));
}

void update_dz(int n, float dx, float dy, float dt, thrust::device_vector<float> &hx,
               thrust::device_vector<float> &hy, thrust::device_vector<float> &dz) {

    thrust::for_each(thrust::device, 
                     thrust::make_counting_iterator(0), 
                     thrust::make_counting_iterator((int)dz.size()),
                     DZUpdateOp(n, dx, dy, dt, 
                                thrust::raw_pointer_cast(hx.data()), 
                                thrust::raw_pointer_cast(hy.data()), 
                                thrust::raw_pointer_cast(dz.data())));
}

void update_ez(thrust::device_vector<float> &ez, thrust::device_vector<float> &dz) {
    thrust::transform(thrust::device, dz.begin(), dz.end(), ez.begin(), 
                      [] __device__(float d) { return d / 1.3f; });
}

void simulate(int cells_along_dimension, float dx, float dy, float dt,
              thrust::device_vector<float> &d_hx,
              thrust::device_vector<float> &d_hy,
              thrust::device_vector<float> &d_dz,
              thrust::device_vector<float> &d_ez) {
    
    for (int step = 0; step < dli::steps; step++) {
        update_hx(cells_along_dimension, dx, dy, dt, d_hx, d_ez);
        update_hy(cells_along_dimension, dx, dy, dt, d_hy, d_ez);
        update_dz(cells_along_dimension, dx, dy, dt, d_hx, d_hy, d_dz);
        update_ez(d_ez, d_dz);
    }
}








__global__ void kernel(dli::temperature_grid_f fine,
                       dli::temperature_grid_f coarse) {
  int coarse_row = blockIdx.x / coarse.extent(1);
  int coarse_col = blockIdx.x % coarse.extent(1);
  int row = threadIdx.x / dli::tile_size;
  int col = threadIdx.x % dli::tile_size;
  int fine_row = coarse_row * dli::tile_size + row;
  int fine_col = coarse_col * dli::tile_size + col;

  float thread_value = fine(fine_row, fine_col);

  using BlockReduce = cub::BlockReduce<float, dli::block_threads>;
  
  __shared__ typename BlockReduce::TempStorage temp_storage;

  float block_sum = BlockReduce(temp_storage).Sum(thread_value);

  if (threadIdx.x == 0) {
    float block_average = block_sum / dli::block_threads;
    coarse(coarse_row, coarse_col) = block_average;
  }
}

void coarse(dli::temperature_grid_f fine, dli::temperature_grid_f coarse) {
  kernel<<<coarse.size(), dli::block_threads>>>(fine, coarse);
}