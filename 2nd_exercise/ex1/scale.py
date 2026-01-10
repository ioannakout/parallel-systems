import subprocess
import re
import matplotlib.pyplot as plt
import os
import sys


POLYNOMIAL_DEGREES = [1000, 50000, 100000] 
THREADS_FOR_PARALLEL = 8  
REPETITIONS = 4

OPENMP_EXE = "openmp_prog"
OPENMP_SRC = "ex2.1.c"

def compile_program():
    print("--- Compiling OpenMP ---")
    cmd = f"gcc -O3 -fopenmp {OPENMP_SRC} -o {OPENMP_EXE}"
    if os.system(cmd) != 0:
        print("Error compiling.")
        sys.exit(1)

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

def parse_output(output):
    # Παίρνουμε Serial και Parallel χρόνο
    serial_match = re.search(r"serial.*time:\s*([0-9\.]+)", output)
    parallel_match = re.search(r"parallel.*time:\s*([0-9\.]+)", output)
    s = float(serial_match.group(1)) if serial_match else 0
    p = float(parallel_match.group(1)) if parallel_match else 0
    return s, p

def collect_data():
    data = {"N": [], "Serial": [], "Parallel": []}
    
    print(f"--- Running Scalability Test (Threads={THREADS_FOR_PARALLEL}) ---")
    for n in POLYNOMIAL_DEGREES:
        print(f"Testing N={n} ... ", end="", flush=True)
        
        avg_s = 0
        avg_p = 0
        
        for r in range(REPETITIONS):
            out = run_command(f"./{OPENMP_EXE} {n} {THREADS_FOR_PARALLEL}")
            s, p = parse_output(out)
            avg_s += s
            avg_p += p
            
        avg_s /= REPETITIONS
        avg_p /= REPETITIONS
        
        data["N"].append(n)
        data["Serial"].append(avg_s)
        data["Parallel"].append(avg_p)
        print(f"Done. (Serial: {avg_s:.4f}s, Parallel: {avg_p:.4f}s)")
        
    return data

def plot_scalability(data):
    plt.figure(figsize=(10, 6))
    
    # Plot Serial Line
    plt.plot(data["N"], data["Serial"], marker='o', label='Serial (1 Thread)', color='red', linestyle='--')
    
    # Plot Parallel Line
    plt.plot(data["N"], data["Parallel"], marker='s', label=f'Parallel ({THREADS_FOR_PARALLEL} Threads)', color='blue', linewidth=2)
    
    plt.xlabel('Polynomial Degree (N)')
    plt.ylabel('Execution Time (seconds)')
    plt.title('Scalability: Time vs Problem Size (N)')
    plt.legend()
    plt.grid(True)
    
    filename = "scalability_N.png"
    plt.savefig(filename)
    print(f"\nGraph saved as '{filename}'")

if __name__ == "__main__":
    compile_program()
    results = collect_data()
    plot_scalability(results)
