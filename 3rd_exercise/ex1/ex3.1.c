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

int main(int argc, char** argv[]){

    int my_rank;
    int comm_sz;
    int n;
    int local_n;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);

    if (argc != 2) {
        if (rank == 0) printf("Usage: %s <degree_n>\n", argv[0]);
        MPI_Finalize();
        return 1;
    }

    n = atoi(argv[1]);

    int *A = NULL;       // Πλήρες Α (Μόνο στο rank 0)
    int *B = NULL;       // Πλήρες Β (Σε όλους)
    int *local_A = NULL; // Το κομμάτι του Α (Σε όλους)
    long long *local_C = NULL; // Το μερικό αποτέλεσμα (Σε όλους)
    long long *C = NULL;

    local_n = (n + 1) / size;
}