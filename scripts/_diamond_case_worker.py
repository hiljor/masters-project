"""Run one diamond_test algorithm/k case in an isolated process."""

import json
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from horse_algos.tools.map_loader import load_graph_from_map
from horse_algos.algorithms import cpp_algorithms, milp_ortools
from horse_algos.algorithms.cpp_algorithms import CppImportantSeparators, CppNaive
from horse_algos.algorithms.milp_ortools import MILP_OR

# diamond_test measures its own 600-second stopping point rather than using
# the older empirical k table generated for the regular benchmark suite.
cpp_algorithms.get_max_k = lambda *_args: None
milp_ortools.get_max_k = lambda *_args: None

ALGORITHMS = {
    "Brute Force (C++)": CppNaive,
    "Important Separators (C++)": CppImportantSeparators,
    "MILP (OR-Tools)": MILP_OR,
}


def run_once(algorithm, graph, start, target, k, timeout_seconds):
    result_box = {"result": None, "error": None}

    def invoke():
        try:
            result_box["result"] = algorithm.run(graph, start, target, k)
        except Exception as error:  # report algorithm errors to the parent
            result_box["error"] = f"{type(error).__name__}: {error}"

    started = time.perf_counter()
    thread = threading.Thread(target=invoke, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    elapsed = time.perf_counter() - started

    if thread.is_alive():
        return False, None, elapsed, "TIMEOUT"
    if result_box["error"] is not None:
        return False, None, elapsed, result_box["error"]
    return True, result_box["result"], elapsed, None


def main():
    if len(sys.argv) != 5:
        raise SystemExit(
            "Usage: _diamond_case_worker.py <algorithm> <map> <k> <timeout>"
        )

    algorithm_name, map_name, k_text, timeout_text = sys.argv[1:]
    algorithm_class = ALGORITHMS[algorithm_name]
    graph, start, target = load_graph_from_map(map_name)
    algorithm = algorithm_class()
    k = int(k_text)
    timeout_seconds = float(timeout_text)
    runtimes = []
    final_result = None

    for _ in range(10):
        success, result, elapsed, error = run_once(
            algorithm, graph, start, target, k, timeout_seconds
        )
        if not success:
            print(json.dumps({
                "success": False,
                "result": None,
                "error": error,
                "runtimes": runtimes,
            }))
            return
        runtimes.append(elapsed)
        final_result = result

    print(json.dumps({
        "success": True,
        "result": str(final_result),
        "error": None,
        "runtimes": runtimes,
    }))


if __name__ == "__main__":
    main()