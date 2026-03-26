from horse_algos.graph import Graph

class ImportantSeparators:
  
  @property
  def name(self):
    return "Important Separators"
  
  def run(self, graph: Graph, s: int, t: int, k: int) -> int:
    return important_separators(graph, s, t, k)

def important_separators(graph: Graph, s: int, t: int, k: int) -> int:
  """ Approach using important separators. """
  
  