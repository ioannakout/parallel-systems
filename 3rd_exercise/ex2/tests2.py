import subprocess
import re
import matplotlib.pyplot as plt
import os
import sys

# --- CONFIGURATION ---
EXECUTABLE = "./ex3.2"       # Your specific executable name
OUTPUT_DIR = "plots"         # Folder to save images
ITERATIONS = 20              # Fixed number of iterations for stability

# --- PARAMETER LISTS AS REQUESTED ---
SIZES = [1024, 2048, 4096, 8192]
PROCS = [1, 2, 4, 8]
# Generating 0.1 to 0.9 and adding 0.99
SPARSITIES = [round(x * 0.1, 1) for x in range(1, 10)] + [0.99]

# Create output directory
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def run_experiment(procs, size, sparsity, iterations):
    """
    Runs the MPI C program and returns a dictionary with the parsed times.
    """
    cmd = ["mpiexec", "-n", str(procs), EXECUTABLE, str(size), str(sparsity), str(iterations)]
    
    print(f"Running: N={size}, Sparsity={sparsity}, P={procs}...", end=" ", flush=True)
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout
        
        # Regex to parse the specific output format of your C code
        data = {}
        patterns = {
            "csr_build":  r"\(i\)\s+CSR Build Time:\s+([0-9\.]+)",
            "comm_time":  r"\(ii\)\s+Comm Time.*:\s+([0-9\.]+)",
            "csr_calc":   r"\(iii\)\s+CSR Parallel Calc:\s+([0-9\.]+)",
            "csr_total":  r"\(iv\)\s+CSR Total.*:\s+([0-9\.]+)",
            "dense_calc": r"\(v\)\s+Dense Parallel Calc:\s+([0-9\.]+)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                data[key] = float(match.group(1))
            else:
                data[key] = 0.0
        
        print("Done.")
        return data

    except subprocess.CalledProcessError as e:
        print(f"\nError! MPI Failed. Output:\n{e.stderr}")
        return None
    except FileNotFoundError:
        print(f"\nError: Executable '{EXECUTABLE}' not found.")
        sys.exit(1)

# ==========================================
# 1. CSR vs DENSE Comparison (Varying Sparsity)
# ==========================================
def plot_sparsity_impact():
    # Fixed parameters for this test
    FIXED_SIZE = 4096
    FIXED_PROCS = 4
    
    print(f"\n--- Experiment 1: Sparsity Impact (N={FIXED_SIZE}, P={FIXED_PROCS}) ---")
    
    csr_times = []
    dense_times = []
    
    for s in SPARSITIES:
        res = run_experiment(FIXED_PROCS, FIXED_SIZE, s, ITERATIONS)
        if res:
            csr_times.append(res['csr_total'])
            dense_times.append(res['dense_calc'])

    plt.figure(figsize=(10, 6))
    plt.plot(SPARSITIES, csr_times, marker='o', label='CSR Total Time', color='blue')
    plt.plot(SPARSITIES, dense_times, marker='s', label='Dense Calc Time', color='red', linestyle='--')
    
    plt.title(f'Impact of Sparsity on Execution Time\n(N={FIXED_SIZE}, Procs={FIXED_PROCS})')
    plt.xlabel('Sparsity (% Zeros)')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{OUTPUT_DIR}/sparsity_impact.png")
    plt.close()

# ==========================================
# 2. SCALABILITY / SPEEDUP (Varying Processes)
# ==========================================
def plot_scalability():
    # Fixed parameters for this test
    FIXED_SIZE = 8192
    FIXED_SPARSITY = 0.8
    
    print(f"\n--- Experiment 2: Scalability (N={FIXED_SIZE}, S={FIXED_SPARSITY}) ---")
    
    times = []
    
    for p in PROCS:
        res = run_experiment(p, FIXED_SIZE, FIXED_SPARSITY, ITERATIONS)
        if res:
            times.append(res['csr_calc']) # Measuring calculation scaling

    # Calculate Speedup (T_1 / T_p)
    if times:
        t_base = times[0]
        speedup = [t_base / t for t in times]
        ideal = PROCS # Ideal linear speedup

        plt.figure(figsize=(10, 6))
        plt.plot(PROCS, speedup, marker='o', label='Actual Speedup', linewidth=2)
        plt.plot(PROCS, ideal, linestyle='--', color='gray', label='Ideal Speedup')
        
        plt.title(f'Parallel Scalability (Strong Scaling)\n(N={FIXED_SIZE}, Sparsity={FIXED_SPARSITY})')
        plt.xlabel('Number of Processes')
        plt.ylabel('Speedup')
        plt.xticks(PROCS)
        plt.grid(True)
        plt.legend()
        plt.savefig(f"{OUTPUT_DIR}/scalability.png")
        plt.close()

# ==========================================
# 3. MATRIX SIZE IMPACT (Varying N)
# ==========================================
def plot_size_impact():
    # Fixed parameters
    FIXED_PROCS = 4
    FIXED_SPARSITY = 0.9
    
    print(f"\n--- Experiment 3: Size Impact (P={FIXED_PROCS}, S={FIXED_SPARSITY}) ---")
    
    csr_times = []
    dense_times = []
    
    for n in SIZES:
        res = run_experiment(FIXED_PROCS, n, FIXED_SPARSITY, ITERATIONS)
        if res:
            csr_times.append(res['csr_calc'])
            dense_times.append(res['dense_calc'])

    plt.figure(figsize=(10, 6))
    plt.plot(SIZES, csr_times, marker='o', label='CSR Time')
    plt.plot(SIZES, dense_times, marker='s', label='Dense Time')
    
    plt.title(f'Execution Time vs Matrix Size\n(Procs={FIXED_PROCS}, Sparsity={FIXED_SPARSITY})')
    plt.xlabel('Matrix Dimension (N)')
    plt.ylabel('Time (seconds)')
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{OUTPUT_DIR}/size_impact.png")
    plt.close()

if __name__ == "__main__":
    print(f"Starting Experiments with executable: {EXECUTABLE}")
    print(f"Output folder: {OUTPUT_DIR}")
    
    plot_sparsity_impact()
    plot_scalability()
    plot_size_impact()
    
    print("\nAll experiments finished. Check the 'plots' directory.")