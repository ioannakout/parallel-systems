#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
//global variables
int thread_count;
int n;//number od iterations

int counter = 0;//counter to track how many threads have arrived at the barrier so far.
volatile int shared_flag = 0;//helps with busy-waiting, 
pthread_mutex_t barrier_mutex;

//function ot measure time
double get_time_diff(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

void barrier_wait(int *local_flag){
    //toggle the local sense for the current phase (wikipedia)
    *local_flag = !(*local_flag);
    //enter critical section to update the counter
    pthread_mutex_lock(&barrier_mutex);
    counter++;

    if (counter == thread_count) {
        //last thread to arrive
        counter = 0;  //reset fro the next barrier
        pthread_mutex_unlock(&barrier_mutex);
        shared_flag = *local_flag; //update shared_flag to match local_flag
    }else{
        //not the last thread
        pthread_mutex_unlock(&barrier_mutex);

        // busy waiting
        while (shared_flag != *local_flag);
    }
}


void* Thread_work(void* rank) {
    long my_rank = (long) rank;
    (void)my_rank;//for unused variable warning
    int flag = 0; //initialize local sense flag

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
    //initialize global variables and mutex
    counter = 0;
    shared_flag = 0;
    pthread_mutex_init(&barrier_mutex, NULL);
    //start measuring time
    clock_gettime(CLOCK_MONOTONIC, &start);
    //create threads
    for (thread = 0; thread < thread_count; thread++) {
        pthread_create(&thread_handles[thread], NULL, Thread_work, (void*) thread);
    }
    //wait for threads to finish
    for (thread = 0; thread < thread_count; thread++) {
        pthread_join(thread_handles[thread], NULL);
    }
    //stop measuring time
    clock_gettime(CLOCK_MONOTONIC, &end);
    //clean up
    pthread_mutex_destroy(&barrier_mutex);
    free(thread_handles);
    printf("Time with the trird way: %.6f seconds\n", get_time_diff(start, end));
    return 0;

}