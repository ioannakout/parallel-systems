#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <time.h>

typedef long long ll;

int main(int argc, char* argv[]) {
    if (argc != 5) {
        fprintf(stderr, "Different amount arguments than 4 passed\n");
        exti(1);
    }
    ll n = atoll(argv[1]);
    int sparsity = atoi(argv[2]);
    ll loopCount = atoll(argv[3]);
    int thread_count = atoi(argv[4]);

    
    return 0;
}