import pytest
from copy import deepcopy
from horse_algos.algorithms.cpp_algorithms import CppNaive, CppImportantSeparators, CppMILP, CPP_AVAILABLE

@pytest.mark.skipif(not CPP_AVAILABLE, reason="C++ extension not available")
class TestCppAlgorithms:
    SMALL_CASES = ["case_basic", "case_impossible", "case_optimal", "case_inf_set", "case_pal", "case_pal2", "case_horse_cherry"]
    LARGE_CASES = ["case_horse_cherry2", "case_horse_dots"]

    @pytest.mark.parametrize("algorithm", [CppNaive(), CppImportantSeparators(), CppMILP()])
    @pytest.mark.parametrize("case_name", SMALL_CASES)
    def test_small_matrix(self, request, algorithm, case_name):
        data = request.getfixturevalue(case_name)
        result_val, _ = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
        assert result_val == data.expected, f"{algorithm.name} failed on {case_name}, returned {result_val}"

    @pytest.mark.parametrize("algorithm", [CppImportantSeparators()])
    @pytest.mark.parametrize("case_name", LARGE_CASES)
    def test_large_matrix(self, request, algorithm, case_name):
        data = request.getfixturevalue(case_name)
        result_val, _ = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
        assert result_val == data.expected, f"{algorithm.name} failed on {case_name}, returned {result_val}"
