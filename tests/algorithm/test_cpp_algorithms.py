import pytest
from copy import deepcopy
from horse_algos.algorithms.cpp_algorithms import CppNaive, CppImportantSeparators, CPP_AVAILABLE
from horse_algos.tools.map_loader import load_graph_from_map

@pytest.mark.skipif(not CPP_AVAILABLE, reason="C++ extension not available")
class TestCppAlgorithms:
    SMALL_CASES = ["case_basic", "case_impossible", "case_optimal", "case_inf_set", "case_pal", "case_pal2", "case_diamonds_small"]
    LARGE_CASES = ["case_diamonds", "case_dots", "case_portals_cherries"]

    @pytest.mark.parametrize("algorithm", [CppNaive(), CppImportantSeparators()])
    @pytest.mark.parametrize("case_name", SMALL_CASES)
    def test_small_matrix(self, request, algorithm, case_name):
        data = request.getfixturevalue(case_name)
        result_val, _ = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
        assert float(result_val) == float(data.expected), f"{algorithm.name} failed on {case_name}, returned {result_val}"

    @pytest.mark.parametrize("algorithm", [CppImportantSeparators()])
    @pytest.mark.parametrize("case_name", LARGE_CASES)
    def test_large_matrix(self, request, algorithm, case_name):
        data = request.getfixturevalue(case_name)
        result_val, _ = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
        assert float(result_val) == float(data.expected), f"{algorithm.name} failed on {case_name}, returned {result_val}"

    def test_naive_rejects_runtime_over_threshold(self):
        """horse_dots.txt at k=4 was benchmarked at ~608s (see
        results/benchmark_results.csv), well beyond the 200s time limit
        derived from the empirical model in runtime_limits.py, even though
        its raw combination count (98,491,965) is under the hard
        100,000,000 combinatorial cap. It should therefore be rejected
        with a RuntimeError before ever invoking the C++ solver."""
        graph, s, t = load_graph_from_map("horse_dots.txt")
        with pytest.raises(RuntimeError, match="too expensive"):
            CppNaive().run(deepcopy(graph), s, t, 4)

    def test_important_separators_rejects_runtime_over_threshold(self):
        """horse_dots.txt at k=13 was benchmarked at ~1751s (see
        results/benchmark_results.csv), far beyond the 200s time limit.
        It should be rejected with a RuntimeError before invoking the
        C++ solver."""
        graph, s, t = load_graph_from_map("horse_dots.txt")
        with pytest.raises(RuntimeError, match="too expensive"):
            CppImportantSeparators().run(deepcopy(graph), s, t, 13)

    def test_important_separators_allows_runtime_under_threshold(self):
        """horse_dots.txt at k=10 was benchmarked at ~55s, comfortably
        under the 200s limit, and should run successfully."""
        graph, s, t = load_graph_from_map("horse_dots.txt")
        result_val, _ = CppImportantSeparators().run(deepcopy(graph), s, t, 10)
        assert result_val != float("-inf")
