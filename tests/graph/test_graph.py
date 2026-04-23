import pytest
from horse_algos.graph import Graph, minSeparator

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

def test_adj_list_init():
    #  0 -- 1 -- 2
    adjList = [
        [1],
        [0, 2],
        [1]
    ]
    nodeValues = [10, 20, 30]

    # Init with adjList
    graph = Graph(adjList=adjList, nodeValues=nodeValues)

    assert graph.adjList == adjList
    assert graph.adjMatrix == [
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0]
    ]
    assert graph.nodeValues == nodeValues

    # Check that it still works
    assert graph.value(1) == 20
    assert graph.includedValue(0, 2, set()) == 60
