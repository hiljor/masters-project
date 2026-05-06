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
  
  # Only consider nodes that are NOT s, NOT t, and NOT in the graph's infSet
  removable_nodes = [i for i in range(len(graph.adjList)) 
                     if i not in graph.infSet 
                     and i not in  [s,t]]
  
  for comb in allKCombinations(len(removable_nodes), k):
    # Map indices back to actual node indices
    comb_set = {removable_nodes[i] for i in comb}
    
    if path(graph, s, t, comb_set):
      continue
    else:
      value = graph.includedValue(s, t, comb_set)
      optimal = max(optimal, value)
         
  return optimal
      