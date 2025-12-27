import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import time

# --- ΡΥΘΜΙΣΕΙΣ ---
C_SOURCE = "ex1.3.c"
EXECUTABLE = "./ex1.3"

# Παράμετροι Πειράματος
# Επειδή η πολυπλοκότητα είναι O(N), χρειαζόμαστε μεγάλα N για να δούμε χρόνους.
# Δοκιμάζουμε: 10^7, 5*10^7, 10^8
N_VALUES = [10000000, 50000000, 100000000] 
REPEAT = 4  # 4 Επαναλήψεις για μέσο όρο

def compile_code():
    print(f"Compiling {C_SOURCE} with optimization (-O3)...")
    cmd = ["gcc", "-O3", "-Wall", "-o", "ex1.3", C_SOURCE, "-lpthread"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Compilation failed!")
        print(result.stderr)
        exit(1)
    print("Compilation successful.\n")

def run_experiment(n):
    serial_times = []
    parallel_times = []

    print(f"--> Running for N={n} ({REPEAT} times)...")
    
    for i in range(REPEAT):
        try:
            # Το ex1.3 παίρνει μόνο το N ως όρισμα
            result = subprocess.run(
                [EXECUTABLE, str(n)], 
                capture_output=True, 
                text=True, 
                timeout=60 
            )
            output = result.stdout
            
            # Regex για Parsing (δέχεται και . και ,)
            s_match = re.search(r"serial execution time:\s+([0-9.,]+)", output, re.IGNORECASE)
            p_match = re.search(r"parallel execution time:\s+([0-9.,]+)", output, re.IGNORECASE)

            if s_match and p_match:
                s_val = float(s_match.group(1).replace(',', '.'))
                p_val = float(p_match.group(1).replace(',', '.'))
                serial_times.append(s_val)
                parallel_times.append(p_val)
            else:
                print(f"    Run {i+1}: Error parsing output.")
                # print(output) # Uncomment for debugging

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

    results = []

    print("\n" + "="*80)
    print(f"{'N':<15} {'Avg Serial(s)':<15} {'Avg Parallel(s)':<15} {'Speedup':<10}")
    print("="*80)

    for n in N_VALUES:
        s_time, p_time = run_experiment(n)
        
        if s_time is None: continue 

        speedup = s_time / p_time if p_time > 0 else 0

        print(f"{n:<15} {s_time:<15.4f} {p_time:<15.4f} {speedup:<10.2f}")

        results.append({
            "N": n,
            "Serial Time (s)": s_time,
            "Parallel Time (s)": p_time,
            "Speedup": speedup
        })

    # --- DATAFRAME & CSV ---
    df = pd.DataFrame(results)
    df.set_index("N", inplace=True)
    
    df.to_csv("ex1_3_results.csv")
    print("\n[OK] CSV table saved to 'ex1_3_results.csv'")

    # --- 1. ΠΙΝΑΚΑΣ ΩΣ ΕΙΚΟΝΑ ---
    plt.figure(figsize=(8, 4))
    ax = plt.gca()
    ax.axis('off')
    df_rounded = df.round(4)
    table = ax.table(cellText=df_rounded.values, colLabels=df_rounded.columns, rowLabels=df_rounded.index, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)
    plt.title("Results for Array Statistics (4 Threads)", y=1.1)
    plt.savefig("ex1_3_table.png", bbox_inches='tight', dpi=300)
    print("[OK] Table image saved to 'ex1_3_table.png'")

    # --- 2. ΓΡΑΦΗΜΑ SPEEDUP ---
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df["Speedup"], marker='o', linestyle='-', color='b', label='Observed Speedup')
    
    # Γραμμή αναφοράς (Speedup = 1, δηλαδή καμία βελτίωση)
    plt.axhline(y=1, color='r', linestyle='--', label='No Speedup (Serial)')
    # Γραμμή αναφοράς (Ideal Speedup = 4)
    plt.axhline(y=4, color='g', linestyle='--', label='Ideal Speedup (4 Threads)')

    plt.title('Speedup vs Array Size (N)')
    plt.xlabel('Array Size (N)')
    plt.ylabel('Speedup')
    plt.xscale('linear') # Μπορείς να το αλλάξεις σε 'log' αν θες
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig("ex1_3_speedup.png")
    print("[OK] Speedup graph saved to 'ex1_3_speedup.png'")

    # --- 3. ΓΡΑΦΗΜΑ ΧΡΟΝΟΥ (Time vs N) ---
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df["Serial Time (s)"], marker='x', linestyle='--', label='Serial Time')
    plt.plot(df.index, df["Parallel Time (s)"], marker='o', linestyle='-', label='Parallel Time (4 Threads)')
    
    plt.title('Execution Time vs Array Size')
    plt.xlabel('Array Size (N)')
    plt.ylabel('Time (Seconds)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig("ex1_3_time.png")
    print("[OK] Execution Time graph saved to 'ex1_3_time.png'")

if __name__ == "__main__":
    main()
