from horse_algos.graph import Graph, minSeparator, path


class ImportantSeparators:

    @property
    def name(self):
        return "Important Separators"

    def run(self, graph: Graph, s: int, t: int, k: int) -> int:
        return important_separators(graph, s, t, k)


def important_separators(graph: Graph, s: int, t: int, k: int) -> int:
    """Approach using important separators."""
    best_separator = None
    max_source_size = 0

    def branch(current_k, Z = set()):
        nonlocal best_separator, max_source_size

        # Should find the smallest important separator S between s and t in 
        # the current graph state, but may not be correct
        # TODO: ASK PÅL, CORRECT
        
        S = minSeparator(graph, s, t)
        print(f"Current separator: {S}, size: {len(S)}, k left: {current_k}")
        if len(S) > current_k:
            return 0

        # Base case evaluation
        if current_k == 0 or len(S) == 0:
            size = graph.includedValue(s, t, Z)
            if size > max_source_size:
                max_source_size = size
                best_separator = Z.copy()
            return 0

        marker = len(graph.history)
        
        graph.uniteBySeparator(s, S)
        v = next(iter(S))

        # --- BRANCH 1: v IS in the separator ---
        branch_marker = len(graph.history)
        graph.deactivate(v)
        Z.add(v)
        branch(current_k - 1)
        # Cleanup
        graph.undo(branch_marker)
        Z.remove(v)

        # --- BRANCH 2: v is NOT in the separator ---
        graph.unite(s, v)
        branch(current_k)
        
        # Cleanup whole call
        graph.undo(marker)

    branch(k)
    return max_source_size
