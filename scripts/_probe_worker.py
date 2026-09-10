"""Internal worker used by scripts/find_max_k.py to time a single
(algorithm, map, k) run in an isolated subprocess.

Running each probe in its own subprocess (rather than in-process with a
thread-based timeout) means the parent script can forcibly kill a probe
that runs past the time budget, instead of merely giving up waiting on a
background thread that keeps consuming CPU.

Usage:
    python scripts/_probe_worker.py <algorithm> <map_file> <k>

Prints "ELAPSED <seconds>" to stdout on success and exits 0.
Exits non-zero (with the error printed to stderr) on failure.
"""

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from horse_algos.tools.map_loader import load_graph_from_map  # noqa: E402
from horse_algos.algorithms.cpp_algorithms import CppNaive, CppImportantSeparators  # noqa: E402
from horse_algos.algorithms.milp_ortools import MILP_OR  # noqa: E402

ALGORITHMS = {
    "Brute Force (C++)": CppNaive,
    "Important Separators (C++)": CppImportantSeparators,
    "MILP (OR-Tools)": MILP_OR,
}


def main():
    if len(sys.argv) != 4:
        print("Usage: _probe_worker.py <algorithm> <map_file> <k>", file=sys.stderr)
        sys.exit(2)

    algo_name, map_file, k_str = sys.argv[1], sys.argv[2], sys.argv[3]
    k = int(k_str)

    algo_cls = ALGORITHMS.get(algo_name)
    if algo_cls is None:
        print(f"Unknown algorithm: {algo_name}", file=sys.stderr)
        sys.exit(2)

    graph, s, t = load_graph_from_map(map_file)
    algorithm = algo_cls()

    start = time.perf_counter()
    try:
        algorithm.run(graph, s, t, k)
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        print(f"ELAPSED {elapsed}")
        sys.exit(1)
    elapsed = time.perf_counter() - start
    print(f"ELAPSED {elapsed}")
    sys.exit(0)


if __name__ == "__main__":
    main()
