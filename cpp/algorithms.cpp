#include "algorithms.hpp"
#include <algorithm>
#include <cmath>

// Helper for combinations (naive)
void getCombinations(int n, int k, std::vector<int>& current, int start, std::vector<std::vector<int>>& result) {
    result.push_back(current);
    if (current.size() == (size_t)k) return;
    for (int i = start; i < n; ++i) {
        current.push_back(i);
        getCombinations(n, k, current, i + 1, result);
        current.pop_back();
    }
}

std::pair<int, std::set<int>> solve_naive(const std::vector<std::vector<int>>& adjList, const std::vector<int>& nodeValues, const std::set<int>& infSet, int s, int t, int k) {
    Graph graph(adjList, nodeValues, infSet);
    int n = nodeValues.size();
    std::vector<int> removable_nodes;
    for (int i = 0; i < n; ++i) {
        if (infSet.find(i) == infSet.end() && i != s && i != t) {
            removable_nodes.push_back(i);
        }
    }

    int optimal = -1000000000; // Large negative
    std::set<int> best_cut;

    std::vector<std::vector<int>> all_combs;
    std::vector<int> current;
    getCombinations(removable_nodes.size(), k, current, 0, all_combs);

    for (const auto& comb : all_combs) {
        std::set<int> comb_set;
        for (int idx : comb) comb_set.insert(removable_nodes[idx]);

        if (graph.hasPath(s, t, comb_set)) continue;
        
        int value = graph.includedValue(s); // Note: C++ version doesn't subtract cutset from value, it uses is_active
        // Wait, the Python version uses includedValue(s, t, comb_set) which DOES take the cutset.
        // My C++ Graph::includedValue(s) uses is_active. I should temporarily deactivate the cutset.
        
        int marker = graph.history.size();
        for (int node : comb_set) graph.deactivate(node);
        int val = graph.includedValue(s);
        graph.undo(marker);

        if (val > optimal) {
            optimal = val;
            best_cut = comb_set;
        }
    }
    return {optimal, best_cut};
}

void branch(Graph& graph, int s, int t, int current_k, std::set<int>& Z, int& max_source_size, std::set<int>& best_separator) {
    std::set<int> X = graph.minSeparator(s, t);

    if (X.size() > (size_t)current_k || X.empty()) {
        if (!graph.hasPath(s, t, {})) {
            int size = graph.includedValue(s);
            if (size > max_source_size) {
                max_source_size = size;
                best_separator = Z;
            }
        }
        return;
    }

    if (current_k == 0) return;

    int marker = graph.history.size();
    graph.uniteBySeparator(s, X);
    int v = *X.begin();

    // Branch 1: v IS in the separator
    int branch_marker = graph.history.size();
    graph.deactivate(v);
    Z.insert(v);
    branch(graph, s, t, current_k - 1, Z, max_source_size, best_separator);
    graph.undo(branch_marker);
    Z.erase(v);

    // Branch 2: v is NOT in the separator
    graph.unite(s, v);
    branch(graph, s, t, current_k, Z, max_source_size, best_separator);

    graph.undo(marker);
}

std::pair<int, std::set<int>> solve_important_separators(const std::vector<std::vector<int>>& adjList, const std::vector<int>& nodeValues, const std::set<int>& infSet, int s, int t, int k) {
    Graph graph(adjList, nodeValues, infSet);
    int max_source_size = -1000000000;
    std::set<int> best_separator;
    std::set<int> Z;
    branch(graph, s, t, k, Z, max_source_size, best_separator);
    return {max_source_size, best_separator};
}
