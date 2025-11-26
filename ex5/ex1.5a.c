#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

int thread_count;
int n;

pthread_barrier_t barrier;
double get_time_diff(struct timespec start, struct timespec end) {
    // Η διαίρεση με το 1e9 (1.000.000.000) μετατρέπει τα nanoseconds σε δευτερόλεπτα
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

void* Thread_work(void* rank){
    long my_rank = (long) rank;

    for(int i = 0; i < n; i++){
        int result = pthread_barrier_wait(&barrier);
    }

    return NULL;
}

int main(int argc, char* argv[]){
    if(argc != 3){
        printf("wrong input");
        return 1;
    }

    thread_count = atoi(argv[1]);
    n = atoi(argv[2]);

    pthread_t* thread_handles = malloc(thread_count * sizeof(pthread_t));

    struct timespec start, end;

    pthread_barrier_init(&barrier, NULL, thread_count);
    printf("threads : %d , repeats: %d \n",thread_count, n );

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (long i = 0; i < thread_count; i++) {
        pthread_create(&thread_handles[i], NULL, Thread_work, (void*)i);
    }

    for (int i = 0; i < thread_count; i++) {
        pthread_join(thread_handles[i], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    pthread_barrier_destroy(&barrier);

    free(thread_handles);
    printf("Time with the first way: %.6f seconds\n", get_time_diff(start, end));
    return 0;

}