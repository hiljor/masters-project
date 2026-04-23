import itertools as it


from horse_algos.graph import Graph, path
from horse_algos.tools.helper import allKCombinations
from horse_algos.algorithms.algorithm import Algorithm

class Naive(Algorithm):
  
  @property
  def name(self):
    return "Brute Force"
  
  def run(self, graph: Graph, s: int, t: int, k: int) -> int | float:
    return naive(graph, s, t, k)

def naive(graph: Graph, s: int, t: int, k: int) -> int | float:
  """ Naive brute force approach that respects the graph's infSet.
  """
  
  optimal = float("-inf")
  
  # Only consider nodes that are NOT in the graph's infSet
  removable_nodes = [i for i in range(len(graph.adjList)) if i not in graph.infSet]
  
  for comb in it.combinations(removable_nodes, k):
    comb_set = set(comb)
    if s in comb_set or t in comb_set:
      continue
    elif path(graph, s, t, comb_set):
      continue
    else:
      value = graph.includedValue(s, t, comb_set)
      optimal = max(optimal, value)
         
  return optimal
      