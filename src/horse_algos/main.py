import sys
import os
from pathlib import Path
from horse_algos.tools.map_loader import load_graph_from_map
from horse_algos.algorithms.naive import Naive
from horse_algos.algorithms.important_separator import ImportantSeparators
from horse_algos.timer.timer import AlgorithmTimer

def run_benchmarks():
    """Runs a set of benchmarks on the algorithms using available data."""
    timer = AlgorithmTimer()
    
    # Automatically discover datasets in the data directory
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "data"
    datasets = sorted([f.name for f in data_dir.glob("*.txt")])
    
    if not datasets:
        print(f"No datasets found in {data_dir}")
        return

    # Algorithms to test
    algorithms = [
        Naive(),
        ImportantSeparators()
    ]
    
    # Parameters for testing
    k_values = [1, 2, 3]

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

    print("\nBenchmark Results:")
    print(timer.get_summary())

    # Export to CSV
    csv_path = repo_root / "benchmark_results.csv"
    timer.to_csv(str(csv_path))
    print(f"\nResults exported to {csv_path}")

if __name__ == "__main__":
    run_benchmarks()
