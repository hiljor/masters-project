from pathlib import Path

from horse_algos.graph import Graph


def load_graph_from_map(filename: str) -> tuple[Graph, int, int]:
    """Load a map from the repository's data directory and build a Graph.

    Args:
        filename: A map name such as "map" or "map.txt".

    Returns:
        A tuple of (graph, start_node, t_node).
    """
    graph, start_node, t_node, _ = load_map_with_metadata(filename)
    return graph, start_node, t_node


def load_map_with_metadata(
    filename: str,
) -> tuple[Graph, int, int, dict[tuple[int, int], int]]:
    """Load a map and return the graph, special nodes, and coordinate-to-ID mapping.

    Returns:
        A tuple of (graph, start_node, t_node, coords_to_id).
    """
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = repo_root / "data"
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found at {data_dir}")

    candidate_path = Path(filename)
    if candidate_path.is_file():
        return _load_graph_from_file(candidate_path)

    candidate_name = candidate_path.name
    candidates = [data_dir / candidate_name]
    if candidate_path.suffix == "":
        candidates.append(data_dir / f"{candidate_name}.txt")

    for candidate in candidates:
        if candidate.is_file():
            return _load_graph_from_file(candidate)

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(
        f"Unable to find map file '{filename}' in {data_dir}. Searched: {searched}"
    )


def _load_graph_from_file(path: Path) -> tuple[Graph, int, int, dict[tuple[int, int], int]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Map file '{path}' is empty.")
    return _build_graph_from_lines(lines)


def _build_graph_from_lines(lines: list[str]) -> tuple[Graph, int, int, dict[tuple[int, int], int]]:
    height = len(lines)
    width = max(len(line) for line in lines)

    coords_to_id: dict[tuple[int, int], int] = {}
    node_values: list[int] = []
    inf_set: set[int] = set()
    portal_groups: dict[str, list[int]] = {}
    start_node: int | None = None

    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char in {" ", "c", "H"} or char.isdigit():
                node_id = len(node_values)
                coords_to_id[(x, y)] = node_id
                node_values.append(4 if char == "c" else 1)
                if char == "H":
                    if start_node is not None:
                        raise ValueError("Map contains multiple 'H' start nodes.")
                    start_node = node_id
                    inf_set.add(node_id)
                elif char == "c":
                    inf_set.add(node_id)
                elif char.isdigit():
                    inf_set.add(node_id)
                    portal_groups.setdefault(char, []).append(node_id)

    if start_node is None:
        raise ValueError("Map must contain exactly one 'H' start node.")

    for label, ids in portal_groups.items():
        if len(ids) != 2:
            raise ValueError(
                f"Portal '{label}' must appear exactly twice, but found {len(ids)} occurrences."
            )

    total_nodes = len(node_values) + 1
    adjacency_list: list[list[int]] = [[] for _ in range(total_nodes)]

    for (x, y), node_id in coords_to_id.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor_id = coords_to_id.get((x + dx, y + dy))
            if neighbor_id is not None:
                adjacency_list[node_id].append(neighbor_id)

    for ids in portal_groups.values():
        # connect paired portal nodes with a bidirectional portal edge
        first, second = ids
        if second not in adjacency_list[first]:
            adjacency_list[first].append(second)
        if first not in adjacency_list[second]:
            adjacency_list[second].append(first)

    t_node = len(node_values)
    border_blank_nodes: list[int] = []
    for (x, y), node_id in coords_to_id.items():
        if x == 0 or y == 0 or x == width - 1 or y == height - 1:
            if lines[y][x] == " ":
                border_blank_nodes.append(node_id)

    for node_id in border_blank_nodes:
        adjacency_list[node_id].append(t_node)
    adjacency_list[t_node].extend(border_blank_nodes)
    node_values.append(0)

    return Graph(adjList=adjacency_list, nodeValues=node_values, infSet=inf_set), start_node, t_node, coords_to_id
