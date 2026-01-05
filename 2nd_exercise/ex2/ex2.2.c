#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <time.h>

#define MAX_VALUE 100

typedef long long ll;
int thread_count;

void fill_array(int** array, ll n, float sparsity) {
    // Loop over the whole array
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {

            // Get the chance that the value will be a zero or a normal value (between 0.0 and 1.0
            // as rand() <= RAND_MAX so rand()/RAND_MAX <= 1.0) and cast the rand() to a double
            double valueChance = (double)rand() / RAND_MAX;
            
            // Assign 0 if chance is inside the sparsity value, else choose
            // a random number between 1 and MAX_VALUE (+ 1 to avoid 0)
            if (valueChance < sparsity)
                array[i][j] = 0;
            else
                array[i][j] = (rand() % MAX_VALUE) + 1;
        }
    }
}

void create_csr(int* values, int* rows, int* cols, int** array, ll n) {  

    // Loop over all the rows and columns and count every rows non-zero elements
    # pragma omp parallel for num_threads(thread_count) \
        schedule(static)
    for (int i = 0; i < n; i++) {
        int count = 0;
        for (int j = 0; j < n; j++)
            if (array[i][j] != 0)
                count++;

        // i + 1 is explained next
        rows[i+1] = count;
    }

    /**
     * We need to keep track of where every row starts so we can immediately know where
     * inside the columns array the first element of the row is located at. Hence, we'll
     * make it so every row adds all the values found in the predecessor, which essentially
     * stacks, so rows[i + 1] = rows[0] + rows[1] + rows[2] + ... + rows[i] etc. For this to
     * work we initialize rows[0] = 0 since it does not have any preceding values.
     */
    rows[0] = 0;
    for (int i = 0; i < n; i++)
        rows[i+1] += rows[i]; 

    // Loop again over the rows and the columns and assign the values into the values and cols array
    # pragma omp parallel for num_threads(thread_count) \
        schedule(static)
    for (int i = 0; i < n; i ++) {

        // Hold where each row starts at from the previous sum
        int rowPos = rows[i];

        for (int j = 0; j < n; j++) {
            if (array[i][j] != 0) {
                values[rowPos] = array[i][j];
                cols[rowPos] = j;
                rowPos++;
            }
        }

    }

}

void create_vector(int* vector, int n) {
    for (int i = 0; i < n; i++) {
        vector[i] = rand() % MAX_VALUE;
    }
}

void csr_vector_multiplication(int* vector, int* values, int* rows, int* cols, ll* resultCSR, int n) {
    // Multiplicate CSR with the vector using parallel threads
    #pragma omp parallel for num_threads(thread_count) \
        schedule(static)
    for (int i = 0; i < n; i++) {

        int startRow = rows[i];
        int endRow = rows[i+1];

        int sum = 0;

        for (int k = startRow; k < endRow; k++)
            sum += values[k] * vector[cols[k]];

        resultCSR[i] = sum;
    }
}

void dense_vector_multiplication(int** array, int* vector, ll* resultDense, int n) {
    // Multiplicate Dense array with the vector using parallel threads
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < n; i++) {

        int sum = 0;

        for (int j = 0; j < n; j++) {
            sum += array[i][j] * vector[j];
        }
        resultDense[i] = sum;
    }
}

int main(int argc, char* argv[]) {

    // Check if the 
    if (argc != 5) {
        fprintf(stderr, "Different amount arguments than 4 passed\n");
        exit(1);
    }

    // Ensuring we get a different number each rand
    srand(time(NULL));

    // Extract values given from user
    ll n = atoll(argv[1]);
    float sparsity = atof(argv[2]);
    int loopCount = atoll(argv[3]);
    thread_count = atoi(argv[4]);

    if (sparsity > 100) {
        fprintf(stderr, "Sparsity is out of bounds\n");
        exit(1);
    }

    // Ensure sparsity is between 0.0 and 1.0
    if (sparsity > 1.0)
        sparsity /= 100.0;

    if (thread_count > 100) {
        fprintf(stderr, "Please provide less threads to do the task\n");
        exit(1);
    }

    /**
     * Because we would like the quickest dense array, we don't want to allocate (malloc)
     * the array one time for every line, since this would have the memory allocating in
     * the heap scattered for each call of array[i][j], so we create an array with the size
     * of the whole 2d-array(n*n) and assign the 2d-array's lines to start exactly n cells
     * away from the next in memory (i * n where n is the gap between each line and i shows
     * which line is next) so it's closer for the memory to pick it up
     */
    int** array = malloc(sizeof(int*) * n);
    int* memAssist = malloc(n * n * sizeof(int));

    if (array == NULL || memAssist == NULL) {
        fprintf(stderr, "Memory could not be allocated\n");
        exit(1);
    }

    for (int i = 0; i < n; i ++)
        array[i] = &memAssist[i * n];
    
    // Creating dense array
    fill_array(array, n, sparsity);

    // Allocate memory for the vector
    int* vector = malloc(sizeof(ll) * n);

    // Creating the vector
    create_vector(vector, n);


    // Allocating memory for the CSR (we assume for simplicity they will be full)
    int* values = malloc(sizeof(int) * n * n);
    int* rows = malloc(sizeof(int) * (n + 1));
    int* cols = malloc(sizeof(int) * n * n);

    if (values == NULL || rows == NULL || cols == NULL) {
        fprintf(stderr, "Memory could not be allocated\n");
        exit(1);
    }

    // Create and time the creation of the CSR representation
    double startTime = omp_get_wtime();
    create_csr(values, rows, cols, array, n);
    double endTime = omp_get_wtime();
    printf("CSR creation took %f seconds\n", endTime - startTime);

    // Reallocating memory to resize the arrays to their intended size (Cutback on memory allocated especially for high sparsity)
    values = realloc(values, sizeof(int) * rows[n]);
    cols = realloc(cols, sizeof(int) * rows[n]);

    // Allocate memory to save the results of the multiplication and time it
    ll* resultCSR = malloc(sizeof(ll) * n);
    startTime = omp_get_wtime();
    for (int i = 0; i < loopCount; i ++)    // Loop over the number given by the user
        csr_vector_multiplication(vector, values, rows, cols, resultCSR, n);
    endTime = omp_get_wtime();
    printf("CSR multiplication with a vector over %d loops took %f seconds\n", loopCount, endTime - startTime);

    ll* resultDense = malloc(sizeof(ll) * n);
    startTime = omp_get_wtime();
    for (int i = 0; i < loopCount; i ++)    // Loop over the number given by the user
        dense_vector_multiplication(array, vector, resultDense, n);
    endTime = omp_get_wtime();
    printf("Dense multiplication with a vector over %d loops took %f seconds\n", loopCount, endTime - startTime);

    // Free the allocated memory
    free(vector);
    free(resultCSR);
    free(resultDense);

    free(values);
    free(rows);
    free(cols);

    free(memAssist);
    free(array);
    
    return 0;
}