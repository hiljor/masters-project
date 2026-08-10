import sys
import os
import multiprocessing
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from horse_algos.visual.visualise import load_and_visualize_benchmarks

# Add the project root and src directory to sys.path to allow running as a script
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))

from horse_algos.tools.map_loader import load_graph_from_map, load_graph_from_lines
from horse_algos.algorithms.naive import Naive
from horse_algos.algorithms.important_separator import ImportantSeparators
from horse_algos.algorithms.milp_ortools import MILP_OR, MILP_AVAILABLE
from horse_algos.algorithms.cpp_algorithms import CppNaive, CppImportantSeparators, CPP_AVAILABLE
from horse_algos.timer.timer import TIMEOUT_SECONDS, AlgorithmTimer, run_algorithm_timed, TimerResult
from data.generate import TEST_SIZES, generate_size_test


def finalize_benchmark_results(timer: AlgorithmTimer, csv_path: Path) -> None:
  """Finalizes and outputs benchmark results after all threads complete.
  
  This function:
  - Checks for consistency between algorithm results on the same test
  - Prints a summary of all results
  - Exports results to CSV file
  - Prints export confirmation
  
  Args:
      timer: The AlgorithmTimer instance with recorded results
      csv_path: Path to the CSV file for export
  """
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
  timer.to_csv(str(csv_path))
  print(f"\nResults exported to {csv_path}")


def finalize_size_test_results(timer: AlgorithmTimer, csv_path: Path) -> None:
  """Finalizes and outputs size test results after all threads complete.
  
  This function:
  - Prints a summary of all results
  - Exports results to CSV file
  - Prints export confirmation
  
  Args:
      timer: The AlgorithmTimer instance with recorded results
      csv_path: Path to the CSV file for export
  """
  print("\nSize Test Results:")
  print(timer.get_summary())
  timer.to_csv(str(csv_path))
  print(f"\nSize test results exported to {csv_path}")


