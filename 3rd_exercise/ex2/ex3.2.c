#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>

typedef long long ll;

// Double rand value
double rand_double() {
    return (double)rand() / (double)RAND_MAX;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);     // Initialize the MPI

    // 
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Argument variables
    int n, iterations;
    double sparsity;

    // Flag in case we run into errors
    int error_flag = 0;

    // Check arguments passed from the user
    if (rank == 0) {
        if (argc != 4) {
            fprintf(stderr, "Usage: %s <n> <sparsity> <iterations>\n", argv[0]);
            error_flag = 1;
        } else {
            n = atoi(argv[1]);
            sparsity = atof(argv[2]);
            iterations = atoi(argv[3]);
            
            if (n % size != 0) {
                fprintf(stderr, "Error: n (%d) must be divisible by MPI size (%d)\n", n, size);
                error_flag = 1;
            }
        }
    }

    // Communicate the case of an error to everyone so they can all check for exit
    MPI_Bcast(&error_flag, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (error_flag) {
        MPI_Finalize();
        return 1;
    }

    // Broadcast all arguments to every process
    MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&sparsity, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(&iterations, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // Get the size each process will have
    int local_rows = n / size;

    
    // The dense 2d-array from Rank 0
    ll **denseArray = NULL;
    ll *denseStorage = NULL;
    
    // A vector
    ll *vectorCSR = NULL;
    
    // The CSR essentials from Rank 0
    ll *csr_values = NULL;
    int *csr_col_ind = NULL;
    int *csr_row_ptr = NULL;

    // Local variables for each process
    ll *local_dense = (ll*)malloc(local_rows * n * sizeof(ll)); 
    ll *local_vectorCSR = (ll*)malloc(n * sizeof(ll));
    ll *local_vectorDense = (ll*)malloc(local_rows * sizeof(ll));
    
    // Local CSR arrays
    ll *local_csr_val = NULL;
    int *local_csr_col = NULL;
    int *local_csr_row_ptr = (int*)malloc((local_rows + 1) * sizeof(int));
    int local_non_zero = 0;

    // Timers we will need
    double timeStart, timeEnd;
    double timeBuild = 0, timeComm = 0, timeCalc = 0, timeDense = 0;

    // Creations, Rank 0
    if (rank == 0) {
        srand(time(NULL));
        
        // Allocating memory for the 2d-array
        denseArray = (ll**)malloc(n * sizeof(ll*));
        denseStorage = (ll*)malloc(n * n * sizeof(ll));
        if (denseArray == NULL || denseStorage == NULL) {
            fprintf(stderr, "Memory allocation failed\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        
        // Have the dense array be continuous in memory
        for (int i = 0; i < n; i++)
            denseArray[i] = &denseStorage[i * n];

        vectorCSR = (ll*)malloc(n * sizeof(ll));

        // Initialize vector
        for (int i = 0; i < n; i++)
            vectorCSR[i] = (ll)((rand() % 10) + 1);

        printf("Rank 0: Generating Matrix n=%d...\n", n);
        int nonZero = 0;
        
        // Randomize every element in the array into a random number based on the sparsity
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                // Initialization of a non zero value will happen when
                // the random double value is bigger than the sparsity 
                if (rand_double() > sparsity) {
                    denseArray[i][j] = (ll)((rand() % 10) + 1);
                    nonZero++;
                } else {
                    denseArray[i][j] = 0;
                }
            }
        }

        // CSR Creation time
        timeStart = MPI_Wtime();
        
        // CSR Values
        csr_values = (ll*)malloc(nonZero * sizeof(ll));
        csr_col_ind = (int*)malloc(nonZero * sizeof(int));
        csr_row_ptr = (int*)malloc((n + 1) * sizeof(int));

        // Initialize the values of the CSR representation
        int nonZeroCount = 0;
        csr_row_ptr[0] = 0;      
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                ll val = denseArray[i][j];
                if (val != 0) {
                    csr_values[nonZeroCount] = val;        // Non zero value goes here
                    csr_col_ind[nonZeroCount] = j;         // Non zero value's column goes hereq
                    nonZeroCount++;                        // Increment the non zero values' count
                }
            }
            // How many non zero values the current and all the previous
            // rows have (rows[i+1] - rows[i] would give rows[i+1] = 0)
            csr_row_ptr[i+1] = nonZeroCount;
        }
        timeEnd = MPI_Wtime();
        timeBuild = timeEnd - timeStart;
    }

    // Deliver CSR to all processes
    if (rank == 0)
        timeStart = MPI_Wtime();

    // Broadcast the starting vector
    if (rank == 0) {
        for(int i=0; i<n; i++)
            local_vectorCSR[i] = vectorCSR[i];
    }
    MPI_Bcast(local_vectorCSR, n, MPI_LONG_LONG, 0, MPI_COMM_WORLD);

    // Broadcast CSR manually
    if (rank == 0) {
        // Loop over the processes
        for (int dest = 0; dest < size; dest++) {
            // Keep the start and the end of the current row
            int rowStart = dest * local_rows;
            int rowEnd = rowStart + local_rows;
            int countNonZero = csr_row_ptr[rowEnd] - csr_row_ptr[rowStart];

            // Rank 0
            if (dest == 0) {

                // Local variables initialization
                local_non_zero = countNonZero;
                local_csr_val = (ll*)malloc(local_non_zero * sizeof(ll));
                local_csr_col = (int*)malloc(local_non_zero * sizeof(int));

                // Store the non zero values of the local rows and their columns
                int start_idx = csr_row_ptr[rowStart];
                for(int k=0; k<local_non_zero; k++) {
                    local_csr_val[k] = csr_values[start_idx + k];
                    local_csr_col[k] = csr_col_ind[start_idx + k];
                }

                // Assign the rows to the pther processes
                local_csr_row_ptr[0] = 0;
                for(int i=0; i<local_rows; i++) {
                    local_csr_row_ptr[i+1] = csr_row_ptr[rowStart + i + 1] - csr_row_ptr[rowStart];
                }

            } else {

                // Send the number of non zero values
                MPI_Send(&countNonZero, 1, MPI_INT, dest, 0, MPI_COMM_WORLD);

                // If there are non zero values, send the values and their columns
                if (countNonZero > 0) {
                    int start_idx = csr_row_ptr[rowStart];
                    MPI_Send(&csr_values[start_idx], countNonZero, MPI_LONG_LONG, dest, 1, MPI_COMM_WORLD);
                    MPI_Send(&csr_col_ind[start_idx], countNonZero, MPI_INT, dest, 2, MPI_COMM_WORLD);
                }

                // Send the rows
                int *temp_row_lens = (int*)malloc(local_rows * sizeof(int));
                for(int i=0; i<local_rows; i++) {
                    temp_row_lens[i] = csr_row_ptr[rowStart + i + 1] - csr_row_ptr[rowStart + i];
                }

                MPI_Send(temp_row_lens, local_rows, MPI_INT, dest, 3, MPI_COMM_WORLD);

                // Free the temporary array
                free(temp_row_lens);
            }
        }
    } else {

        // Receive the amount of non zero values that the row has
        MPI_Recv(&local_non_zero, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        local_csr_val = (ll*)malloc(local_non_zero * sizeof(ll));
        local_csr_col = (int*)malloc(local_non_zero * sizeof(int));

        // Receive the values and their columns
        if (local_non_zero > 0) {
            MPI_Recv(local_csr_val, local_non_zero, MPI_LONG_LONG, 0, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            MPI_Recv(local_csr_col, local_non_zero, MPI_INT, 0, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        // Receive the local rows
        int *recv_row_lens = (int*)malloc(local_rows * sizeof(int));
        MPI_Recv(recv_row_lens, local_rows, MPI_INT, 0, 3, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

        local_csr_row_ptr[0] = 0;
        for(int i=0; i<local_rows; i++) {
            local_csr_row_ptr[i+1] = local_csr_row_ptr[i] + recv_row_lens[i];
        }

        // Free the temporary array
        free(recv_row_lens);
    }

    if (rank == 0) {
        timeEnd = MPI_Wtime();
        timeComm = timeEnd - timeStart; // Time to send
    }

    // Calculate CSR
    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) timeStart = MPI_Wtime();

    // Loop over the iterations given from user
    for (int k = 0; k < iterations; k++) {

        // Loop over the local row
        for (int i = 0; i < local_rows; i++) {
            ll sum = 0;
            int row_start = local_csr_row_ptr[i];
            int row_end   = local_csr_row_ptr[i+1];
            for (int j = row_start; j < row_end; j++) {
                sum += local_csr_val[j] * local_vectorCSR[ local_csr_col[j] ];
            }
            local_vectorDense[i] = sum;
        }

        // Gather all the local values into rank 0
        MPI_Allgather(local_vectorDense, local_rows, MPI_LONG_LONG, 
                      local_vectorCSR, local_rows, MPI_LONG_LONG, 
                      MPI_COMM_WORLD);
    }

    if (rank == 0) {
        timeEnd = MPI_Wtime();
        timeCalc = timeEnd - timeStart; // (iii) Χρόνος Εκτέλεσης CSR
    }

    // Calculate Dense
    // Reset vector
    if (rank == 0) {
        for (int i = 0; i < n; i++)
            local_vectorCSR[i] = vectorCSR[i];
    }
    MPI_Bcast(local_vectorCSR, n, MPI_LONG_LONG, 0, MPI_COMM_WORLD);

    // Scatter the denseStorage (Because I'ts 1d)
    MPI_Scatter(denseStorage, local_rows * n, MPI_LONG_LONG, 
                local_dense, local_rows * n, MPI_LONG_LONG, 
                0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) timeStart = MPI_Wtime();

    // Calculate the multiplications
    for (int k = 0; k < iterations; k++) {
        for (int i = 0; i < local_rows; i++) {
            ll sum = 0;
            for (int j = 0; j < n; j++) {
                // Local_dense is a 1D array which represents a 2d array and it's values are grabbed like this
                sum += local_dense[i * n + j] * local_vectorCSR[j];
            }
            local_vectorDense[i] = sum;
        }
        // Gather results
        MPI_Allgather(local_vectorDense, local_rows, MPI_LONG_LONG, 
                      local_vectorCSR, local_rows, MPI_LONG_LONG, 
                      MPI_COMM_WORLD);
    }

    if (rank == 0) {
        timeEnd = MPI_Wtime();
        timeDense = timeEnd - timeStart;    // Execution time Dense array
    }

    // If process 0 is executing, print the results and free the rank 0 allocates
    if (rank == 0) {
        printf("\n=== RESULTS ===\n");
        printf("Size: %d, Sparsity: %.2f, Iterations: %d\n", n, sparsity, iterations);
        
        printf("(i)   CSR Build Time:       %f sec\n", timeBuild);
        printf("(ii)  Comm Time (0->All):   %f sec\n", timeComm);
        printf("(iii) CSR Parallel Calc:    %f sec\n", timeCalc);
        printf("(iv)  CSR Total (i+ii+iii): %f sec\n", timeBuild + timeComm + timeCalc);
        printf("(v)   Dense Parallel Calc:  %f sec\n", timeDense);

        free(denseArray);
        free(denseStorage);
        
        free(vectorCSR);
        free(csr_values);
        free(csr_col_ind);
        free(csr_row_ptr);
    }

    free(local_vectorCSR);
    free(local_dense);
    free(local_vectorDense);
    if(local_csr_val) free(local_csr_val);
    if(local_csr_col) free(local_csr_col);
    free(local_csr_row_ptr);

    MPI_Finalize();
    return 0;
}