
class Graph:
  def __init__(self, adjMatrix: list[list[int]], nodeValues: list[int]):
    self.adjMatrix = adjMatrix
    self.adjList = self._adjMatrixToAdjList(adjMatrix)
    self.nodeValues = nodeValues
  
  def _adjMatrixToAdjList(self, adjMatrix: list[list[int]]) -> list[list[int]]:
    adjList = [[] for _ in range(len(adjMatrix))]
    for i in range(len(adjMatrix)):
      for j in range(len(adjMatrix[i])):
        if adjMatrix[i][j] == 1:
          adjList[i].append(j)
    return adjList
  
  def path(self, a: int, b: int, cutset: set[int]) -> bool:
    return path(self.adjList, a, b, cutset)
  
  def value(self, vertex: int) -> int:
    """ Returns the value of the given vertex. """
    return self.nodeValues[vertex]
  
  def includedValue(self, s: int, t: int, cutset: set[int]) -> int:
    """ Returns the total value of the component that includes vertex
        s, given that the vertices in cutset are removed from the graph.

        Args:
            s: The vertex whose component value we want to calculate.
            t: The other vertex (not used in this function, but included for consistency with path).
            cutset: A set of vertices that are removed from the graph.
    """
    visited = set()
    stack = [s]
    totalValue = 0
    while stack:
      vertex = stack.pop()
      if vertex in visited or vertex in cutset:
        continue
      visited.add(vertex)
      totalValue += self.value(vertex)
      for neighbor in self.adjList[vertex]:
          stack.append(neighbor)
    return totalValue
  

class ContractionGraph(Graph):
    def __init__(self, adjMatrix: list[list[int]], nodeValues: list[int]):
        super().__init__(adjMatrix, nodeValues)
        n = len(adjMatrix)
        # parent[i] = i means it's the root of its own set
        self.parent = list(range(n))
        # rank helps keep the tree balanced
        self.rank = [0] * n
        self.is_active = [True] * n
        # history stores (parent_node, child_node, rank_was_increased)
        self.history = []

    def find(self, x):
        """Finds the root of the set containing x without path compression."""
        while x != self.parent[x]:
            x = self.parent[x]
        return x

    def unite(self, a, b):
        """Unites sets containing a and b using Union by Rank."""
        root_a = self.find(a)
        root_b = self.find(b)
        
        if root_a != root_b:
            # We want root_a to be the one with the higher rank
            if self.rank[root_a] < self.rank[root_b]:
                root_a, root_b = root_b, root_a
            
            rank_increased = False
            if self.rank[root_a] == self.rank[root_b]:
                self.rank[root_a] += 1
                rank_increased = True
            
            # Make root_a the parent of root_b
            self.parent[root_b] = root_a
            self.history.append({
                'u': root_a, 
                'v': root_b, 
                'rank_increased': rank_increased
            })
            return True
        return False

    def undo(self, target_size):
        """Rolls back the DSU state to a specific history size."""
        while len(self.history) > target_size:
            m = self.history.pop()
            # Reset the child's parent to itself
            self.parent[m['v']] = m['v']
            # If the parent's rank was increased during 'unite', revert it
            if m['rank_increased']:
                self.rank[m['u']] -= 1


def path(adjList: list[list[int]], a: int, b: int, cutset: set[int]) -> bool:
  """ Returns true if there exists a path in the graph between a and b
      that does not include any of the vertices in cutset. False otherwise.

      Args:
          adjList: The adjacency list of the graph.
          a: The starting vertex.
          b: The ending vertex.
          cutset: A set of vertices that cannot be included in the path.
  """
  
  visited = set()
  stack = [a]

  while stack:
    vertex = stack.pop()
    if vertex == b:
      return True
    if vertex in visited or vertex in cutset:
      continue
    visited.add(vertex)
    for neighbor in adjList[vertex]:
        stack.append(neighbor)

  return False