import subprocess
import sys
import time

# ================= ΡΥΘΜΙΣΕΙΣ =================
C_SOURCE_FILE = "ex1.1.c"      # <--- ΒΕΒΑΙΩΣΟΥ ΟΤΙ ΤΟ ΟΝΟΜΑ ΕΙΝΑΙ ΙΔΙΟ ΜΕ ΤΟ C ΑΡΧΕΙΟ ΣΟΥ
EXECUTABLE = "poly_app"
OUTPUT_FILE = "results.txt"

# Παράμετροι N: Βάζουμε μεγάλα νούμερα επειδή η time() μετράει δευτερόλεπτα
DEGREES_N = [20000, 40000, 60000, 80000] 
THREAD_COUNTS = [1, 2, 4, 8] 
REPETITIONS = 3 
# =============================================

def run_command(cmd_list):
    try:
        result = subprocess.run(cmd_list, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Σφάλμα: {' '.join(cmd_list)}")
        print(e.stderr)
        sys.exit(1)

def main():
    print(f"--- Έναρξη Πειραμάτων (Αρχείο: {C_SOURCE_FILE}) ---")

    # 1. Compile
    print("--> Μεταγλώττιση...")
    run_command(["gcc", "-O3", "-o", EXECUTABLE, C_SOURCE_FILE, "-lpthread"])
    print("--> Επιτυχία!\n")

    # 2. Run Experiments
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Results (Date: {time.ctime()})\n=================================\n")
        
        for n in DEGREES_N:
            print(f"\nTest: Degree N={n}")
            f.write(f"\n>>> Degree N={n} <<<\n")
            for t in THREAD_COUNTS:
                f.write(f"--- Threads: {t} ---\n")
                for r in range(1, REPETITIONS + 1):
                    print(f"  Threads {t}, Run {r}...", end=" ", flush=True)
                    output = run_command([f"./{EXECUTABLE}", str(n), str(t)])
                    f.write(f"Run #{r}:\n{output}\n")
                    print("Done.")

    print(f"\nΤέλος! Τα αποτελέσματα είναι στο αρχείο: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
