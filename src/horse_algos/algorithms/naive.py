import itertools as it


from horse_algos.tools.graph import Graph
from horse_algos.tools.helper import allKCombinations
from horse_algos.algorithms.algorithm import algorithm

class Naive(algorithm):
  
  @property
  def name(self):
    return "Brute Force"
  
  def run(self, graph: Graph, s: int, t: int, k: int) -> int:
    return naive(graph, s, t, k)

def naive(graph: Graph, s: int, t: int, k: int) -> int:
  """ Naive brute force approach
  """
  
  for comb in allKCombinations(len(graph.adjList), k):
    if s in comb or t in comb:
      continue
    elif graph.path(s, t, set(comb)):
      continue
    else:
      return graph.includedValue(s, t, set(comb))
  
  # if no cutset of size k disconnects s and t, return 0
  return 0
      