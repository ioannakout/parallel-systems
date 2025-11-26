#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

int thread_count;
int n;

int counter = 0;
volatile int shared_flag = 0;
pthread_mutex_t barrier_mutex;

double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

void barrier_wait(int *local_flag){
    //"local_sense's value is toggled", wikipedia
    *local_flag = !(*local_flag);

    pthread_mutex_lock(&barrier_mutex);
    counter++;

    if (counter == thread_count) {
        
        counter = 0;  
        pthread_mutex_unlock(&barrier_mutex);
        shared_flag = *local_flag; 
    }else{
        
        pthread_mutex_unlock(&barrier_mutex);

        // busy waiting
        // Wikipedia: "threads will keep waiting with the condition that the flag... is not equal to local_sense"
        while (shared_flag != *local_flag);
    }
}


void* Thread_work(void* rank) {
    long my_rank = (long) rank;
    int flag = 0; 

    for (int i = 0; i < n; i++)  barrier_wait(&flag);
        
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
    long thread;
    struct timespec start, end;

    counter = 0;
    shared_flag = 0;
    pthread_mutex_init(&barrier_mutex, NULL);

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (thread = 0; thread < thread_count; thread++) {
        pthread_create(&thread_handles[thread], NULL, Thread_work, (void*) thread);
    }

    for (thread = 0; thread < thread_count; thread++) {
        pthread_join(thread_handles[thread], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    pthread_mutex_destroy(&barrier_mutex);
    free(thread_handles);
    printf("Time with the trird way: %.6f seconds\n", get_time_diff(start, end));
    return 0;

}