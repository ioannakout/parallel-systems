import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import sys

# --- Ρυθμίσεις ---
C_FILENAME = "ex2.3.c"
EXECUTABLE = "ex2.3"
if os.name == 'nt': 
    EXECUTABLE += ".exe"

# Μεγέθη Πινάκων (Δοκιμάζουμε 10^7 και 5*10^7)
DATA_SIZES = [10000000, 50000000] 

THREADS = [1, 2, 4, 8]
REPETITIONS = 4  # ΑΛΛΑΓΗ: Τρέχει 4 φορές το καθένα

def compile_code():
    print(f"Compiling {C_FILENAME}...")
    compile_cmd = ["gcc", "-O2", "-fopenmp", C_FILENAME, "-o", EXECUTABLE]
    try:
        subprocess.check_call(compile_cmd)
        print("Compilation successful!\n")
    except subprocess.CalledProcessError:
        print("Error: Compilation failed.")
        sys.exit(1)

def run_experiment(n, mode, threads):
    # Εντολή: ./ex2.3 <n> <mode> <threads>
    cmd = [f"./{EXECUTABLE}", str(n), mode, str(threads)]
    if os.name == 'nt':
        cmd[0] = EXECUTABLE
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        # Έλεγχος αν πέτυχε η ταξινόμηση
        if "elements are sorted" not in output:
            print(f"  [ERROR] Sort failed for N={n}, Mode={mode}")
            return None

        # Ανάγνωση χρόνου
        time_match = re.search(r"time of execution:\s*([0-9.]+)", output)
        
        if time_match:
            return float(time_match.group(1))
        else:
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def create_graphs(df):
    plt.figure(figsize=(10, 6))
    for n in DATA_SIZES:
        subset = df[df["Size"] == n]
        if not subset.empty:
            plt.plot(subset["Threads"], subset["Speedup"], marker='o', linestyle='-', label=f'N={n}')
    
    plt.plot(THREADS, THREADS, 'k:', label='Ideal Linear Speedup', alpha=0.5)
    plt.title("MergeSort Speedup using OpenMP Tasks")
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup (Serial / Parallel)")
    plt.legend()
    plt.grid(True)
    plt.savefig("graph_mergesort_speedup.png")
    print("\nGraph saved: graph_mergesort_speedup.png")

def main():
    compile_code()
    results_data = []

    print("Starting Experiments (4 Repetitions per test)...")
    print("=" * 60)

    for n in DATA_SIZES:
        print(f"\n---> Testing Array Size N = {n}")
        
        # 1. SERIAL EXECUTION
        print(f"  [SERIAL] Running {REPETITIONS} times...")
        serial_times = []
        for r in range(REPETITIONS):
            t = run_experiment(n, "serial", 1)
            if t is not None: 
                serial_times.append(t)
                print(f"    Run {r+1}/{REPETITIONS}: {t:.6f} sec") # Εμφάνιση κάθε τρεξίματος
        
        avg_serial = np.mean(serial_times) if serial_times else 0
        print(f"  >> Average Serial Time: {avg_serial:.6f} sec\n")

        # 2. PARALLEL EXECUTION (για κάθε αριθμό νημάτων)
        for t in THREADS:
            print(f"  [PARALLEL] Threads: {t} | Running {REPETITIONS} times...")
            par_times = []
            for r in range(REPETITIONS):
                val = run_experiment(n, "parallel", t)
                if val is not None: 
                    par_times.append(val)
                    print(f"    Run {r+1}/{REPETITIONS}: {val:.6f} sec") # Εμφάνιση κάθε τρεξίματος
            
            if par_times:
                avg_par = np.mean(par_times)
                speedup = avg_serial / avg_par if avg_par > 0 else 0
                print(f"  >> Average Parallel Time ({t} thr): {avg_par:.6f} sec | Speedup: {speedup:.2f}x\n")
                
                results_data.append({
                    "Size": n,
                    "Threads": t,
                    "Avg Serial": avg_serial,
                    "Avg Parallel": avg_par,
                    "Speedup": speedup
                })

    # Τελικός Πίνακας Αποτελεσμάτων
    if results_data:
        df = pd.DataFrame(results_data)
        
        print("\n" + "="*30)
        print(" FINAL AVERAGE RESULTS TABLE ")
        print("="*30)
        # Μορφοποίηση για ωραία εκτύπωση
        print(df.to_string(index=False, formatters={
            'Avg Serial': '{:.4f}'.format,
            'Avg Parallel': '{:.4f}'.format,
            'Speedup': '{:.2f}'.format
        }))
        
        df.to_csv("mergesort_results.csv", index=False)
        print("\nResults saved to 'mergesort_results.csv'")
        create_graphs(df)

if __name__ == "__main__":
    main()