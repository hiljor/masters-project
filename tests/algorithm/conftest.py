import pytest
from collections import namedtuple
from horse_algos.graph import Graph, path, minSeparator
from horse_algos.tools.map_loader import load_graph_from_map

TestData = namedtuple("TestData", ["graph", "s", "t", "k", "expected"])

# Graph nodes are indexed from 0 to n-1, where n is the number of nodes in the graph.
# value is denoted in parentheses next to the node index for clarity.

@pytest.fixture
def case_basic():
    # 0(1) -- 1(5) -- 2(0)
    adjMatrix = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    return TestData(graph=Graph(adjMatrix, [1, 5, 0], infSet=set()), s=0, t=2, k=1, expected=1)


@pytest.fixture
def case_impossible():
    # 0(1) -- 1(5) -- 2(0)
    adjMatrix = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    return TestData(graph=Graph(adjMatrix, [1, 5, 0], infSet=set()), s=0, t=2, k=0, expected=float("-inf"))
  

# A graph where deleting the left column of 3 nodes gives 1 value, and deleting the right column of 4 nodes gives 6 value.
adjList = [
  [1,2,3],
  [0,4,5,6,7,8,9],
  [0,6,7,8,9],
  [0,6,7,8,9],
  [1,6,7],
  [1,6,7],
  [1,2,3,4,5,1,2,10],
  [1,2,3,4,5,2,10],
  [1,2,3,10],
  [3,10],
  [6,7,8,9]
]
@pytest.fixture
def case_pal():
    # Test k=4. Cut {6, 7, 8, 9} gives S={0, 1, 2, 3, 4, 5}, total value 6.
    return TestData(graph=Graph(adjList=adjList, nodeValues=[1]*11, infSet=set()), s=0, t=10, k=4, expected=6)
  
@pytest.fixture
def case_pal2():
    # Test k=3. Cut {3, 6, 7} gives S={0, 1, 2, 4, 5}, total value 5.
    return TestData(graph=Graph(adjList=adjList, nodeValues=[1]*11, infSet=set()), s=0, t=10, k=3, expected=1)


@pytest.fixture
def case_optimal():
    # 0(1) -- 1(5) -- 2(9) -- 3(2) -- 4(0)
    adjMatrix = [
        [0, 1, 0, 0, 0],
        [1, 0, 1, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 0, 1],
        [0, 0, 0, 1, 0],
    ]
    return TestData(graph=Graph(adjMatrix, [1, 5, 9, 2, 0], infSet=set()), s=0, t=4, k=1, expected=15)

@pytest.fixture
def case_inf_set():
    # 0(1) -- 1(5) -- 2(10) -- 3(0)
    # k=1. Min separator is {1} (value 1) or {2} (value 1+5=6).
    # If infSet={2}, then we MUST pick {1}. Expected 1.
    # If infSet={1}, then we MUST pick {2}. Expected 6.
    adjMatrix = [
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [0, 0, 1, 0]
    ]
    return TestData(graph=Graph(adjMatrix, [1, 5, 10, 0], infSet={2}), s=0, t=3, k=1, expected=1)

@pytest.fixture
def case_horse_cherry():
    graph, s, t = load_graph_from_map("horse_diamonds.txt")
    return TestData(graph=graph, s=s, t=t, k=2, expected=1)

@pytest.fixture
def case_horse_cherry2():
    graph, s, t = load_graph_from_map("horse_diamonds.txt")
    return TestData(graph=graph, s=s, t=t, k=7, expected=39)

@pytest.fixture
def case_horse_dots():
    graph, s, t = load_graph_from_map("horse_dots.txt")
    return TestData(graph=graph, s=s, t=t, k=8, expected=11)