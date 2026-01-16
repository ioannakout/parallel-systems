import subprocess
import re
import statistics
import matplotlib.pyplot as plt
import sys

# --- Configuration ---
EXECUTABLE = "./ex2.2"
RUNS_PER_EXPERIMENT = 3  # Run experiment 3 times to get the average value

# Updated Constants as requested
N_LIST = [100, 1000, 10000] # Iterate over these sizes
LOOPS = 20                  # Loops set between 10 and 20
THREADS = 4                 # Fixed to 4 threads

# Sparsity list remains the same
SPARSITY_LIST = [0.1, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 0.99]

def parse_output(output):
    # Get the time from the C output
    csr_pattern = r"CSR multiplication.*?took\s+(\d+\.\d+)\s+seconds"
    dense_pattern = r"Dense multiplication.*?took\s+(\d+\.\d+)\s+seconds"
    
    # Check if the outputs are the same
    csr_match = re.search(csr_pattern, output)
    dense_match = re.search(dense_pattern, output)
    
    return {
        "csr": float(csr_match.group(1)) if csr_match else None,
        "dense": float(dense_match.group(1)) if dense_match else None
    }

def main():
    # Dict that saves speedups for the last comparison
    # Key will be N, Value will be list of speedups
    all_speedups_data = {} 

    print(f"--- Benchmarking Configuration ---")
    print(f"   Threads fixed at: {THREADS}")
    print(f"   Loops: {LOOPS}")
    print(f"   N Sizes: {N_LIST}")
    print(f"   Sparsities: {SPARSITY_LIST}\n")

    # Loop over the different Matrix sizes (N)
    for n_val in N_LIST:
        print(f"\nRunning experiments for Matrix Size N={n_val} ...")
        
        # Lists for current N size
        current_sparsity = []
        current_dense = []
        current_csr = []
        current_speedup = []

        # Run every sparsity in list for the current N
        for sp in SPARSITY_LIST:
            print(f"   Sparsity: {sp} ... ", end="", flush=True)
            
            temp_csr = []
            temp_dense = []

            # Run each instance three times
            for r in range(RUNS_PER_EXPERIMENT):
                # Call that will be executed: ./ex2.2 <N> <Sparsity> <Loops> <Threads>
                cmd = [EXECUTABLE, str(n_val), str(sp), str(LOOPS), str(THREADS)]
                
                # Run the program with the according parameters and parse the time
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    times = parse_output(res.stdout)
                    
                    if times['csr'] is not None and times['dense'] is not None:
                        temp_csr.append(times['csr'])
                        temp_dense.append(times['dense'])
                except Exception as e:
                    print(f"Error: {e}")
                    # We continue to try the next run instead of crashing immediately
                    continue

            # Find the averages and calculate speedup
            if temp_csr and temp_dense:
                avg_csr = statistics.mean(temp_csr)
                avg_dense = statistics.mean(temp_dense)
                
                # Avoid division by zero if time is 0.000000
                if avg_csr > 0:
                    speedup = avg_dense / avg_csr 
                else:
                    speedup = 0

                current_sparsity.append(sp)
                current_csr.append(avg_csr)
                current_dense.append(avg_dense)
                current_speedup.append(speedup)
                print(f" Speedup: {speedup:.2f}x (Dense: {avg_dense:.4f}s / CSR: {avg_csr:.4f}s)")
            else:
                print("Fail (Could not parse output)")

        # Save for the final graph
        all_speedups_data[n_val] = current_speedup

        # --- PLOTTING FOR CURRENT N ---
        plt.figure(figsize=(12, 6))
        
        # Subplot 1: Time (s)
        plt.subplot(1, 2, 1)
        plt.plot(current_sparsity, current_dense, 'o-', color='red', label='Dense')
        plt.plot(current_sparsity, current_csr, 's-', color='blue', label='CSR')
        plt.title(f'Time Comparison (N={n_val}, Threads={THREADS})')
        plt.xlabel('Sparsity')
        plt.ylabel('Time (s)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)

        # Subplot 2: Speedup
        plt.subplot(1, 2, 2)
        plt.plot(current_sparsity, current_speedup, '^-', color='green', label='Speedup')
        plt.title(f'Speedup (N={n_val}, Threads={THREADS})')
        plt.xlabel('Sparsity')
        plt.ylabel('Speedup Factor')
        plt.grid(True, linestyle='--', alpha=0.6)
        
        # Annotations
        for i, val in enumerate(current_speedup):
             plt.annotate(f"{val:.1f}x", (current_sparsity[i], current_speedup[i]), xytext=(0,10), textcoords='offset points')

        filename = f"benchmark_N_{n_val}.png"
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        print(f"   Graph saved as: {filename}")

    # --- FINAL COMBINED PLOT ---
    print("\nGenerating combined comparison...")
    plt.figure(figsize=(10, 7))
    
    for n_val in N_LIST:
        # Only plot if we have data
        if n_val in all_speedups_data and len(all_speedups_data[n_val]) > 0:
            # Ensure lengths match in case of partial failures
            limit = min(len(SPARSITY_LIST), len(all_speedups_data[n_val]))
            plt.plot(SPARSITY_LIST[:limit], all_speedups_data[n_val][:limit], marker='o', label=f'N={n_val}')

    plt.title(f'Speedup Comparison by Matrix Size (Threads={THREADS})')
    plt.xlabel('Sparsity (Percentage of Zeros)')
    plt.ylabel('Speedup Factor (Dense / CSR)')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    
    plt.savefig("combined_speedup_by_N.png", dpi=300)
    print("All tests run successfully. Created comparison 'combined_speedup_by_N.png'")

if __name__ == "__main__":
    main()