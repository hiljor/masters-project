from pathlib import Path

import pytest
from horse_algos.graph import Graph
from horse_algos.tools.map_loader import load_graph_from_map


def test_load_graph_from_map_returns_graph_and_special_nodes():
    graph, start_node, t_node = load_graph_from_map("horse_diamonds.txt")

    assert isinstance(graph, Graph)
    assert isinstance(start_node, int)
    assert isinstance(t_node, int)
    assert t_node == len(graph.adjList) - 1
    assert start_node in graph.infSet
    assert graph.adjList[t_node]

    data_path = Path(__file__).resolve().parents[1] / "data" / "horse_diamonds.txt"
    lines = data_path.read_text(encoding="utf-8").splitlines()
    width = max(len(line) for line in lines)
    height = len(lines)

    coords = []
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char in {" ", "c", "H"} or char.isdigit():
                coords.append(((x, y), char))

    id_by_coord = {coord: index for index, (coord, _) in enumerate(coords)}
    expected_border_blank_ids = [
        id_by_coord[(x, y)]
        for (x, y), char in coords
        if char == " " and (x == 0 or y == 0 or x == width - 1 or y == height - 1)
    ]

    assert sorted(graph.adjList[t_node]) == sorted(expected_border_blank_ids)
    for node_id in expected_border_blank_ids:
        assert t_node in graph.adjList[node_id]

    expected_inf_ids = {
        id_by_coord[(x, y)]
        for (x, y), char in coords
        if char in {"c", "H"}
    }
    assert graph.infSet == expected_inf_ids

    expected_start_id = next(id_by_coord[(x, y)] for (x, y), char in coords if char == "H")
    assert start_node == expected_start_id

    for (x, y), char in coords:
        node_id = id_by_coord[(x, y)]
        expected_value = 4 if char == "c" else 1
        assert graph.nodeValues[node_id] == expected_value

    assert graph.nodeValues[t_node] == 0


def test_load_graph_with_portal_pair(tmp_path):
    map_text = """H 1
###
  1"""
    map_path = tmp_path / "portal_map.txt"
    map_path.write_text(map_text, encoding="utf-8")

    graph, start_node, t_node = load_graph_from_map(str(map_path))

    assert isinstance(graph, Graph)
    assert start_node in graph.infSet

    coords = []
    for y, line in enumerate(map_text.splitlines()):
        for x, char in enumerate(line):
            if char in {" ", "c", "H"} or char.isdigit():
                coords.append(((x, y), char))

    id_by_coord = {coord: index for index, (coord, _) in enumerate(coords)}
    portal_nodes = [id_by_coord[(x, y)] for (x, y), char in coords if char == "1"]

    assert len(portal_nodes) == 2
    first, second = portal_nodes
    assert second in graph.adjList[first]
    assert first in graph.adjList[second]
    assert all(node_id in graph.infSet for node_id in portal_nodes)
    assert all(graph.nodeValues[node_id] == 1 for node_id in portal_nodes)
    assert graph.nodeValues[start_node] == 1
    assert graph.nodeValues[t_node] == 0


def test_load_graph_from_map_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_graph_from_map("this_map_does_not_exist")
