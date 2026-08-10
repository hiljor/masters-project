#include "algorithms.hpp"
#include <algorithm>
#include <cmath>

void evaluate_combinations(
    const std::vector<int>& removable_nodes,
    int k,
    int start,
    std::vector<int>& current,
    Graph& graph,
    int s,
    int t,
    int& optimal,
    std::set<int>& best_cut
) {
    std::set<int> comb_set;
    for (int idx : current) {
        comb_set.insert(removable_nodes[idx]);
    }

    if (!graph.hasPath(s, t, comb_set)) {
        int marker = graph.history.size();
        for (int node : comb_set) graph.deactivate(node);
        int val = graph.includedValue(s);
        graph.undo(marker);

        if (val > optimal) {
            optimal = val;
            best_cut = comb_set;
        }
    }

    if ((int)current.size() == k) {
        return;
    }

    for (int i = start; i < (int)removable_nodes.size(); ++i) {
        current.push_back(i);
        evaluate_combinations(removable_nodes, k, i + 1, current, graph, s, t, optimal, best_cut);
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
    std::vector<int> current;
    evaluate_combinations(removable_nodes, k, 0, current, graph, s, t, optimal, best_cut);
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
