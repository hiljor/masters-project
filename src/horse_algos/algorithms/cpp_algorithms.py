import os
import sys
from horse_algos.algorithms.algorithm import Algorithm

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
        
        adj_list = graph.adjList
        node_values = graph.nodeValues
        inf_set = graph.infSet
        
        result_val, cutset = horse_algos_cpp.solve_important_separators(adj_list, node_values, inf_set, s, t, k)
        if result_val <= -1000000:
            result_val = float("-inf")
        return result_val, set(cutset)
