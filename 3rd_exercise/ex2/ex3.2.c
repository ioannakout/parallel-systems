#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>

typedef long long ll;

double rand_double() {
    return (double)rand() / (double)RAND_MAX;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    int N, iterations;
    double sparsity;
    int error_flag = 0;

    // --- ΒΗΜΑ 1: Έλεγχος Ορισμάτων ---
    if (rank == 0) {
        if (argc != 4) {
            fprintf(stderr, "Usage: %s <N> <sparsity> <iterations>\n", argv[0]);
            error_flag = 1;
        } else {
            N = atoi(argv[1]);
            sparsity = atof(argv[2]);
            iterations = atoi(argv[3]);
            
            if (N % size != 0) {
                fprintf(stderr, "Error: N (%d) must be divisible by MPI size (%d)\n", N, size);
                error_flag = 1;
            }
        }
    }

    MPI_Bcast(&error_flag, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (error_flag) {
        MPI_Finalize();
        return 1;
    }

    MPI_Bcast(&N, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&sparsity, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(&iterations, 1, MPI_INT, 0, MPI_COMM_WORLD);

    int local_rows = N / size;

    // --- Δομές Δεδομένων ---
    ll *dense_matrix = NULL;
    ll *vectorCSR = NULL; // Αρχικό διάνυσμα
    
    // CSR (Rank 0)
    ll *csr_values = NULL;
    int *csr_col_ind = NULL;
    int *csr_row_ptr = NULL;

    // Τοπικά δεδομένα
    ll *local_dense = (ll*)malloc(local_rows * N * sizeof(ll)); // Για τον Dense
    ll *local_vectorCSR = (ll*)malloc(N * sizeof(ll));
    ll *local_vectorDense = (ll*)malloc(local_rows * sizeof(ll));
    
    // CSR Local
    ll *local_csr_val = NULL;
    int *local_csr_col = NULL;
    int *local_csr_row_ptr = (int*)malloc((local_rows + 1) * sizeof(int));
    int local_nnz = 0;

    // Χρονόμετρα
    double t_start, t_end;
    double t_csr_build = 0, t_comm = 0, t_csr_calc = 0, t_dense_calc = 0;

    // ==========================================
    // ΦΑΣΗ 1: Δημιουργία & CSR (Rank 0)
    // ==========================================
    if (rank == 0) {
        srand(time(NULL));
        dense_matrix = (ll*)malloc(N * N * sizeof(ll));
        vectorCSR = (ll*)malloc(N * sizeof(ll));

        // Αρχικοποίηση διανύσματος με 1
        for (int i = 0; i < N; i++) vectorCSR[i] = 1;

        printf("Rank 0: Generating Matrix N=%d...\n", N);
        int total_nnz = 0;
        for (int i = 0; i < N * N; i++) {
            if (rand_double() > sparsity) {
                dense_matrix[i] = (ll)((rand() % 10) + 1);
                total_nnz++;
            } else {
                dense_matrix[i] = 0;
            }
        }

        // (i) Χρόνος Κατασκευής CSR
        t_start = MPI_Wtime();
        
        csr_values = (ll*)malloc(total_nnz * sizeof(ll));
        csr_col_ind = (int*)malloc(total_nnz * sizeof(int));
        csr_row_ptr = (int*)malloc((N + 1) * sizeof(int));

        int nnz_count = 0;
        csr_row_ptr[0] = 0;
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                ll val = dense_matrix[i * N + j];
                if (val != 0) {
                    csr_values[nnz_count] = val;
                    csr_col_ind[nnz_count] = j;
                    nnz_count++;
                }
            }
            csr_row_ptr[i+1] = nnz_count;
        }
        t_end = MPI_Wtime();
        t_csr_build = t_end - t_start;
    }

    // ==========================================
    // ΦΑΣΗ 2: Διανομή CSR (Χειροκίνητη)
    // ==========================================
    if (rank == 0) t_start = MPI_Wtime();

    // Broadcast το αρχικό διάνυσμα
    if (rank == 0) {
        for(int i=0; i<N; i++) local_vectorCSR[i] = vectorCSR[i];
    }
    MPI_Bcast(local_vectorCSR, N, MPI_LONG_LONG, 0, MPI_COMM_WORLD);

    // Χειροκίνητη διανομή CSR (όπως πριν)
    if (rank == 0) {
        for (int dest = 0; dest < size; dest++) {
            int r_start = dest * local_rows;
            int r_end = r_start + local_rows;
            int count_nnz = csr_row_ptr[r_end] - csr_row_ptr[r_start];

            if (dest == 0) {
                local_nnz = count_nnz;
                local_csr_val = (ll*)malloc(local_nnz * sizeof(ll));
                local_csr_col = (int*)malloc(local_nnz * sizeof(int));
                int start_idx = csr_row_ptr[r_start];
                for(int k=0; k<local_nnz; k++) {
                    local_csr_val[k] = csr_values[start_idx + k];
                    local_csr_col[k] = csr_col_ind[start_idx + k];
                }
                local_csr_row_ptr[0] = 0;
                for(int i=0; i<local_rows; i++) {
                    local_csr_row_ptr[i+1] = csr_row_ptr[r_start + i + 1] - csr_row_ptr[r_start];
                }
            } else {
                MPI_Send(&count_nnz, 1, MPI_INT, dest, 0, MPI_COMM_WORLD);
                if (count_nnz > 0) {
                    int start_idx = csr_row_ptr[r_start];
                    MPI_Send(&csr_values[start_idx], count_nnz, MPI_LONG_LONG, dest, 1, MPI_COMM_WORLD);
                    MPI_Send(&csr_col_ind[start_idx], count_nnz, MPI_INT, dest, 2, MPI_COMM_WORLD);
                }
                int *temp_row_lens = (int*)malloc(local_rows * sizeof(int));
                for(int i=0; i<local_rows; i++) {
                    temp_row_lens[i] = csr_row_ptr[r_start + i + 1] - csr_row_ptr[r_start + i];
                }
                MPI_Send(temp_row_lens, local_rows, MPI_INT, dest, 3, MPI_COMM_WORLD);
                free(temp_row_lens);
            }
        }
    } else {
        MPI_Recv(&local_nnz, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        local_csr_val = (ll*)malloc(local_nnz * sizeof(ll));
        local_csr_col = (int*)malloc(local_nnz * sizeof(int));
        if (local_nnz > 0) {
            MPI_Recv(local_csr_val, local_nnz, MPI_LONG_LONG, 0, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            MPI_Recv(local_csr_col, local_nnz, MPI_INT, 0, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
        int *recv_row_lens = (int*)malloc(local_rows * sizeof(int));
        MPI_Recv(recv_row_lens, local_rows, MPI_INT, 0, 3, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        local_csr_row_ptr[0] = 0;
        for(int i=0; i<local_rows; i++) {
            local_csr_row_ptr[i+1] = local_csr_row_ptr[i] + recv_row_lens[i];
        }
        free(recv_row_lens);
    }

    if (rank == 0) {
        t_end = MPI_Wtime();
        t_comm = t_end - t_start; // (ii) Χρόνος Αποστολής
    }

    // ==========================================
    // ΦΑΣΗ 3: Υπολογισμός CSR
    // ==========================================
    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) t_start = MPI_Wtime();

    for (int k = 0; k < iterations; k++) {
        for (int i = 0; i < local_rows; i++) {
            ll sum = 0;
            int row_start = local_csr_row_ptr[i];
            int row_end   = local_csr_row_ptr[i+1];
            for (int j = row_start; j < row_end; j++) {
                sum += local_csr_val[j] * local_vectorCSR[ local_csr_col[j] ];
            }
            local_vectorDense[i] = sum;
        }
        MPI_Allgather(local_vectorDense, local_rows, MPI_LONG_LONG, 
                      local_vectorCSR, local_rows, MPI_LONG_LONG, 
                      MPI_COMM_WORLD);
    }

    if (rank == 0) {
        t_end = MPI_Wtime();
        t_csr_calc = t_end - t_start; // (iii) Χρόνος Εκτέλεσης CSR
    }

    // ==========================================
    // ΦΑΣΗ 4: Υπολογισμός DENSE (Πυκνός)
    // ==========================================
    
    // 1. Επαναφορά του διανύσματος X στην αρχική κατάσταση (όλα 1)
    if (rank == 0) {
        for (int i = 0; i < N; i++) local_vectorCSR[i] = vectorCSR[i];
    }
    MPI_Bcast(local_vectorCSR, N, MPI_LONG_LONG, 0, MPI_COMM_WORLD);

    // 2. Διανομή του Πυκνού Πίνακα
    // Χρησιμοποιούμε MPI_Scatter που είναι στις διαφάνειες (σελ. 71)
    // Επειδή N διαιρείται ακριβώς, κάθε διεργασία παίρνει 'local_rows * N' στοιχεία
    MPI_Scatter(dense_matrix, local_rows * N, MPI_LONG_LONG, 
                local_dense, local_rows * N, MPI_LONG_LONG, 
                0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) t_start = MPI_Wtime();

    for (int k = 0; k < iterations; k++) {
        for (int i = 0; i < local_rows; i++) {
            ll sum = 0;
            for (int j = 0; j < N; j++) {
                // local_dense είναι μονοδιάστατος, άρα i*N + j
                sum += local_dense[i * N + j] * local_vectorCSR[j];
            }
            local_vectorDense[i] = sum;
        }
        MPI_Allgather(local_vectorDense, local_rows, MPI_LONG_LONG, 
                      local_vectorCSR, local_rows, MPI_LONG_LONG, 
                      MPI_COMM_WORLD);
    }

    if (rank == 0) {
        t_end = MPI_Wtime();
        t_dense_calc = t_end - t_start; // (v) Χρόνος Εκτέλεσης Dense
    }

    // ==========================================
    // ΑΠΟΤΕΛΕΣΜΑΤΑ (5 Ζητούμενα)
    // ==========================================
    if (rank == 0) {
        printf("\n=== RESULTS ===\n");
        printf("Size: %d, Sparsity: %.2f, Iterations: %d\n", N, sparsity, iterations);
        
        printf("(i)   CSR Build Time:       %f sec\n", t_csr_build);
        printf("(ii)  Comm Time (0->All):   %f sec\n", t_comm);
        printf("(iii) CSR Parallel Calc:    %f sec\n", t_csr_calc);
        printf("(iv)  CSR Total (i+ii+iii): %f sec\n", t_csr_build + t_comm + t_csr_calc);
        printf("(v)   Dense Parallel Calc:  %f sec\n", t_dense_calc);
        
        printf("\nResult Sample (First 10): ");
        for(int i=0; i < (N<10?N:10); i++) printf("%lld ", local_vectorCSR[i]);
        printf("\n");

        free(dense_matrix); free(vectorCSR);
        free(csr_values); free(csr_col_ind); free(csr_row_ptr);
    }

    free(local_vectorCSR);
    free(local_dense);
    free(local_vectorDense);
    if(local_csr_val) free(local_csr_val);
    if(local_csr_col) free(local_csr_col);
    free(local_csr_row_ptr);

    MPI_Finalize();
    return 0;
}