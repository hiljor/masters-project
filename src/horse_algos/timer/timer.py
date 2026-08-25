import os
import time
import json
import threading
import csv
import statistics
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from horse_algos.graph import Graph
from horse_algos.algorithms.algorithm import Algorithm

TIMEOUT_SECONDS = 180  # 3 minutes timeout for each algorithm run


class TimeoutException(Exception):
    """Raised when an algorithm execution exceeds the timeout limit."""
    pass


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs.

    Attributes:
        warmup_runs: Number of runs executed and discarded before timing begins.
        iterations: Number of timed runs to record per experiment setup.
        target_cv: Optional early-stop threshold. Stop if the Coefficient of
            Variation (std_dev / mean) falls below this value (as a fraction,
            e.g. 0.03 = 3%) after a minimum of min_runs_for_early_stop runs.
        min_runs_for_early_stop: Minimum number of timed runs before early-stop
            is considered.
    """
    warmup_runs: int = 5
    iterations: int = 30
    target_cv: Optional[float] = 0.03
    min_runs_for_early_stop: int = 10


@dataclass
class BenchmarkStats:
    """Summary statistics for a set of benchmark runs.

    Attributes:
        median: Median runtime (primary metric, less sensitive to OS noise).
        mean: Average runtime across iterations.
        std_dev: Sample standard deviation of the runs.
        min: Best-case runtime.
        max: Worst-case runtime.
        p95: 95th percentile runtime.
        cv: Coefficient of variation (std_dev / mean) as a percentage.
        raw_runtimes: Raw array of recorded timings (seconds).
    """
    median: float
    mean: float
    std_dev: float
    min: float
    max: float
    p95: float
    cv: float  # percentage
    raw_runtimes: List[float] = field(default_factory=list)


def _percentile(data: List[float], p: float) -> float:
    """Computes the p-th percentile of a list using linear interpolation.

    Args:
        data: List of numeric values.
        p: Percentile to compute (0-100).

    Returns:
        The p-th percentile value.
    """
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def compute_stats(raw_runtimes: List[float]) -> BenchmarkStats:
    """Computes summary statistics from a list of raw runtimes.

    Args:
        raw_runtimes: List of runtime measurements in seconds.

    Returns:
        A BenchmarkStats object with computed statistics.
    """
    if not raw_runtimes:
        return BenchmarkStats(
            median=0.0, mean=0.0, std_dev=0.0,
            min=0.0, max=0.0, p95=0.0, cv=0.0,
            raw_runtimes=[],
        )

    mean = statistics.mean(raw_runtimes)
    std_dev = statistics.stdev(raw_runtimes) if len(raw_runtimes) > 1 else 0.0
    cv = (std_dev / mean * 100.0) if mean > 0 else 0.0

    return BenchmarkStats(
        median=statistics.median(raw_runtimes),
        mean=mean,
        std_dev=std_dev,
        min=min(raw_runtimes),
        max=max(raw_runtimes),
        p95=_percentile(raw_runtimes, 95),
        cv=cv,
        raw_runtimes=raw_runtimes,
    )


def benchmark_runner(
    algorithm: Algorithm,
    graph: Graph,
    s: int,
    t: int,
    k: int,
    config: Optional[BenchmarkConfig] = None,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> tuple[bool, Any, Optional[str], BenchmarkStats]:
    """Runs an algorithm with warmup, multiple iterations, and statistics.

    This is the core benchmarking helper. It:
    1. Runs the algorithm `warmup_runs` times (timings discarded).
    2. Runs the algorithm up to `iterations` times, measuring each run with
       a high-resolution monotonic clock (time.perf_counter_ns).
    3. Optionally stops early if the Coefficient of Variation falls below
       `target_cv` after `min_runs_for_early_stop` runs.
    4. Computes summary statistics (median, mean, std_dev, min, max, p95, cv).

    Args:
        algorithm: The algorithm to benchmark.
        graph: The graph object.
        s: Start vertex.
        t: Target vertex.
        k: Parameter k.
        config: Benchmark configuration (warmup_runs, iterations, target_cv).
        timeout_seconds: Maximum seconds to allow per run.

    Returns:
        Tuple of (success: bool, result: Any, error: Optional[str], stats: BenchmarkStats).
    """
    if config is None:
        config = BenchmarkConfig()

    # --- Warmup Phase ---
    # Run the algorithm warmup_runs times without recording timings.
    # If any warmup run fails (error or timeout), return immediately.
    for _ in range(config.warmup_runs):
        success, result, error = run_algorithm_with_timeout(
            algorithm, graph, s, t, k, timeout_seconds
        )
        if not success:
            return (False, None, error, compute_stats([]))

    # --- Measurement Phase ---
    raw_runtimes: List[float] = []
    final_result = result

    for i in range(config.iterations):
        start_ns = time.perf_counter_ns()
        success, result, error = run_algorithm_with_timeout(
            algorithm, graph, s, t, k, timeout_seconds
        )
        elapsed_ns = time.perf_counter_ns() - start_ns
        elapsed_s = elapsed_ns / 1e9

        if not success:
            return (False, None, error, compute_stats(raw_runtimes))

        final_result = result
        raw_runtimes.append(elapsed_s)

        # Early-stop check: after min_runs_for_early_stop runs, if CV < target_cv, stop.
        if (
            config.target_cv is not None
            and len(raw_runtimes) >= config.min_runs_for_early_stop
        ):
            stats = compute_stats(raw_runtimes)
            if stats.mean > 0 and stats.cv < config.target_cv * 100.0:
                break

    stats = compute_stats(raw_runtimes)
    return (True, final_result, None, stats)


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
                f"{timer_result.stats.median:.6f}",
                f"{timer_result.stats.mean:.6f}",
                f"{timer_result.stats.std_dev:.6f}",
                f"{timer_result.stats.min:.6f}",
                f"{timer_result.stats.max:.6f}",
                f"{timer_result.stats.p95:.6f}",
                f"{timer_result.stats.cv:.2f}",
                timer_result.result,
                json.dumps(timer_result.stats.raw_runtimes),
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
    result_container: dict[str, Any] = {"result": None, "error": None}
    exception_container: dict[str, Optional[Exception]] = {"exception": None}

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
    config: Optional[BenchmarkConfig] = None,
) -> "TimerResult":
    """Runs an algorithm with warmup, multiple iterations, and statistics.

    This function enforces a strict timeout at the worker process level using
    threading. If the algorithm exceeds the timeout, it returns a timeout error
    result.

    Args:
        algorithm: The algorithm to run
        dataset_name: Name of the dataset
        graph: The graph object
        s: Start vertex
        t: Target vertex
        k: Parameter k
        csv_path: Optional path to CSV file for immediate result recording
        config: Benchmark configuration (warmup_runs, iterations, target_cv)

    Returns:
        TimerResult containing the execution results and statistics
    """
    success, result, error, stats = benchmark_runner(
        algorithm, graph, s, t, k, config=config
    )

    # Create result based on success/failure
    if success:
        # Convert result to string representation (algorithms return tuples)
        result_str = str(result)
        timer_result = TimerResult(
            algorithm_name=algorithm.name,
            dataset_name=dataset_name,
            stats=stats,
            result=result_str,
            parameters={"s": s, "t": t, "k": k},
        )
    else:
        timer_result = TimerResult(
            algorithm_name=algorithm.name,
            dataset_name=dataset_name,
            stats=stats,
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
    stats: BenchmarkStats
    result: Any
    parameters: Dict[str, Any]


class AlgorithmTimer:
    """A utility class to time the execution of algorithms on datasets."""

    def __init__(self, csv_path: str = "", config: Optional[BenchmarkConfig] = None):
        """Initializes the timer and optionally prepares the CSV file for incremental recording.

        Args:
            csv_path: Optional file path where benchmark results are written
                incrementally after each algorithm run. If provided, the header
                is written immediately.
            config: Benchmark configuration (warmup_runs, iterations, target_cv).
        """
        self.results: List[TimerResult] = []
        self.csv_path = csv_path
        self.config = config or BenchmarkConfig()
        self._lock = threading.Lock()
        if self.csv_path:
            import csv
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Algorithm", "Dataset", "k",
                    "Median (s)", "Mean (s)", "Std Dev (s)",
                    "Min (s)", "Max (s)", "P95 (s)", "CV (%)",
                    "Result", "Raw Runtimes"
                ])

    def time_algorithm(
        self,
        algorithm: Algorithm,
        dataset_name: str,
        graph: Graph,
        s: int,
        t: int,
        k: int,
    ) -> TimerResult:
        """Times an algorithm with warmup and multiple iterations, stores the result,
        and optionally writes it to a CSV file.

        Args:
            algorithm: The algorithm instance to run.
            dataset_name: Name of the dataset being used.
            graph: The Graph object.
            s: Start vertex.
            t: Target vertex.
            k: Parameter k for the algorithm.

        Returns:
            A TimerResult object containing the timing information and statistics.
        """
        timer_result = run_algorithm_timed(
            algorithm,
            dataset_name,
            graph,
            s,
            t,
            k,
            config=self.config,
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
                        f"{timer_result.stats.median:.6f}",
                        f"{timer_result.stats.mean:.6f}",
                        f"{timer_result.stats.std_dev:.6f}",
                        f"{timer_result.stats.min:.6f}",
                        f"{timer_result.stats.max:.6f}",
                        f"{timer_result.stats.p95:.6f}",
                        f"{timer_result.stats.cv:.2f}",
                        timer_result.result,
                        json.dumps(timer_result.stats.raw_runtimes),
                    ])
                    f.flush()
                    os.fsync(f.fileno())

    def get_summary(self) -> str:
        """Returns a string summary of all recorded results."""
        if not self.results:
            return "No results recorded."

        lines = [
            f"{'Algorithm':<25} | {'Dataset':<15} | {'k':<3} | {'Median (s)':<10} | {'CV (%)':<7} | {'Result':<10}",
            "-" * 85
        ]
        for r in self.results:
            lines.append(
                f"{r.algorithm_name:<25} | {r.dataset_name:<15} | {r.parameters['k']:<3} | "
                f"{r.stats.median:<10.4f} | {r.stats.cv:<7.2f} | {r.result:<10}"
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
            writer.writerow([
                "Algorithm", "Dataset", "k",
                "Median (s)", "Mean (s)", "Std Dev (s)",
                "Min (s)", "Max (s)", "P95 (s)", "CV (%)",
                "Result", "Raw Runtimes"
            ])
            for r in self.results:
                writer.writerow([
                    r.algorithm_name,
                    r.dataset_name,
                    r.parameters["k"],
                    f"{r.stats.median:.6f}",
                    f"{r.stats.mean:.6f}",
                    f"{r.stats.std_dev:.6f}",
                    f"{r.stats.min:.6f}",
                    f"{r.stats.max:.6f}",
                    f"{r.stats.p95:.6f}",
                    f"{r.stats.cv:.2f}",
                    r.result,
                    json.dumps(r.stats.raw_runtimes),
                ])