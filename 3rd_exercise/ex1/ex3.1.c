#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <mpi.h>

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

int main(int argc, char* argv[]){

    int my_rank, comm_sz;
    int n;
    int local_n;

    int *A = NULL;               // Full A (Rank 0 only)
    int *B = NULL;               // Full B (Everyone)
    long long *C = NULL;         // Result (Rank 0 only)
    int *local_A = NULL;         // Part of A that the process processed
    long long *local_C = NULL;   //Part of process's result
    int *elements = NULL;      // Counts for scatter
    int *index = NULL;

    

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);

    if (argc != 2) {
        if (my_rank == 0) printf("Usage: %s <degree_n>\n", argv[0]);
        MPI_Finalize();
        return 1;
    }

    n = atoi(argv[1]);  // polynomial degre
    int coeffs = n + 1;  // for a n-degree polynomial has n +1 coeffs
    int results = 2 * n + 1;

    // Allocate global arrays
    elements = malloc(comm_sz * sizeof(int));
    index = malloc(comm_sz * sizeof(int));
   
    B = malloc(coeffs * sizeof(int));

    //check if memory failed
    if ( !elements|| !index || !B ) {
        printf("memory allocation failed\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
        
    }

    // Calculate distribution
    int remainder = coeffs % comm_sz;
    int sum = 0;

    for (int i = 0; i < comm_sz; i++) {
        elements[i] = coeffs / comm_sz; // Basic share
        if (i < remainder) elements[i]++; 
        index[i] = sum;    
        sum += elements[i];
    }

    local_n = elements[my_rank];

    // Allocate local arrays
    local_A = malloc(local_n * sizeof(int));
    local_C = calloc(results, sizeof(long long)); // We use calloc to initialize array with 0, which is required for the += operator later
    
    //check if memory failed
    if (!local_A || !local_C) {
        printf("memory allocation failed\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
        
    }
    // Rank 0 inits data
    if (my_rank == 0) {
        A = malloc(coeffs * sizeof(int));
        C = malloc(results * sizeof(long long));
        
        if ( !A || !C) {
            printf("memory allocation failed\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
            
        }
        
        
        srand(time(NULL));
        random_pol(n, A);
        random_pol(n, B);
    }
    
    double start, end_dist, end_calc, end_reduce;

    // Συγχρονισμός πριν ξεκινήσει το χρονόμετρο
    MPI_Barrier(MPI_COMM_WORLD);
    start = MPI_Wtime();

    // Broadcast B
    MPI_Bcast(B, coeffs, MPI_INT, 0, MPI_COMM_WORLD);
    
    // Scatter A
    MPI_Scatterv(A, elements, index, MPI_INT, 
                 local_A, local_n, MPI_INT, 
                 0, MPI_COMM_WORLD);

    end_dist = MPI_Wtime(); // End scatter

    //Calculation
    int my_offset = index[my_rank];

    for (int i = 0; i < local_n; i++) {
        for (int j = 0; j <coeffs; j++) {
            local_C[my_offset + i + j] += (long long)local_A[i] * B[j];
        }
    }

    end_calc = MPI_Wtime(); // End calc

    // Reduce results
    MPI_Reduce(local_C, C, results, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    end_reduce = MPI_Wtime();  // End reduce

double dist_time  = end_dist - start;
double calc_time  = end_calc - end_dist;
double reduce_time= end_reduce - end_calc;
double total_time = end_reduce - start;

double distMax, calcMax, reduceMax, totalMax;

MPI_Reduce(&dist_time, &distMax, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
MPI_Reduce(&calc_time, &calcMax, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
MPI_Reduce(&reduce_time, &reduceMax, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
MPI_Reduce(&total_time, &totalMax, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    // Print results
    if (my_rank == 0) {
        printf("Results for n=%d, %d processes\n", n, comm_sz);
         printf("Scatter time: %f\n", distMax);
        printf("Calc time: %f\n", calcMax);
        printf("Reduce time: %f\n", reduceMax);
        printf("Total time: %f\n", totalMax);
        
        // print for small n
        if (n < 100) {
            printf("Polynomial C: ");
            for(int i=0; i < results; i++) printf("%lld ", C[i]);
            printf("\n");
        }

        free(A);
        free(C);
    }

    //free memory
    free(B);
    free(local_A);
    free(local_C);
    free(elements);
    free(index);

    MPI_Finalize();
    return 0;

    
}