def run_benchmarks():
  """Runs a set of benchmarks on the algorithms using available data."""
  print("Starting benchmarks...")
  results_dir = repo_root / "results"
  results_dir.mkdir(parents=True, exist_ok=True)
  csv_path = results_dir / "benchmark_results.csv"
  timer = AlgorithmTimer(csv_path=str(csv_path))
  
  # Automatically discover datasets in the data directory
  data_dir = repo_root / "data"
  datasets = sorted([f.name for f in data_dir.glob("*.txt")])
  
  if not datasets:
      print(f"No datasets found in {data_dir}")
      return

  # Algorithms to test
  algorithms = [
      #Naive(),
      #ImportantSeparators(),
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
  k_values = range(1, 16)
  worker_count = 10

  def benchmark_tasks():
      tasks = []

      for dataset in datasets:
          try:
              graph, s, t = load_graph_from_map(dataset)
              print(f"Loaded {dataset}: {len(graph.nodeValues)} nodes")
              for k in k_values:
                  for algo in algorithms:
                      tasks.append((algo, dataset, graph, s, t, k))
          except FileNotFoundError as e:
              print(f"Error loading {dataset}: {e}")
          except Exception as e:
              print(f"An error occurred while loading {dataset}: {e}")

      for size in TEST_SIZES:
          try:
              level_map = generate_size_test(size)
              map_lines = ["".join(row) for row in level_map]
              graph, s, t = load_graph_from_lines(map_lines)
              print(f"Generated test of size {size}x{size}")
              for k in k_values:
                  for algo in algorithms:
                      tasks.append((algo, f"Generated_{size}x{size}", graph, s, t, k))
          except Exception as e:
              print(f"An error occurred while generating size {size}: {e}")

      return tasks

  tasks = benchmark_tasks()

  with ProcessPoolExecutor(max_workers=worker_count) as executor:
      future_to_task = {
          executor.submit(run_algorithm_timed, algo, dataset, graph, s, t, k, str(csv_path)):
          (algo.name, dataset, k)
          for algo, dataset, graph, s, t, k in tasks
      }

      for future in as_completed(future_to_task):
          algo_name, dataset, k = future_to_task[future]
          try:
              # timeout here is a safety net; worker enforces actual timeout internally
              result = future.result(timeout=TIMEOUT_SECONDS + 10)
              timer.record_result(result)
          except Exception as exc:
              error_result = TimerResult(
                  algorithm_name=algo_name,
                  dataset_name=dataset,
                  execution_time=0.0,
                  result=f"ERROR: {type(exc).__name__}: {exc}",
                  parameters={"s": 0, "t": 0, "k": k},
              )
              timer.record_result(error_result)
              print(f"Benchmark {algo_name} on {dataset} k={k} failed: {exc}")

  finalize_benchmark_results(timer, csv_path)
    
# Tests only CPP Important separators against OR-tools on generated datasets of increasing size, to see their performance difference as size increases. We thought (or hoped) that our FPT algorithm may perform well on smaller k size but large map size, whereas OR-tools perform better on higher k size.
def run_size_test():
  print("\nRunning size test...")
  results_dir = repo_root / "results"
  results_dir.mkdir(parents=True, exist_ok=True)
  csv_path = results_dir / "size_test_results.csv"
  timer = AlgorithmTimer(csv_path=str(csv_path))
  
  algorithms = []
  if CPP_AVAILABLE:
      algorithms.append(CppImportantSeparators())
  else:
      print("C++ Important Separators not available; skipping this algorithm in size test.")
  
  if MILP_AVAILABLE:
      algorithms.append(MILP_OR())
  else:
      print("Google OR-Tools not available; skipping MILP in size test.")
  
  k_values = [8]
  worker_count = 10

  def size_test_tasks():
      tasks = []
      for size in TEST_SIZES:
          try:
              level_map = generate_size_test(size)
              map_lines = ["".join(row) for row in level_map]
              graph, s, t = load_graph_from_lines(map_lines)
              print(f"Generated test of size {size}x{size}: {len(graph.nodeValues)} nodes")
              for k in k_values:
                  for algo in algorithms:
                      tasks.append((algo, f"SizeTest_{size}x{size}", graph, s, t, k))
          except Exception as e:
              print(f"An error occurred while processing generated size {size}: {e}")
      return tasks

  tasks = size_test_tasks()

  with ProcessPoolExecutor(max_workers=worker_count) as executor:
      future_to_task = {
          executor.submit(run_algorithm_timed, algo, dataset, graph, s, t, k, str(csv_path)):
          (algo.name, dataset, k)
          for algo, dataset, graph, s, t, k in tasks
      }

      for future in as_completed(future_to_task):
          algo_name, dataset, k = future_to_task[future]
          try:
              # timeout here is a safety net; worker enforces actual timeout internally
              result = future.result(timeout=TIMEOUT_SECONDS + 10)
              timer.record_result(result)
          except Exception as exc:
              error_result = TimerResult(
                  algorithm_name=algo_name,
                  dataset_name=dataset,
                  execution_time=0.0,
                  result=f"ERROR: {type(exc).__name__}: {exc}",
                  parameters={"s": 0, "t": 0, "k": k},
              )
              timer.record_result(error_result)
              print(f"Size test {algo_name} on {dataset} k={k} failed: {exc}")

  finalize_size_test_results(timer, csv_path)

if __name__ == "__main__":
  """Main entry point for benchmark and testing suite.
  
  Process rundown:
  1. Benchmark Phase (run_benchmarks):
     - Loads datasets from data/ directory
     - Tests all available algorithms (Naive, ImportantSeparators, C++, MILP)
     - Runs tests across multiple k values
     - Each worker process immediately writes results to CSV as it completes
     - Provides fault tolerance: results are persisted even if worker crashes
  
  2. Size Test Phase (run_size_test):
     - Generates synthetic test graphs of increasing sizes
     - Compares C++ ImportantSeparators vs MILP OR-Tools performance
     - Tests at fixed k value to isolate size effect
     - Each worker process immediately writes results to CSV as it completes
  
  3. Finalization:
     - After all threads complete, post-processing functions handle:
       * Consistency checks (verify algorithms agree on results)
       * Summary printing (formatted table of all results)
       * CSV export (comprehensive results file)
     - Separating finalization from threading allows safe error handling
  
  Note: 180-second timeout is enforced at worker level via threading,
  ensuring no process gets stuck. Results are written to CSV immediately
  upon completion, making the benchmark resilient to interruptions.
  """
  # Run comprehensive benchmarks on available datasets
  run_benchmarks()
  
  # Run performance comparison tests at varying sizes
  run_size_test()
  
  load_and_visualize_benchmarks()
