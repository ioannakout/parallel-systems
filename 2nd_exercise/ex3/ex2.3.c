#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <omp.h>

void merge(int array[], int merge_buffer[],int l, int m, int r){
   //segment that will be merged into the buffer
    for (int i = l; i <= r; i++) merge_buffer[i] = array[i];
    
    int i = l;       // left half [l..m]
    int j = m + 1;   // right half [m+1..r]
    int k = l;       // write index to array
    //merge back into array
    while (i <= m && j <= r) {
        if (merge_buffer[i] <= merge_buffer[j]) array[k++] = merge_buffer[i++];
        else array[k++] = merge_buffer[j++];
    }

    // remaining elements from the left half
    while (i <= m) array[k++] = merge_buffer[i++];
}

void mergeSortSerial(int array[], int merge_buffer[], int l, int r) {
    if (l < r) {
        int m = l + (r - l) / 2;
        mergeSortSerial(array,merge_buffer, l, m);
        mergeSortSerial(array, merge_buffer, m + 1, r);
        merge(array,merge_buffer,  l, m, r);
    }
}

void mergeSortParallel(int array[], int merge_buffer[], int l, int r) {
    if (l < r) {
        int m = l + (r - l) / 2;
        //left half
        #pragma omp task if(r - l > 5000)
        mergeSortParallel(array, merge_buffer, l, m);

        // right half
        #pragma omp task if(r - l > 5000)
        mergeSortParallel(array,merge_buffer, m + 1, r);

        #pragma omp taskwait//wait for both tasks to finish before merging
        merge(array,merge_buffer, l, m, r);
    }
}


int main(int argc, char* argv[]){

    if(argc != 4) {
        printf("Wrong input\n");
        return 1;
    }
    
    int n = atoi(argv[1]); //size of array
    char* wayofexecut = argv[2]; //way of execution
    long thread_count = strtol(argv[3], NULL, 10); //number of threads

   
   int *array = (int *)malloc(n * sizeof(int)); //allocate array
   int *merge_buffer = (int *)malloc(n * sizeof(int)); //alocate merge buffer
    if (array == NULL || merge_buffer == NULL) {
        fprintf(stderr, "memory allocation failed\n");
        free(array);
        free(merge_buffer);
        return 1;
    }

    srand(27); //deterministic random values
    for (long i = 0; i < n; i++) {
        array[i] = rand() % 10;
    }

    double start_time , end_time;
    //serial execution
    if (strcmp(wayofexecut, "serial") == 0) {
        printf("serial execution\n");
        start_time = omp_get_wtime();
        mergeSortSerial(array,merge_buffer, 0, n - 1); 
        end_time = omp_get_wtime();

    //parallel execution
    } else if (strcmp(wayofexecut, "parallel") == 0) {
        printf("parallel execution(%ld threads)\n", thread_count);
        omp_set_num_threads(thread_count);
        start_time = omp_get_wtime();
         
        #pragma omp parallel// parallel region
        {
            #pragma omp single
            mergeSortParallel(array, merge_buffer, 0, n - 1); 
        }
        end_time = omp_get_wtime();
    } 
    else {
        printf("wrong input\n");
        free(array);
        free(merge_buffer);
        return 1;
    }
    //check if array is sorted
    int sorted = 1;
    for (long i = 0; i < n - 1; i++) {
        if (array[i] > array[i+1]) {sorted = 0; break; }
    }
    double time = end_time - start_time;

    if (sorted) {
        printf("elements are sorted\n");
        printf("time of execution: %f seconds\n", time);
    } else {
        printf("sort failed\n");
    }

    //free memory
    free(array);
    free(merge_buffer);
    return 0;


}
