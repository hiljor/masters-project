import math
import os
import sys
from horse_algos.algorithms.algorithm import Algorithm
from horse_algos.algorithms.runtime_limits import TIME_LIMIT_SECONDS, get_max_k

# Try to add DLL directory for MinGW if on Windows
if sys.platform == "win32":
    # This is a bit of a hack, but necessary if built with MinGW
    # Ideally, the user environment should have this or we bundle it.
    mingw_path = "C:\\msys64\\ucrt64\\bin"
    if os.path.exists(mingw_path):
        os.add_dll_directory(mingw_path)

try:
    from horse_algos import horse_algos_cpp
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False

class CppNaive(Algorithm):
    """C++ implementation of the Brute Force (Naive) algorithm."""
    @property
    def name(self):
        return "Brute Force (C++)"

    def run(self, graph, s: int, t: int, k: int):
        """Runs the C++ brute force solver on the given graph."""
        if not CPP_AVAILABLE:
            raise ImportError("C++ extension not available")
        removable_nodes = [i for i in range(len(graph.nodeValues))
                           if i not in graph.infSet and i != s and i != t]
        n_removable = len(removable_nodes)
        if k > n_removable:
            raise RuntimeError(
                f"Brute force C++ cannot remove {k} nodes when only {n_removable} are removable."
            )

        # Primary guard: reject k values that our empirical measurements
        # (see scripts/find_max_k.py, which runs each map once at
        # increasing k and stops as soon as a run exceeds the time
        # budget) found to take too long to run on a map with this exact
        # shape.
        edges = sum(len(adj) for adj in graph.adjList)
        max_k = get_max_k(self.name, len(graph.nodeValues), edges, n_removable)
        if max_k is not None:
            if k > max_k:
                raise RuntimeError(
                    f"Brute force C++ too expensive: k={k} exceeds the empirically "
                    f"measured max k={max_k} (nodes={len(graph.nodeValues)}, edges={edges}, "
                    f"removable={n_removable}) that completes within "
                    f"{TIME_LIMIT_SECONDS:,.0f}s."
                )
        else:
            # Fallback guard: this graph shape was never measured by
            # scripts/find_max_k.py (e.g. a custom map drawn in the web
            # UI), so fall back to a static combinatorial cap to protect
            # against a runaway choose(n_removable, k) blowup.
            max_combinations = 100_000_000
            combinations = math.comb(n_removable, k)
            if combinations > max_combinations:
                raise RuntimeError(
                    f"Brute force C++ too expensive: choose({n_removable},{k}) = {combinations:,} > {max_combinations:,}."
                )

        # Convert graph to format expected by C++
        # C++ solve_naive expects: adj_list (list of lists), node_values (list), inf_set (set), s, t, k
        adj_list = graph.adjList
        node_values = graph.nodeValues
        inf_set = graph.infSet
        
        result_val, cutset = horse_algos_cpp.solve_naive(adj_list, node_values, inf_set, s, t, k)
        if result_val <= -1000000:
            result_val = float("-inf")
        return result_val, set(cutset)

class CppImportantSeparators(Algorithm):
    """C++ implementation of the Important Separators algorithm."""
    @property
    def name(self):
        return "Important Separators (C++)"

    def run(self, graph, s: int, t: int, k: int):
        """Runs the C++ important separators solver on the given graph."""
        if not CPP_AVAILABLE:
            raise ImportError("C++ extension not available")

        # Reject k values that our empirical measurements (see
        # scripts/find_max_k.py, which runs each map once at increasing k
        # and stops as soon as a run exceeds the time budget) found to
        # take too long to run on a map with this exact shape. Important
        # Separators' runtime grows roughly exponentially in k, so this
        # guard protects against multi-hour runs on large k values.
        removable_nodes = [i for i in range(len(graph.nodeValues))
                           if i not in graph.infSet and i != s and i != t]
        edges = sum(len(adj) for adj in graph.adjList)
        max_k = get_max_k(self.name, len(graph.nodeValues), edges, len(removable_nodes))
        if max_k is not None and k > max_k:
            raise RuntimeError(
                f"Important Separators C++ too expensive: k={k} exceeds the "
                f"empirically measured max k={max_k} (nodes={len(graph.nodeValues)}, "
                f"edges={edges}, removable={len(removable_nodes)}) that completes "
                f"within {TIME_LIMIT_SECONDS:,.0f}s."
            )

        adj_list = graph.adjList
        node_values = graph.nodeValues
        inf_set = graph.infSet
        
        result_val, cutset = horse_algos_cpp.solve_important_separators(adj_list, node_values, inf_set, s, t, k)
        if result_val <= -1000000:
            result_val = float("-inf")
        return result_val, set(cutset)

