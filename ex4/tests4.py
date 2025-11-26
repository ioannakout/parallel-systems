import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Βεβαιώσου ότι αυτό είναι το σωστό path/όνομα για το εκτελέσιμο
# Αφού κάνεις make test4, το εκτελέσιμο θα είναι στο φάκελο ex4/
EXECUTABLE = "ex4/ex1.4" 

# Έλεγχος αν υπάρχει το αρχείο
if not os.path.exists(EXECUTABLE):
    # Δοκιμή εναλλακτικού (αν τρέχει μέσα από το ex4/)
    if os.path.exists("./ex1.4"):
        EXECUTABLE = "./ex1.4"

sizes = [10000]
PERTHREAD = [1000, 5000, 10000]
RATIOS = [10, 30, 50]
threads_list = [1, 2, 4, 8]
locktype = [0, 1, 2, 3]

lock_names = {
    0: "Coarse-Mutex",
    1: "Fine-Mutex",
    2: "Coarse-RWLock",
    3: "Fine-RWLock",
}

results = []

print("Running tests...\n")

# ===============================
#   RUN PROGRAM AND COLLECT DATA
# ===============================
for locks in locktype:
    for threads in threads_list:
        for transaction in PERTHREAD:
            for ratio in RATIOS:
                
                # Προετοιμασία εντολής
                cmd = [
                    EXECUTABLE,
                    str(sizes[0]),
                    str(transaction),
                    str(ratio),
                    str(locks),
                    str(threads)
                ]

                try:
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True # Θα πετάξει error αν το C πρόγραμμα κρασάρει
                    )

                    # extract time from program output
                    # C Output format: "Elapsed time: 0.001234 seconds"
                    time_ms = None
                    for line in result.stdout.splitlines():
                        if "Elapsed time" in line:
                            try:
                                # Παίρνουμε το προτελευταίο στοιχείο (τον αριθμό)
                                time_sec = float(line.split()[-2])
                                # Μετατροπή σε ms για να ταιριάζει με το plot label
                                time_ms = time_sec * 1000.0 
                            except ValueError:
                                print(f"Error parsing time from line: {line}")
                                pass

                    if time_ms is not None:
                        results.append({
                            "locktype": locks,
                            "threads": threads,
                            "transactionsPerThread": transaction,
                            "ratio": ratio,
                            "time": time_ms,
                        })
                    else:
                        print(f"Warning: No time found for settings: {cmd}")

                except subprocess.CalledProcessError as e:
                    print(f"Error running command: {' '.join(cmd)}")
                    print(e.stderr)
                except FileNotFoundError:
                    print(f"Error: Executable '{EXECUTABLE}' not found.")
                    print("Please run 'make test4' first to compile the C program.")
                    sys.exit(1)

# Convert to DataFrame
df = pd.DataFrame(results)

if df.empty:
    print("No results collected. Check executable path and output format.")
    sys.exit(1)

print("\nCollected Data (First 5 rows):")
print(df.head())


for lock in locktype:
    # Φιλτράρισμα για τον συγκεκριμένο τύπο κλειδώματος
    df_lock = df[df["locktype"] == lock]

    if df_lock.empty:
        continue

    plt.figure(figsize=(10, 6))

    for ratio in RATIOS:
        df_ratio = df_lock[df_lock["ratio"] == ratio]
        
        # ΕΠΙΛΟΓΗ: Plotting για κάθε txs amount ξεχωριστά για να μην μπερδεύονται οι γραμμές
        for tx in PERTHREAD:
            df_plot = df_ratio[df_ratio["transactionsPerThread"] == tx]
            
            # Sort by threads to ensure line is drawn correctly
            df_plot = df_plot.sort_values(by="threads")

            plt.plot(
                df_plot["threads"],
                df_plot["time"],
                marker="o",
                label=f"Reads {ratio}% (TransactionsPerThread: {tx})"
            )

    plt.title(f"Performance — {lock_names[lock]}")
    plt.xlabel("Threads")
    plt.ylabel("Time (ms)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    filename = f"plot_{lock_names[lock].replace('-', '_')}.png"
    plt.savefig(filename)
    plt.close()

print("\nPlots saved.")