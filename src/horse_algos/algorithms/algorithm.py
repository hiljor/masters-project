from abc import ABC, abstractmethod
import threading
from horse_algos.graph import Graph

# Thread-local storage for cancellation state
_local = threading.local()

def set_cancelled(val: bool):
    """ Sets the cancellation state for the current thread. """
    _local.cancelled = val

def is_cancelled() -> bool:
    """ Returns True if the current thread's task has been cancelled. """
    return getattr(_local, "cancelled", False)

class Algorithm(ABC):
  @property
  @abstractmethod
  def name(self):
    """ The display name of the algorithm """
    pass

  @abstractmethod
  def run(self, graph: Graph, s: int, t: int, k: int) -> tuple[int | float, set[int]]:
    """ Runs the algorithm on the given graph with the given parameters. 
    Returns a tuple of (max_value, cutset).

    Args:
        graph: The graph to run the algorithm on (should have infSet configured).
        s: The vertex whose component value we want to calculate.
        t: The other vertex.
        k: The size of the cutset to remove.
    """
    pass