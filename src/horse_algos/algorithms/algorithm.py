from abc import ABC, abstractmethod
from horse_algos.graph import Graph

class Algorithm:
  @property
  @abstractmethod
  def name(self):
    """ The display name of the algorithm """
    pass
  
  @abstractmethod
  def run(self, graph: Graph, s: int, t: int, k: int) -> int:
    """ Runs the algorithm on the given graph with the given parameters. Returns the included value of the component of s after removing the cutset of size k that disconnects s and t, or 0 if no such cutset exists.

    Args:
        graph: The graph to run the algorithm on (should have infSet configured).
        s: The vertex whose component value we want to calculate.
        t: The other vertex.
        k: The size of the cutset to remove.
    """
    pass