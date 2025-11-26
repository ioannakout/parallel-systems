#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

//global variables
int *pol1 , *pol2;
long long *result_serial, *result_parallel;
long thread_count;//number of threads
int n ; //degree of the polynomial
long long **local_results;

//creates random coefficients
int random_coef(){
    int r = rand()%10 + 1;//%10 for smalles numbers
    if(rand()%2 == 1) r = -r ;
    return r;
}
//creates a random polynomial with the previous randoms coefficients
void random_pol(int degree,int *pol){
    for( int i = 0; i <= degree; i++){
        pol[i]= random_coef();
    }   
}

void serial_execution(){
    for(int i = 0; i <= n; i++){
        for(int j = 0; j <= n; j++){
            result_serial[i +j] +=(long long)pol1[i] * pol2[j];
        }
    }
}

void* parallel_execution(void* rank ) {
    long my_rank = (long) rank;//gets thread number
    int total_elements = n + 1;//total number of coefficients

    //distribution among the threads
    int my_start =( my_rank * total_elements) / thread_count;
    int my_end = (my_rank + 1) * total_elements / thread_count;
    
    //for avoiding race conditions
    long long* local_result = local_results[my_rank];

    for(int i = my_start; i < my_end; i ++){
        for( int j = 0; j <= n; j++){
            
            local_result[i + j] +=(long long) pol1[i] * pol2[j];
        }
    }
    return NULL;
}
//function to measure time
double get_time_diff(struct timespec start, struct timespec end) {
    
    return (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
}


int main(int argc, char *argv[]){
    if(argc != 3) {
        printf("Wrong input");
        return 1;
    }

    n = atoi(argv[1]);
    thread_count = strtol(argv[2], NULL, 10);
    srand(time(NULL));//random number generator
    
    //alocate memory
    pol1 = malloc((n+1)*sizeof(int));
    pol2 = malloc((n+1)*sizeof(int));
    result_serial = calloc((2*n + 1 ),sizeof(long long));//calloc for initialization to 0
    result_parallel = calloc((2*n + 1),sizeof(long long));

    struct timespec start,end;
    //initialization starts
    clock_gettime(CLOCK_MONOTONIC, &start);

    random_pol(n, pol1);
    random_pol(n, pol2);

            
    pthread_t* thread_handles;
    thread_handles = malloc(thread_count*sizeof(pthread_t));

    local_results = malloc(thread_count * sizeof(long long*));
    for(long i = 0; i < thread_count; i++){
        local_results[i] = calloc(2*n + 1, sizeof(long long));
    }
    //initialization ends
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("initialization time: %.6f seconds\n", get_time_diff(start, end));

    clock_gettime(CLOCK_MONOTONIC, &start); //serial execution
    serial_execution();
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("serial execution time: %.6f seconds\n", get_time_diff(start, end));

    //start of parallel execution
    clock_gettime(CLOCK_MONOTONIC, &start);

    //create threads
    for(long i = 0; i < thread_count; i++){
        pthread_create(&thread_handles[i], NULL, parallel_execution, (void*)i);
    }
    //wait for threads to finish
    for(long i = 0; i < thread_count; i ++){
        pthread_join(thread_handles[i], NULL);
    }
    //sum local results into the global array
    for(int i = 0; i <= 2*n; i++){
        for(long j = 0; j < thread_count; j++){
            result_parallel[i] += local_results[j][i];
        }
    }
    //end of parallel execution
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("parallel execution time: %.6f seconds\n", get_time_diff(start, end));

    //verification
    int errors = 0;
    for (int i = 0; i <= 2 * n; i++) {
        if (result_serial[i] != result_parallel[i]) {
            errors++;
            if (errors == 1) printf("first error at index %d: Serial=%lld, Parallel=%lld\n", i, result_serial[i], result_parallel[i]);
        }
    }
    if (errors == 0) printf("no errors \n");
    else printf("failed with %d errors.\n", errors);
    
    //free allocates memory
    for (long t = 0; t < thread_count; t++) free(local_results[t]);
    free(local_results);
    free(thread_handles);
    free(pol1);
    free(pol2);
    free(result_serial);
    free(result_parallel);
    
    return 0;
}