from horse_algos.graph import Graph, minSeparator, path
from horse_algos.algorithms.algorithm import Algorithm, is_cancelled


class ImportantSeparators(Algorithm):

    @property
    def name(self):
        return "Important Separators"

    def run(self, graph: Graph, s: int, t: int, k: int) -> tuple[int | float, set[int]]:
        return important_separators(graph, s, t, k)


def important_separators(graph: Graph, s: int, t: int, k: int) -> tuple[int | float, set[int]]:
    """Approach using important separators that respects the graph's infSet."""
    best_separator = set()
    max_source_size = float("-inf")

    def branch(current_k, Z):

        nonlocal best_separator, max_source_size
        
        if is_cancelled():
            return

        X = minSeparator(graph, s, t)
        
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
    return max_source_size, best_separator
