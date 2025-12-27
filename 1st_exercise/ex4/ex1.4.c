// bank_sim.c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <string.h>
#include <stdint.h>

// Provide readability
typedef long long LL;

// Array of acounts and it's size
LL *accounts = NULL;
LL n = 0;

// Mutual-Exclusion Locks
pthread_mutex_t mutex;
pthread_mutex_t *account_mutexes = NULL;

// Read-Write Locks
pthread_rwlock_t rwlock;
pthread_rwlock_t *account_rwlocks = NULL;

// The initial total and the number of transactions per thread
LL initialTotal = 0;
LL transactionPerThread = 0;

// Number of threads, percentage of transactions that are
// 0 coarse mutex, 1 fine mutex, 2 coarse rw, 3 fine rw
long threadCount;
int percentageRead = 50;
int mode = 0; // 0 coarse mutex, 1 fine mutex, 2 coarse rw, 3 fine rw
int read_work_us = 0; // microseconds sleep after read

// Timer help function
double time_diff(struct timespec a, struct timespec b) {
    return (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
}

// thread-safe rand: using rand_r with per-thread seed
unsigned int thread_rand(unsigned int *seedp) {
    return rand_r(seedp);
}

// Executing the different locks based on mode
static void lock_account_for_write(size_t idx1, size_t idx2) {
    if (mode == 0) {
        pthread_mutex_lock(&mutex);
    } else if (mode == 1) {
        // lock in index order to avoid deadlock
        if (idx1 == idx2) {
            pthread_mutex_lock(&account_mutexes[idx1]);
        } else {
            size_t a = idx1 < idx2 ? idx1 : idx2;
            size_t b = idx1 < idx2 ? idx2 : idx1;
            pthread_mutex_lock(&account_mutexes[a]);
            pthread_mutex_lock(&account_mutexes[b]);
        }
    } else if (mode == 2) {
        pthread_rwlock_wrlock(&rwlock);
    } else if (mode == 3) {
        if (idx1 == idx2) {
            pthread_rwlock_wrlock(&account_rwlocks[idx1]);
        } else {
            size_t a = idx1 < idx2 ? idx1 : idx2;
            size_t b = idx1 < idx2 ? idx2 : idx1;
            pthread_rwlock_wrlock(&account_rwlocks[a]);
            pthread_rwlock_wrlock(&account_rwlocks[b]);
        }
    } else {
        fprintf(stderr, "Uninitialized mode, [0-3] needed\n");
        exit(1);
    }
}

static void unlock_account_for_write(size_t idx1, size_t idx2) {
    if (mode == 0) {
        pthread_mutex_unlock(&mutex);
    } else if (mode == 1) {
        if (idx1 == idx2) {
            pthread_mutex_unlock(&account_mutexes[idx1]);
        } else {
            size_t a = idx1 < idx2 ? idx1 : idx2;
            size_t b = idx1 < idx2 ? idx2 : idx1;
            pthread_mutex_unlock(&account_mutexes[b]);
            pthread_mutex_unlock(&account_mutexes[a]);
        }
    } else if (mode == 2) {
        pthread_rwlock_unlock(&rwlock);
    } else {
        if (idx1 == idx2) {
            pthread_rwlock_unlock(&account_rwlocks[idx1]);
        } else {
            size_t a = idx1 < idx2 ? idx1 : idx2;
            size_t b = idx1 < idx2 ? idx2 : idx1;
            pthread_rwlock_unlock(&account_rwlocks[b]);
            pthread_rwlock_unlock(&account_rwlocks[a]);
        }
    } // No reason to check incorrect mode,
      // would have already exited program
}

static void lock_account_for_read(size_t idx) {
    if (mode == 0) {
        pthread_mutex_lock(&mutex);
    } else if (mode == 1) {
        pthread_mutex_lock(&account_mutexes[idx]);
    } else if (mode == 2) {
        pthread_rwlock_rdlock(&rwlock);
    } else if (mode == 3) {
        pthread_rwlock_rdlock(&account_rwlocks[idx]);
    } else {
        fprintf(stderr, "Uninitialized mode, [0-3] needed\n");
        exit(1);
    }
}

static void unlock_account_for_read(size_t idx) {
    if (mode == 0) {
        pthread_mutex_unlock(&mutex);
    } else if (mode == 1) {
        pthread_mutex_unlock(&account_mutexes[idx]);
    } else if (mode == 2) {
        pthread_rwlock_unlock(&rwlock);
    } else {
        pthread_rwlock_unlock(&account_rwlocks[idx]);
    }
}

// The thread function
void *thread_func(void *thread) {
    long my_thread = (long) thread;
    unsigned int seed = (unsigned int) time(NULL) ^ (unsigned int) (my_thread * 1103515245);

    LL local_sum_reads = 0;

    for (LL iterator = 0; iterator < transactionPerThread; iterator++) {
        // pick read or write
        int is_read = (thread_rand(&seed) % 100) < percentageRead;

        if (is_read) {
            size_t idx = thread_rand(&seed) % n;
            // lock for read
            lock_account_for_read(idx);
            LL val = accounts[idx];
            // simulate extra work inside critical section if requested
            if (read_work_us > 0) {
                // sleep a few microseconds to enlarge critical region
                usleep(read_work_us);
            } else {
                // small CPU work (cheap)
                val = val * 1 - 0; // no-op but prevents optimizing away
            }
            local_sum_reads += val;
            unlock_account_for_read(idx);
        } else {
            // transfer
            size_t a = thread_rand(&seed) % n;
            size_t b = thread_rand(&seed) % n;
            while (b == a && n > 1) {
                b = thread_rand(&seed) % n;
            }
            // choose amount 1..100
            LL amount = (thread_rand(&seed) % 100) + 1;

            // lock involved accounts
            lock_account_for_write(a, b);

            // do transfer
            accounts[a] -= amount;
            accounts[b] += amount;

            unlock_account_for_write(a, b);
        }
    }

    // optional: you could return local_sum_reads in heap, but we don't need it now
    return NULL;
}

// Initialize 
void init_accounts(size_t n) {
    accounts = malloc(sizeof(LL) * n);
    if (!accounts) {
        perror("malloc accounts");
        exit(EXIT_FAILURE);
    }
    for (size_t i = 0; i < n; ++i) {
        // random initial balance 0..999
        accounts[i] = (LL) (rand() % 1000);
        initialTotal += accounts[i];
    }
}

void free_locks() {
    if (account_mutexes) {
        for (size_t i = 0; i < n; ++i)
            pthread_mutex_destroy(&account_mutexes[i]);
        free(account_mutexes);
    }
    if (account_rwlocks) {
        for (size_t i = 0; i < n; ++i)
            pthread_rwlock_destroy(&account_rwlocks[i]);
        free(account_rwlocks);
    }
    pthread_mutex_destroy(&mutex);
    pthread_rwlock_destroy(&rwlock);
}

int main(int argc, char **argv) {

    if (argc < 6) 
        exit(EXIT_FAILURE);
    
    // Number of accounts
    n = (size_t) atol(argv[1]);

    // Number of transactions per thread
    transactionPerThread = atoll(argv[2]);

    // Percentage of transactions that read
    percentageRead = atoi(argv[3]);
    mode = atoi(argv[4]);
    threadCount = atol(argv[5]);

    if (argc >= 7) read_work_us = atoi(argv[6]);

    if (n < 1 || transactionPerThread < 0 || percentageRead < 0 || percentageRead > 100 || mode < 0 || mode > 3 || threadCount < 1)
        exit(EXIT_FAILURE);

    // Reset time for rand
    srand((unsigned) time(NULL));

    // initialize locks as needed
    pthread_mutex_init(&mutex, NULL);
    pthread_rwlock_init(&rwlock, NULL);

    if (mode == 1) {
        account_mutexes = malloc(sizeof(pthread_mutex_t) * n);
        if (!account_mutexes) 
            exit(EXIT_FAILURE);

        for (size_t i = 0; i < n; ++i)
            pthread_mutex_init(&account_mutexes[i], NULL);

    } else if (mode == 3) {
        account_rwlocks = malloc(sizeof(pthread_rwlock_t) * n);
        if (!account_rwlocks) { perror("malloc"); exit(EXIT_FAILURE); }
        for (size_t i = 0; i < n; ++i)
            pthread_rwlock_init(&account_rwlocks[i], NULL);
    }

    init_accounts(n);

    printf("Configuration:\n");
    printf("  accounts = %lld\n", n);
    printf("  tx/thread = %lld\n", transactionPerThread);
    printf("  read %% = %d\n", percentageRead);
    printf("  mode = %d (%s)\n", mode,
           mode==0? "coarse-mutex" : mode==1? "fine-mutex" : mode==2? "coarse-rw" : "fine-rw");
    printf("  threads = %ld\n", threadCount);
    printf("  read_work_us = %d\n", read_work_us);
    printf("Initial total balance = %lld\n", initialTotal);

    pthread_t *threads = malloc(sizeof(pthread_t) * threadCount);
    if (!threads) { perror("malloc threads"); exit(EXIT_FAILURE); }

    struct timespec tstart, tend;
    clock_gettime(CLOCK_MONOTONIC, &tstart);

    for (long i = 0; i < threadCount; ++i) {
        int rc = pthread_create(&threads[i], NULL, thread_func, (void *) i);
        if (rc != 0) {
            fprintf(stderr, "pthread_create failed: %d\n", rc);
            exit(EXIT_FAILURE);
        }
    }

    for (long i = 0; i < threadCount; ++i) {
        pthread_join(threads[i], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &tend);

    // compute final total
    LL final_total = 0;
    for (size_t i = 0; i < n; ++i) final_total += accounts[i];

    printf("Final total balance = %lld\n", final_total);
    if (final_total == initialTotal) {
        printf("Verification: SUCCESS (total preserved)\n");
    } else {
        printf("Verification: FAILED (total changed)\n");
    }

    printf("Elapsed time: %.6f seconds\n", time_diff(tstart, tend));

    // cleanup
    free(threads);
    free(accounts);
    free_locks();

    return 0;
}
