import time
import multiprocessing
from dataclasses import dataclass
from typing import Any, Dict, List
from horse_algos.graph import Graph
from horse_algos.algorithms.algorithm import Algorithm

TIMEOUT_SECONDS = 60


def _run_algorithm(algorithm: Algorithm, graph: Graph, s: int, t: int, k: int, result_queue: multiprocessing.Queue):
    try:
        result = algorithm.run(graph, s, t, k)
        result_queue.put(("ok", result))
    except Exception as exc:
        result_queue.put(("exc", repr(exc)))


@dataclass
class TimerResult:
    algorithm_name: str
    dataset_name: str
    execution_time: float
    result: Any
    parameters: Dict[str, Any]

class AlgorithmTimer:
    """A utility class to time the execution of algorithms on datasets."""

    def __init__(self, csv_path: str = None):
        """Initializes the timer and optionally prepares the CSV file for incremental recording.

        Args:
            csv_path: Optional file path where benchmark results are written
                incrementally after each algorithm run. If provided, the header
                is written immediately.
        """
        self.results: List[TimerResult] = []
        self.csv_path = csv_path
        if self.csv_path:
            import csv
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Algorithm", "Dataset", "k", "Time", "Result"])

    def time_algorithm(
        self,
        algorithm: Algorithm,
        dataset_name: str,
        graph: Graph,
        s: int,
        t: int,
        k: int,
        timeout_seconds: int = TIMEOUT_SECONDS,
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
        start_time = time.perf_counter()
        ctx = multiprocessing.get_context("spawn")
        result_queue = ctx.Queue()
        process = ctx.Process(
            target=_run_algorithm,
            args=(algorithm, graph, s, t, k, result_queue),
        )
        process.start()
        process.join(timeout_seconds)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        if process.is_alive():
            process.terminate()
            process.join()
            result = "DNF"
        else:
            if result_queue.empty():
                if process.exitcode != 0:
                    raise RuntimeError(
                        f"Algorithm process failed with exit code {process.exitcode}"
                    )
                result = "DNF"
            else:
                status, payload = result_queue.get()
                if status == "ok":
                    result = payload
                else:
                    raise RuntimeError(f"Algorithm raised an exception: {payload}")

        timer_result = TimerResult(
            algorithm_name=algorithm.name,
            dataset_name=dataset_name,
            execution_time=duration,
            result=result,
            parameters={"s": s, "t": t, "k": k},
        )

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

        return timer_result

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
            writer.writerow(["Algorithm", "Dataset", "k", "Time", "Result"])
            for r in self.results:
                writer.writerow([
                    r.algorithm_name,
                    r.dataset_name,
                    r.parameters["k"],
                    f"{r.execution_time:.6f}",
                    r.result
                ])
