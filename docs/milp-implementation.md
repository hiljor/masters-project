# MILP Implementation Plan (Google OR-Tools)

This document outlines the plan for implementing a Mixed Integer Linear Program (MILP) to solve the maximum weight $s$-component $s-t$ cut problem with a budget $k$ using Google OR-Tools.

## 1. Mathematical Model

### Variables
- $x_v \in \{0, 1\}$: Binary variable where $x_v = 1$ if node $v$ is in the $s$-component, $0$ otherwise.
- $y_v \in \{0, 1\}$: Binary variable where $y_v = 1$ if node $v$ is removed (part of the cutset), $0$ otherwise.

### Objective
Maximize the total value of the $s$-component:
$$\max \sum_{v \in V_{active}} w_v x_v$$
where $w_v$ is the weight of node $v$.

### Constraints
1. **Source and Sink**:
   - $x_s = 1$ ($s$ is always in its own component).
   - $x_t = 0$ ($t$ must be separated from $s$).

2. **Connectivity**:
   - For every edge $(u, v) \in E$ where $u, v$ are active:
     $$x_u \le x_v + y_v$$
     (If $u$ is in the $s$-component, its neighbor $v$ must either be in the $s$-component or be removed).

3. **Node State**:
   - For every node $v$:
     $$x_v + y_v \le 1$$
     (A node cannot be both in the $s$-component and removed).

4. **Budget**:
   - Total number of removed nodes cannot exceed $k$:
     $$\sum_{v \in V_{active}} y_v \le k$$

5. **Irremovable Nodes**:
   - For every $v \in I$ (irremovable set) or $v \in \{s, t\}$:
     $$y_v = 0$$

## 2. Technology Stack

- **Library**: `Google OR-Tools`
  - **Reasoning**: Powerful, industrial-grade solver suite with excellent performance and native support for both Python and C++.
- **Solvers**: 
  - Python: `ortools.linear_solver.pywraplp` (SCIP or CBC backend).
  - C++: `operations_research::MPSolver` (SCIP or CBC backend).

## 3. Implementation Steps

### Phase 1: Environment Setup
1. **Python**:
   - Add `ortools` to `requirements.txt`.
   - Install dependencies: `pip install ortools`.
2. **C++**:
   - Update `CMakeLists.txt` to find and link `ortools`.
   - Ensure `ortools` is installed on the build system.

### Phase 2: Python Implementation
1. Create `src/horse_algos/algorithms/milp_ortools.py`.
2. Implement the `MILP` class inheriting from `Algorithm`.
3. Use `pywraplp.Solver.CreateSolver('SCIP')`.
4. Define variables, constraints, and objective using the high-level Python API.

### Phase 3: C++ Implementation
1. Create `cpp/milp_solver.cpp` and `cpp/milp_solver.hpp`.
2. Implement the MILP model using `operations_research::MPSolver`.
3. Expose the C++ implementation via `cpp/bindings.cpp` for use in Python.
4. Update `src/horse_algos/algorithms/cpp_algorithms.py` to include the MILP solver.

### Phase 4: Integration
1. Update `src/horse_algos/algorithms/__init__.py` to export the new `MILP` classes (both Python and C++ wrapped).
2. The GUI (`web/server.py`) will automatically discover the new algorithms.

### Phase 5: Verification
1. Create `tests/algorithm/test_milp_ortools.py`.
2. Run parity tests comparing Python MILP, C++ MILP, and Naive results.
3. Verify performance improvements of C++ MILP over Python MILP for large graphs.

## 4. Example Usage (Python)
```python
from horse_algos.algorithms.milp_ortools import MILP
from horse_algos.graph import Graph

# Initialize graph and solver
solver = MILP()
max_val, cutset = solver.run(graph, s, t, k)
```
