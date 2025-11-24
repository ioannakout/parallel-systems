import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# ================= ΡΥΘΜΙΣΕΙΣ =================
SOURCE_FILE = "ex1.1.c"     # Το όνομα του αρχείου C
EXECUTABLE = "./ex1.1"      # Το όνομα του εκτελέσιμου
REPETITIONS = 3             # Πόσες φορές θα τρέξει κάθε πείραμα για μέσο όρο

# Λίστα με τους βαθμούς N. 
# ΠΡΟΣΟΧΗ: Το 10^6 (1000000) είναι πολύ βαρύ για τον σειριακό (O(N^2)).
# Για τα τελικά πειράματα, αν έχεις υπομονή, ξε-σχολίασε το 100000.
# Για γρήγορο έλεγχο τώρα, άσε τα μικρότερα νούμερα.
DEGREES = [1000, 5000, 10000, 20000, 50000] 

# Αριθμός νημάτων για δοκιμή
THREADS = [1, 2, 4, 8]  
# =============================================

def compile_code():
    """Μεταγλωττίζει τον C κώδικα."""
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Error: File '{SOURCE_FILE}' not found!")
        sys.exit(1)

    print(f"🔨 Compiling {SOURCE_FILE}...")
    # -O3: Optimization, -pthread: Threads, -lm: Math lib
    cmd = ["gcc", "-O3", "-pthread", SOURCE_FILE, "-o", "ex1.1", "-lm"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Compilation Failed!")
        print(result.stderr)
        sys.exit(1)
    print("✅ Compilation Successful.\n")

def parse_output(output):
    """Διαβάζει το output της C και εξάγει τους χρόνους."""
    data = {}
    
    # Regex για εντοπισμό των χρόνων στο output
    # Ψάχνει αριθμούς με υποδιαστολή μετά το "time:"
    serial_match = re.search(r"Serial execution time:\s+([0-9.]+)", output)
    parallel_match = re.search(r"Parallel execution time:\s+([0-9.]+)", output)
    verification_match = re.search(r"Verification (SUCCESSFUL|FAILED)", output)
    
    if serial_match:
        data['serial_time'] = float(serial_match.group(1))
    else:
        data['serial_time'] = None

    if parallel_match:
        data['parallel_time'] = float(parallel_match.group(1))
    else:
        data['parallel_time'] = None
        
    if verification_match:
        data['status'] = verification_match.group(1)
    else:
        data['status'] = "UNKNOWN"
        
    return data

def run_experiments():
    """Τρέχει τα πειράματα και συλλέγει δεδομένα."""
    results = []
    total_runs = len(DEGREES) * len(THREADS) * REPETITIONS
    count = 0

    print(f"🚀 Starting Experiments (Total runs: {total_runs})")
    print("-" * 60)
    print(f"{'N':<10} | {'Threads':<8} | {'Rep':<4} | {'Status':<12} | {'Serial (s)':<10} | {'Parallel (s)':<10}")
    print("-" * 60)

    for n in DEGREES:
        for t in THREADS:
            for r in range(REPETITIONS):
                count += 1
                try:
                    # Εκτέλεση: ./ex1.1 <N> <Threads>
                    cmd = [EXECUTABLE, str(n), str(t)]
                    # Timeout 5 λεπτά ανά εκτέλεση για να μην κολλήσει
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if proc.returncode != 0:
                        print(f"{n:<10} | {t:<8} | {r+1:<4} | ❌ CRASH (Segfault)")
                        continue

                    # Ανάλυση αποτελεσμάτων
                    parsed = parse_output(proc.stdout)
                    
                    # Εκτύπωση γραμμής αποτελέσματος
                    status_icon = "✅" if parsed['status'] == "SUCCESSFUL" else "❌"
                    print(f"{n:<10} | {t:<8} | {r+1:<4} | {status_icon} {parsed['status'][:7]:<9} | {parsed['serial_time']:<10.4f} | {parsed['parallel_time']:<10.4f}")

                    if parsed['status'] == "SUCCESSFUL":
                        results.append({
                            'N': n,
                            'Threads': t,
                            'Serial_Time': parsed['serial_time'],
                            'Parallel_Time': parsed['parallel_time']
                        })
                        
                except subprocess.TimeoutExpired:
                    print(f"{n:<10} | {t:<8} | {r+1:<4} | ⏰ TIMEOUT")
                except Exception as e:
                    print(f"Error: {e}")

    return pd.DataFrame(results)

def generate_plots(df):
    """Δημιουργεί τα γραφήματα."""
    if df.empty:
        print("\n⚠️ No data collected to plot.")
        return

    # Ομαδοποίηση (Group by) και Μέσος Όρος (Mean)
    avg_df = df.groupby(['N', 'Threads']).mean().reset_index()
    
    # Υπολογισμός Speedup = T_serial / T_parallel
    avg_df['Speedup'] = avg_df['Serial_Time'] / avg_df['Parallel_Time']

    print("\n📊 Averaged Results:")
    print(avg_df)

    # --- Plot 1: Χρόνος Εκτέλεσης ---
    plt.figure(figsize=(10, 6))
    for n in DEGREES:
        subset = avg_df[avg_df['N'] == n]
        if not subset.empty:
            plt.plot(subset['Threads'], subset['Parallel_Time'], marker='o', label=f'N={n}')
    
    plt.title("Parallel Execution Time vs Threads")
    plt.xlabel("Number of Threads")
    plt.ylabel("Time (seconds)")
    plt.legend()
    plt.grid(True)
    plt.savefig("execution_time.png")
    print("\n✅ Saved plot: execution_time.png")

    # --- Plot 2: Speedup (Επιτάχυνση) ---
    plt.figure(figsize=(10, 6))
    for n in DEGREES:
        subset = avg_df[avg_df['N'] == n]
        if not subset.empty:
            plt.plot(subset['Threads'], subset['Speedup'], marker='s', linestyle='--', label=f'N={n}')

    # Ιδανική Γραμμή (Ideal Speedup y=x)
    plt.plot(THREADS, THREADS, 'k:', alpha=0.5, label='Ideal Linear Speedup')
    
    plt.title("Speedup vs Threads")
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup (Serial / Parallel)")
    plt.legend()
    plt.grid(True)
    plt.savefig("speedup.png")
    print("✅ Saved plot: speedup.png")

if __name__ == "__main__":
    compile_code()
    data = run_experiments()
    generate_plots(data)
