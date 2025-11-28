#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
//global variables
int thread_count;
int n;//iterations

int counter = 0;//counts how many threads have reached the barrier
pthread_mutex_t barrier_mutex;
pthread_cond_t barrier_cond;

int thread_cycle = 0; //it ensures the barrier is safely reusable without race conditions
//function ot measure time
double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

void barrier_wait(){
    //enter critical section
    pthread_mutex_lock(&barrier_mutex);
    int my_cycle = thread_cycle;//locally store which cycle the thread entered
    counter++;
    if (counter == thread_count){//last thread
        counter = 0;
        thread_cycle++;
        pthread_cond_broadcast(&barrier_cond);
    } else{
        //wait here only while the cycle hasn't changed
        while (my_cycle == thread_cycle){
            pthread_cond_wait(&barrier_cond, &barrier_mutex);}
    }
    //leave critical section
    pthread_mutex_unlock(&barrier_mutex);
    
}

void* thread_work(void* rank){
    long my_rank = (long) rank;
    (void)my_rank;//for unused variable warning
    for(int i = 0; i < n; i++) barrier_wait();

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
    //initialize mutex and condition variable
    pthread_mutex_init(&barrier_mutex, NULL);
    pthread_cond_init(&barrier_cond, NULL);
    //start measuring time
    clock_gettime(CLOCK_MONOTONIC, &start);
    //create threads
    for (long i = 0; i < thread_count; i++) {
        pthread_create(&thread_handles[i], NULL, thread_work, (void*)i);
    }
    //wait for threads to finish
    for (int i = 0; i < thread_count; i++) {
        pthread_join(thread_handles[i], NULL);
    }
    //stop measuring time
    clock_gettime(CLOCK_MONOTONIC, &end);
    //clean up
    pthread_mutex_destroy(&barrier_mutex);
    pthread_cond_destroy(&barrier_cond);
    //free memory
    free(thread_handles);
    printf("Time with the second way: %.6f seconds\n", get_time_diff(start, end));
    return 0;
}