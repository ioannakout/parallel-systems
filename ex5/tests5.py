import subprocess
import re
import statistics
import os
import sys
import matplotlib.pyplot as plt

# --- ΡΥΘΜΙΣΕΙΣ ---
PROGRAMS = [
    {"src": "ex1.5a.c", "exe": "ex1.5a", "name": "1.5a (Pthread Barrier)"},
    {"src": "ex1.5b.c", "exe": "ex1.5b", "name": "1.5b (Mutex/Cond)"},
    {"src": "ex1.5c.c", "exe": "ex1.5c", "name": "1.5c (Sense Reversal)"},
]

# Νήματα για εκτέλεση
THREAD_COUNTS = [1, 2, 4, 8]

# Επαναλήψεις για εκτέλεση (Όλα όσα θες να τρέξουν)
ITERATION_COUNTS = [1000, 10000, 100000, 1000000]

# Επαναλήψεις ΜΟΝΟ για τα ΓΡΑΦΙΚΑ
ITERATIONS_TO_PLOT = [100000, 1000000]

# Πόσες φορές να τρέξει το κάθε πείραμα
REPEATS = 4

def compile_programs():
    print("--- Compilation Started ---")
    for prog in PROGRAMS:
        cmd = ["gcc", "-g", "-Wall", "-o", prog["exe"], prog["src"], "-lpthread"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✔ Compiled {prog['src']} successfully.")
            else:
                print(f"✘ Error compiling {prog['src']}:\n{result.stderr}")
                sys.exit(1)
        except FileNotFoundError:
            print("Error: GCC not found.")
            sys.exit(1)
    print("--- Compilation Finished ---\n")

def run_single_experiment(exe, threads, loops):
    times = []
    print(f"   Running {exe} (Threads: {threads}, Loops: {loops})...", end=" ", flush=True)

    for _ in range(REPEATS):
        cmd = [f"./{exe}", str(threads), str(loops)]
        try:
            # --- Η ΑΛΛΑΓΗ ΕΔΩ ---
            # timeout=60: Αν περάσει το 1 λεπτό, το σταματάει.
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = result.stdout
            
            # Ψάχνουμε τον αριθμό πριν το "seconds"
            match = re.search(r"([\d\.]+)\s*seconds", output, re.IGNORECASE)
            
            if match:
                times.append(float(match.group(1)))
            else:
                print(f"\n❌ Error parsing output! Output:\n{output}")
                return None

        except subprocess.TimeoutExpired:
            # Εδώ μπαίνει αν περάσουν τα 60 δευτερόλεπτα
            print("❌ TIMED OUT (>60s) - Deadlock or too slow!")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    avg = statistics.mean(times) if times else 0
    print(f"✔ Done ({avg:.6f}s)")
    return avg

def create_plots(results):
    print("\nGenerating Plots for selected iterations...")
    
    for loops in ITERATIONS_TO_PLOT:
        # Έλεγχος αν υπάρχουν δεδομένα για αυτό το loop
        has_data = False
        for prog in PROGRAMS:
             if results[prog["name"]].get(loops):
                 has_data = True
                 break
        
        if not has_data:
            print(f"⚠ Skipping plot for {loops} (No successful runs)")
            continue

        plt.figure(figsize=(10, 6))
        
        for prog in PROGRAMS:
            prog_name = prog["name"]
            data = results[prog_name].get(loops, [])
            
            if data:
                threads = [d[0] for d in data]
                times = [d[1] for d in data]
                plt.plot(threads, times, marker='o', label=prog_name)

        plt.title(f'Barrier Performance ({loops} Iterations)')
        plt.xlabel('Number of Threads')
        plt.ylabel('Average Time (seconds)')
        plt.grid(True)
        plt.legend()
        
        filename = f'plot_{loops}.png'
        plt.savefig(filename)
        print(f"✔ Saved graph: {filename}")
        plt.close()

def main():
    compile_programs()
    
    all_results = {prog["name"]: {loop: [] for loop in ITERATION_COUNTS} for prog in PROGRAMS}

    print(f"\n{'Algorithm':<25} | {'Loops':<10} | {'Threads':<8} | {'Avg Time (s)':<15}")
    print("-" * 65)

    for prog in PROGRAMS:
        for loops in ITERATION_COUNTS:
            for threads in THREAD_COUNTS:
                avg_time = run_single_experiment(prog["exe"], threads, loops)
                
                if avg_time is not None:
                    print(f"{prog['name']:<25} | {loops:<10} | {threads:<8} | {avg_time:.6f}")
                    all_results[prog["name"]][loops].append((threads, avg_time))
        print("-" * 65)

    try:
        create_plots(all_results)
    except Exception as e:
        print(f"Could not create plots: {e}")

    # Cleanup
    for prog in PROGRAMS:
        if os.path.exists(prog["exe"]):
            os.remove(prog["exe"])

if __name__ == "__main__":
    main()
