import pytest
from copy import deepcopy
from horse_algos.algorithms.naive import Naive
from horse_algos.algorithms.important_separator import ImportantSeparators

CASES = ["case_basic", "case_impossible", "case_optimal", "case_inf_set"]

@pytest.mark.parametrize("algorithm", [Naive(), ImportantSeparators()])
@pytest.mark.parametrize("case_name", CASES )
def test_matrix(request, algorithm, case_name):
    # 'case_name' is now automatically filled with "case_basic", "case_impossible", etc.
    data = request.getfixturevalue(case_name)

    result = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)

    assert result == data.expected, f"{algorithm.name} failed on {case_name}, returned"