import subprocess
import re
import sys
import os
import matplotlib.pyplot as plt

# Files to compile and execute
C_SOURCE_FILE = "ex1.2.c"
EXECUTABLE = "./ex1.2"

# The different testing threads and number of iterations per thread
THREAD_COUNTS = [1, 2, 4, 8, 16]
ITERATION_COUNTS = [1_000_000, 5_000_000, 10_000_000]

# The three different methods that the code runs on
METHODS = ["Mutex", "RWLock", "Atomic"]

# Compile C
def compile_c_code():
    # Compile with the right flags
    cmd = ["gcc", "-g", "-Wall", "-o", EXECUTABLE, C_SOURCE_FILE, "-lpthread"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # If the code could not be compiled
    if result.returncode != 0:
        print("Compile error:")
        print(result.stderr)
        sys.exit(1)


def parse_output(output):
    results = {}
    pattern = re.compile(r'\[(.*?)\s*\].*?Χρόνος:\s*([\d\.]+)\s*sec')

    for line in output.splitlines():
        match = pattern.search(line)
        if match:
            method = match.group(1).strip()
            time_sec = float(match.group(2))
            results[method] = time_sec
    return results


# Run the different tests initialized above
def run_benchmark():
    all_results = {method: {} for method in METHODS}

    print(f"{'Threads':<8} | {'Iterations':<12} | {'Method':<10} | Time")

    # Nested for loop so each thread count runs on all different iterations
    for iters in ITERATION_COUNTS:
        for threads in THREAD_COUNTS:

            cmd = [EXECUTABLE, str(threads), str(iters)]
            proc = subprocess.run(cmd, capture_output=True, text=True)

            if proc.returncode != 0:
                print("ERROR:", proc.stderr)
                continue

            parsed = parse_output(proc.stdout)

            for method, time_val in parsed.items():
                print(f"{threads:<8} | {iters:<12} | {method:<10} | {time_val:.4f}s")

                if iters not in all_results[method]:
                    all_results[method][iters] = []
                all_results[method][iters].append(time_val)

    return all_results


# Creating a plot for each method used
def plot_per_method(all_results):
    for method in METHODS:
        plt.figure()
        for iterations in ITERATION_COUNTS:
            times = all_results[method][iterations]
            plt.plot(THREAD_COUNTS, times, marker="o", label=f"{iterations} iters")

        plt.title(f"{method} – Time per thread")
        plt.xlabel("Threads")
        plt.ylabel("Time (sec)")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"plot_{method}.png")
        print(f"Saved plot: plot_{method}.png")
        plt.close()


# Comparison on each method for each fixed iteration
def plot_comparison_fixed_iters(all_results):
    for iterations in ITERATION_COUNTS:
        plt.figure()

        for method in METHODS:
            times = all_results[method][iterations]
            plt.plot(THREAD_COUNTS, times, marker="o", label=method)

        plt.title(f"Comparison – {iterations} iterations per thread")
        plt.xlabel("Threads")
        plt.ylabel("Time (sec)")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"compare_{iterations}.png")
        print(f"Saved: compare_{iterations}.png")
        plt.close()


if __name__ == "__main__":
    if not os.path.exists(C_SOURCE_FILE):
        print(f"File {C_SOURCE_FILE} doesn't exist.")
        sys.exit(1)

    compile_c_code()
    results = run_benchmark()

    plot_per_method(results)
    plot_comparison_fixed_iters(results)