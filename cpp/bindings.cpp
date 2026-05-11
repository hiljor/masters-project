#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "algorithms.hpp"
#include "milp_solver.hpp"

namespace py = pybind11;
using namespace horse_algos;

PYBIND11_MODULE(horse_algos_cpp, m) {
    m.doc() = "C++ extension for horse algorithm project";
    
    m.def("solve_naive", &solve_naive, "Brute force solver",
          py::arg("adj_list"), py::arg("node_values"), py::arg("inf_set"), py::arg("s"), py::arg("t"), py::arg("k"));
    
    m.def("solve_important_separators", &solve_important_separators, "Important separators solver",
          py::arg("adj_list"), py::arg("node_values"), py::arg("inf_set"), py::arg("s"), py::arg("t"), py::arg("k"));

    py::class_<MILPResult>(m, "MILPResult")
        .def_readonly("max_value", &MILPResult::max_value)
        .def_readonly("cutset", &MILPResult::cutset);

    py::class_<MILPSolver>(m, "MILPSolver")
        .def(py::init<>())
        .def("solve", &MILPSolver::solve, "Solves the maximum weight s-component s-t cut problem using MILP",
             py::arg("adj_list"), py::arg("node_values"), py::arg("inf_set"), py::arg("is_active"), py::arg("s"), py::arg("t"), py::arg("k"));
}
