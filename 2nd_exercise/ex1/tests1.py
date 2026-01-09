import subprocess
import re
import matplotlib.pyplot as plt
import os
import sys


POLYNOMIAL_DEGREES = [10000, 50000, 100000] 
THREAD_COUNTS = [1, 2, 4, 8]
REPETITIONS = 4 

# Ονόματα αρχείων
OPENMP_SRC = "ex2.1.c"
OPENMP_EXE = "openmp_prog"
PTHREADS_SRC = "ex1.1.c"
PTHREADS_EXE = "pthreads_prog"

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

def parse_output(output):
    serial_match = re.search(r"serial.*time:\s*([0-9\.]+)", output)
    parallel_match = re.search(r"parallel.*time:\s*([0-9\.]+)", output)
    
    s_time = float(serial_match.group(1)) if serial_match else None
    p_time = float(parallel_match.group(1)) if parallel_match else None
    return s_time, p_time

def perform_experiments():
    results = {"OpenMP": {}, "Pthreads": {}}

    for prog_type, exe in [("OpenMP", OPENMP_EXE), ("Pthreads", PTHREADS_EXE)]:
        print(f"Running experiments for {prog_type}...")
        
        for n in POLYNOMIAL_DEGREES:
            results[prog_type][n] = {}
            avg_pure_serial = 0 
            
            for t in THREAD_COUNTS:
                total_p = 0
                total_s = 0 
                
                print(f"  N={n}, Threads={t}...", end="", flush=True)
                for r in range(REPETITIONS):
                    output = run_command(f"./{exe} {n} {t}")
                    s, p = parse_output(output)
                    if s and p:
                        total_s += s
                        total_p += p
                
                avg_p = total_p / REPETITIONS
                avg_s = total_s / REPETITIONS
                avg_pure_serial = avg_s 
                
                speedup = avg_pure_serial / avg_p if avg_p > 0 else 0
                
                results[prog_type][n][t] = {
                    "time": avg_p,
                    "speedup": speedup
                }
                print(f" Done. (Avg Time: {avg_p:.4f}s)")
            
            results[prog_type][n]["pure_serial"] = avg_pure_serial

    return results

def print_tables(results):
    for prog_type, data in results.items():
        print(f"\n=== {prog_type} Results (Average of {REPETITIONS} runs) ===")
        print(f"{'N':<10} {'Threads':<15} {'Avg Time(s)':<15} {'Speedup':<10}")
        print("-" * 55)
        for n, t_data in data.items():
            for t in THREAD_COUNTS:
                label = "1 (Serial)" if t == 1 else str(t)
                metrics = t_data[t]
                print(f"{n:<10} {label:<15} {metrics['time']:<15.4f} {metrics['speedup']:<10.2f}")
            print("-" * 55)

def plot_comparison(results):
    max_n = max(POLYNOMIAL_DEGREES)
    x_labels = ["1\n(Serial)" if t == 1 else str(t) for t in THREAD_COUNTS]
    
    # Γράφημα 1: Σύγκριση Χρόνου
    plt.figure(figsize=(10, 6))
    omp_times = [results["OpenMP"][max_n][t]["time"] for t in THREAD_COUNTS]
    pth_times = [results["Pthreads"][max_n][t]["time"] for t in THREAD_COUNTS]
    
    plt.plot(THREAD_COUNTS, omp_times, marker='o', label='OpenMP', linewidth=2)
    plt.plot(THREAD_COUNTS, pth_times, marker='s', linestyle='--', label='Pthreads', linewidth=2)
    
    plt.xlabel('Number of Threads')
    plt.ylabel('Time (seconds)')
    plt.title(f'Execution Time Comparison (N={max_n})')
    plt.xticks(THREAD_COUNTS, x_labels)
    plt.legend()
    plt.grid(True)
    plt.savefig('comparison_time.png')
    print("\nGraph saved: comparison_time.png")

    # Γράφημα 2: Σύγκριση Speedup
    plt.figure(figsize=(10, 6))
    omp_speedup = [results["OpenMP"][max_n][t]["speedup"] for t in THREAD_COUNTS]
    pth_speedup = [results["Pthreads"][max_n][t]["speedup"] for t in THREAD_COUNTS]
    
    plt.plot(THREAD_COUNTS, omp_speedup, marker='o', label='OpenMP', linewidth=2)
    plt.plot(THREAD_COUNTS, pth_speedup, marker='s', linestyle='--', label='Pthreads', linewidth=2)
    plt.plot(THREAD_COUNTS, THREAD_COUNTS, 'k:', label='Ideal', alpha=0.5)
    
    plt.xlabel('Number of Threads')
    plt.ylabel('Speedup')
    plt.title(f'Speedup Comparison (N={max_n})')
    plt.xticks(THREAD_COUNTS, x_labels)
    plt.legend()
    plt.grid(True)
    plt.savefig('comparison_speedup.png')
    print("Graph saved: comparison_speedup.png")

def plot_omp_only(results):
    # ΝΕΑ ΣΥΝΑΡΤΗΣΗ: Γράφημα μόνο για OpenMP
    max_n = max(POLYNOMIAL_DEGREES)
    x_labels = ["1\n(Serial)" if t == 1 else str(t) for t in THREAD_COUNTS]
    
    omp_times = [results["OpenMP"][max_n][t]["time"] for t in THREAD_COUNTS]
    omp_speedup = [results["OpenMP"][max_n][t]["speedup"] for t in THREAD_COUNTS]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Αριστερός Άξονας (Χρόνος)
    color = 'tab:blue'
    ax1.set_xlabel('Number of Threads')
    ax1.set_ylabel('Execution Time (s)', color=color)
    ax1.plot(THREAD_COUNTS, omp_times, color=color, marker='o', linewidth=2, label='Time')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_xticks(THREAD_COUNTS)
    ax1.set_xticklabels(x_labels)
    ax1.grid(True)

    # Δεξιός Άξονας (Speedup)
    ax2 = ax1.twinx()  
    color = 'tab:green'
    ax2.set_ylabel('Speedup', color=color)  
    ax2.plot(THREAD_COUNTS, omp_speedup, color=color, marker='s', linestyle='--', linewidth=2, label='Speedup')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title(f'OpenMP Performance Analysis (N={max_n})')
    fig.tight_layout()  
    plt.savefig('openmp_analysis.png')
    print("Graph saved: openmp_analysis.png (Shows Time & Speedup for OMP)")

if __name__ == "__main__":
    data = perform_experiments()
    print_tables(data)
    plot_comparison(data)
    plot_omp_only(data) # Κλήση της νέας συνάρτησης

    print("\n Graphing complete. Starting Scalability Script \n")

    subprocess.run([sys.executable, "scale.py"], check=True)