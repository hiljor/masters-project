"""Run and plot an extended runtime experiment.

Usage:
    python scripts/diamond_test.py --map horse_dots.txt --name diamond_test
"""

import csv
import json
import statistics
import subprocess
import sys
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP_NAME = "horse_dots.txt"
DEFAULT_EXPERIMENT_NAME = "diamond_test"
MAX_K = 20
REPETITIONS = 10
TIMEOUT_SECONDS = 600.0
KILL_GRACE_SECONDS = 20.0
WORKER_COUNT = 8
CASE_WORKER = Path(__file__).resolve().parent / "_diamond_case_worker.py"
ALGORITHM_NAMES = [
    "Brute Force (C++)",
    "Important Separators (C++)",
    "MILP (OR-Tools)",
]


def run_case(algorithm_name, k, map_name):
    command = [
        sys.executable,
        str(CASE_WORKER),
        algorithm_name,
        map_name,
        str(k),
        str(TIMEOUT_SECONDS),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + KILL_GRACE_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "algorithm": algorithm_name,
            "k": k,
            "success": False,
            "result": None,
            "error": "TIMEOUT",
            "runtimes": [],
        }

    output = completed.stdout.strip().splitlines()
    if output:
        try:
            payload = json.loads(output[-1])
            payload.update({"algorithm": algorithm_name, "k": k})
            return payload
        except json.JSONDecodeError:
            pass

    error = completed.stderr.strip() or f"worker exited with code {completed.returncode}"
    return {
        "algorithm": algorithm_name,
        "k": k,
        "success": False,
        "result": None,
        "error": error,
        "runtimes": [],
    }


def stats(runtimes):
    if not runtimes:
        return [0.0] * 7
    mean = statistics.mean(runtimes)
    standard_deviation = statistics.stdev(runtimes) if len(runtimes) > 1 else 0.0
    return [
        statistics.median(runtimes),
        mean,
        standard_deviation,
        min(runtimes),
        max(runtimes),
        statistics.quantiles(runtimes, n=20)[18] if len(runtimes) > 1 else runtimes[0],
        standard_deviation / mean * 100 if mean else 0.0,
    ]


def write_results(rows, csv_path, map_name):
    header = [
        "Algorithm", "Dataset", "k", "Median (s)", "Mean (s)",
        "Std Dev (s)", "Min (s)", "Max (s)", "P95 (s)", "CV (%)",
        "Result", "Raw Runtimes",
    ]
    with csv_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for row in rows:
            values = stats(row["runtimes"])
            writer.writerow([
                row["algorithm"], map_name, row["k"],
                *[f"{value:.6f}" for value in values[:6]],
                f"{values[6]:.2f}",
                row["result"] if row["success"] else f"ERROR: {row['error']}",
                json.dumps(row["runtimes"]),
            ])


def plot_results(rows, image_path, legend_fontsize=20):
    colors = {
        "Brute Force (C++)": "blue",
        "Important Separators (C++)": "orange",
        "MILP (OR-Tools)": "green",
    }
    figure, axis = plt.subplots(figsize=(30, 14))
    figure.subplots_adjust(left=0.06, right=0.98, bottom=0.12, top=0.94)

    all_runtimes = [runtime for row in rows for runtime in row["runtimes"] if runtime > 0]
    for algorithm_name in ALGORITHM_NAMES:
        algorithm_rows = [row for row in rows if row["algorithm"] == algorithm_name]
        completed = [row for row in algorithm_rows if row["success"]]
        if completed:
            line, = axis.plot(
                [row["k"] for row in completed],
                [statistics.median(row["runtimes"]) for row in completed],
                marker="o", linewidth=2, markersize=14, label=algorithm_name,
                color=colors[algorithm_name],
            )
            axis.fill_between(
                [row["k"] for row in completed],
                [min(row["runtimes"]) for row in completed],
                [max(row["runtimes"]) for row in completed],
                color=line.get_color(), alpha=0.2, linewidth=0, zorder=1,
            )
        timed_out = [row for row in algorithm_rows if row.get("error") == "TIMEOUT"]
        if timed_out:
            axis.scatter(
                [row["k"] for row in timed_out],
                [TIMEOUT_SECONDS] * len(timed_out),
                marker="x", s=250, linewidths=3, color=colors[algorithm_name],
            )

    axis.set_xlabel("k", fontsize=42)
    axis.set_ylabel("Time (seconds)", fontsize=42)
    axis.tick_params(axis="both", labelsize=34)
    axis.set_xticks(range(1, MAX_K + 1))
    axis.set_yscale("log")
    axis.set_ylim(bottom=min(all_runtimes) * 0.7, top=TIMEOUT_SECONDS * 1.25)
    axis.minorticks_on()
    axis.grid(True, which="major", alpha=0.5)
    axis.grid(True, which="minor", linestyle=":", alpha=0.42)
    axis.legend(fontsize=legend_fontsize, markerscale=0.8, loc="upper left", frameon=True)

    figure.savefig(image_path, dpi=180)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=DEFAULT_MAP_NAME, dest="map_name")
    parser.add_argument("--name", default=DEFAULT_EXPERIMENT_NAME, dest="experiment_name")
    arguments = parser.parse_args()

    results_dir = REPO_ROOT / "results"
    image_dir = REPO_ROOT / "data" / "img"
    results_dir.mkdir(exist_ok=True)
    image_dir.mkdir(exist_ok=True)
    csv_path = results_dir / f"{arguments.experiment_name}.csv"
    image_path = image_dir / f"{arguments.experiment_name}.png"
    rows = []
    # Each algorithm advances independently. A timeout at one k removes only
    # that algorithm from later cases; other algorithms keep progressing.
    active_algorithms = set(ALGORITHM_NAMES)

    with ProcessPoolExecutor(max_workers=WORKER_COUNT) as executor:
        for k in range(1, MAX_K + 1):
            futures = {
                executor.submit(run_case, algorithm_name, k, arguments.map_name): algorithm_name
                for algorithm_name in sorted(active_algorithms)
            }
            for future in as_completed(futures):
                row = future.result()
                rows.append(row)
                status = "completed" if row["success"] else row["error"]
                print(f"{row['algorithm']} k={k}: {status}", flush=True)
                if not row["success"]:
                    active_algorithms.discard(row["algorithm"])
            if not active_algorithms:
                break

    rows.sort(key=lambda row: (row["algorithm"], row["k"]))
    write_results(rows, csv_path, arguments.map_name)
    legend_fontsize = 30 if arguments.experiment_name == "dry_portals_test" else 20
    plot_results(rows, image_path, legend_fontsize=legend_fontsize)
    print(f"Saved {csv_path}")
    print(f"Saved {image_path}")


if __name__ == "__main__":
    main()