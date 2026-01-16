import subprocess
import re
import matplotlib.pyplot as plt
import os
import statistics

# --- 1. ΡΥΘΜΙΣΕΙΣ ---
EXECUTABLE = "./ex3.2"       # Το εκτελέσιμο
MACHINES_FILE = "machines"
OUTPUT_DIR = "plots"     # Νέος φάκελος για τα αποτελέσματα
ITERATIONS_INNER = 1         # Επαναλήψεις MESA στο C (το κρατάμε χαμηλά)
REPEATS = 4                  # Πόσες φορές θα τρέξουμε το κάθε τεστ (Python level)

# Μεγέθη Πινάκων
SIZES = [1024, 2048, 4096, 8192]

# Ποσοστά Μηδενικών
SPARSITIES = [0.0, 0.4, 0.8, 0.9, 0.99]

# Διεργασίες (Μέχρι 10 PC x 4 Cores = 40, προσαρμοσμένο για να μην κολλάει)
PROCS = [1, 2, 4, 8, 16, 32, 64]

# --- 2. PRE-CHECK ---
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- 3. CORE FUNCTION ΜΕ AVERAGE ---
def run_experiment_avg(procs, size, sparsity, iterations):
    csr_times = []
    dense_times = []
    
    # Τρέχουμε το πείραμα REPEATS φορές
    for i in range(REPEATS):
        cmd = ["mpiexec"]
        if procs > 1 and os.path.exists(MACHINES_FILE):
            cmd.extend(["-f", MACHINES_FILE])
        
        cmd.extend(["-n", str(procs), EXECUTABLE, str(size), str(sparsity), str(iterations)])
        
        try:
            # Timeout για να μην περιμένουμε αιώνια αν κολλήσει
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
            
            # Parsing
            m_csr = re.search(r"CSR Parallel Calc.*?([0-9]+\.[0-9]+)", result.stdout)
            m_dense = re.search(r"Dense Parallel Calc.*?([0-9]+\.[0-9]+)", result.stdout)
            
            if m_csr: csr_times.append(float(m_csr.group(1)))
            if m_dense: dense_times.append(float(m_dense.group(1)))
            
        except subprocess.TimeoutExpired:
            print(f"      [Run {i+1}/{REPEATS}] Timeout! Skipping...")
        except Exception as e:
            # Αν αποτύχει μια φορά, δεν σταματάμε, πάμε στην επόμενη
            print(f"      [Run {i+1}/{REPEATS}] Error: {e}")

    # Υπολογισμός Μέσου Όρου (αν έχουμε αποτελέσματα)
    avg_csr = statistics.mean(csr_times) if csr_times else None
    avg_dense = statistics.mean(dense_times) if dense_times else None
    
    return avg_csr, avg_dense

# --- 4. ΓΡΑΦΗΜΑ 1: SCALABILITY (SPEEDUP) ---
def plot_scalability():
    print("\n=== 1. Scalability (Averaged over 4 runs) ===")
    fixed_sparsity = 0.2  # Βάζουμε 0.2 (πιο πυκνό) για να δούμε SPEEDUP!
    
    plt.figure(figsize=(10, 6))
    
    for size in SIZES:
        print(f"Testing N={size}...", end=" ", flush=True)
        active_procs = []
        speedups = []
        base_time = None 
        
        for p in PROCS:
            csr, _ = run_experiment_avg(p, size, fixed_sparsity, ITERATIONS_INNER)
            
            if csr:
                if p == 1: base_time = csr # Κρατάμε τον χρόνο του P=1
                
                if base_time:
                    s = base_time / csr
                    active_procs.append(p)
                    speedups.append(s)
                    # Debug print για να βλέπεις τι γίνεται
                    print(f" [P={p} -> {s:.2f}x]", end="", flush=True)
        
        if speedups:
            plt.plot(active_procs, speedups, marker='o', label=f'N={size}')
        print(" Done.")

    # Ιδανική γραμμή
    plt.plot(PROCS, PROCS, 'k--', alpha=0.3, label='Ideal')
    
    plt.title(f'Average Speedup vs Processes\n(Sparsity={fixed_sparsity}, Runs={REPEATS})')
    plt.xlabel('Processes')
    plt.ylabel('Speedup')
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{OUTPUT_DIR}/scalability_avg.png")
    plt.close()

# --- 5. ΓΡΑΦΗΜΑ 2: CSR vs DENSE ---
def plot_csr_dense():
    print("\n=== 2. CSR vs Dense (Averaged) ===")
    fixed_size = 8192
    fixed_proc = 4
    
    csr_res = []
    dense_res = []
    
    print(f"Testing N={fixed_size}, P={fixed_proc}...", end=" ", flush=True)
    for s in SPARSITIES:
        c, d = run_experiment_avg(fixed_proc, fixed_size, s, ITERATIONS_INNER)
        if c is not None:
            csr_res.append(c)
            dense_res.append(d)
        else:
            csr_res.append(0)
            dense_res.append(0)
    print(" Done.")

    plt.figure(figsize=(10, 6))
    plt.plot(SPARSITIES, csr_res, 'b-o', label='CSR (Average)')
    plt.plot(SPARSITIES, dense_res, 'r--s', label='Dense (Average)')
    
    plt.title(f'CSR vs Dense Execution Time\n(N={fixed_size}, P={fixed_proc})')
    plt.xlabel('Sparsity')
    plt.ylabel('Time (sec)')
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{OUTPUT_DIR}/csr_dense_avg.png")
    plt.close()

# --- 6. ΓΡΑΦΗΜΑ 3: SIZE IMPACT ---
def plot_size_impact():
    print("\n=== 3. Size Impact (Averaged) ===")
    fixed_sparsity = 0.2
    test_procs = [1, 8, PROCS[-1]] # 1, 8 και Max
    
    plt.figure(figsize=(10, 6))
    
    for p in test_procs:
        print(f"Testing P={p}...", end=" ", flush=True)
        times = []
        sizes_tested = []
        
        for size in SIZES:
            c, _ = run_experiment_avg(p, size, fixed_sparsity, ITERATIONS_INNER)
            if c:
                times.append(c)
                sizes_tested.append(size)
        
        plt.plot(sizes_tested, times, marker='s', label=f'P={p}')
        print(" Done.")

    plt.title(f'Time vs Matrix Size\n(Sparsity={fixed_sparsity})')
    plt.xlabel('Matrix Size (N)')
    plt.ylabel('Time (sec)')
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{OUTPUT_DIR}/size_impact_avg.png")
    plt.close()

if __name__ == "__main__":
    if not os.path.exists(EXECUTABLE):
        print("Error: Compile first!")
    else:
        plot_scalability()
        plot_csr_dense()
        plot_size_impact()
        print(f"\nAll plots saved in {OUTPUT_DIR}/")