#include "graph.hpp"
#include <algorithm>
#include <queue>
#include <limits>
#include <iostream>

Graph::Graph(const std::vector<std::vector<int>>& adjList, const std::vector<int>& nodeValues, const std::set<int>& infSet)
    : adjList(adjList), nodeValues(nodeValues), infSet(infSet) {
    int n = nodeValues.size();
    parent.resize(n);
    rank.resize(n, 0);
    is_active.resize(n, true);
    for (int i = 0; i < n; ++i) parent[i] = i;
}

int Graph::find(int x) {
    while (x != parent[x]) {
        x = parent[x];
    }
    return x;
}

bool Graph::unite(int a, int b) {
    int root_a = find(a);
    int root_b = find(b);
    if (root_a != root_b) {
        if (rank[root_a] < rank[root_b]) std::swap(root_a, root_b);
        bool rank_increased = false;
        if (rank[root_a] == rank[root_b]) {
            rank[root_a]++;
            rank_increased = true;
        }
        parent[root_b] = root_a;
        history.push_back({"union", root_a, root_b, rank_increased, -1});
        return true;
    }
    return false;
}

void Graph::deactivate(int v) {
    is_active[v] = false;
    history.push_back({"deactivate", -1, -1, false, v});
}

void Graph::undo(int target_size) {
    while (history.size() > (size_t)target_size) {
        HistoryEntry m = history.back();
        history.pop_back();
        if (m.type == "deactivate") {
            is_active[m.node] = true;
        } else {
            parent[m.v] = m.v;
            if (m.rank_increased) {
                rank[m.u]--;
            }
        }
    }
}

int Graph::includedValue(int s) {
    std::set<int> visited;
    std::vector<int> stack = {s};
    int totalValue = 0;
    while (!stack.empty()) {
        int vertex = stack.back();
        stack.pop_back();
        if (visited.count(vertex) || !is_active[vertex]) continue;
        visited.insert(vertex);
        totalValue += nodeValues[vertex];
        for (int neighbor : adjList[vertex]) {
            stack.push_back(neighbor);
        }
    }
    return totalValue;
}

void Graph::uniteBySeparator(int s, const std::set<int>& separator) {
    std::set<int> visited;
    std::vector<int> stack = {s};
    while (!stack.empty()) {
        int vertex = stack.back();
        stack.pop_back();
        if (visited.count(vertex) || separator.count(vertex) || !is_active[vertex]) continue;
        visited.insert(vertex);
        unite(s, vertex);
        for (int neighbor : adjList[vertex]) {
            stack.push_back(neighbor);
        }
    }
}

bool Graph::hasPath(int a, int b, const std::set<int>& cutset) {
    std::set<int> visited;
    std::vector<int> stack = {a};
    while (!stack.empty()) {
        int vertex = stack.back();
        stack.pop_back();
        if (visited.count(vertex) || cutset.count(vertex) || !is_active[vertex]) continue;
        if (vertex == b) return true;
        visited.insert(vertex);
        for (int neighbor : adjList[vertex]) {
            stack.push_back(neighbor);
        }
    }
    return false;
}

std::vector<std::vector<double>> Graph::generateFlowMatrix(int s, int t) {
    int n = nodeValues.size();
    std::vector<std::vector<double>> flowMatrix(2 * n, std::vector<double>(2 * n, 0));
    
    int root_s = find(s);
    int root_t = find(t);
    std::set<int> inf_roots;
    for (int node : infSet) inf_roots.insert(find(node));
    inf_roots.insert(root_s);
    inf_roots.insert(root_t);

    double inf = std::numeric_limits<double>::infinity();

    for (int i = 0; i < n; ++i) {
        if (!is_active[i]) continue;
        
        flowMatrix[2 * i][2 * i + 1] = inf_roots.count(find(i)) ? inf : 1.0;
        
        int root_i = find(i);
        if (root_i != i && is_active[root_i]) {
            flowMatrix[2 * i + 1][2 * root_i] = inf;
            flowMatrix[2 * root_i + 1][2 * i] = inf;
        }

        for (int neighbor : adjList[i]) {
            if (is_active[neighbor]) {
                flowMatrix[2 * i + 1][2 * neighbor] = inf;
            }
        }
    }
    return flowMatrix;
}

std::set<int> Graph::minSeparator(int s, int t) {
    auto flowMatrix = generateFlowMatrix(s, t);
    int num_nodes = flowMatrix.size();
    int source_node = 2 * s + 1;
    int sink_node = 2 * t;
    double inf = std::numeric_limits<double>::infinity();

    auto bfs = [&](std::vector<int>& parent) {
        std::fill(parent.begin(), parent.end(), -1);
        std::queue<int> q;
        q.push(source_node);
        parent[source_node] = source_node;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v = 0; v < num_nodes; ++v) {
                if (parent[v] == -1 && flowMatrix[u][v] > 0) {
                    parent[v] = u;
                    if (v == sink_node) return true;
                    q.push(v);
                }
            }
        }
        return false;
    };

    std::vector<int> parent(num_nodes);
    while (bfs(parent)) {
        double path_flow = inf;
        for (int v = sink_node; v != source_node; v = parent[v]) {
            path_flow = std::min(path_flow, flowMatrix[parent[v]][v]);
        }
        if (path_flow == inf) break;
        for (int v = sink_node; v != source_node; v = parent[v]) {
            int u = parent[v];
            if (flowMatrix[u][v] != inf) flowMatrix[u][v] -= path_flow;
            if (flowMatrix[v][u] != inf) flowMatrix[v][u] += path_flow;
        }
    }

    std::vector<bool> can_reach_t(num_nodes, false);
    std::queue<int> q;
    q.push(sink_node);
    can_reach_t[sink_node] = true;
    while (!q.empty()) {
        int v = q.front(); q.pop();
        for (int u = 0; u < num_nodes; ++u) {
            if (!can_reach_t[u] && flowMatrix[u][v] > 0) {
                can_reach_t[u] = true;
                q.push(u);
            }
        }
    }

    std::set<int> min_cut;
    for (int i = 0; i < (int)adjList.size(); ++i) {
        if (i == s || i == t) continue;
        if (!can_reach_t[2 * i] && can_reach_t[2 * i + 1]) {
            min_cut.insert(i);
        }
    }
    return min_cut;
}
