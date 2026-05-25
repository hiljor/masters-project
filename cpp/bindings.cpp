#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "algorithms.hpp"

namespace py = pybind11;

PYBIND11_MODULE(horse_algos_cpp, m) {
    m.doc() = "C++ extension for horse algorithm project";
    
    m.def("solve_naive", &solve_naive, "Brute force solver",
          py::arg("adj_list"), py::arg("node_values"), py::arg("inf_set"), py::arg("s"), py::arg("t"), py::arg("k"));
    
    m.def("solve_important_separators", &solve_important_separators, "Important separators solver",
          py::arg("adj_list"), py::arg("node_values"), py::arg("inf_set"), py::arg("s"), py::arg("t"), py::arg("k"));
}
