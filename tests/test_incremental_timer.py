import csv
from pathlib import Path
from horse_algos.timer.timer import AlgorithmTimer
from horse_algos.algorithms.naive import Naive
from horse_algos.graph import Graph

def test_incremental_timer(tmp_path):
    """Tests that AlgorithmTimer writes results incrementally to a CSV file."""
    csv_file = tmp_path / "test_results.csv"
    
    # 1. Initialize timer with csv_path and check that the header is written immediately
    timer = AlgorithmTimer(csv_path=str(csv_file))
    assert csv_file.exists()
    
    with open(csv_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["Algorithm", "Dataset", "k", "Time", "Result"]
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
        assert header == ["Algorithm", "Dataset", "k", "Time", "Result"]
        row = next(reader)
        assert row[0] == algo.name
        assert row[1] == "test_dataset"
        assert row[2] == "1"
        # The execution time should be a float
        assert float(row[3]) >= 0.0
        # Result should be either float("-inf") or a numeric/correct result.
        # For naive, a cut of size <= 1 between 0 and 1:
        # Node 1 is t, Node 0 is s. Deleting node 1 is not allowed (it is target vertex t, wait, can we delete t?
        # Actually node values are [1, 0]. The cut is {} or {1} or {0}.
        # In Naive algorithm, the return is the max total combined value of the s-component after the cut.
        # Let's just assert that there is a result value written in the row.
        assert len(row[4]) > 0
        
        # Ensure no other rows exist
        with pytest.raises(StopIteration):
            next(reader)

import pytest
