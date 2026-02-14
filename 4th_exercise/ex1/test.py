import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import sys

# --- ΡΥΘΜΙΣΕΙΣ (ΠΡΟΣΑΡΜΟΣΜΕΝΕΣ ΓΙΑ MAKEFILE) ---
# Το Makefile έχει ήδη φτιάξει το εκτελέσιμο στο ex1/poly_simd
# Οπότε εδώ απλά δείχνουμε πού είναι.
EXECUTABLE = "ex1/poly_simd" 
FOLDER = "ex1/"

# Παράμετροι Πειράματος
N_VALUES = [10000, 20000, 40000, 80000] 
REPEAT = 3

def run_experiment(n):
    serial_times = []
    simd_times = []

    print(f"Running for N={n} ({REPEAT} times)...")
    
    for i in range(REPEAT):
        try:
            # Εκτέλεση του C προγράμματος
            result = subprocess.run(
                [EXECUTABLE, str(n)], 
                capture_output=True, 
                text=True, 
                timeout=120 # Timeout ασφαλείας
            )
            output = result.stdout
            
            # Regex για να διαβάσουμε τους χρόνους από το output της C
            # Ψάχνουμε γραμμές όπως "Serial execution time: 0.123456"
            s_match = re.search(r"Serial execution time:\s+([0-9.,]+)", output)
            v_match = re.search(r"SIMD execution time:\s+([0-9.,]+)", output)

            if s_match and v_match:
                s_val = float(s_match.group(1).replace(',', '.'))
                v_val = float(v_match.group(1).replace(',', '.'))
                serial_times.append(s_val)
                simd_times.append(v_val)
            else:
                print(f"   ⚠️ Run {i+1}: Could not parse output.")

        except subprocess.TimeoutExpired:
            print(f"   ⏳ Run {i+1}: TIMEOUT! (Skipping)")
            return None, None

    if not serial_times: return None, None

    avg_serial = np.mean(serial_times)
    avg_simd = np.mean(simd_times)
    
    print(f"   => Avg: Serial={avg_serial:.4f}s | SIMD={avg_simd:.4f}s")
    return avg_serial, avg_simd

def main():
        
    results = {
        "N": [],
        "Serial (s)": [],
        "SIMD (s)": [],
        "Speedup": []
    }

    print(f"{'N':<10} {'Serial (s)':<15} {'SIMD (s)':<15} {'Speedup (x)':<15}")
    print("-" * 55)

    for n in N_VALUES:
        s_time, v_time = run_experiment(n)
        
        if s_time is None: continue 

        speedup = s_time / v_time if v_time > 0 else 0

        print(f"{n:<10} {s_time:<15.4f} {v_time:<15.4f} {speedup:<15.2f}")

        results["N"].append(n)
        results["Serial (s)"].append(s_time)
        results["SIMD (s)"].append(v_time)
        results["Speedup"].append(speedup)

    # --- ΑΠΟΘΗΚΕΥΣΗ ΣΕ CSV ---
    df = pd.DataFrame(results)
    df.to_csv(FOLDER+"simd_results.csv", index=False)
    print("\nResults saved to 'ex1/simd_results.csv'.")

    # --- ΓΡΑΦΗΜΑ 1: ΧΡΟΝΟΙ ΕΚΤΕΛΕΣΗΣ ---
    plt.figure(figsize=(10, 6))
    plt.plot(df["N"], df["Serial (s)"], marker='o', label='Serial', linestyle='-', color='red')
    plt.plot(df["N"], df["SIMD (s)"], marker='s', label='SIMD (AVX2)', linestyle='-', color='blue')
    
    plt.title('Execution Time: Serial vs SIMD')
    plt.xlabel('Polynomial Degree (N)')
    plt.ylabel('Time (Seconds)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(FOLDER+"simd_time_comparison.png")
    print("Graph saved: 'ex1/simd_time_comparison.png'")

    # --- ΓΡΑΦΗΜΑ 2: SPEEDUP ---
    plt.figure(figsize=(10, 6))
    plt.plot(df["N"], df["Speedup"], marker='o', color='green', linewidth=2)
    
    # Προσθήκη οριζόντιας γραμμής για το θεωρητικό μέγιστο (περίπου 4x για integers αν όλα ήταν τέλεια)
    plt.axhline(y=4, color='gray', linestyle='--', alpha=0.5, label='Theoretical Max (4x)')
    
    plt.title('SIMD Speedup vs Problem Size')
    plt.xlabel('Polynomial Degree (N)')
    plt.ylabel('Speedup Factor (Serial / SIMD)')
    plt.ylim(0, 5) # Το όριο στον άξονα Υ
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    for i, txt in enumerate(df["Speedup"]):
        plt.annotate(f"{txt:.2f}x", (df["N"][i], df["Speedup"][i]), textcoords="offset points", xytext=(0,10), ha='center')

    plt.savefig(FOLDER+"simd_speedup.png")
    print("Graph saved: 'ex1/simd_speedup.png'")

if __name__ == "__main__":
    main()