import itertools as it


from horse_algos.graph import Graph
from horse_algos.tools.helper import allKCombinations
from horse_algos.algorithms.algorithm import Algorithm

class Naive(Algorithm):
  
  @property
  def name(self):
    return "Brute Force"
  
  def run(self, graph: Graph, s: int, t: int, k: int) -> int:
    return naive(graph, s, t, k)

def naive(graph: Graph, s: int, t: int, k: int) -> int:
  """ Naive brute force approach
  """
  
  optimal = float("-inf")
  
  for comb in allKCombinations(len(graph.adjList), k):
    if s in comb or t in comb:
      continue
    elif graph.path(s, t, set(comb)):
      continue
    else:
      value = graph.includedValue(s, t, set(comb))
      optimal = max(optimal, value)
         
  return optimal
      