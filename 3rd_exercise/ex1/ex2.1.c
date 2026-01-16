#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <omp.h>

//global variables
int *pol1 , *pol2;
long long *result_serial, *result_parallel;
long thread_count; //number of threads
int n ; //degree of the polynomial


//creates random coefficients
int random_coef(){
    int r = rand()%10 + 1;  //%10 for smallest numbers
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
    for (int i = 0; i <= 2 * n; i++) result_serial[i] = 0;

    for(int i = 0; i <= n; i++){
        for(int j = 0; j <= n; j++){
            result_serial[i +j] +=(long long)pol1[i] * pol2[j];
        }
    }
}

void parallel_execution(){
    #pragma omp parallel for num_threads((int)thread_count)\
        default(none) shared(pol1, pol2, result_parallel, n)\
        schedule(static)
    for(int j = 0; j <= 2*n; j++){
        long long sum = 0;  //local sum for each thread

        //find the correct start and end for the loop
        int start = (j > n) ? j - n : 0;
        int end = (j < n) ? j : n;

        for (int i = start; i <= end; i++) {
            sum += (long long)pol1[i] * (long long)pol2[j - i];
        }
        
        
        result_parallel[j] = sum;
    }
}

int main(int argc, char* argv[]){

    if(argc != 3) {
        printf("Wrong input\n");
        return 1;
    }
    //add a check for negative numbers
    n = atoi(argv[1]);
    thread_count = strtol(argv[2], NULL, 10);

    if (n <= 0 || thread_count <= 0) {
        printf("error\n");
        return 1;
    }

    //allocate memory
    double start_alloc = omp_get_wtime(); //measuring time for allocation for all required arrays
    pol1 = malloc((n+1)*sizeof(int));
    pol2 = malloc((n+1)*sizeof(int));
    result_serial = calloc((2*n + 1 ),sizeof(long long));
    result_parallel = calloc((2*n + 1),sizeof(long long));
    //check if memory failed
    if (!pol1 || !pol2 || !result_serial || !result_parallel) {
        printf("memory allocation failed\n");
        return 1;
    }

    double end_alloc = omp_get_wtime();
    double time_alloc = end_alloc - start_alloc;
    printf("allocation time of pol1, pol2, result_serial and result_parallel: %f seconds\n", time_alloc);

    

    srand(time(NULL));
    //create polynomials
    double start_pol = omp_get_wtime();
    random_pol(n, pol1);
    random_pol(n, pol2);
    double end_pol = omp_get_wtime();
    double time_pol = end_pol - start_pol;
    printf("initialization time of polynomials: %f seconds\n", time_pol);

    //measuring time in serial execution
    double start_serial = omp_get_wtime();
    serial_execution();
    double end_serial = omp_get_wtime();
    double time_serial = end_serial - start_serial;
    printf("serial time: %f seconds\n", time_serial);

    // measuring time in parallel execution
    double start_parallel = omp_get_wtime();
    parallel_execution();
    double end_parallel = omp_get_wtime();
    double time_parallel = end_parallel - start_parallel;
    printf("parallel time: %f seconds\n", time_parallel);

    //correctness check
    int correct = 1;
    for (int i = 0; i <= 2 * n; i++) {
        if (result_serial[i] != result_parallel[i]) {
            correct = 0;
            break;
        }
    }
    printf("verification: %s\n", correct ? "SUCCESS" : "FAILED");

    //free memory
    free(pol1); 
    free(pol2); 
    free(result_serial); 
    free(result_parallel);
    return 0;
}