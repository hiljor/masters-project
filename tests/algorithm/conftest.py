import pytest
from collections import namedtuple
from horse_algos.graph import Graph, path, minSeparator

TestData = namedtuple("TestData", ["graph", "s", "t", "k", "expected"])

# Graph nodes are indexed from 0 to n-1, where n is the number of nodes in the graph.
# value is denoted in parentheses next to the node index for clarity.

@pytest.fixture
def case_basic():
    # 0(1) -- 1(5) -- 2(0)
    adjMatrix = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    return TestData(graph=Graph(adjMatrix, [1, 5, 0]), s=0, t=2, k=1, expected=1)


@pytest.fixture
def case_impossible():
    # 0(1) -- 1(5) -- 2(0)
    adjMatrix = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    return TestData(graph=Graph(adjMatrix, [1, 5, 0]), s=0, t=2, k=0, expected=float("-inf"))


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
    return TestData(graph=Graph(adjMatrix, [1, 5, 9, 2, 0]), s=0, t=4, k=1, expected=15)
