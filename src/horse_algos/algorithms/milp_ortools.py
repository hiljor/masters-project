from ortools.linear_solver import pywraplp
from horse_algos.graph import Graph
from horse_algos.algorithms.algorithm import Algorithm, is_cancelled

class MILP_OR(Algorithm):
    """ MILP implementation using Google OR-Tools. """

    @property
    def name(self):
        return "MILP (OR-Tools)"

    def run(self, graph: Graph, s: int, t: int, k: int) -> tuple[int | float, set[int]]:
        """ Runs the MILP algorithm on the given graph. """
        
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

        # Solve the problem.
        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            max_val = objective.Value()
            cutset = {i for i in range(n) if y[i].solution_value() > 0.5}
            return max_val, cutset
        else:
            # If no optimal solution found (should not happen for this problem), return -inf.
            return float("-inf"), set()
