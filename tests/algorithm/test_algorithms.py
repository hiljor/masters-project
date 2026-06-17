import pytest
from copy import deepcopy
from horse_algos.algorithms.milp_ortools import MILP_OR
from horse_algos.algorithms.naive import Naive
from horse_algos.algorithms.important_separator import ImportantSeparators

SMALL_CASES = ["case_basic", "case_impossible", "case_optimal", "case_inf_set", "case_pal", "case_pal2", "case_diamonds_small"]
LARGE_CASES = ["case_diamonds", "case_dots", "case_portals_cherries"]

@pytest.mark.parametrize("algorithm", [Naive(), ImportantSeparators(), MILP_OR()])
@pytest.mark.parametrize("case_name", SMALL_CASES)
def test_small_matrix(request, algorithm, case_name):
    data = request.getfixturevalue(case_name)
    result_val, _ = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
    assert result_val == data.expected, f"{algorithm.name} failed on {case_name}, returned {result_val}"

@pytest.mark.parametrize("algorithm", [ImportantSeparators(), MILP_OR()])
@pytest.mark.parametrize("case_name", LARGE_CASES)
def test_large_matrix(request, algorithm, case_name):
    data = request.getfixturevalue(case_name)
    result_val, _ = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
    assert result_val == data.expected, f"{algorithm.name} failed on {case_name}, returned {result_val}"