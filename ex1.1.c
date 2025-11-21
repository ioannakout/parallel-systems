#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

int *pol1 , *pol2, *result_serial, *result_parallel;
long thread_count;
int n ; //βαθμος πολυωνυμου
int **local_results;

int random_coef(){
    int r = rand() + 1;
    if(rand()%2 == 1) r = -r ;
    return r;
}

void random_pol(int degree,int *pol){
    for( int i = 0; i <= degree; i++){
        pol[i]= random_coef();
    }   
}

void serial_execution(){
    for(int i = 0; i <= n; i++){
        for(int j = 0; j <= n; j++){
            result_serial[i +j] += pol1[i] * pol2[j];
        }
    }

    
}

void* parallel_execution(void* rank ) {
    long my_rank = (long) rank;
    
    int local_n = (n + 1) / thread_count;
    int my_start = my_rank * local_n;
    int my_end = my_start + local_n - 1;
    if (my_end > n) my_end = n;

    int* local_result = local_results[my_rank];

    for(int i = my_start; i <= my_end; i ++){
        for( int j = 0; j <= n; j++){
            
            local_result[i + j] += pol1[i] * pol2[j];
        }
    }
    return NULL;
}


int main(int argc, char *argv[]){
    if(argc != 3) {
        printf("Wrong input");
        return 1;
    }

    n = atoi(argv[1]);
    thread_count = strtol(argv[2], NULL, 10);
    

    pol1 = malloc((n+1)*sizeof(int));
    pol2 = malloc((n+1)*sizeof(int));
    result_serial = calloc((2*n + 1 ),sizeof(int));
    result_parallel = calloc((2*n + 1),sizeof(int));

    random_pol(n, pol1);
    random_pol(n, pol2);

    if( thread_count == 0) serial_execution();
    else{
            pthread_t* thread_handles;
            thread_handles = malloc(thread_count*sizeof(pthread_t));

            local_results = malloc(thread_count * sizeof(int*));
            for(long i = 0; i < thread_count; i++){
                local_results[i] = calloc(2*n + 1, sizeof(int));
            }

            for(long i = 0; i < thread_count; i++){
                pthread_create(&thread_handles[i], NULL, parallel_execution, (void*)i);
            }

            for(long i = 0; i < thread_count; i ++){
                pthread_join(thread_handles[i], NULL);
            }

            for(int i = 0; i <= 2*n; i++){
                for(long t = 0; t < thread_count; t++){
                    result_parallel[i] += local_results[t][i];
                }
            }
            for(long t = 0; t < thread_count; t++) free(local_results[t]);
            
            printf("the result with serial execution:\n");
            for(int i = 0; i <= 2*n; i++ ){
                printf("%d", result_serial[i]);
            }
            printf("\n");

            printf("the result with parallel execution:\n");
            for(int i = 0; i <=2*n; i++){
                printf("%d", result_parallel[i]);
            }
            printf("\n");
            free(local_results);
            free(thread_handles);

        }
    free(pol1);
    free(pol2);
    free(result_serial);
    free(result_parallel);
    
    return 0;
}