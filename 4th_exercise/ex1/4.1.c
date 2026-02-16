#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <immintrin.h>

// Global variables
int *pol1, *pol2;
long long *result_serial, *result_simd;
int n; 

// Χρησιμοποιούμε aligned allocation για βέλτιστη απόδοση,
// ακόμα και αν χρησιμοποιούμε unaligned instructions.
void* allocate_aligned(size_t size) {
    void* ptr;
    // Ευθυγράμμιση στα 32 bytes (256 bits)
    if (posix_memalign(&ptr, 32, size) != 0) {
        perror("posix_memalign failed");
        exit(1);
    }
    return ptr;
}

int random_coef() {
    int r = rand() % 10 + 1;
    if (rand() % 2 == 1) r = -r;
    return r;
}

void random_pol(int degree, int *pol) {
    for (int i = 0; i <= degree; i++) {
        pol[i] = random_coef();
    }
}

// Serial algorithm
__attribute__((optimize("no-tree-vectorize")))
void serial_execution() {
    for (int i = 0; i <= n; i++) {
        for (int j = 0; j <= n; j++) {
            result_serial[i + j] += (long long)pol1[i] * pol2[j];
        }
    }
}

// --- SIMD ΑΛΓΟΡΙΘΜΟΣ (AVX2) ---
void simd_execution() {
    for (int i = 0; i <= n; i++) {
        long long p1_scalar = pol1[i];
        
        // Μικρή βελτιστοποίηση: Αν ο συντελεστής είναι 0, δεν κάνουμε τίποτα
        if (p1_scalar == 0) continue;

        // Broadcast p1[i] σε όλα τα στοιχεία του vector (4 x 64-bit)
        __m256i vec_p1 = _mm256_set1_epi64x(p1_scalar);

        int j = 0;
        
        // Κύριος βρόχος - Επεξεργασία 4 στοιχείων τη φορά
        for (; j <= n - 3; j += 4) {
            // Φόρτωση 4 integers (32-bit) από το pol2
            // Χρησιμοποιούμε unaligned load (loadu) γιατί το j μπορεί να μην πέφτει πάντα σε 32-byte boundary
            __m128i p2_small = _mm_loadu_si128((__m128i const*)&pol2[j]);
            
            // Μετατροπή (expand) των 4 ints (32-bit) σε 4 long longs (64-bit)
            __m256i vec_p2 = _mm256_cvtepi32_epi64(p2_small);

            // Φόρτωση προηγούμενου αποτελέσματος από τον πίνακα result
            // Χρησιμοποιούμε loadu (unaligned) γιατί το i+j αλλάζει και χαλάει το alignment
            __m256i vec_res = _mm256_loadu_si256((__m256i const*)&result_simd[i + j]);

            // Πολλαπλασιασμός: (p1 * p2)
            // H mul_epi32 πολλαπλασιάζει τα low 32-bits κάθε 64-bit lane και βγάζει 64-bit αποτέλεσμα
            __m256i prod = _mm256_mul_epi32(vec_p1, vec_p2);

            // Πρόσθεση στο τρέχον αποτέλεσμα
            vec_res = _mm256_add_epi64(vec_res, prod);

            // Αποθήκευση πίσω στη μνήμη (Unaligned store)
            _mm256_storeu_si256((__m256i *)&result_simd[i + j], vec_res);
        }

        // Cleanup: Διαχείριση των υπολοίπων στοιχείων (αν n % 4 != 0)
        for (; j <= n; j++) {
            result_simd[i + j] += (long long)pol1[i] * pol2[j];
        }
    }
}

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <n>\n", argv[0]);
        return 1;
    }

    n = atoi(argv[1]);
    srand(time(NULL));

    // Allocation μεγέθους
    // Βάζουμε λίγο padding (+8) για να μην βγούμε εκτός ορίων με τα SIMD reads
    size_t size_pol = (n + 8) * sizeof(int);
    size_t size_res = (2 * n + 8) * sizeof(long long);

    // Χρησιμοποιούμε aligned memory allocation για καλύτερη απόδοση
    pol1 = allocate_aligned(size_pol);
    pol2 = allocate_aligned(size_pol);
    result_serial = allocate_aligned(size_res);
    result_simd = allocate_aligned(size_res);

    // Αρχικοποίηση αποτελεσμάτων σε 0
    // (Χρησιμοποιούμε loop αντί για memset για ασφάλεια με τα sizes)
    for(int k=0; k<=2*n + 4; k++) {
        result_serial[k] = 0;
        result_simd[k] = 0;
    }

    struct timespec start, end;

    // Initialization
    random_pol(n, pol1);
    random_pol(n, pol2);

    // --- SERIAL ---
    clock_gettime(CLOCK_MONOTONIC, &start);
    serial_execution();
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("Serial execution time: %.6f seconds\n", get_time_diff(start, end));

    // --- SIMD ---
    clock_gettime(CLOCK_MONOTONIC, &start);
    simd_execution();
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("SIMD execution time:   %.6f seconds\n", get_time_diff(start, end));

    // --- VERIFICATION ---
    int errors = 0;
    // Ελέγχουμε μέχρι 2*n
    for (int i = 0; i <= 2 * n; i++) {
        if (result_serial[i] != result_simd[i]) {
            errors++;
            if (errors == 1) printf("Error at index %d: Serial=%lld SIMD=%lld\n", i, result_serial[i], result_simd[i]);
        }
    }
    
    if (errors == 0) printf("Verification: SUCCESS\n");
    else printf("Verification: FAILED with %d errors\n", errors);

    free(pol1);
    free(pol2);
    free(result_serial);
    free(result_simd);

    return 0;
}