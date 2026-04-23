import pytest
from copy import deepcopy
from horse_algos.graph import Graph, path, minSeparator

def test_flow():
    #  0 -- 1
    # | |   |  
    # | 4 --| (4 and 1 are not connected)
    # 3 --- 2
    adjMatrix = [
        [0, 1, 0, 1, 1],
        [1, 0, 1, 0, 0],
        [0, 1, 0, 1, 1],
        [1, 0, 1, 0, 0],
        [1, 0, 1, 0, 0],
    ]
    
    s = 0
    t = 2

    graph = Graph(adjMatrix, [1, 1, 1, 1, 1])
    cutset = minSeparator(graph, s, t)
    assert cutset == {1, 3, 4}, f"Expected minimum separator to be {1}, but got {cutset}"