import subprocess
import re
import sys
import os

# --- Ρυθμίσεις ---
C_SOURCE_FILE = "ex1.2.c"
EXECUTABLE = "./ex1.2"

# Συνδυασμοί για έλεγχο
# Δοκιμάζουμε: 1, 2, 4, 8, 16 νήματα
THREAD_COUNTS = [1, 2, 4, 8, 16]
# Δοκιμάζουμε: 1 εκ., 5 εκ., 10 εκ. επαναλήψεις ανά νήμα
ITERATION_COUNTS = [1000000, 4000000, 7000000]

def compile_c_code():
    """Μεταγλωττίζει τον C κώδικα."""
    print(f"--- Μεταγλώττιση του {C_SOURCE_FILE} ---")
    # Προσθέτουμε το -D_GNU_SOURCE για συμβατότητα και -O3 για βελτιστοποίηση
    cmd = ["gcc", "-g", "-Wall", "-o", EXECUTABLE, C_SOURCE_FILE, "-lpthread"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Σφάλμα κατά τη μεταγλώττιση:")
        print(result.stderr)
        sys.exit(1)
    print("Επιτυχής μεταγλώττιση.\n")

def parse_output(output):
    """Εξάγει τη μέθοδο και τον χρόνο από την έξοδο του C προγράμματος."""
    results = {}
    # Regex για να ταιριάζει με τη μορφή: [Method    ] ... | Χρόνος: 0.1234 sec
    # Προσαρμόστε το αν αλλάξετε τα printf στον C κώδικα
    pattern = re.compile(r'\[(.*?)\s*\] .*? Χρόνος:\s*([\d\.]+)\s*sec')
    
    for line in output.splitlines():
        match = pattern.search(line)
        if match:
            method = match.group(1).strip()
            time_sec = float(match.group(2))
            results[method] = time_sec
    return results

def run_benchmark():
    """Τρέχει τα τεστ και τυπώνει τα αποτελέσματα."""
    # Κεφαλίδα Πίνακα
    print(f"{'Threads':<8} | {'Iterations':<12} | {'Method':<10} | {'Time (sec)':<10}")
    print("-" * 50)

    for iters in ITERATION_COUNTS:
        print(f"\n--- Testing with {iters} iterations per thread ---")
        for threads in THREAD_COUNTS:
            try:
                # Εκτέλεση του C προγράμματος
                cmd = [EXECUTABLE, str(threads), str(iters)]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                
                if proc.returncode != 0:
                    print(f"Error running with {threads} threads: {proc.stderr}")
                    continue

                # Ανάλυση αποτελεσμάτων
                data = parse_output(proc.stdout)
                
                # Εκτύπωση αποτελεσμάτων για κάθε μέθοδο που βρέθηκε
                for method, time_val in data.items():
                    print(f"| {threads:<8} | {iters:<12} | {method:<10} | {time_val:.4f} |")
                
                print(f"-------------------------------------------------")

            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    if not os.path.exists(C_SOURCE_FILE):
        print(f"Δεν βρέθηκε το αρχείο {C_SOURCE_FILE}. Βεβαιωθείτε ότι είναι στον ίδιο φάκελο.")
        sys.exit(1)
        
    compile_c_code()
    run_benchmark()