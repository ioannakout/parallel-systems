import subprocess
import re
import sys
import os
import matplotlib.pyplot as plt
import statistics

# ---------------- CONFIGURATION ----------------
C_SOURCE_FILE = "ex1.2.c"
EXECUTABLE = "./ex1.2"

# Running for different thread count and iterations per each thread
THREAD_COUNTS = [1, 2, 4, 8, 16]
ITERATION_COUNTS = [1_000_000, 5_000_000, 10_000_000]

# The locks the exercise is running on and the number of times it will run to find the average speed
METHODS = ["Mutex", "RWLock", "Atomic"]
NUM_RUNS = 4

# Compiling the .c code
def compile_c_code():
    print("Compiling C code...")

    # Command to compile the code in the terminal
    cmd = ["gcc", "-g", "-Wall", "-o", EXECUTABLE, C_SOURCE_FILE, "-lpthread"]
    result = subprocess.run(cmd, capture_output=True, text=True) # Running the command
    if result.returncode != 0: # Fail case
        print("Compile error:", result.stderr)
        sys.exit(1)
    print("Compilation successful.\n")

# Parse
def parse_output(output):
    results = {}
    pattern = re.compile(r'\[(.*?)\s*\].*?Time:\s*([\d\.]+)\s*sec')
    for line in output.splitlines():
        match = pattern.search(line)
        if match:
            method = match.group(1).strip()
            time_sec = float(match.group(2))
            results[method] = time_sec
    return results

# Benchmark
def run_benchmark():

    final_data = {m: {t: {} for t in THREAD_COUNTS} for m in METHODS}
    
    # Total time the program will run on every thread
    total_steps = len(ITERATION_COUNTS) * len(THREAD_COUNTS) * NUM_RUNS
    current_step = 0
    print(f"Starting Benchmark ({NUM_RUNS} runs per config)...")

    # For all iterations and for all the threads
    for iters in ITERATION_COUNTS:
        for threads in THREAD_COUNTS:
            # Store temporary variable
            temp_times = {m: [] for m in METHODS}

            # Running the test 4 times
            for r in range(NUM_RUNS):
                current_step += 1   # Change the step
                print(f"\rProgress: {current_step}/{total_steps} (T:{threads}, N:{iters}, Run:{r+1})", end='', flush=True)

                # Run the code for each count of thread and iteration count
                cmd = [EXECUTABLE, str(threads), str(iters)]
                proc = subprocess.run(cmd, capture_output=True, text=True)

                if proc.returncode != 0: # Fail check
                    continue

                # Parse the answer
                parsed = parse_output(proc.stdout)

                for m, t_val in parsed.items():
                    if m in temp_times:
                        temp_times[m].append(t_val)

            
            for m in METHODS:
                if temp_times[m]:
                    avg = statistics.mean(temp_times[m])
                    final_data[m][threads][iters] = avg

    print("\nBenchmark completed.\n")
    return final_data

# Combined Table
def save_combined_table_image(data):
    """
    Creates an image that stores 2d-arrays (Iterations per Thread, Amount of threads) that stores
    the time it took for the proccess to finish on each cell for all the methods the excercise runs on. 
    """
    # Figure with 3 subplots and 1 column
    # Increase height for breathing room
    fig, axes = plt.subplots(len(METHODS), 1, figsize=(10, 12))
    
    # In case there is only 1 method, then this 1 variable would not be a list, so we make it so it is one for the plot
    if len(METHODS) == 1:
        axes = [axes]

    fig.suptitle(f"Execution Time Comparison (Average of {NUM_RUNS} runs)", fontsize=16, y=0.98)

    # Column names
    col_labels = [str(x) for x in ITERATION_COUNTS]

    # For each method available
    for i, method in enumerate(METHODS):
        ax = axes[i]
        ax.axis('off')

        # Prepare the data for the array
        row_labels = []
        cell_text = []
        for t in THREAD_COUNTS:
            row_labels.append(f"{t} threads")
            row_data = []
            for iters in ITERATION_COUNTS:
                val = data[method][t].get(iters, 0.0)
                row_data.append(f"{val:.4f}")
            cell_text.append(row_data)

        # Array title
        ax.set_title(f"Method: {method}", fontsize=12, fontweight='bold', loc='center')

        # Create the array
        table = ax.table(cellText=cell_text,
                         rowLabels=row_labels,
                         colLabels=col_labels,
                         loc='center',
                         cellLoc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

    # Adjust distance to avoid array collision
    plt.tight_layout(rect=[0, 0, 1, 0.96]) 
    
    # Name it and save it in the directory
    filename = "comparison_table.png"
    plt.savefig(filename, bbox_inches='tight', dpi=150)
    plt.close()

# Time vs Thread
def plot_time_vs_threads(data):

    # For all the methods available
    for method in METHODS:

        # Start drawing
        plt.figure(figsize=(10, 6))

        # For the different iterations per thread chosen
        for iters in ITERATION_COUNTS:
            times = [] # Empty list
            for t in THREAD_COUNTS: # Run for all thread counts
                times.append(data[method][t][iters]) # Append each value
            plt.plot(THREAD_COUNTS, times, marker='o', label=f"{iters} iters")

        # Create the graph
        plt.title(f"Execution Time vs Threads ({method})")
        plt.xlabel("Number of Threads")
        plt.ylabel("Time (seconds)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(THREAD_COUNTS)
        plt.savefig(f"plot_time_{method}.png")
        plt.close()

# Run main
if __name__ == "__main__":
    if not os.path.exists(C_SOURCE_FILE):
        print(f"Error: {C_SOURCE_FILE} not found.")
        sys.exit(1)

    compile_c_code()
    results = run_benchmark()

    # Combined table fo precise time comparison
    save_combined_table_image(results)

    # Plots that showcase each locks different speed-up or slow-down
    plot_time_vs_threads(results)