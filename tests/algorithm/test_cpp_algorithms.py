import pytest
from copy import deepcopy
from horse_algos.algorithms.cpp_algorithms import CppNaive, CppImportantSeparators, CPP_AVAILABLE
from horse_algos.algorithms.runtime_limits import get_max_k
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

    def test_naive_rejects_k_beyond_measured_max(self):
        """runtime_limits.MAX_K_TABLE (populated by scripts/find_max_k.py,
        which times each map once at increasing k and stops as soon as a
        run exceeds the time budget) records a measured max k for
        horse_dots.txt's Brute Force (C++) shape. Requesting a k one
        above that measured max should be rejected with a RuntimeError
        before ever invoking the C++ solver, exactly like the existing
        combinatorial guard."""
        graph, s, t = load_graph_from_map("horse_dots.txt")
        removable = len([i for i in range(len(graph.nodeValues))
                          if i not in graph.infSet and i != s and i != t])
        edges = sum(len(adj) for adj in graph.adjList)
        max_k = get_max_k("Brute Force (C++)", len(graph.nodeValues), edges, removable)
        assert max_k is not None, "expected a measured max k for horse_dots.txt in runtime_limits.py"

        with pytest.raises(RuntimeError, match="too expensive"):
            CppNaive().run(deepcopy(graph), s, t, max_k + 1)

    def test_important_separators_rejects_k_beyond_measured_max(self):
        """Same guard as above, applied to Important Separators (C++)."""
        graph, s, t = load_graph_from_map("horse_dots.txt")
        removable = len([i for i in range(len(graph.nodeValues))
                          if i not in graph.infSet and i != s and i != t])
        edges = sum(len(adj) for adj in graph.adjList)
        max_k = get_max_k("Important Separators (C++)", len(graph.nodeValues), edges, removable)
        assert max_k is not None, "expected a measured max k for horse_dots.txt in runtime_limits.py"

        with pytest.raises(RuntimeError, match="too expensive"):
            CppImportantSeparators().run(deepcopy(graph), s, t, max_k + 1)

    def test_important_separators_allows_k_at_measured_max(self):
        """A k at (not beyond) the measured max should still run
        successfully."""
        graph, s, t = load_graph_from_map("horse_dots.txt")
        removable = len([i for i in range(len(graph.nodeValues))
                          if i not in graph.infSet and i != s and i != t])
        edges = sum(len(adj) for adj in graph.adjList)
        max_k = get_max_k("Important Separators (C++)", len(graph.nodeValues), edges, removable)
        assert max_k is not None

        result_val, _ = CppImportantSeparators().run(deepcopy(graph), s, t, max_k)
        assert result_val != float("-inf")

    def test_get_max_k_returns_none_for_unmeasured_shape(self):
        """A graph shape that was never measured (e.g. a tiny synthetic
        test graph) should not have any limit enforced, so unit-test
        graphs used elsewhere in the suite keep working unmodified."""
        assert get_max_k("Brute Force (C++)", nodes=3, edges=2, removable=1) is None
        assert get_max_k("Unknown Algorithm", nodes=1, edges=1, removable=1) is None


class TestGetMaxKLookup:
    """Hardware-independent unit tests for the MAX_K_TABLE lookup helper
    itself, using an injected fake table instead of the real (machine-
    dependent) measurements."""

    def test_lookup_hit(self, monkeypatch):
        import horse_algos.algorithms.runtime_limits as runtime_limits
        monkeypatch.setattr(runtime_limits, "MAX_K_TABLE", {
            "Brute Force (C++)": {(10, 20, 5): 3},
        })
        assert runtime_limits.get_max_k("Brute Force (C++)", 10, 20, 5) == 3

    def test_lookup_miss_returns_none(self, monkeypatch):
        import horse_algos.algorithms.runtime_limits as runtime_limits
        monkeypatch.setattr(runtime_limits, "MAX_K_TABLE", {
            "Brute Force (C++)": {(10, 20, 5): 3},
        })
        assert runtime_limits.get_max_k("Brute Force (C++)", 99, 99, 99) is None
        assert runtime_limits.get_max_k("Some Other Algorithm", 10, 20, 5) is None
