import time
from dataclasses import dataclass
from typing import Any, Dict, List
from horse_algos.graph import Graph
from horse_algos.algorithms.algorithm import Algorithm

@dataclass
class TimerResult:
    algorithm_name: str
    dataset_name: str
    execution_time: float
    result: Any
    parameters: Dict[str, Any]

class AlgorithmTimer:
    """A utility class to time the execution of algorithms on datasets."""

    def __init__(self):
        self.results: List[TimerResult] = []

    def time_algorithm(
        self, 
        algorithm: Algorithm, 
        dataset_name: str, 
        graph: Graph, 
        s: int, 
        t: int, 
        k: int
    ) -> TimerResult:
        """Times a single run of an algorithm and stores the result.

        Args:
            algorithm: The algorithm instance to run.
            dataset_name: Name of the dataset being used.
            graph: The Graph object.
            s: Start vertex.
            t: Target vertex.
            k: Parameter k for the algorithm.

        Returns:
            A TimerResult object containing the timing information.
        """
        start_time = time.perf_counter()
        result = algorithm.run(graph, s, t, k)
        end_time = time.perf_counter()

        duration = end_time - start_time
        
        timer_result = TimerResult(
            algorithm_name=algorithm.name,
            dataset_name=dataset_name,
            execution_time=duration,
            result=result,
            parameters={"s": s, "t": t, "k": k}
        )
        
        self.results.append(timer_result)
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
