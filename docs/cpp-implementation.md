# C++ Algorithm Implementation Plan

This document outlines the plan for converting the core algorithms (Naive and Important Separators) from Python to C++ to improve performance.

## 1. Challenges: Python vs. C++

### Performance & Complexity
- **Python:** Highly expressive but slow for heavy recursion and combinatorial tasks. The `Important Separators` algorithm and `Naive` brute-force suffer from Python's overhead in large graphs.
- **C++:** Offers significant speedups due to direct memory management and compiled code. The recursive branching in `Important Separators` will benefit most.

### Data Structures
- **Mapping:** We must ensure that the C++ `Graph` class exactly mirrors the behavior of the Python `Graph` class, especially regarding `infSet` (irremovable nodes), `deactivate()`, `unite()`, and `undo()`.
- **Interoperability:** Use `pybind11` to bridge the two languages. This allows passing Python `list` and `set` objects directly to C++ functions.

### Maintenance
- Double implementation means we must keep both versions in sync.
- Verification is key: C++ results must exactly match Python results for the same inputs.

## 2. Implementation Steps

### Phase 1: C++ Core (Completed/Refining)
- Implement `Graph` class in `cpp/graph.hpp` and `cpp/graph.cpp`.
- Implement `solve_naive` and `solve_important_separators` in `cpp/algorithms.cpp`.
- Expose these via `cpp/bindings.cpp`.

### Phase 2: Python Integration
- Create a new Python module (e.g., `horse_algos.algorithms.cpp_wrapper`) or update existing ones to call the C++ extension.
- Ensure the C++ extension is compiled and available as `horse_algos_cpp`.

### Phase 3: GUI Update
- Modify `web/server.py` to:
    - Attempt to load the C++ module.
    - Add a `language` parameter to the `SolveRequest`.
    - Route the request to either the Python or C++ implementation.
- Modify `web/index.html` to:
    - Add a "Language" dropdown (Python/C++).
    - Send the selected language in the solve request.

### Phase 4: Verification & Testing
- Write equivalent tests in `tests/algorithm/test_cpp_algorithms.py`.
- Ensure parity between Python and C++ outputs.

## 3. Build Requirements
- CMake (>= 3.10)
- C++17 Compiler
- `pybind11`
- Python Development Headers
