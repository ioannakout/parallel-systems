import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import sys
import time

# What to run and where to store graphs
EXECUTABLE = "ex1/poly_simd" 
FOLDER = "ex1/"

# Parameters for the different testing
N_VALUES = [32000, 64000, 96000, 128000]    # Number of values
REPEAT = 5                                  # Amount of times each test is run
WARMUP_N = 32000                            # Size of to warmup

# Function that runs the code and returns the timers
def run_process(n, run_index=0, is_warmup=False):
    try:
        # Start timer and run the command to execute the code
        start_time = time.time()
        result = subprocess.run(
            [EXECUTABLE, str(n)], 
            capture_output=True, 
            text=True, 
            timeout=180
        )
        
        # Check if the code run
        if result.returncode != 0:
            print(f"Error (Return code {result.returncode})")
            return None, None

        # Save the result
        output = result.stdout
        
        # Extract the times of each algorithm
        s_match = re.search(r"Serial execution time:\s+([0-9.,]+)", output, re.IGNORECASE)
        v_match = re.search(r"SIMD execution time:\s+([0-9.,]+)", output, re.IGNORECASE)

        if s_match and v_match:
            s_val = float(s_match.group(1).replace(',', '.'))
            v_val = float(v_match.group(1).replace(',', '.'))
            return s_val, v_val
        else:
            print("Parse Error")
            return None, None

    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return None, None
    except Exception as e:
        print(f"Exception: {e}")
        return None, None

def main():

    # Check the executable exists
    if not os.path.exists(EXECUTABLE):
        print(f"Error: Executable {EXECUTABLE} not found. Run 'make' first.")
        return

    # Warm it up
    print("\nStarting CPU Warm-up phase...")
    run_process(WARMUP_N, is_warmup=True)
    print("Warm-up complete. Starting benchmarks.\n")

    # Sav ethe results
    results = {
        "N": [],
        "Serial_Mean": [], "Serial_Std": [],
        "SIMD_Mean": [], "SIMD_Std": [],
        "Speedup_Mean": []
    }

    # Print table head
    print(f"{'N':<10} {'Serial (avg ± std)':<25} {'SIMD (avg ± std)':<25} {'Speedup':<10}")
    print("-" * 75)

    # Loop over the values
    for n in N_VALUES:
        serial_runs = []
        simd_runs = []
        
        # Run it REPEAT times
        for i in range(REPEAT):

            # Run the process and save the results
            s, v = run_process(n, i)
            if s is not None and v is not None:
                serial_runs.append(s)
                simd_runs.append(v)
        
        if not serial_runs: continue

        # Calculate statistics
        s_mean = np.mean(serial_runs)
        s_std = np.std(serial_runs)
        v_mean = np.mean(simd_runs)
        v_std = np.std(simd_runs)
        
        # Speedup based on means
        speedup = s_mean / v_mean if v_mean > 0 else 0

        # Print Row
        s_str = f"{s_mean:.4f} ± {s_std:.4f}"
        v_str = f"{v_mean:.4f} ± {v_std:.4f}"
        print(f"{n:<10} {s_str:<25} {v_str:<25} {speedup:<10.2f}")

        # Save Data
        results["N"].append(n)
        results["Serial_Mean"].append(s_mean)
        results["Serial_Std"].append(s_std)
        results["SIMD_Mean"].append(v_mean)
        results["SIMD_Std"].append(v_std)
        results["Speedup_Mean"].append(speedup)

    # Save to the CSV
    df = pd.DataFrame(results)
    csv_path = FOLDER + "simd_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nResults saved to '{csv_path}'.")

    # Execution time with error bars
    plt.figure(figsize=(10, 6))
    
    # Serial plot
    plt.errorbar(df["N"], df["Serial_Mean"], yerr=df["Serial_Std"], 
                 fmt='-o', color='red', ecolor='darkred', capsize=5, label='Serial')
    
    # SIMD plot
    plt.errorbar(df["N"], df["SIMD_Mean"], yerr=df["SIMD_Std"], 
                 fmt='-s', color='blue', ecolor='darkblue', capsize=5, label='SIMD (AVX2)')

    plt.title('Execution Time: Serial vs SIMD (with Std Dev)')
    plt.xlabel('Polynomial Degree (N)')
    plt.ylabel('Time (Seconds)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(FOLDER + "simd_time_comparison.png")
    print(f"Graph saved: '{FOLDER}simd_time_comparison.png'")

    # Speedup plot
    plt.figure(figsize=(10, 6))
    plt.plot(df["N"], df["Speedup_Mean"], marker='o', color='green', linewidth=2, label='Measured Speedup')
    
    plt.axhline(y=4, color='gray', linestyle='--', alpha=0.5, label='Theoretical Max (4x)')
    
    plt.title('SIMD Speedup vs Problem Size')
    plt.xlabel('Polynomial Degree (N)')
    plt.ylabel('Speedup Factor')
    plt.ylim(0, 5)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    for i, txt in enumerate(df["Speedup_Mean"]):
        plt.annotate(f"{txt:.2f}x", (df["N"][i], df["Speedup_Mean"][i]), 
                     textcoords="offset points", xytext=(0,10), ha='center')

    plt.savefig(FOLDER + "simd_speedup.png")
    print(f"Graph saved: '{FOLDER}simd_speedup.png'")

if __name__ == "__main__":
    main()