#include "milp_solver.hpp"
#include "ortools/linear_solver/linear_solver.h"
#include <numeric>

namespace horse_algos {

using namespace operations_research;

MILPSolver::MILPSolver() {}

MILPResult MILPSolver::solve(const std::vector<std::vector<int>>& adjList, 
                         const std::vector<int>& nodeValues, 
                         const std::set<int>& infSet,
                         const std::vector<bool>& is_active,
                         int s, int t, int k) {
    // Create the linear solver with the SCIP backend.
    std::unique_ptr<MPSolver> solver(MPSolver::CreateSolver("SCIP"));
    if (!solver) {
        return {-1.0, {}};
    }

    int n = adjList.size();
    const double infinity = solver->infinity();

    // x[v] = 1 if node v is in the s-component, 0 otherwise.
    std::vector<MPVariable*> x(n);
    // y[v] = 1 if node v is removed (part of the cutset), 0 otherwise.
    std::vector<MPVariable*> y(n);

    for (int i = 0; i < n; ++i) {
        x[i] = solver->MakeBoolVar("x_" + std::to_string(i));
        y[i] = solver->MakeBoolVar("y_" + std::to_string(i));
    }

    // Objective: Maximize the total value of the s-component.
    MPObjective* const objective = solver->MutableObjective();
    for (int i = 0; i < n; ++i) {
        if (is_active[i]) {
            objective->SetCoefficient(x[i], nodeValues[i]);
        }
    }
    objective->SetMaximization();

    // Constraint 1: Source and Sink.
    solver->MakeRowConstraint(1.0, 1.0)->SetCoefficient(x[s], 1.0);
    solver->MakeRowConstraint(0.0, 0.0)->SetCoefficient(x[t], 1.0);

    // Constraint 2: Connectivity and 3: Node State.
    for (int i = 0; i < n; ++i) {
        if (!is_active[i]) {
            solver->MakeRowConstraint(0.0, 0.0)->SetCoefficient(x[i], 1.0);
            solver->MakeRowConstraint(0.0, 0.0)->SetCoefficient(y[i], 1.0);
            continue;
        }

        // x[i] + y[i] <= 1
        MPConstraint* const node_state = solver->MakeRowConstraint(-infinity, 1.0);
        node_state->SetCoefficient(x[i], 1.0);
        node_state->SetCoefficient(y[i], 1.0);

        // Connectivity: x[i] <= x[neighbor] + y[neighbor]  =>  x[i] - x[neighbor] - y[neighbor] <= 0
        for (int neighbor : adjList[i]) {
            if (is_active[neighbor]) {
                MPConstraint* const conn = solver->MakeRowConstraint(-infinity, 0.0);
                conn->SetCoefficient(x[i], 1.0);
                conn->SetCoefficient(x[neighbor], -1.0);
                conn->SetCoefficient(y[neighbor], -1.0);
            }
        }
    }

    // Constraint 4: Budget: sum(y) <= k
    MPConstraint* const budget = solver->MakeRowConstraint(-infinity, static_cast<double>(k));
    for (int i = 0; i < n; ++i) {
        budget->SetCoefficient(y[i], 1.0);
    }

    // Constraint 5: Irremovable Nodes.
    for (int node : infSet) {
        solver->MakeRowConstraint(0.0, 0.0)->SetCoefficient(y[node], 1.0);
    }
    
    // s and t cannot be in the cutset.
    solver->MakeRowConstraint(0.0, 0.0)->SetCoefficient(y[s], 1.0);
    solver->MakeRowConstraint(0.0, 0.0)->SetCoefficient(y[t], 1.0);

    const MPSolver::ResultStatus result_status = solver->Solve();

    if (result_status != MPSolver::OPTIMAL) {
        return {-1.0, {}};
    }

    MILPResult result;
    result.max_value = objective->Value();
    for (int i = 0; i < n; ++i) {
        if (y[i]->solution_value() > 0.5) {
            result.cutset.insert(i);
        }
    }

    return result;
}

} // namespace horse_algos
