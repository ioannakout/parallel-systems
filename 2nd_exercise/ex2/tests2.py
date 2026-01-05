import subprocess
import re
import csv
import statistics

# ================= ΡΥΘΜΙΣΕΙΣ ΠΕΙΡΑΜΑΤΩΝ =================
EXECUTABLE = "./ex2.2"
OUTPUT_FILE = "results.csv"
RUNS_PER_EXPERIMENT = 4  # Πόσες φορές θα τρέξει το κάθε πείραμα για μέσο όρο

# Ορίστε εδώ τις παραμέτρους που θέλετε να δοκιμάσετε
# Παράδειγμα: Strong Scaling (Σταθερό N, αλλάζουμε Threads)
THREADS_LIST = [1, 2, 4, 8, 16]
SIZES_LIST = [1000, 5000]     # N
SPARSITIES_LIST = [0.6, 0.9]  # 0.6 = 60% zeros
LOOPS = 1000                  # Επαναλήψεις μέσα στη C (inner loop)

def parse_output(output):
    """
    Διαβάζει το κείμενο που τυπώνει η C και εξάγει τους χρόνους.
    Προσαρμόστε τα regex αν αλλάξετε τα print στη C.
    """
    # Regex patterns με βάση τα μηνύματα που μου έστειλες
    csr_pattern = r"CSR multiplication.*?took\s+(\d+\.\d+)\s+seconds"
    dense_pattern = r"Dense multiplication.*?took\s+(\d+\.\d+)\s+seconds"
    create_pattern = r"CSR creation.*?took\s+(\d+\.\d+)\s+seconds"

    csr_match = re.search(csr_pattern, output)
    dense_match = re.search(dense_pattern, output)
    create_match = re.search(create_pattern, output)

    return {
        "csr_time": float(csr_match.group(1)) if csr_match else None,
        "dense_time": float(dense_match.group(1)) if dense_match else None,
        "create_time": float(create_match.group(1)) if create_match else None,
    }

def run_experiment():
    results = []
    
    # Άνοιγμα αρχείου CSV για εγγραφή
    with open(OUTPUT_FILE, mode='w', newline='') as csv_file:
        fieldnames = ['Size', 'Sparsity', 'Threads', 'Loops', 'Avg_Create_Time', 'Avg_CSR_Time', 'Avg_Dense_Time', 'Speedup']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        total_experiments = len(SIZES_LIST) * len(SPARSITIES_LIST) * len(THREADS_LIST)
        current_exp = 0

        for n in SIZES_LIST:
            for sp in SPARSITIES_LIST:
                for th in THREADS_LIST:
                    current_exp += 1
                    print(f"--- Experiment {current_exp}/{total_experiments}: N={n}, Sparsity={sp}, Threads={th} ---")
                    
                    temp_csr = []
                    temp_dense = []
                    temp_create = []

                    # Εκτέλεση πολλές φορές για μέσο όρο
                    for r in range(RUNS_PER_EXPERIMENT):
                        # Εντολή: ./ex2.2 1000 0.6 1000 4
                        # ΠΡΟΣΟΧΗ: Βεβαιώσου ότι η σειρά των ορισμάτων ταιριάζει με τη main σου!
                        cmd = [EXECUTABLE, str(n), str(sp), str(LOOPS), str(th)]
                        
                        try:
                            # Εκτέλεση της εντολής
                            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                            output = result.stdout
                            
                            parsed = parse_output(output)
                            
                            if parsed['csr_time'] is not None: temp_csr.append(parsed['csr_time'])
                            if parsed['dense_time'] is not None: temp_dense.append(parsed['dense_time'])
                            if parsed['create_time'] is not None: temp_create.append(parsed['create_time'])

                        except subprocess.CalledProcessError as e:
                            print(f"Error running command: {e}")
                        except Exception as e:
                            print(f"An unexpected error occurred: {e}")

                    # Υπολογισμός Μέσων Όρων
                    if temp_csr:
                        avg_csr = statistics.mean(temp_csr)
                        avg_create = statistics.mean(temp_create)
                        # Ο Dense μπορεί να μην τρέχει πάντα ή να είναι πολύ αργός
                        avg_dense = statistics.mean(temp_dense) if temp_dense else 0.0
                        
                        # Υπολογισμός Speedup (Dense / CSR)
                        speedup = avg_dense / avg_csr if avg_csr > 0 and avg_dense > 0 else 0

                        # Εγγραφή στο CSV
                        writer.writerow({
                            'Size': n,
                            'Sparsity': sp,
                            'Threads': th,
                            'Loops': LOOPS,
                            'Avg_Create_Time': f"{avg_create:.6f}",
                            'Avg_CSR_Time': f"{avg_csr:.6f}",
                            'Avg_Dense_Time': f"{avg_dense:.6f}",
                            'Speedup': f"{speedup:.4f}"
                        })
                        
                        print(f"   Avg CSR: {avg_csr:.4f}s | Avg Dense: {avg_dense:.4f}s | Speedup: {speedup:.2f}x")
                        # Flush για να γράφονται τα δεδομένα αμέσως
                        csv_file.flush()

    print(f"\nAll experiments finished. Results saved in {OUTPUT_FILE}")

if __name__ == "__main__":
    run_experiment()