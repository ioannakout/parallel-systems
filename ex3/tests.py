import os

# --- ΡΥΘΜΙΣΕΙΣ ---
PROGRAM = "./ex1.3"      # Το εκτελέσιμο
LOOPS = 4                # Επαναλήψεις για μέσο όρο

# Λίστα με τα Ν που θέλουμε να δοκιμάσουμε
# 100.000, 1.000.000, 10.000.000, 100.000.000
SIZES = [100000, 1000000, 10000000, 100000000]

print(f"=== ΕΝΑΡΞΗ ΠΕΙΡΑΜΑΤΩΝ ΓΙΑ ΤΟ {PROGRAM} ===\n")

for N in SIZES:
    print(f"--> Δοκιμή με μέγεθος N = {N} (Τρέχει {LOOPS} φορές)...")
    
    sum_init = 0
    sum_par = 0
    sum_ser = 0
    
    for i in range(LOOPS):
        # Εκτέλεση εντολής
        cmd = f"{PROGRAM} {N}"
        output = os.popen(cmd).read()
        
        # Ανάγνωση γραμμή-γραμμή
        for line in output.split('\n'):
            # Μετατροπή σε μικρά (lower) για να μην έχουμε θέμα με κεφαλαία/μικρά
            line_lower = line.lower()
            
            try:
                if "initialization time" in line_lower:
                    parts = line.split()
                    sum_init += float(parts[-2]) # Παίρνουμε τον αριθμό πριν το "seconds"
                    
                elif "parallel execution time" in line_lower:
                    parts = line.split()
                    sum_par += float(parts[-2])
                    
                elif "serial execution time" in line_lower:
                    parts = line.split()
                    sum_ser += float(parts[-2])
            except ValueError:
                continue # Αν αποτύχει η μετατροπή σε αριθμό, προχωράμε

    # Υπολογισμός Μέσων Όρων
    avg_init = sum_init / LOOPS
    avg_par = sum_par / LOOPS
    avg_ser = sum_ser / LOOPS
    
    print(f"    [N={N}] Avg Init:     {avg_init:.6f} sec")
    print(f"    [N={N}] Avg Parallel: {avg_par:.6f} sec")
    print(f"    [N={N}] Avg Serial:   {avg_ser:.6f} sec")
    
    # Υπολογισμός Speedup (Επιτάχυνση)
    if avg_par > 0:
        speedup = avg_ser / avg_par
        print(f"    [N={N}] Speedup:      {speedup:.4f}x")
        if speedup < 1:
            print("            (Παρατήρηση: Ο παράλληλος είναι ΠΙΟ ΑΡΓΟΣ λόγω False Sharing)")
    else:
        print("    [N={N}] Speedup:      N/A")
        
    print("-" * 50)

print("\nΌλα τα πειράματα ολοκληρώθηκαν.")
