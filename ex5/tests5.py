import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import time

# --- ΡΥΘΜΙΣΕΙΣ ---
# Διόρθωση ονομάτων αρχείων σύμφωνα με την υπόδειξή σου
SOURCES = [
    ("ex1.5a.c", "Pthread Barrier"),
    ("ex1.5b.c", "Cond Var Barrier"),
    ("ex1.5c.c", "Sense Reversal")
]

# Παράμετροι Πειράματος
# Δοκιμάζουμε 2, 4 και 8 νήματα (για να δούμε τι γίνεται όταν threads > cores)
THREAD_COUNTS = [2, 4, 8]
# Αριθμός επαναλήψεων (μεγάλος αριθμός για να μετρήσουμε διαφορές)
N_REPEATS = [100000, 1000000] 
REPEAT_EXP = 4  # 4 επαναλήψεις για μέσο όρο

def compile_all():
    print("--- Compiling C Codes ---")
    for src, label in SOURCES:
        exe = src.replace(".c", "") # π.χ. ex1.5a
        
        if not os.path.exists(src):
            print(f"Error: File {src} not found! Please check naming.")
            continue
            
        print(f"Compiling {src} -> {exe}...")
        cmd = ["gcc", "-O3", "-Wall", "-o", exe, src, "-lpthread"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Compilation failed for {src}!")
            print(result.stderr)
            exit(1)
    print("Compilation successful.\n")

def run_experiment(executable, threads, n):
    times = []
    
    for i in range(REPEAT_EXP):
        try:
            # Εκτέλεση: ./ex1.5a <threads> <repeats>
            result = subprocess.run(
                [f"./{executable}", str(threads), str(n)], 
                capture_output=True, 
                text=True, 
                timeout=30 # Λίγο μεγαλύτερο timeout για τα βαριά πειράματα
            )
            output = result.stdout
            
            # Regex για να πιάσουμε τον χρόνο (ψάχνουμε "seconds")
            # Δέχεται και τελεία και κόμμα
            match = re.search(r":\s+([0-9.,]+)\s+seconds", output, re.IGNORECASE)

            if match:
                val = float(match.group(1).replace(',', '.'))
                times.append(val)
            else:
                print(f"    Run {i+1}: Error parsing output for {executable} (T={threads})")

        except subprocess.TimeoutExpired:
            print(f"    Run {i+1}: TIMEOUT! (Skipping {executable} T={threads})")
            return None

    return np.mean(times) if times else 0

def main():
    compile_all()

    results = []

    print(f"{'Method':<20} {'Threads':<10} {'Repeats(N)':<12} {'Avg Time(s)':<15}")
    print("-" * 60)

    # Τρέχουμε τα πειράματα
    for src, label in SOURCES:
        exe = src.replace(".c", "")
        if not os.path.exists(exe): continue

        for n in N_REPEATS:
            for t in THREAD_COUNTS:
                avg_time = run_experiment(exe, t, n)
                
                # Αν αποτύχει (π.χ. timeout), βάζουμε 0 ή None
                display_time = avg_time if avg_time else 0.0
                
                print(f"{label:<20} {t:<10} {n:<12} {display_time:<15.4f}")

                results.append({
                    "Method": label,
                    "Threads": t,
                    "Repeats": n,
                    "Time (s)": display_time
                })

    # --- SAVE CSV ---
    df = pd.DataFrame(results)
    df.to_csv("ex1_5_results.csv", index=False)
    print("\n[OK] Results saved to 'ex1_5_results.csv'")

    # --- 1. TABLE IMAGE ---
    plt.figure(figsize=(10, len(results)*0.5 + 2))
    ax = plt.gca()
    ax.axis('off')
    
    # Διαμόρφωση πίνακα για καλύτερη εμφάνιση
    df_pivot = df.pivot(index=['Method', 'Repeats'], columns='Threads', values='Time (s)')
    
    table = ax.table(cellText=df_pivot.round(4).values, 
                     colLabels=[f"{t} Threads" for t in df_pivot.columns], 
                     rowLabels=[f"{m} (N={n})" for m, n in df_pivot.index],
                     loc='center', cellLoc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    plt.title("Barrier Execution Times (Seconds)", y=1.05)
    plt.savefig("ex1_5_table.png", bbox_inches='tight', dpi=300)
    print("[OK] Table image saved to 'ex1_5_table.png'")

    # --- 2. BAR CHARTS (Ένα για κάθε N) ---
    for n in N_REPEATS:
        plt.figure(figsize=(10, 6))
        subset = df[df["Repeats"] == n]
        
        # Bar Chart αντί για Line επειδή συγκρίνουμε μεθόδους
        bar_width = 0.25
        x = np.arange(len(THREAD_COUNTS))
        
        methods = subset["Method"].unique()
        for i, method in enumerate(methods):
            data = subset[subset["Method"] == method]
            # Ευθυγράμμιση δεδομένων με τα x (σε περίπτωση που λείπουν τιμές)
            times = []
            for t in THREAD_COUNTS:
                row = data[data["Threads"] == t]
                if not row.empty:
                    times.append(row["Time (s)"].values[0])
                else:
                    times.append(0)
            
            plt.bar(x + i*bar_width, times, width=bar_width, label=method)

        plt.title(f'Barrier Performance Comparison (N = {n})')
        plt.xlabel('Number of Threads')
        plt.ylabel('Execution Time (seconds)')
        plt.xticks(x + bar_width, THREAD_COUNTS)
        plt.grid(True, alpha=0.3, axis='y')
        plt.legend()
        
        filename = f"ex1_5_chart_N_{n}.png"
        plt.savefig(filename)
        print(f"[OK] Graph saved to '{filename}'")

if __name__ == "__main__":
    main()
