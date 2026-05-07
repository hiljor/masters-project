#ifndef GRAPH_HPP
#define GRAPH_HPP

#include <vector>
#include <set>
#include <map>
#include <string>

struct HistoryEntry {
    std::string type; // "union" or "deactivate"
    int u;
    int v;
    bool rank_increased;
    int node;
};

class Graph {
public:
    std::vector<std::vector<int>> adjList;
    std::vector<int> nodeValues;
    std::set<int> infSet;
    std::vector<int> parent;
    std::vector<int> rank;
    std::vector<bool> is_active;
    std::vector<HistoryEntry> history;

    Graph(const std::vector<std::vector<int>>& adjList, const std::vector<int>& nodeValues, const std::set<int>& infSet);

    int find(int x);
    bool unite(int a, int b);
    void deactivate(int v);
    void undo(int target_size);
    int includedValue(int s);
    void uniteBySeparator(int s, const std::set<int>& separator);
    bool hasPath(int a, int b, const std::set<int>& cutset);
    std::set<int> minSeparator(int s, int t);

private:
    std::vector<std::vector<double>> generateFlowMatrix(int s, int t);
};

#endif
