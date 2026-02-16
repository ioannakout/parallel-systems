CC = gcc
CFLAGS = -O3 -mavx2 -Wall
SRC_DIR = ex1
SRC = $(SRC_DIR)/4.1.c
EXEC = $(SRC_DIR)/poly_simd
SCRIPT = $(SRC_DIR)/test.py

# Another way to run the benchmark
all: benchmark

# Code that compiles the .c file
compile: $(SRC)
	@echo "--> Compiling C code..."
	$(CC) $(CFLAGS) $(SRC) -o $(EXEC)
	@echo "Compilation successful: $(EXEC)"

# Compile the .c file and run the python script
benchmark: compile
	@echo "--> Running Python Benchmark..."
	python3 $(SCRIPT)

# Clean
clean:
	rm -f $(EXEC) *.csv *.png
	@echo "Cleaned up executable and results."

.PHONY: all compile benchmark clean