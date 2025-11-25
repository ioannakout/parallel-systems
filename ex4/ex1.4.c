#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

long n;
long transactionPerThread;
long m;
long k;
int threadCount;
pthread_mutex_t mutex;
pthread_rwlock_t rwlock;

int main(int argc, char* argv[]) {
    if (argv != 5)
        exit(1);

    n = strtol(argv[1], NULL, 10);
    transactionPerThread = strtol(argv[2], NULL, 10);
    m = strtol(argv[3], NULL, 10);
    k = strtol(argv[4], NULL, 10);

    long* jointAccount = malloc(n * sizeof(long));
    pthread_mutex_init(&mutex, NULL);



    pthread_mutex_destroy(&mutex);
}