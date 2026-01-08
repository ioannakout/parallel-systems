import subprocess
import re
import matplotlib.pyplot as plt
import os
import sys


DATA_SIZES = [10000000, 20000000, 50000000, 100000000] 
THREAD_COUNTS = [1, 2, 4, 8]
REPETITIONS = 4  

SRC_FILE = "ex2.3.c"
EXE_FILE = "mergesort_prog"

def compile_program():
    print("--- Compilation ---")
    cmd = f"gcc -O3 -fopenmp {SRC_FILE} -o {EXE_FILE}"
    if os.system(cmd) != 0:
        print("Error compiling. Make sure gcc is installed and supports OpenMP.")
        sys.exit(1)
    print("Compilation Successful.\n")

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

def parse_time(output):
    match = re.search(r"time of execution:\s*([0-9\.]+)", output)
    if match:
        return float(match.group(1))
    return None

def perform_experiments():
    results = {}

    for n in DATA_SIZES:
        results[n] = {}
        print(f"=== Running experiments for N = {n} ===")
        
        # 1. Serial Execution
        print(f"  Running Serial...", end="", flush=True)
        total_serial = 0
        for r in range(REPETITIONS):
            out = run_command(f"./{EXE_FILE} {n} serial 1")
            t = parse_time(out)
            if t: total_serial += t
        
        avg_serial = total_serial / REPETITIONS
        results[n]["serial_time"] = avg_serial
        print(f" Done. ({avg_serial:.4f}s)")

        # 2. Parallel Executions
        results[n]["parallel"] = {}
        for t in THREAD_COUNTS:
            print(f"  Running Parallel ({t} threads)...", end="", flush=True)
            total_par = 0
            for r in range(REPETITIONS):
                out = run_command(f"./{EXE_FILE} {n} parallel {t}")
                t_val = parse_time(out)
                if t_val: total_par += t_val
            
            avg_par = total_par / REPETITIONS
            speedup = avg_serial / avg_par if avg_par > 0 else 0
            
            results[n]["parallel"][t] = {
                "time": avg_par,
                "speedup": speedup
            }
            print(f" Done. ({avg_par:.4f}s, Speedup: {speedup:.2f}x)")
        print("-" * 40)

    return results

def plot_graphs(results):
    # 1. Threads vs Time (Για το μεγαλύτερο N)
    max_n = max(DATA_SIZES)
    plt.figure(figsize=(10, 6))
    times = [results[max_n]["parallel"][t]["time"] for t in THREAD_COUNTS]
    plt.plot(THREAD_COUNTS, times, marker='o', linewidth=2, label=f"N={max_n}")
    plt.xlabel('Number of Threads')
    plt.ylabel('Time (s)')
    plt.title(f'Execution Time vs Threads (N={max_n})')
    plt.grid(True)
    plt.xticks(THREAD_COUNTS)
    plt.savefig('mergesort_threads_time.png')
    print("\nGraph saved: mergesort_threads_time.png")

    # 2. Threads vs Speedup (Για το μεγαλύτερο N)
    plt.figure(figsize=(10, 6))
    speedups = [results[max_n]["parallel"][t]["speedup"] for t in THREAD_COUNTS]
    plt.plot(THREAD_COUNTS, speedups, marker='s', color='green', linewidth=2, label='Speedup')
    plt.plot(THREAD_COUNTS, THREAD_COUNTS, 'k:', label='Ideal', alpha=0.5)
    plt.xlabel('Number of Threads')
    plt.ylabel('Speedup')
    plt.title(f'Speedup vs Threads (N={max_n})')
    plt.grid(True)
    plt.legend()
    plt.xticks(THREAD_COUNTS)
    plt.savefig('mergesort_threads_speedup.png')
    print("Graph saved: mergesort_threads_speedup.png")

    # 3. N vs Time (Scalability - ΤΟ ΝΕΟ ΓΡΑΦΗΜΑ)
    plt.figure(figsize=(10, 6))
    
    # Serial Line
    serial_times = [results[n]["serial_time"] for n in DATA_SIZES]
    plt.plot(DATA_SIZES, serial_times, marker='o', linestyle='--', color='red', label='Serial (1 Thread)')
    
    # Parallel (8 Threads) Line
    max_threads = max(THREAD_COUNTS)
    parallel_times = [results[n]["parallel"][max_threads]["time"] for n in DATA_SIZES]
    plt.plot(DATA_SIZES, parallel_times, marker='s', linewidth=2, color='blue', label=f'Parallel ({max_threads} Threads)')
    
    plt.xlabel('Array Size (N)')
    plt.ylabel('Time (s)')
    plt.title('Scalability: Time vs Array Size (N)')
    plt.legend()
    plt.grid(True)
    
    # Format x-axis to show millions (e.g., 10M, 100M)
    plt.ticklabel_format(style='plain', axis='x') 
    
    plt.savefig('mergesort_scalability_N.png')
    print("Graph saved: mergesort_scalability_N.png (ΤΟ ΝΕΟ ΓΡΑΦΗΜΑ)")

if __name__ == "__main__":
    compile_program()
    data = perform_experiments()
    plot_graphs(data)