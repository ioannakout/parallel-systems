CC = gcc
CFLAGS = -O3 -mavx2 -Wall
SRC_DIR = ex1
SRC = $(SRC_DIR)/4.1.c
EXEC = $(SRC_DIR)/poly_simd
SCRIPT = $(SRC_DIR)/test.py

# Default target: Κάνει compile και τρέχει το benchmark
all: benchmark

# Compile: Δημιουργεί το εκτελέσιμο μέσα στον φάκελο ex1
compile: $(SRC)
	@echo "--> Compiling C code..."
	$(CC) $(CFLAGS) $(SRC) -o $(EXEC)
	@echo "✅ Compilation successful: $(EXEC)"

# Benchmark: Τρέχει το python script
# Περνάμε το όνομα του εκτελέσιμου ως argument στο script για να ξέρει πού να το βρει
benchmark: compile
	@echo "--> Running Python Benchmark..."
	python3 $(SCRIPT)

# Clean: Καθαρίζει τα παραγόμενα αρχεία
clean:
	rm -f $(EXEC) *.csv *.png
	@echo "✅ Cleaned up executable and results."

.PHONY: all compile benchmark clean