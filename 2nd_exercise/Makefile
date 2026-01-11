CC = gcc
CFLAGS = -g -Wall -fopenmp

PYTHON = python3

EX1_DIR = ex1
EX2_DIR = ex2
EX3_DIR = ex3

EX1_SRC = $(EX1_DIR)/ex2.1.c
EX2_SRC = $(EX2_DIR)/ex2.2.c
EX3_SRC = $(EX3_DIR)/ex2.3.c

EX1_EXE = $(EX1_DIR)/ex2.1
EX2_EXE = $(EX2_DIR)/ex2.2
EX3_EXE = $(EX3_DIR)/ex2.3

all: ex2.1 ex2.2 ex2.3

ex2.1: $(EX1_EXE)
ex2.2: $(EX2_EXE)
ex2.3: $(EX3_EXE)

$(EX1_EXE): $(EX1_SRC)
	$(CC) $(CFLAGS) $< -o $@

$(EX2_EXE): $(EX2_SRC)
	$(CC) $(CFLAGS) $< -o $@

$(EX3_EXE): $(EX3_SRC)
	$(CC) $(CFLAGS) $< -o $@

tests: ex2.1 ex2.2 ex2.3
	$(MAKE) test1
	$(MAKE) test2
	$(MAKE) test3

test1: $(EX1_EXE)
	@echo "\n Running experiments in ex1..."
	@cd $(EX1_DIR) && $(PYTHON) tests1.py

test2: $(EX2_EXE)
	@echo "\n Running experiments in ex2..."
	@cd $(EX2_DIR) && $(PYTHON) tests2.py

test3: $(EX3_EXE)
	@echo "\n Running experiments in ex3..."
	@cd $(EX3_DIR) && $(PYTHON) tests3.py

clean:
	rm -f $(EX1_EXE) $(EX2_EXE) $(EX3_EXE)

.PHONY: all tests test1 test2 test3 clean