CC = mpicc
CFLAGS = -g -Wall

PYTHON = python3

EX1_DIR = ex1
EX2_DIR = ex2

EX1_SRC = $(EX1_DIR)/ex3.1.c
EX2_SRC = $(EX2_DIR)/ex3.2.c

EX1_EXE = $(EX1_DIR)/ex3.1
EX2_EXE = $(EX2_DIR)/ex3.2

all: ex3.1 ex3.2

ex3.1: $(EX1_EXE)
ex3.2: $(EX2_EXE)

$(EX1_EXE): $(EX1_SRC)
	$(CC) $(CFLAGS) $< -o $@

$(EX2_EXE): $(EX2_SRC)
	$(CC) $(CFLAGS) $< -o $@

tests: ex3.1 ex3.2
	$(MAKE) test1
	$(MAKE) test2

test1: $(EX1_EXE)
	@echo "\n Running experiments in ex1..."
	@cd $(EX1_DIR) && $(PYTHON) tests1.py

test2: $(EX2_EXE)
	@echo "\n Running experiments in ex2..."
	@cd $(EX2_DIR) && $(PYTHON) tests2.py

clean:
	rm -f $(EX1_EXE) $(EX2_EXE)

.PHONY: all tests test1 test2 clean