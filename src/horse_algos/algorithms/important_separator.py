from horse_algos.graph import Graph, minSeparator, path


class ImportantSeparators:

    @property
    def name(self):
        return "Important Separators"

    def run(self, graph: Graph, s: int, t: int, k: int) -> int | float:
        return important_separators(graph, s, t, k)


def important_separators(graph: Graph, s: int, t: int, k: int) -> int | float:
    """Approach using important separators that respects the graph's infSet."""
    best_separator = None
    max_source_size = float("-inf")

    def branch(current_k, Z):

        nonlocal best_separator, max_source_size

        # Should find the smallest important separator S between s and t in 
        # the current graph state, but may not be correct
        # TODO: ASK PÅL, CORRECT
        
        X = minSeparator(graph, s, t)
        print(f"Current separator: {X}, size: {len(X)}, k left: {current_k}")
        
        # Base case evaluation
        if len(X) > current_k or len(X) == 0:
            if not path(graph, s, t, set()): # If s and t are disconnected
              size = graph.includedValue(s, t, Z)
              if size > max_source_size:
                  max_source_size = size
                  best_separator = Z.copy()
            return

        if current_k == 0:
            return

        marker = len(graph.history)
        
        graph.uniteBySeparator(s, X)
        v = next(iter(X))

        # --- BRANCH 1: v IS in the separator ---
        branch_marker = len(graph.history)
        graph.deactivate(v)
        Z.add(v)
        branch(current_k - 1, Z)
        # Cleanup
        graph.undo(branch_marker)
        Z.remove(v)

        # --- BRANCH 2: v is NOT in the separator ---
        graph.unite(s, v)
        branch(current_k, Z)
        
        # Cleanup whole call
        graph.undo(marker)

    branch(k, set())
    return max_source_size
