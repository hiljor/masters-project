import pytest
from horse_algos.graph import Graph
from horse_algos.algorithms.milp_ortools import MILP_OR
from horse_algos.algorithms.naive import Naive

def test_milp_basic():
    # A simple graph where removing node 1 separates 0 and 2
    # 0 -- 1 -- 2
    adj = [[1], [0, 2], [1]]
    values = [10, 1, 10]
    graph = Graph(adjList=adj, nodeValues=values)
    
    solver = MILP_OR()
    # If k=1, removing node 1 is the best cut to separate 0 and 2.
    # The s-component will be {0}, value 10.
    val, cutset = solver.run(graph, 0, 2, 1)
    
    assert val == 10
    assert cutset == {1}

def test_milp_budget():
    # 0 -- 1 -- 2 -- 3
    # Values: 10, 5, 5, 10
    # k=1: Cut 1 or 2. Best is cut 2 (s-comp: {0,1}, val: 15)
    # k=2: Best is cut 2 (s-comp: {0,1}, val: 15). Actually cut 1 and 2 doesn't help more.
    adj = [[1], [0, 2], [1, 3], [2]]
    values = [10, 5, 5, 10]
    graph = Graph(adjList=adj, nodeValues=values)
    
    solver = MILP_OR()
    val, cutset = solver.run(graph, 0, 3, 1)
    assert val == 15
    assert cutset == {2} or cutset == {1} # Wait, if cut 1, s-comp is {0}, val 10. If cut 2, s-comp is {0,1}, val 15.
    assert val == 15
    assert 2 in cutset

def test_milp_vs_naive():
    # Larger random-ish graph
    adj = [
        [1, 2],    # 0
        [0, 3, 4], # 1
        [0, 4],    # 2
        [1, 5],    # 3
        [1, 2, 5], # 4
        [3, 4]     # 5
    ]
    values = [10, 20, 30, 40, 50, 60]
    graph = Graph(adjList=adj, nodeValues=values)
    
    s, t, k = 0, 5, 2
    
    val_naive, cut_naive = Naive().run(graph, s, t, k)
    val_milp, cut_milp = MILP_OR().run(graph, s, t, k)
    
    assert val_milp == val_naive

def test_milp_inf_set():
    # 0 -- 1 -- 2, k=1. If node 1 is irremovable, no solution separates 0 and 2.
    adj = [[1], [0, 2], [1]]
    values = [10, 1, 10]
    graph = Graph(adjList=adj, nodeValues=values, infSet={1})
    
    solver = MILP_OR()
    val, cutset = solver.run(graph, 0, 2, 1)
    
    # Should not be able to separate 0 and 2 if 1 is irremovable
    # Actually MILP should find no solution or return -inf if constrained.
    # In my implementation it returns -inf if not optimal.
    assert val == float("-inf")
