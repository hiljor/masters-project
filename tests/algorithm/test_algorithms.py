import pytest
from copy import deepcopy
from horse_algos.algorithms.naive import Naive
from horse_algos.algorithms.important_separator import ImportantSeparators

SMALL_CASES = ["case_basic", "case_impossible", "case_optimal", "case_inf_set", "case_pal", "case_pal2", "case_horse_cherry"]
LARGE_CASES = ["case_horse_cherry2", "case_horse_dots"]

@pytest.mark.parametrize("algorithm", [Naive(), ImportantSeparators()])
@pytest.mark.parametrize("case_name", SMALL_CASES)
def test_small_matrix(request, algorithm, case_name):
    data = request.getfixturevalue(case_name)
    result = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
    assert result == data.expected, f"{algorithm.name} failed on {case_name}, returned"

@pytest.mark.parametrize("algorithm", [ImportantSeparators()])
@pytest.mark.parametrize("case_name", LARGE_CASES)
def test_large_matrix(request, algorithm, case_name):
    data = request.getfixturevalue(case_name)
    result = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
    assert result == data.expected, f"{algorithm.name} failed on {case_name}, returned"