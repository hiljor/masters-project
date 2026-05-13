import pytest
from copy import deepcopy
from horse_algos.algorithms.milp_ortools import MILP_OR

@pytest.mark.parametrize("case_name", ["case_horse_cherry2"])
def test_milp_large(request, case_name):
    data = request.getfixturevalue(case_name)
    solver = MILP_OR()
    result_val, _ = solver.run(deepcopy(data.graph), data.s, data.t, data.k)
    assert result_val == data.expected, f"MILP failed on {case_name}, returned {result_val}"
