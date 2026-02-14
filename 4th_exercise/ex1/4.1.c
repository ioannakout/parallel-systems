#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <immintrin.h> // Header για AVX εντολές

// Global μεταβλητές
int *pol1, *pol2;
long long *result_serial, *result_simd;
int n; // Βαθμός του πολυωνύμου

// Δημιουργία τυχαίων συντελεστών
int random_coef() {
    int r = rand() % 10 + 1;
    if (rand() % 2 == 1) r = -r;
    return r;
}

// Αρχικοποίηση πολυωνύμου
void random_pol(int degree, int *pol) {
    for (int i = 0; i <= degree; i++) {
        pol[i] = random_coef();
    }
}

// Κλασικός Σειριακός Αλγόριθμος
void serial_execution() {
    for (int i = 0; i <= n; i++) {
        for (int j = 0; j <= n; j++) {
            result_serial[i + j] += (long long)pol1[i] * pol2[j];
        }
    }
}

// Διανυσματικός Σειριακός Αλγόριθμος (SIMD - AVX2)
void simd_execution() {
    for (int i = 0; i <= n; i++) {
        // Broadcast την τιμή του pol1[i] σε ένα vector 256-bit (4 x 64-bit integers)
        // Μετατροπή σε long long για να ταιριάζει με το αποτέλεσμα
        long long p1_scalar = pol1[i];
        
        // Μικρή βελτιστοποίηση: αν το p1 είναι 0, παρακάμπτουμε τη λούπα
        if (p1_scalar == 0) continue;

        __m256i vec_p1 = _mm256_set1_epi64x(p1_scalar);

        int j = 0;
        // Κύριος βρόχος SIMD: Επεξεργασία ανά 4 στοιχεία
        // Σταματάμε στο n-3 για να είμαστε σίγουροι ότι έχουμε 4 στοιχεία να διαβάσουμε
        for (; j <= n - 3; j += 4) {
            
            // Φόρτωση 4 integers (32-bit) από το pol2 (unaligned load)
            __m128i p2_small = _mm_loadu_si128((__m128i const*)&pol2[j]);
            
            // Μετατροπή (expansion) των 4 ints σε 4 long longs (64-bit) στο AVX register
            __m256i vec_p2 = _mm256_cvtepi32_epi64(p2_small);

            // Φόρτωση των τρεχόντων αποτελεσμάτων από τον πίνακα result_simd
            __m256i vec_res = _mm256_loadu_si256((__m256i const*)&result_simd[i + j]);

            // Πολλαπλασιασμός: (pol1[i] * pol2[j...j+3])
            // Η _mm256_mul_epi32 πολλαπλασιάζει τα χαμηλά 32-bit κάθε 64-bit lane
            // και παράγει 64-bit αποτέλεσμα. Επειδή κάναμε cvtepi32_epi64, τα δεδομένα μας
            // είναι σωστά τοποθετημένα για αυτή την εντολή.
            __m256i prod = _mm256_mul_epi32(vec_p1, vec_p2);

            // Πρόσθεση στο υπάρχον αποτέλεσμα
            vec_res = _mm256_add_epi64(vec_res, prod);

            // Αποθήκευση πίσω στη μνήμη
            _mm256_storeu_si256((__m256i *)&result_simd[i + j], vec_res);
        }

        // Cleanup loop: Διαχείριση των υπολοίπων στοιχείων (αν n δεν διαιρείται ακριβώς με το 4)
        for (; j <= n; j++) {
            result_simd[i + j] += (long long)pol1[i] * pol2[j];
        }
    }
}

// Συνάρτηση μέτρησης χρόνου
double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char *argv[]) {
    if (argc != 2) { // Αλλαγή: χρειαζόμαστε μόνο το n
        printf("Usage: %s <polynomial_degree_n>\n", argv[0]);
        return 1;
    }

    n = atoi(argv[1]);
    srand(time(NULL));

    // Allocation
    // Χρησιμοποιούμε malloc, αλλά για καλύτερη απόδοση SIMD θα μπορούσαμε να χρησιμοποιήσουμε aligned_alloc
    // Εδώ χρησιμοποιούμε unaligned loads/stores για απλότητα συμβατή με τον προηγούμενο κώδικα.
    pol1 = malloc((n + 1) * sizeof(int));
    pol2 = malloc((n + 1) * sizeof(int));
    result_serial = calloc((2 * n + 1), sizeof(long long));
    result_simd = calloc((2 * n + 1), sizeof(long long));

    struct timespec start, end;

    // --- INITIALIZATION ---
    clock_gettime(CLOCK_MONOTONIC, &start);
    random_pol(n, pol1);
    random_pol(n, pol2);
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("Initialization time: %.6f seconds\n", get_time_diff(start, end));

    // --- SERIAL EXECUTION ---
    clock_gettime(CLOCK_MONOTONIC, &start);
    serial_execution();
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("Serial execution time: %.6f seconds\n", get_time_diff(start, end));

    // --- SIMD EXECUTION ---
    clock_gettime(CLOCK_MONOTONIC, &start);
    simd_execution();
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("SIMD execution time:   %.6f seconds\n", get_time_diff(start, end));

    // --- VERIFICATION ---
    int errors = 0;
    for (int i = 0; i <= 2 * n; i++) {
        if (result_serial[i] != result_simd[i]) {
            errors++;
            if (errors == 1) 
                printf("First error at index %d: Serial=%lld, SIMD=%lld\n", i, result_serial[i], result_simd[i]);
        }
    }
    
    if (errors == 0) 
        printf("Verification SUCCESS: Serial and SIMD results match.\n");
    else 
        printf("Verification FAILED with %d errors.\n", errors);

    // Free memory
    free(pol1);
    free(pol2);
    free(result_serial);
    free(result_simd);

    return 0;
}