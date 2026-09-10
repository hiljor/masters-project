"""Empirically discovers, for each (algorithm, map) pair, the maximum k
value that can be solved in under TIME_LIMIT_SECONDS of real wall-clock
time.

Unlike a curve-fitting/regression approach, this script does the simplest
possible thing: for each map, it runs each algorithm exactly once at
k=1, 2, 3, ... (increasing), timing each run with a real stopwatch. As
soon as a run either errors out or takes longer than TIME_LIMIT_SECONDS,
it stops trying larger k values for that (algorithm, map) pair and
records the largest k that finished within the time budget.

Each probe run happens in its own subprocess (via scripts/_probe_worker.py)
so that a run which exceeds the time budget can be forcibly killed rather
than left to run to completion in the background.

The resulting table is written to
src/horse_algos/algorithms/runtime_limits.py, keyed by a structural
signature of the graph (nodes, edges, removable node count) since a
Graph object doesn't carry its source filename. horse_algos.algorithms
.cpp_algorithms then uses that table to reject (with a RuntimeError,
mirroring the existing brute-force combinatorial guard) any k above the
measured limit for a matching map, before ever starting real work.

Run with:  python scripts/find_max_k.py
"""

import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from horse_algos.tools.map_loader import load_graph_from_map  # noqa: E402

# A single run that takes longer than this is considered "too expensive".
TIME_LIMIT_SECONDS = 210.0

# Wall-clock ceiling given to the subprocess before it is forcibly killed.
# Kept slightly above TIME_LIMIT_SECONDS so the probe has a chance to
# print its own elapsed time when it lands right at the boundary.
KILL_TIMEOUT_SECONDS = TIME_LIMIT_SECONDS + 15.0

# Highest k value that will ever be probed, even if every run so far has
# stayed comfortably under the time limit.
MAX_K_TO_TRY = 15

PROBE_WORKER = Path(__file__).resolve().parent / "_probe_worker.py"
OUTPUT_PATH = REPO_ROOT / "src" / "horse_algos" / "algorithms" / "runtime_limits.py"

ALGORITHM_NAMES = [
    "Brute Force (C++)",
    "Important Separators (C++)",
    "MILP (OR-Tools)",
]


def graph_signature(graph, s, t):
    """A structural fingerprint of a graph used to look up its measured
    max-k limits at runtime, since a bare Graph object doesn't carry its
    source filename.

    Returns:
        A tuple (nodes, edges, removable) where `removable` is the number
        of nodes that are neither s, t, nor in the irremovable infSet.
    """
    nodes = len(graph.nodeValues)
    edges = sum(len(adj) for adj in graph.adjList)
    removable = len([
        i for i in range(nodes)
        if i not in graph.infSet and i != s and i != t
    ])
    return (nodes, edges, removable)


def probe_once(algo_name, map_file, k):
    """Runs a single (algorithm, map, k) probe in a subprocess.

    Returns:
        A tuple (success: bool, elapsed_seconds: float, message: str).
        `elapsed_seconds` is the wall-clock time actually observed (best
        effort even on failure/timeout).
    """
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(PROBE_WORKER), algo_name, map_file, str(k)],
            capture_output=True,
            text=True,
            timeout=KILL_TIMEOUT_SECONDS,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return False, elapsed, f"killed after exceeding {KILL_TIMEOUT_SECONDS:.0f}s"

    elapsed = time.perf_counter() - start
    # Prefer the subprocess's own more precise measurement if available.
    for line in proc.stdout.splitlines():
        if line.startswith("ELAPSED "):
            try:
                elapsed = float(line.split(" ", 1)[1])
            except ValueError:
                pass

    if proc.returncode != 0:
        message = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else f"exit code {proc.returncode}"
        return False, elapsed, message

    return True, elapsed, ""


def find_max_k(algo_name, map_file, max_k=MAX_K_TO_TRY):
    """Probes k=1, 2, 3, ... once each until a run exceeds the time limit,
    errors out, or max_k is reached.

    Returns:
        The largest k that completed successfully within
        TIME_LIMIT_SECONDS, or 0 if even k=1 failed/exceeded the limit.
    """
    last_good_k = 0
    for k in range(1, max_k + 1):
        success, elapsed, message = probe_once(algo_name, map_file, k)

        if not success:
            print(f"    k={k}: FAILED ({message}) after {elapsed:.2f}s -> stopping")
            break

        print(f"    k={k}: {elapsed:.2f}s")
        if elapsed > TIME_LIMIT_SECONDS:
            print(f"    k={k} exceeded {TIME_LIMIT_SECONDS:.0f}s limit -> stopping")
            break

        last_good_k = k

    return last_good_k


RUNTIME_LIMITS_TEMPLATE = '''"""Empirically-measured per-map k limits.

Auto-generated by scripts/find_max_k.py. Do not edit by hand; re-run the
discovery script instead if the benchmark hardware or datasets change.

For each (algorithm, map) pair, scripts/find_max_k.py ran the algorithm
once at k=1, 2, 3, ... (increasing) and timed each run with a real
stopwatch, stopping as soon as a run exceeded {time_limit:.0f} seconds or
failed. MAX_K_TABLE records the largest k that finished within that
budget, keyed by a structural signature of the graph (nodes, edges,
removable node count) since a Graph object doesn't carry its source
filename.
"""

TIME_LIMIT_SECONDS = {time_limit}

# {{algorithm_name: {{(nodes, edges, removable): max_k}}}}
MAX_K_TABLE = {table!r}


def get_max_k(algorithm_name: str, nodes: int, edges: int, removable: int):
    """Looks up the empirically-measured max k for a graph matching the
    given structural signature.

    Returns:
        The largest k known to finish within TIME_LIMIT_SECONDS for this
        (algorithm, graph shape), or None if this graph shape was not
        part of the measured datasets (in which case no limit should be
        enforced).
    """
    per_algo = MAX_K_TABLE.get(algorithm_name)
    if not per_algo:
        return None
    return per_algo.get((nodes, edges, removable))
'''


def main():
    """CLI entry point.

    Usage:
        python scripts/find_max_k.py                 # full discovery run, writes runtime_limits.py
        python scripts/find_max_k.py --dry-run [maps] # probe only, print results, don't write output
        python scripts/find_max_k.py map1.txt map2.txt  # full run limited to specific maps (still writes)
    """
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args = [a for a in args if a != "--dry-run"]

    data_dir = REPO_ROOT / "data"
    map_files = sorted(f.name for f in data_dir.glob("*.txt"))
    if args:
        map_files = [m for m in map_files if m in args]
    if not map_files:
        print(f"No matching map files found in {data_dir}")
        return

    table = {name: {} for name in ALGORITHM_NAMES}

    for map_file in map_files:
        graph, s, t = load_graph_from_map(map_file)
        signature = graph_signature(graph, s, t)
        print(f"\n=== {map_file} (nodes={signature[0]}, edges={signature[1]}, removable={signature[2]}) ===")

        for algo_name in ALGORITHM_NAMES:
            print(f"  {algo_name}:")
            max_k = find_max_k(algo_name, map_file)
            table[algo_name][signature] = max_k
            print(f"  -> max k for {map_file} within {TIME_LIMIT_SECONDS:.0f}s: {max_k}")

    if dry_run:
        print("\n--dry-run set: not writing runtime_limits.py")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(RUNTIME_LIMITS_TEMPLATE.format(
            time_limit=TIME_LIMIT_SECONDS,
            table=table,
        ))
    print(f"\nWrote max-k table to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
