import sys
import os
from pathlib import Path

# Add the project root and src directory to sys.path to allow running as a script
repo_root = Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root))
sys.path.append(str(repo_root / "src"))

from horse_algos.tools.map_loader import load_graph_from_map, load_graph_from_lines
from horse_algos.algorithms.naive import Naive
from horse_algos.algorithms.important_separator import ImportantSeparators
from horse_algos.algorithms.milp_ortools import MILP_OR, MILP_AVAILABLE
from horse_algos.algorithms.cpp_algorithms import CppNaive, CppImportantSeparators, CPP_AVAILABLE
from horse_algos.timer.timer import AlgorithmTimer
from data.generate import TEST_SIZES, generate_size_test

def run_benchmarks():
    """Runs a set of benchmarks on the algorithms using available data."""
    print("Starting benchmarks...")
    csv_path = repo_root / "benchmark_results.csv"
    timer = AlgorithmTimer(csv_path=str(csv_path))
    
    # Automatically discover datasets in the data directory
    data_dir = repo_root / "data"
    datasets = sorted([f.name for f in data_dir.glob("*.txt")])
    
    if not datasets:
        print(f"No datasets found in {data_dir}")
        return

    # Algorithms to test
    algorithms = [
        Naive(),
        ImportantSeparators(),
    ]

    # Add C++ implementations when available
    if CPP_AVAILABLE:
        algorithms.extend([CppNaive(), CppImportantSeparators()])
    else:
        print("C++ implementations not available; skipping C++ benchmarks.")

    # Add MILP when available
    if MILP_AVAILABLE:
        algorithms.append(MILP_OR())
    else:
        print("Google OR-Tools not available; skipping MILP benchmarks.")
    
    # Parameters for testing
    k_values = [1, 2, 3]

    ## RUN FILE DATASETS
    for dataset in datasets:
        try:
            graph, s, t = load_graph_from_map(dataset)
            print(f"Loaded {dataset}: {len(graph.nodeValues)} nodes")
            
            for k in k_values:
                for algo in algorithms:
                    print(f"Running {algo.name} on {dataset} with k={k}...")
                    timer.time_algorithm(algo, dataset, graph, s, t, k)
                    
        except FileNotFoundError as e:
            print(f"Error loading {dataset}: {e}")
        except Exception as e:
            print(f"An error occurred while processing {dataset}: {e}")
    
    ## RUN GENERATED DATASETS
    for size in TEST_SIZES:
        try:
            level_map = generate_size_test(size)
            map_lines = ["".join(row) for row in level_map]
            graph, s, t = load_graph_from_lines(map_lines)
            print(f"Generated test of size {size}x{size}")
            
            for k in k_values:
                for algo in algorithms:
                    print(f"Running {algo.name} on generated size {size} with k={k}...")
                    timer.time_algorithm(algo, f"Generated_{size}x{size}", graph, s, t, k)
                    
        except Exception as e:
            print(f"An error occurred while processing generated size {size}: {e}")

    # Confirm that algorithms that ran the same test produced the same result
    results_by_test = {}
    for result in timer.results:
        test_key = (result.dataset_name, result.parameters['k'])
        if test_key not in results_by_test:
            results_by_test[test_key] = result.result
        else:
            if results_by_test[test_key] != result.result:
                print(f"Warning: Inconsistent results for {result.dataset_name} with k={result.parameters['k']}")
                print(f"Previous result: {results_by_test[test_key]}, Current result: {result.result}")

    print("\nBenchmark Results:")
    print(timer.get_summary())
    print(f"\nResults exported to {csv_path}")

if __name__ == "__main__":
    run_benchmarks()
