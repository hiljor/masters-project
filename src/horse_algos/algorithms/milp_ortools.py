try:
    from ortools.linear_solver import pywraplp
    MILP_AVAILABLE = True
except ImportError:
    MILP_AVAILABLE = False

from horse_algos.graph import Graph
from horse_algos.algorithms.algorithm import Algorithm, is_cancelled

class MILP_OR(Algorithm):
    """ MILP implementation using Google OR-Tools. """

    @property
    def name(self):
        return "MILP (OR-Tools)"

    def run(self, graph: Graph, s: int, t: int, k: int) -> tuple[int | float, set[int]]:
        """ Runs the MILP algorithm on the given graph. """
        
        if not MILP_AVAILABLE:
            raise ImportError("Google OR-Tools not available. Please install it with 'pip install ortools'.")

        # Create the linear solver with the SCIP backend.
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            raise RuntimeError("SCIP solver not available.")

        # Check for cancellation before starting the solve.
        if is_cancelled():
            return float("-inf"), set()

        n = len(graph.adjList)
        inf = solver.infinity()

        # x[v] = 1 if node v is in the s-component, 0 otherwise.
        x = [solver.BoolVar(f'x_{i}') for i in range(n)]
        
        # y[v] = 1 if node v is removed (part of the cutset), 0 otherwise.
        y = [solver.BoolVar(f'y_{i}') for i in range(n)]

        # Objective: Maximize the total value of the s-component.
        # Only consider active nodes.
        objective = solver.Objective()
        for i in range(n):
            if graph.is_active[i]:
                objective.SetCoefficient(x[i], graph.nodeValues[i])
        objective.SetMaximization()

        # Constraint 1: Source and Sink.
        solver.Add(x[s] == 1)
        solver.Add(x[t] == 0)

        # Constraint 2: Connectivity and 3: Node State.
        for i in range(n):
            if not graph.is_active[i]:
                # If node is inactive, it cannot be in the s-component and cannot be removed (it's already gone).
                solver.Add(x[i] == 0)
                solver.Add(y[i] == 0)
                continue
            
            # x[i] + y[i] <= 1 (A node cannot be both in the s-component and removed).
            solver.Add(x[i] + y[i] <= 1)

            # Connectivity: x[u] <= x[v] + y[v] for each edge (u, v).
            for neighbor in graph.adjList[i]:
                if graph.is_active[neighbor]:
                    solver.Add(x[i] <= x[neighbor] + y[neighbor])

        # Constraint 4: Budget.
        solver.Add(sum(y) <= k)

        # Constraint 5: Irremovable Nodes.
        for i in graph.infSet:
            solver.Add(y[i] == 0)
        
        # s and t cannot be in the cutset.
        solver.Add(y[s] == 0)
        solver.Add(y[t] == 0)

        # Flow variables for connectivity/reachability checks.
        # Since the graph is directed, we define a directed flow variable for each unique directed edge.
        in_neighbors = [set() for _ in range(n)]
        unique_adj = [set() for _ in range(n)]
        
        for u in range(n):
            if not graph.is_active[u]:
                continue
            for v in graph.adjList[u]:
                if graph.is_active[v]:
                    in_neighbors[v].add(u)
                    unique_adj[u].add(v)

        flow = {}
        for u in range(n):
            if not graph.is_active[u]:
                continue
            for v in unique_adj[u]:
                flow[(u, v)] = solver.NumVar(0.0, inf, f'f_{u}_{v}')

        # Flow conservation constraints
        sum_x_except_s = solver.Sum(x[j] for j in range(n) if j != s)
        for i in range(n):
            if not graph.is_active[i]:
                continue
            
            incoming_flow = solver.Sum(flow[(u, i)] for u in in_neighbors[i])
            outgoing_flow = solver.Sum(flow[(i, w)] for w in unique_adj[i])

            if i == s:
                solver.Add(outgoing_flow - incoming_flow == sum_x_except_s)
            else:
                solver.Add(incoming_flow - outgoing_flow == x[i])
                solver.Add(incoming_flow <= n * x[i])

        # Solve the problem.
        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            cutset = {i for i in range(n) if y[i].solution_value() > 0.5}
            exact_val = graph.includedValue(s, t, cutset)
            return exact_val, cutset
        else:
            # If no optimal solution found (should not happen for this problem), return -inf.
            return float("-inf"), set()
