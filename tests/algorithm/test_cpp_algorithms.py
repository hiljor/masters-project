import pytest
from copy import deepcopy
from horse_algos.algorithms.cpp_algorithms import CppNaive, CppImportantSeparators, CPP_AVAILABLE

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
