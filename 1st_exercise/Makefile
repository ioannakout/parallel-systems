CC = gcc
CFLAGS = -g -Wall -lpthread

PYTHON = python3

EX1_DIR = ex1
EX2_DIR = ex2
EX3_DIR = ex3
EX4_DIR = ex4
EX5_DIR = ex5

EX1_SRC = $(EX1_DIR)/ex1.1.c
EX2_SRC = $(EX2_DIR)/ex1.2.c
EX3_SRC = $(EX3_DIR)/ex1.3.c
EX4_SRC = $(EX4_DIR)/ex1.4.c
EX5_SRC = $(EX5_DIR)/ex1.5.c

EX1_EXE = $(EX1_DIR)/ex1.1
EX2_EXE = $(EX2_DIR)/ex1.2
EX3_EXE = $(EX3_DIR)/ex1.3
EX4_EXE = $(EX4_DIR)/ex1.4
EX5_EXE = $(EX5_DIR)/ex1.5

all: ex1.1 ex1.2 ex1.3 ex1.4 ex1.5

ex1.1: $(EX1_EXE)
ex1.2: $(EX2_EXE)
ex1.3: $(EX3_EXE)
ex1.4: $(EX4_EXE)
ex1.5: $(EX5_EXE)

$(EX1_EXE): $(EX1_SRC)
	$(CC) $(CFLAGS) $< -o $@

$(EX2_EXE): $(EX2_SRC)
	$(CC) $(CFLAGS) $< -o $@

$(EX3_EXE): $(EX3_SRC)
	$(CC) $(CFLAGS) $< -o $@

$(EX4_EXE): $(EX4_SRC)
	$(CC) $(CFLAGS) $< -o $@

# ----------------------------
# Clean
# ----------------------------

tests: ex1.1 ex1.2 ex1.3 ex1.4 ex1.5
	$(MAKE) test1
	$(MAKE) experiment1.2
	$(MAKE) experiment1.3
	$(MAKE) experiment1.4
	$(MAKE) experiment1.5

# ----------------------------
# Run experiments (one by one)
# ----------------------------
test1: $(EX1_EXE)
	@echo "\n🏃 Running experiments in ex1..."
	@cd $(EX1_DIR) && $(PYTHON) tests1.py

test2: $(EX2_EXE)
	@echo "\n🏃 Running experiments in ex2..."
	@cd $(EX2_DIR) && $(PYTHON) tests2.py

test3: $(EX3_EXE)
	@echo "\n🏃 Running experiments in ex3..."
	@cd $(EX3_DIR) && $(PYTHON) tests3.py

test4: $(EX4_EXE)
	@echo "\n🏃 Running experiments in ex4..."
	@cd $(EX4_DIR) && $(PYTHON) tests4.py

test5: $(EX4_EXE)
	@echo "\n🏃 Running experiments in ex5..."
	@cd $(EX5_DIR) && $(PYTHON) tests5.py

clean:
	rm -f $(EX1_EXE) $(EX2_EXE) $(EX3_EXE) $(EX4_EXE) $(EX5_EXE)

.PHONY: all ex1 ex2 ex3 ex4 clean