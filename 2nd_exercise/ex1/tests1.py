import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import sys

# --- Ρυθμίσεις Αρχείων ---
C_FILENAME = "ex2.1.c"
EXECUTABLE = "ex2.1"
if os.name == 'nt': 
    EXECUTABLE += ".exe"

# --- Παράμετροι Πειραμάτων ---
DEGREES = [5000, 10000, 20000] 
THREADS = [1, 2, 4, 8]
REPETITIONS = 4

def compile_code():
    print(f"Compiling {C_FILENAME}...")
    compile_cmd = ["gcc", "-O2", "-fopenmp", C_FILENAME, "-o", EXECUTABLE]
    try:
        subprocess.check_call(compile_cmd)
        print("Compilation successful!\n")
    except subprocess.CalledProcessError:
        print("Error: Compilation failed. Make sure gcc is installed and supports OpenMP.")
        sys.exit(1)

def run_experiment(degree, thread_count):
    cmd = [f"./{EXECUTABLE}", str(degree), str(thread_count)]
    if os.name == 'nt':
        cmd[0] = EXECUTABLE
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        # --- ΔΙΟΡΘΩΣΗ ΕΔΩ ---
        # Τώρα ψάχνουμε ακριβώς τα strings που τυπώνει το πρόγραμμά σου
        # Χρησιμοποιούμε re.IGNORECASE για να μην έχουμε θέμα με κεφαλαία/μικρά
        
        # Ψάχνει για "initialization time..."
        init_match = re.search(r"initialization time.*:\s*([0-9.]+)", output, re.IGNORECASE)
        
        # Ψάχνει για "serial time: ..."
        serial_match = re.search(r"serial time:\s*([0-9.]+)", output, re.IGNORECASE)
        
        # Ψάχνει για "parallel time: ..."
        parallel_match = re.search(r"parallel time:\s*([0-9.]+)", output, re.IGNORECASE)
        
        if init_match and serial_match and parallel_match:
            return float(init_match.group(1)), float(serial_match.group(1)), float(parallel_match.group(1))
        else:
            # Αν αποτύχει, τυπώνει τι διάβασε για να καταλάβουμε το λάθος
            # (Αυτό το βλέπεις τώρα στην εικόνα σου ως Warning)
            return None, None, None

    except Exception as e:
        print(f"Error running experiment: {e}")
        return None, None, None

def create_graphs(df):
    # Γράφημα Χρόνου
    plt.figure(figsize=(10, 6))
    for n in DEGREES:
        subset = df[df["Degree (N)"] == n]
        plt.plot(subset["Threads"], subset["Avg Parallel Time"], marker='o', label=f'N={n}')
    
    plt.title("Parallel Execution Time vs Threads")
    plt.xlabel("Number of Threads")
    plt.ylabel("Time (seconds)")
    plt.legend()
    plt.grid(True)
    plt.savefig("graph_time_vs_threads.png")
    print("Graph saved: graph_time_vs_threads.png")
    
    # Γράφημα Speedup
    plt.figure(figsize=(10, 6))
    for n in DEGREES:
        subset = df[df["Degree (N)"] == n]
        plt.plot(subset["Threads"], subset["Speedup"], marker='s', linestyle='--', label=f'N={n}')
    
    plt.plot(THREADS, THREADS, 'k:', label='Ideal Linear Speedup', alpha=0.5)
    
    plt.title("Speedup vs Threads")
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup (Serial / Parallel)")
    plt.legend()
    plt.grid(True)
    plt.savefig("graph_speedup.png")
    print("Graph saved: graph_speedup.png")

def main():
    compile_code()
    results_data = []

    print(f"{'Degree':<10} {'Threads':<10} {'Rep':<5} {'Serial(s)':<12} {'Parallel(s)':<12}")
    print("-" * 65)

    for n in DEGREES:
        for t in THREADS:
            serial_times = []
            parallel_times = []
            init_times = []
            
            for r in range(REPETITIONS):
                init, ser, par = run_experiment(n, t)
                if init is not None:
                    init_times.append(init)
                    serial_times.append(ser)
                    parallel_times.append(par)
                    print(f"{n:<10} {t:<10} {r+1:<5} {ser:<12.4f} {par:<12.4f}")
            
            if serial_times and parallel_times:
                avg_init = np.mean(init_times)
                avg_serial = np.mean(serial_times)
                avg_parallel = np.mean(parallel_times)
                speedup = avg_serial / avg_parallel if avg_parallel > 0 else 0
                
                results_data.append({
                    "Degree (N)": n,
                    "Threads": t,
                    "Avg Init Time": avg_init,
                    "Avg Serial Time": avg_serial,
                    "Avg Parallel Time": avg_parallel,
                    "Speedup": speedup
                })

    if results_data:
        df = pd.DataFrame(results_data)
        print("\n\n=== Average Results Table ===")
        print(df.to_string(index=False))
        df.to_csv("experiment_results_ex2.1.csv", index=False)
        print("\nResults saved to 'experiment_results_ex2.1.csv'")
        create_graphs(df)
    else:
        print("\nNo results collected. Check if the output format matches the regex.")

if __name__ == "__main__":
    main()