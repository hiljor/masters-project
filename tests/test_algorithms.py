import pytest
from copy import deepcopy
from horse_algos.algorithms.naive import Naive

CASES = ["case_basic", "case_impossible", "case_optimal"]

@pytest.mark.parametrize("algorithm", [Naive()])
@pytest.mark.parametrize("case_name", CASES )
def test_matrix(request, algorithm, case_name):
    # 'case_name' is now automatically filled with "case_basic", "case_impossible", etc.
    data = request.getfixturevalue(case_name)
    
    result = algorithm.run(deepcopy(data.graph), data.s, data.t, data.k)
    
    assert result == data.expected, f"{algorithm.name} failed on {case_name}, returned"