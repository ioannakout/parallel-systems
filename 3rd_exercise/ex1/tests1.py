import subprocess
import re
import matplotlib.pyplot as plt

# --- ΡΥΘΜΙΣΕΙΣ ---
MPI_EXEC = "./ex3.1"
OMP_EXEC = "./ex2.1"

# Προτεινόμενες τιμές για να δεις αποτελέσματα
DEGREES = [1000, 10000, 100000] 
PROCESSES = [1, 2, 4, 8, 16, 32, 64]
REPETITIONS = 4
MACHINES_FILE = "machines"

results = {}

def run_command(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.stdout
    except Exception as e:
        print(f"Error: {e}")
        return ""

def parse_time(output, regex):
    match = re.search(regex, output)
    if match:
        return float(match.group(1))
    return None

print("=== ΕΝΑΡΞΗ ΠΕΙΡΑΜΑΤΩΝ ===")

for n in DEGREES:
    print(f"\n---> Τρέχοντας για N = {n}...")
    results[n] = {'mpi': {}, 'omp': {}, 'omp_serial': 0.0}
    
    # 1. MPI (ex3.1)
    # Κλήση: mpiexec -n <p> ./ex3.1 <n>
    for p in PROCESSES:
        times = []
        for r in range(REPETITIONS):
            out = run_command(["mpiexec", "-f", MACHINES_FILE, "-n", str(p), MPI_EXEC, str(n)])
            t = parse_time(out, r"Total time:\s*([0-9\.]+)")
            if t is not None: times.append(t)
        
        avg_t = sum(times)/len(times) if times else 0
        results[n]['mpi'][p] = avg_t
        print(f"   MPI (P={p}): {avg_t:.6f} s")

    # 2. OpenMP (ex2.1)
    # ΔΙΟΡΘΩΣΗ: Κλήση ./ex2.1 <n> <threads>
    serial_vals = []
    for p in PROCESSES:
        times = []
        for r in range(REPETITIONS):
            # ΕΔΩ ΕΓΙΝΕ Η ΑΛΛΑΓΗ (n πρώτα, μετά p)
            out = run_command([OMP_EXEC, str(n), str(p)])
            
            t_par = parse_time(out, r"parallel time:\s*([0-9\.]+)")
            t_ser = parse_time(out, r"serial time:\s*([0-9\.]+)")
            
            if t_par: times.append(t_par)
            if t_ser: serial_vals.append(t_ser)
        
        avg_t = sum(times)/len(times) if times else 0
        results[n]['omp'][p] = avg_t
        print(f"   OMP (P={p}): {avg_t:.6f} s")
    
    results[n]['omp_serial'] = sum(serial_vals)/len(serial_vals) if serial_vals else 0

print("\n=== ΔΗΜΙΟΥΡΓΙΑ ΓΡΑΦΗΜΑΤΩΝ ===")

target_n = DEGREES[-1] # Παίρνουμε το μεγαλύτερο N για τα plots επιτάχυνσης
p_list = PROCESSES

# --- ΓΡΑΦΗΜΑ 1: MPI PERFORMANCE (TIME & SPEEDUP) ---
mpi_times = [results[target_n]['mpi'][p] for p in p_list]
mpi_base = results[target_n]['mpi'][1]
mpi_speedup = [(mpi_base/t if t>0 else 0) for t in mpi_times]

fig, ax1 = plt.subplots(figsize=(10, 6))

color = 'tab:blue'
ax1.set_xlabel('Processes (P)')
ax1.set_ylabel('Execution Time (s)', color=color)
ax1.plot(p_list, mpi_times, marker='o', color=color, linewidth=2, label='MPI Time')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle='--', alpha=0.5)

ax2 = ax1.twinx()  
color = 'tab:orange'
ax2.set_ylabel('Speedup', color=color)  
ax2.plot(p_list, mpi_speedup, marker='s', linestyle='--', color=color, linewidth=2, label='MPI Speedup')
ax2.tick_params(axis='y', labelcolor=color)

plt.title(f'MPI Performance: Time vs Speedup (N={target_n})')
plt.xticks(p_list)
fig.tight_layout()
plt.savefig('mpi_performance.png')
print("Created: mpi_performance.png")

# --- ΓΡΑΦΗΜΑ 2: MPI SCALABILITY (TIME vs N) ---
plt.figure(figsize=(10, 6))
for p in PROCESSES:
    y_values = [results[n]['mpi'][p] for n in DEGREES]
    plt.plot(DEGREES, y_values, marker='o', label=f'MPI P={p}')

plt.xlabel('Polynomial Degree (N)')
plt.ylabel('Time (sec)')
plt.title('MPI Scalability: Time vs Degree N')
plt.legend()
plt.grid(True, linestyle='--')
plt.savefig('mpi_scalability.png')
print("Created: mpi_scalability.png")

# --- ΓΡΑΦΗΜΑ 3: COMPARISON (MPI vs OMP) ---
omp_times = [results[target_n]['omp'][p] for p in p_list]
serial_time = results[target_n]['omp_serial']

omp_spd = [(serial_time/t if t>0 else 0) for t in omp_times]
mpi_spd = [(serial_time/t if t>0 else 0) for t in mpi_times]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Time Subplot
ax1.plot(p_list, mpi_times, marker='o', label='MPI', color='blue')
ax1.plot(p_list, omp_times, marker='s', label='OpenMP', color='green')
ax1.axhline(y=serial_time, color='red', linestyle='--', label='Serial')
ax1.set_title(f'Time Comparison (N={target_n})')
ax1.set_xlabel('Threads/Processes')
ax1.set_ylabel('Time (s)')
ax1.legend()
ax1.grid(True)
ax1.set_xticks(p_list)

# Speedup Subplot
ax2.plot(p_list, mpi_spd, marker='o', label='MPI Speedup', color='blue')
ax2.plot(p_list, omp_spd, marker='s', label='OpenMP Speedup', color='green')
ax2.plot(p_list, p_list, 'k:', label='Ideal', alpha=0.5)
ax2.set_title(f'Speedup Comparison (N={target_n})')
ax2.set_xlabel('Threads/Processes')
ax2.set_ylabel('Speedup')
ax2.legend()
ax2.grid(True)
ax2.set_xticks(p_list)

plt.tight_layout()
plt.savefig('comparison_final.png')
print("Created: comparison_final.png")