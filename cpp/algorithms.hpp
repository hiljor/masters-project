#ifndef ALGORITHMS_HPP
#define ALGORITHMS_HPP

#include "graph.hpp"
#include <utility>

std::pair<int, std::set<int>> solve_naive(const std::vector<std::vector<int>>& adjList, const std::vector<int>& nodeValues, const std::set<int>& infSet, int s, int t, int k);
std::pair<int, std::set<int>> solve_important_separators(const std::vector<std::vector<int>>& adjList, const std::vector<int>& nodeValues, const std::set<int>& infSet, int s, int t, int k);

#endif
