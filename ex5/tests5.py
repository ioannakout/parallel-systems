import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import time

# --- ΡΥΘΜΙΣΕΙΣ ---
SOURCES = [
    ("ex1.5a.c", "Pthread Barrier"),
    ("ex1.5b.c", "Cond Var Barrier"),
    ("ex1.5c.c", "Sense Reversal")
]

# Παράμετροι Πειράματος
THREAD_COUNTS = [2, 4, 8]
N_REPEATS = [100000, 1000000]
REPEAT_EXP = 4  # Επαναλήψεις για μέσο όρο

def compile_all():
    print("--- Compiling C Codes ---")
    for src, label in SOURCES:
        exe = src.replace(".c", "")
        
        if not os.path.exists(src):
            print(f"Error: File {src} not found!")
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
                timeout=40  # Timeout ασφαλείας
            )
            output = result.stdout
            
            # Regex για ανάγνωση χρόνου (π.χ. "Time: 0.1234 seconds")
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
    plt.figure(figsize=(12, len(results)*0.5 + 2))
    ax = plt.gca()
    ax.axis('off')
    
    # Δημιουργία Pivot Table
    df_pivot = df.pivot(index=['Method', 'Repeats'], columns='Threads', values='Time (s)')
    
    # --- ΔΙΟΡΘΩΣΗ ΣΕΙΡΑΣ ---
    # Ορίζουμε ρητά τη σειρά που θέλουμε να εμφανίζονται στον πίνακα
    desired_order = [
        ("Pthread Barrier", 100000), ("Pthread Barrier", 1000000),
        ("Cond Var Barrier", 100000), ("Cond Var Barrier", 1000000),
        ("Sense Reversal", 100000), ("Sense Reversal", 1000000)
    ]
    # Επαναταξινόμηση
    df_pivot = df_pivot.reindex(desired_order)
    
    table = ax.table(cellText=df_pivot.round(4).values, 
                     colLabels=[f"{t} Threads" for t in df_pivot.columns], 
                     rowLabels=[f"{m} (N={n})" for m, n in df_pivot.index],
                     loc='center', cellLoc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    plt.title("Barrier Execution Times (Seconds)", y=1.05)
    plt.savefig("ex1_5_table_corrected.png", bbox_inches='tight', dpi=300)
    print("[OK] Table image saved to 'ex1_5_table_corrected.png'")

    # --- 2. BAR CHARTS ---
    for n in N_REPEATS:
        plt.figure(figsize=(10, 6))
        subset = df[df["Repeats"] == n]
        
        bar_width = 0.25
        x = np.arange(len(THREAD_COUNTS))
        
        # Ορίζουμε σταθερή σειρά για τα Bars
        method_order = ["Pthread Barrier", "Cond Var Barrier", "Sense Reversal"]
        
        for i, method in enumerate(method_order):
            data = subset[subset["Method"] == method]
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