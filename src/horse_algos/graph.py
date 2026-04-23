from copy import deepcopy


class Graph:
    """Graph class with DSU and node-cut functionality"""

    def __init__(
        self,
        adjMatrix: list[list[int]] = None, # type: ignore
        nodeValues: list[int] = None, # type: ignore
        adjList: list[list[int]] = None, # type: ignore
        infSet: set[int] = None, # type: ignore
    ):
        """Initializes the Graph class with either an adjacency matrix or an adjacency list.

        Args:
            adjMatrix: The adjacency matrix of the graph.
            nodeValues: The values associated with each node.
            adjList: The adjacency list of the graph.
            infSet: The set of nodes that cannot be removed from the graph.

        Raises:
            ValueError: If nodeValues is not provided, or if neither adjMatrix nor adjList is provided.
        """
        if nodeValues is None:
            raise ValueError("nodeValues must be provided.")

        self.nodeValues = nodeValues
        self.infSet = infSet if infSet is not None else set()

        if adjMatrix is not None:
            self.adjMatrix = adjMatrix
            self.adjList = (
                adjList if adjList is not None else self._adjMatrixToAdjList(adjMatrix)
            )
        elif adjList is not None:
            self.adjList = adjList
            self.adjMatrix = self._adjListToAdjMatrix(adjList)
        else:
            raise ValueError("Either adjMatrix or adjList must be provided.")

        n = len(self.nodeValues)

        # parent[i] = i means it's the root of its own set
        self.parent = list(range(n))
        # rank helps keep the tree balanced
        self.rank = [0] * n
        self.is_active = [True] * n
        # history stores (parent_node, child_node, rank_was_increased)
        self.history = []

    def _adjMatrixToAdjList(self, adjMatrix: list[list[int]]) -> list[list[int]]:
        """Converts an adjacency matrix to an adjacency list.

        Args:
            adjMatrix: The adjacency matrix to convert.

        Returns:
            The corresponding adjacency list.
        """
        adjList = [[] for _ in range(len(adjMatrix))]
        for i in range(len(adjMatrix)):
            for j in range(len(adjMatrix[i])):
                if adjMatrix[i][j] == 1:
                    adjList[i].append(j)
        return adjList

    def _adjListToAdjMatrix(self, adjList: list[list[int]]) -> list[list[int]]:
        """Converts an adjacency list to an adjacency matrix.

        Args:
            adjList: The adjacency list to convert.

        Returns:
            The corresponding adjacency matrix.
        """
        n = len(adjList)
        adjMatrix = [[0] * n for _ in range(n)]
        for i in range(n):
            for neighbor in adjList[i]:
                adjMatrix[i][neighbor] = 1
        return adjMatrix

    def value(self, vertex: int) -> int:
        """Returns the value of the given vertex."""
        return self.nodeValues[vertex]

    def includedValue(self, s: int, t: int, cutset: set[int]) -> int:
        """Returns the total value of the component that includes vertex
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
            self.history.append(
                {"u": root_a, "v": root_b, "rank_increased": rank_increased}
            )
            return True
        return False
      
    def uniteBySeparator(self, s: int, separator: set[int]):
        """Unites all nodes on the source side of the separator with s."""
        visited = set()
        stack = [s]
        while stack:
            vertex = stack.pop()
            if vertex in visited or vertex in separator:
                continue
            visited.add(vertex)
            self.unite(s, vertex)
            for neighbor in self.adjList[vertex]:
                stack.append(neighbor)
      
    def deactivate(self, v):
        """Deactivates a vertex, effectively removing it from the graph."""
        self.is_active[v] = False
        # Store a clear type flag to avoid KeyErrors during undo
        self.history.append({"type": "deactivate", "node": v})

    def undo(self, target_size):
        """Rolls back the DSU and activation state to a specific history size."""
        while len(self.history) > target_size:
            m = self.history.pop()
            
            if m.get("type") == "deactivate":
                self.is_active[m["node"]] = True
            else:
                # This is a DSU union entry
                self.parent[m["v"]] = m["v"]
                if m["rank_increased"]:
                    self.rank[m["u"]] -= 1

    def generateFlowMatrix(self, s: int, t: int):
        """Generates a flow matrix for the graph where each node has a capacity of 1,
        unless it is in the same DSU component as s, t, or a node in infSet,
        in which case it has infinite capacity.
        Edges between nodes have infinite capacity.
        DSU unions are respected by adding infinite capacity edges between united nodes.

        Args:
            s: The source node.
            t: The sink node.

        Returns:
            A 2D list representing the flow matrix.
        """
        n = len(self.adjMatrix)
        flowMatrix: list[list[int | float]] = [[0] * (2 * n) for _ in range(2 * n)]
        
        root_s = self.find(s)
        root_t = self.find(t)
        inf_roots = {self.find(node) for node in self.infSet}
        inf_roots.add(root_s)
        inf_roots.add(root_t)

        for i in range(n):
            if not self.is_active[i]:
                continue
            
            # Nodes in components of s, t, or infSet have infinite capacity (cannot be cut)
            flowMatrix[2 * i][2 * i + 1] = float("inf") if self.find(i) in inf_roots else 1
            
            # Respect DSU unions by connecting nodes to their root with infinite capacity
            root_i = self.find(i)
            if root_i != i:
                if self.is_active[root_i]:
                    flowMatrix[2 * i + 1][2 * root_i] = float("inf")
                    flowMatrix[2 * root_i + 1][2 * i] = float("inf")

            for j in range(n):
                # Only add edges between active nodes
                if self.adjMatrix[i][j] == 1 and self.is_active[j]:
                    flowMatrix[2 * i + 1][2 * j] = float("inf")
                    
        return flowMatrix


def path(graph: Graph, a: int, b: int, cutset: set[int]) -> bool:
    """Returns true if there exists a path in the graph between a and b
    that does not include any of the vertices in cutset or inactive nodes.
    False otherwise.

    Args:
        graph: The graph to check for a path.
        a: The starting vertex.
        b: The ending vertex.
        cutset: A set of vertices that cannot be included in the path.
    """

    adjList = graph.adjList
    isActive = graph.is_active
    visited = set()
    stack = [a]

    while stack:
        vertex = stack.pop()
        if vertex == b:
            return True
        if vertex in visited or vertex in cutset or not isActive[vertex]:
            continue
        visited.add(vertex)
        for neighbor in adjList[vertex]:
            stack.append(neighbor)

    return False


def minSeparator(graph: Graph, s: int, t: int) -> set[int]:
    """Returns a minimum separator between s and t in the graph."""  
    flowMatrix = graph.generateFlowMatrix(s, t)
    num_nodes = len(flowMatrix)

    def bfs(source, sink, parent):
        visited = [False] * num_nodes
        queue = [source]
        visited[source] = True
        while queue:
            u = queue.pop(0)
            for v in range(num_nodes):
                if not visited[v] and flowMatrix[u][v] > 0:
                    queue.append(v)
                    visited[v] = True
                    parent[v] = u
                    if v == sink:
                        return True
        return False

    # 1. Source is s_out (2*s + 1), Sink is t_in (2*t)
    source_node = 2 * s + 1
    sink_node = 2 * t

    # 2. Edmonds-Karp to saturate the network
    parent = [-1] * num_nodes
    while bfs(source_node, sink_node, parent):
        path_flow = float("inf")
        curr = sink_node
        while curr != source_node:
            path_flow = min(path_flow, flowMatrix[parent[curr]][curr])
            curr = parent[curr]

        v = sink_node
        while v != source_node:
            u = parent[v]
            flowMatrix[u][v] -= path_flow
            flowMatrix[v][u] += path_flow
            v = parent[v]
        parent = [-1] * num_nodes

    # 3. Find the farthest cut (Important Separator):
    # Find all nodes that can reach the sink in the residual graph
    can_reach_t = [False] * num_nodes
    queue = [sink_node]
    can_reach_t[sink_node] = True

    # Backward BFS on the residual graph
    while queue:
        v = queue.pop(0)
        for u in range(num_nodes):
            # If there is capacity from u to v, then v can be reached from u
            if not can_reach_t[u] and flowMatrix[u][v] > 0:
                can_reach_t[u] = True
                queue.append(u)

    # 4. The separator S is the set of nodes where
    # the 'in' node cannot reach t, but the 'out' node CAN reach t.
    min_cut = set()
    for i in range(len(graph.adjMatrix)):
        if i == s or i == t:
            continue
        # If the internal edge (in -> out) is saturated and is the bottleneck
        if not can_reach_t[2 * i] and can_reach_t[2 * i + 1]:
            min_cut.add(i)

    return min_cut
