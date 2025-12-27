import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import time

# --- ΡΥΘΜΙΣΕΙΣ ---
C_SOURCE = "ex1.1.c"
EXECUTABLE = "./ex1.1"

# Παράμετροι Πειράματος
N_VALUES = [10000, 50000, 100000] 
THREAD_COUNTS = [1, 2, 4] 
REPEAT = 4  

def compile_code():
    print(f"Compiling {C_SOURCE} with optimization (-O3)...")
    cmd = ["gcc", "-O3", "-Wall", "-o", "ex1.1", C_SOURCE, "-lpthread"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Compilation failed!")
        print(result.stderr)
        exit(1)
    print("Compilation successful.\n")

def run_experiment(n, threads):
    serial_times = []
    parallel_times = []

    print(f"--> Running for N={n}, Threads={threads} ({REPEAT} times)...")
    
    for i in range(REPEAT):
        try:
            result = subprocess.run(
                [EXECUTABLE, str(n), str(threads)], 
                capture_output=True, 
                text=True, 
                timeout=600 
            )
            output = result.stdout
            
            s_match = re.search(r"serial execution time:\s+([0-9.,]+)", output, re.IGNORECASE)
            p_match = re.search(r"parallel execution time:\s+([0-9.,]+)", output, re.IGNORECASE)

            if s_match and p_match:
                s_val = float(s_match.group(1).replace(',', '.'))
                p_val = float(p_match.group(1).replace(',', '.'))
                serial_times.append(s_val)
                parallel_times.append(p_val)
            else:
                print(f"    Run {i+1}: Error parsing output.")

        except subprocess.TimeoutExpired:
            print(f"    Run {i+1}: TIMEOUT! (Skipping)")
            return None, None

    avg_serial = np.mean(serial_times) if serial_times else 0
    avg_parallel = np.mean(parallel_times) if parallel_times else 0
    
    print(f"    => Avg: Serial={avg_serial:.4f}s, Parallel={avg_parallel:.4f}s")
    return avg_serial, avg_parallel

def main():
    if not os.path.exists(C_SOURCE):
        print(f"Error: File {C_SOURCE} not found!")
        return

    compile_code()

    data_parallel = {n: [] for n in N_VALUES}
    data_speedup = {n: [] for n in N_VALUES}
    serial_times_map = {} 

    print("\n" + "="*80)
    print(f"{'N':<10} {'Threads':<10} {'Avg Serial(s)':<15} {'Avg Parallel(s)':<15} {'Speedup':<10}")
    print("="*80)

    for n in N_VALUES:
        for t in THREAD_COUNTS:
            s_time, p_time = run_experiment(n, t)
            
            if s_time is None: continue 

            # Αποθήκευση σειριακού χρόνου (ανεξάρτητα από threads, είναι σταθερός για κάθε N)
            if t == THREAD_COUNTS[0]: 
                serial_times_map[n] = s_time
            
            base_serial = serial_times_map.get(n, s_time)
            speedup = base_serial / p_time if p_time > 0 else 0

            print(f"{n:<10} {t:<10} {base_serial:<15.4f} {p_time:<15.4f} {speedup:<10.2f}")

            data_parallel[n].append(p_time)
            data_speedup[n].append(speedup)

    # --- CSV & TABLE IMAGE ---
    df = pd.DataFrame(data_parallel, index=[f"{t} threads" for t in THREAD_COUNTS])
    serial_row = pd.DataFrame({n: [serial_times_map.get(n,0)] for n in N_VALUES}, index=["Serial (Avg)"])
    df_final = pd.concat([serial_row, df])

    df_final.to_csv("ex1_1_results.csv")
    
    plt.figure(figsize=(8, 4))
    ax = plt.gca()
    ax.axis('off')
    df_rounded = df_final.round(4)
    table = ax.table(cellText=df_rounded.values, colLabels=df_rounded.columns, rowLabels=df_rounded.index, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)
    plt.title("Execution Time (Seconds) - Average of 4 Runs", y=1.1)
    plt.savefig("ex1_1_table.png", bbox_inches='tight', dpi=300)
    print("\n[OK] CSV & Table Image saved.")

    # --- GRAPH 1: SPEEDUP ---
    plt.figure(figsize=(10, 6))
    for n in N_VALUES:
        if data_speedup[n]:
            plt.plot(THREAD_COUNTS, data_speedup[n], marker='o', label=f'N = {n}')
    plt.plot(THREAD_COUNTS, THREAD_COUNTS, 'k--', label='Ideal Speedup', alpha=0.5)
    plt.title('Speedup vs Threads')
    plt.xlabel('Number of Threads')
    plt.ylabel('Speedup')
    plt.grid(True, alpha=0.3)
    plt.xticks(THREAD_COUNTS)
    plt.legend()
    plt.savefig("ex1_1_speedup.png")
    print("[OK] Speedup graph saved (ex1_1_speedup.png).")

    # --- GRAPH 2: EXECUTION TIME (με Σειριακό) ---
    plt.figure(figsize=(10, 6))
    
    # Παλέτα χρωμάτων για να ταιριάζουν οι γραμμές
    colors = plt.cm.tab10(np.linspace(0, 1, len(N_VALUES)))

    for idx, n in enumerate(N_VALUES):
        if data_parallel[n]:
            # 1. Καμπύλη Παράλληλων Χρόνων
            plt.plot(THREAD_COUNTS, data_parallel[n], marker='o', color=colors[idx], label=f'N = {n} (Parallel)')
            
            # 2. Οριζόντια Γραμμή για τον Σειριακό Χρόνο
            s_val = serial_times_map.get(n, 0)
            if s_val > 0:
                plt.axhline(y=s_val, color=colors[idx], linestyle='--', alpha=0.7, label=f'N = {n} (Serial)')

    plt.title('Execution Time vs Threads (Compare with Serial)')
    plt.xlabel('Number of Threads')
    plt.ylabel('Time (Seconds)')
    plt.xticks(THREAD_COUNTS)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig("ex1_1_time.png")
    print("[OK] Execution Time graph saved (ex1_1_time.png).")

if __name__ == "__main__":
    main()
