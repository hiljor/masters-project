import os
import time
import threading
import csv
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from horse_algos.graph import Graph
from horse_algos.algorithms.algorithm import Algorithm

TIMEOUT_SECONDS = 180 # 3 minutes timeout for each algorithm run


class TimeoutException(Exception):
    """Raised when an algorithm execution exceeds the timeout limit."""
    pass


def append_result_to_csv(csv_path: str, timer_result: "TimerResult") -> None:
    """Appends a single result to the CSV file in a process-safe manner.
    
    This function is designed to be called from worker processes to write
    results directly to the CSV file without needing to return through the
    main process. It uses file-level synchronization via append mode.
    
    Args:
        csv_path: Path to the CSV file
        timer_result: The TimerResult to append
    """
    if not csv_path:
        return
    
    try:
        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timer_result.algorithm_name,
                timer_result.dataset_name,
                timer_result.parameters["k"],
                f"{timer_result.execution_time:.6f}",
                timer_result.result
            ])
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Warning: Failed to write result to CSV: {e}")


def run_algorithm_with_timeout(
    algorithm: Algorithm,
    graph: Graph,
    s: int,
    t: int,
    k: int,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> tuple[bool, Any, Optional[str]]:
    """Runs an algorithm with strict timeout enforcement using threading.
    
    This function enforces a timeout by running the algorithm in a separate
    thread and monitoring elapsed time. If the algorithm exceeds the timeout,
    a TimeoutException is raised.
    
    Args:
        algorithm: The algorithm to run
        graph: The graph object
        s: Start vertex
        t: Target vertex
        k: Parameter k
        timeout_seconds: Maximum seconds to allow (default: TIMEOUT_SECONDS)
        
    Returns:
        Tuple of (success: bool, result: Any, error: Optional[str])
        - If successful: (True, result, None)
        - If timed out: (False, None, "TIMEOUT")
        - If error: (False, None, error_message)
    """
    result_container = {"result": None, "error": None}
    exception_container = {"exception": None}
    
    def run_in_thread():
        try:
            result_container["result"] = algorithm.run(graph, s, t, k)
        except TimeoutException:
            result_container["error"] = "TIMEOUT"
        except Exception as e:
            exception_container["exception"] = e
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    # Check if thread is still alive (timeout occurred)
    if thread.is_alive():
        return (False, None, "TIMEOUT")
    
    # Check for timeout error
    if result_container["error"] == "TIMEOUT":
        return (False, None, "TIMEOUT")
    
    # Check for exceptions
    if exception_container["exception"] is not None:
        exc = exception_container["exception"]
        return (False, None, f"{type(exc).__name__}: {exc}")
    
    # Success
    return (True, result_container["result"], None)


def run_algorithm_timed(
    algorithm: Algorithm,
    dataset_name: str,
    graph: Graph,
    s: int,
    t: int,
    k: int,
    csv_path: str = "",
) -> "TimerResult":
    """Runs an algorithm with timing and optionally writes result to CSV immediately.
    
    This function enforces a strict timeout at the worker process level using threading.
    If the algorithm exceeds the timeout, it returns a timeout error result.
    
    Args:
        algorithm: The algorithm to run
        dataset_name: Name of the dataset
        graph: The graph object
        s: Start vertex
        t: Target vertex
        k: Parameter k
        csv_path: Optional path to CSV file for immediate result recording
        
    Returns:
        TimerResult containing the execution results
    """
    # NOTE: execution_time is CPU time (time.process_time), not wall-clock time.
    # time.process_time() returns the sum of processor time across all threads
    # of the process, excluding time spent sleeping or waiting on I/O.
    start_cpu = time.process_time()
    
    # Run algorithm with strict timeout enforcement
    success, result, error = run_algorithm_with_timeout(algorithm, graph, s, t, k)
    
    cpu_duration = time.process_time() - start_cpu
    
    # Create result based on success/failure
    if success:
        # Convert result to string representation (algorithms return tuples)
        result_str = str(result)
        timer_result = TimerResult(
            algorithm_name=algorithm.name,
            dataset_name=dataset_name,
            execution_time=cpu_duration,
            result=result_str,
            parameters={"s": s, "t": t, "k": k},
        )
    else:
        timer_result = TimerResult(
            algorithm_name=algorithm.name,
            dataset_name=dataset_name,
            execution_time=cpu_duration,
            result=f"ERROR: {error}",
            parameters={"s": s, "t": t, "k": k},
        )
    
    if csv_path:
        append_result_to_csv(csv_path, timer_result)
    
    return timer_result


@dataclass
class TimerResult:
    algorithm_name: str
    dataset_name: str
    execution_time: float
    result: Any
    parameters: Dict[str, Any]

class AlgorithmTimer:
    """A utility class to time the execution of algorithms on datasets."""

    def __init__(self, csv_path: str = ""):
        """Initializes the timer and optionally prepares the CSV file for incremental recording.

        Args:
            csv_path: Optional file path where benchmark results are written
                incrementally after each algorithm run. If provided, the header
                is written immediately.
        """
        self.results: List[TimerResult] = []
        self.csv_path = csv_path
        self._lock = threading.Lock()
        if self.csv_path:
            import csv
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Algorithm", "Dataset", "k", "Time (CPU s)", "Result"])

    def time_algorithm(
        self,
        algorithm: Algorithm,
        dataset_name: str,
        graph: Graph,
        s: int,
        t: int,
        k: int,
    ) -> TimerResult:
        """Times a single run of an algorithm, stores the result, and optionally writes it to a CSV file.

        Args:
            algorithm: The algorithm instance to run.
            dataset_name: Name of the dataset being used.
            graph: The Graph object.
            s: Start vertex.
            t: Target vertex.
            k: Parameter k for the algorithm.
            timeout_seconds: Maximum seconds to allow the run.

        Returns:
            A TimerResult object containing the timing information.
        """
        timer_result = run_algorithm_timed(
            algorithm,
            dataset_name,
            graph,
            s,
            t,
            k,
        )

        self.record_result(timer_result)
        return timer_result

    def record_result(self, timer_result: TimerResult) -> None:
        with self._lock:
            self.results.append(timer_result)
            if self.csv_path:
                import csv
                with open(self.csv_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timer_result.algorithm_name,
                        timer_result.dataset_name,
                        timer_result.parameters["k"],
                        f"{timer_result.execution_time:.6f}",
                        timer_result.result
                    ])
                    f.flush()
                    os.fsync(f.fileno())

    def get_summary(self) -> str:
        """Returns a string summary of all recorded results."""
        if not self.results:
            return "No results recorded."
        
        lines = [
            f"{'Algorithm':<25} | {'Dataset':<15} | {'k':<3} | {'Time (s)':<10} | {'Result':<10}",
            "-" * 75
        ]
        for r in self.results:
            lines.append(
                f"{r.algorithm_name:<25} | {r.dataset_name:<15} | {r.parameters['k']:<3} | "
                f"{r.execution_time:<10.4f} | {r.result:<10}"
            )
        return "\n".join(lines)

    def to_csv(self, filepath: str):
        """Exports the recorded results to a CSV file.

        Args:
            filepath: The path to the CSV file to create.
        """
        import csv
        if not self.results:
            return

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Algorithm", "Dataset", "k", "Time (CPU s)", "Result"])
            for r in self.results:
                writer.writerow([
                    r.algorithm_name,
                    r.dataset_name,
                    r.parameters["k"],
                    f"{r.execution_time:.6f}",
                    r.result
                ])
