#ifndef MILP_SOLVER_HPP
#define MILP_SOLVER_HPP

#include <vector>
#include <set>
#include <string>
#include "graph.hpp"

namespace horse_algos {

struct MILPResult {
    double max_value;
    std::set<int> cutset;
};

class MILPSolver {
public:
    MILPSolver();
    MILPResult solve(const std::vector<std::vector<int>>& adjList, 
                     const std::vector<int>& nodeValues, 
                     const std::set<int>& infSet,
                     const std::vector<bool>& is_active,
                     int s, int t, int k);

private:
    // Any internal state if needed
};

} // namespace horse_algos

#endif // MILP_SOLVER_HPP
