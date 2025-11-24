#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

int *array0 ,*array1, *array2, *array3; 
int n;

struct array_stats_s {
 long long int info_array_0;
 long long int info_array_1;
 long long int info_array_2;
 long long int info_array_3;
} array_stats;

void *parallel_execution(void *rank){
    long my_rank = (long) rank;
    long long local_count = 0;

    if(my_rank == 0){
        for(int i = 0; i < n; i++){
            if(array0[i] != 0) array_stats.info_array_0++;
        }
        
    }

    else if(my_rank == 1){
        for(int i = 0; i < n; i++){
            if(array1[i] != 0) array_stats.info_array_1++;
        }
    }

    else if(my_rank == 2){
        for(int i = 0; i < n; i++){
            if(array2[i] != 0) array_stats.info_array_2++;
        }
        
    }

    else if(my_rank == 3){
        for(int i = 0; i < n; i++){
            if(array3[i] != 0) array_stats.info_array_3++;
        }
        
    }

    return NULL;

}

void serial_execution(long long *count0, long long *count1, long long *count2, long long *count3){
    *count0 = 0; *count1 = 0; *count2 = 0; *count3 = 0;

    for( int i = 0; i < n ; i++){
        if(array0[i] != 0 ) (*count0)++;
    }

    for( int i = 0; i < n ; i++){
        if(array1[i] != 0 ) (*count1)++;
    }

    for( int i = 0; i < n ; i++){
        if(array2[i] != 0 ) (*count2)++;
    }

    for( int i = 0; i < n ; i++){
        if(array3[i] != 0 ) (*count3)++;
    }

    
}

double get_time_diff(struct timespec start, struct timespec end) {
    // Η διαίρεση με το 1e9 (1.000.000.000) μετατρέπει τα nanoseconds σε δευτερόλεπτα
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(int argc, char*argv[]){
    if( argc != 2){
        printf("wrong input");
        return 1;
    }

    n = atoi(argv[1]);

    struct timespec start,end;

    //initialization
    clock_gettime(CLOCK_MONOTONIC, &start);
    

    array0 = malloc(n * sizeof(int));
    array1 = malloc(n * sizeof(int));
    array2 = malloc(n * sizeof(int));
    array3 = malloc(n * sizeof(int));

    if (!array0 || !array1 || !array2 || !array3) {
        printf("Memory allocation failed\n");
        return 1;
    }

    srand(time(NULL));
    for (int i = 0; i < n; i++) {
        array0[i] = rand() % 10;
        array1[i] = rand() % 10;
        array2[i] = rand() % 10;
        array3[i] = rand() % 10;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("initialization time: %.6f seconds\n", get_time_diff(start,end));

    array_stats.info_array_0 = 0; 
    array_stats.info_array_1 = 0;
    array_stats.info_array_2 = 0;
    array_stats.info_array_3 = 0;

    pthread_t thread_handles[4];
    //start of parallel execution
    clock_gettime(CLOCK_MONOTONIC, &start);

    for(long i = 0; i < 4; i++){
        pthread_create(&thread_handles[i], NULL, parallel_execution, (void*)i);
    }

    for(long i = 0; i < 4; i++){
        pthread_join(thread_handles[i], NULL);
    }
    //end of parallel execution
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("parallel execution time: %.6f seconds\n", get_time_diff(start, end));


    printf("results with parallel execution: %lld, %lld, %lld, %lld\n", array_stats.info_array_0, array_stats.info_array_1, array_stats.info_array_2, array_stats.info_array_3);
    
    long long count0, count1, count2, count3;
    //start of serial execution
    clock_gettime(CLOCK_MONOTONIC, &start);

    serial_execution(&count0, &count1, &count2, &count3);

    //end of serial execution
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("serial execution time: %.6f seconds\n", get_time_diff(start, end));
    printf("results with serial executiion: %lld, %lld, %lld, %lld\n", count0, count1, count2, count3);

    if (array_stats.info_array_0 == count0 && 
        array_stats.info_array_1 == count1 &&
        array_stats.info_array_2 == count2 && 
        array_stats.info_array_3 == count3) {
        
        printf("Verification: SUCCESS (Results match)\n");
    } else {
        printf("Verification: FAILED (Results do NOT match)\n");
    }

    free(array0);
    free(array1);
    free(array2);
    free(array3);

    return 0;
}