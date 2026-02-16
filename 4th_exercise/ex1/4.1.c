#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <immintrin.h>

// Global variables
int *pol1, *pol2;
long long *result_serial, *result_simd;
int n; 

// Alligned allocation function
void* allocate_aligned(size_t size) {
    void* ptr;
    
    // Allign at 32 bytes
    if (posix_memalign(&ptr, 32, size) != 0) {
        perror("posix_memalign failed");
        exit(1);
    }

    return ptr;
}

// Random coefficient calculator
int random_coef() {
    int r = rand() % 10 + 1;
    if (rand() % 2 == 1) r = -r;
    return r;
}

// Random polynomial
void random_pol(int degree, int *pol) {
    for (int i = 0; i <= degree; i++) {
        pol[i] = random_coef();
    }
}

// Serial Algorithm, using __attribute__((optimize("no-tree-vectorize"))), because compile
// uses -O3 which is smart and uses SIMD on serial algorithms on each own which makes the SIMD
// considerably slower than the serial algorithm and this let's us save time by using -O3 whilst
// seeing the true advantage that SIMD has over the serial algorithm
__attribute__((optimize("no-tree-vectorize")))
void serial_execution() {
    for (int i = 0; i <= n; i++) {
        for (int j = 0; j <= n; j++) {
            result_serial[i + j] += (long long)pol1[i] * pol2[j];
        }
    }
}

// SIMD Algorithm
void simd_execution() {
    for (int i = 0; i <= n; i++) {
        long long p1_scalar = pol1[i];
        
        // Skip if scalar is 0
        if (p1_scalar == 0) continue;

        // Broadcast to all the elements of the vector
        __m256i vec_p1 = _mm256_set1_epi64x(p1_scalar);

        int j = 0;
        
        // Main loop, edit 4 integers each time
        for (; j <= n - 3; j += 4) {

            // Load 4 integers using loadu because of j
            __m128i p2_small = _mm_loadu_si128((__m128i const*)&pol2[j]);
            
            // Expand integers to long long in case the multiplications get out of hand
            __m256i vec_p2 = _mm256_cvtepi32_epi64(p2_small);

            // Load previous results using loadu due to possible missalignment
            __m256i vec_res = _mm256_loadu_si256((__m256i const*)&result_simd[i + j]);

            // Multiplication of the two integers and turning them into a long long
            __m256i prod = _mm256_mul_epi32(vec_p1, vec_p2);

            // Add to the current sum
            vec_res = _mm256_add_epi64(vec_res, prod);

            // Store the result using storeu
            _mm256_storeu_si256((__m256i *)&result_simd[i + j], vec_res);
        }

        // Manage the rest of the elements in case n % 4 != 0
        for (; j <= n; j++) {
            result_simd[i + j] += (long long)pol1[i] * pol2[j];
        }
    }
}

// Calculate the time difference
double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <n>\n", argv[0]);
        return 1;
    }

    // Extract the size and randomize every rand call
    n = atoi(argv[1]);
    srand(time(NULL));

    // Allocate sizes with an bit of padding for the SIMD reads which tends to go out of bounds
    size_t size_pol = (n + 8) * sizeof(int);
    size_t size_res = (2 * n + 8) * sizeof(long long);

    // Use alligned allocation for better performance
    pol1 = allocate_aligned(size_pol);
    pol2 = allocate_aligned(size_pol);
    result_serial = allocate_aligned(size_res);
    result_simd = allocate_aligned(size_res);

    // Initialize all elements to 0
    for(int k=0; k<=2*n + 4; k++) {
        result_serial[k] = 0;
        result_simd[k] = 0;
    }

    // Initialize the starting and finishing timers
    struct timespec start, end;

    // Initialization of the polynomials
    random_pol(n, pol1);
    random_pol(n, pol2);

    // Serial execution and time calculation
    clock_gettime(CLOCK_MONOTONIC, &start);
    serial_execution();
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("Serial execution time: %.6f seconds\n", get_time_diff(start, end));

    // SIMD execution and time calculation
    clock_gettime(CLOCK_MONOTONIC, &start);
    simd_execution();
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("SIMD execution time:   %.6f seconds\n", get_time_diff(start, end));

    // Verify the results to make sure there are no errors
    int errors = 0;
    for (int i = 0; i <= 2 * n; i++) {
        if (result_serial[i] != result_simd[i]) {
            errors++;
            if (errors == 1) printf("Error at index %d: Serial=%lld SIMD=%lld\n", i, result_serial[i], result_simd[i]);
        }
    }
    
    // Print according messages
    if (errors == 0) printf("Verification: SUCCESS\n");
    else printf("Verification: FAILED with %d errors\n", errors);

    // Free the variables
    free(pol1);
    free(pol2);
    free(result_serial);
    free(result_simd);

    return 0;
}