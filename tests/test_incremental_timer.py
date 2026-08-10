import csv
import time
from pathlib import Path
import pytest
from horse_algos.timer.timer import AlgorithmTimer
from horse_algos.algorithms.algorithm import Algorithm
from horse_algos.algorithms.naive import Naive
from horse_algos.graph import Graph


class SleepAlgorithm(Algorithm):
    @property
    def name(self):
        return "SleepAlgorithm"

    def run(self, graph: Graph, s: int, t: int, k: int):
        time.sleep(0.5)
        return 42, set()

def test_incremental_timer(tmp_path):
    """Tests that AlgorithmTimer writes results incrementally to a CSV file."""
    csv_file = tmp_path / "test_results.csv"
    
    # 1. Initialize timer with csv_path and check that the header is written immediately
    timer = AlgorithmTimer(csv_path=str(csv_file))
    assert csv_file.exists()
    
    with open(csv_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["Algorithm", "Dataset", "k", "Time (CPU s)", "Result"]
        # Ensure no other rows exist yet
        with pytest.raises(StopIteration):
            next(reader)
            
    # 2. Time an algorithm and check that the row is appended immediately
    algo = Naive()
    # Simple graph: 0(1) -- 1(0)
    adjMatrix = [[0, 1], [1, 0]]
    graph = Graph(adjMatrix, [1, 0], infSet=set())
    
    timer.time_algorithm(algo, "test_dataset", graph, s=0, t=1, k=1)
    
    # Read the file again to check the written row
    with open(csv_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["Algorithm", "Dataset", "k", "Time (CPU s)", "Result"]
        row = next(reader)
        assert row[0] == algo.name
        assert row[1] == "test_dataset"
        assert row[2] == "1"
        # The execution time should be a float
        assert float(row[3]) >= 0.0
        # Result should be written in the row
        assert len(row[4]) > 0

        # Ensure no other rows exist
        with pytest.raises(StopIteration):
            next(reader)


def test_timer_tracks_cpu_time(tmp_path):
    csv_file = tmp_path / "cpu_time_results.csv"
    timer = AlgorithmTimer(csv_path=str(csv_file))

    algo = SleepAlgorithm()
    adjMatrix = [[0, 1], [1, 0]]
    graph = Graph(adjMatrix, [1, 0], infSet=set())

    result = timer.time_algorithm(algo, "cpu_test", graph, s=0, t=1, k=1)
    assert result.execution_time < 0.5
    assert result.result == (42, set())
