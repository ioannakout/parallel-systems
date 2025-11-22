#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

// Καθολικές μεταβλητές
long long shared_counter = 0;
long thread_count;
long long iterations;

// Μηχανισμοί Συγχρονισμού
pthread_mutex_t mutex;
pthread_rwlock_t rwlock;

// --- Βοηθητική συνάρτηση χρονομέτρησης ---
double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

// --- Προσέγγιση 1: Mutex ---
void* Thread_Mutex(void* rank) {
    for (long long i = 0; i < iterations; i++) {
        pthread_mutex_lock(&mutex);
        shared_counter++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

// --- Προσέγγιση 2: Read-Write Lock ---
void* Thread_RWLock(void* rank) {
    for (long long i = 0; i < iterations; i++) {
        pthread_rwlock_wrlock(&rwlock); 
        shared_counter++;
        pthread_rwlock_unlock(&rwlock);
    }
    return NULL;
}

// --- Προσέγγιση 3: Atomic Operations ---
void* Thread_Atomic(void* rank) {
    for (long long i = 0; i < iterations; i++) {
        // Χρήση GCC built-in για ατομική πρόσθεση
        __atomic_fetch_add(&shared_counter, 1, __ATOMIC_SEQ_CST);
    }
    return NULL;
}

void run_test(char* name, void* (*thread_func)(void*)) {
    pthread_t* handles = malloc(thread_count * sizeof(pthread_t));
    struct timespec start, end;
    
    // Επαναφορά μετρητή
    shared_counter = 0;

    // Έναρξη χρονομέτρησης
    clock_gettime(CLOCK_MONOTONIC, &start);

    // Δημιουργία νημάτων
    for (long i = 0; i < thread_count; i++) {
        pthread_create(&handles[i], NULL, thread_func, (void*)i);
    }

    // Αναμονή νημάτων
    for (long i = 0; i < thread_count; i++) {
        pthread_join(handles[i], NULL);
    }

    // Λήξη χρονομέτρησης
    clock_gettime(CLOCK_MONOTONIC, &end);

    printf("[%-10s] Τελική Τιμή: %lld (Στόχος: %lld) | Χρόνος: %.4f sec\n", 
           name, shared_counter, (long long)thread_count * iterations, get_time_diff(start, end));

    free(handles);
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        printf("Χρήση: %s <αριθμός_νημάτων> <επαναλήψεων_ανά_νήμα>\n", argv[0]);
        return 1;
    }

    thread_count = strtol(argv[1], NULL, 10);
    iterations = strtoll(argv[2], NULL, 10);

    printf("--- Ρυθμίσεις: %d Νήματα, %lld Επαναλήψεις/Νήμα ---\n", thread_count, iterations);

    // Αρχικοποίηση κλειδωμάτων
    pthread_mutex_init(&mutex, NULL);
    pthread_rwlock_init(&rwlock, NULL);

    // Εκτέλεση των 3 test
    run_test("Mutex", Thread_Mutex);
    run_test("RWLock", Thread_RWLock);
    run_test("Atomic", Thread_Atomic);

    // Καθαρισμός
    pthread_mutex_destroy(&mutex);
    pthread_rwlock_destroy(&rwlock);

    return 0;
}