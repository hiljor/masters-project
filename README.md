# horse_algos

`horse_algos` contains the Python and C++ implementations of the graph-cut algorithms used in this thesis. The package loads map files in `data/`, evaluates candidate cut sets, and supports the Naive, Important Separators, C++-accelerated, and OR-Tools MILP implementations.

## Publication scope

This repository contains the reusable algorithm implementation, test data, source code, and automated tests used for the thesis work. Benchmark scripts, visualization output, temporary experiment files, and the development GUI are intentionally excluded from the publication copy.

## Installation

Install the package from a source checkout:

```bash
python -m pip install -e .
```

The core package has no third-party runtime dependencies. The optional MILP implementation requires OR-Tools:

```bash
python -m pip install "ortools>=9.15.6755"
```

The C++ implementation requires the `pybind11` build dependency and a compatible C++17 compiler.

## Testing

Run the test suite with:

```bash
python -m pytest
```

Tests that require optional functionality are skipped when the relevant dependency or compiled extension is unavailable. Install the optional dependencies above before running the complete solver suite.

## DOI

Add the DOI assigned by the thesis publisher or repository service to the final publication metadata before submission. The source package itself is versioned independently of the DOI.
