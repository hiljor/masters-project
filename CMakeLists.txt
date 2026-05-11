cmake_minimum_required(VERSION 3.10)
project(horse_algos_cpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

find_package(pybind11 REQUIRED)
find_package(ortools CONFIG REQUIRED)

pybind11_add_module(horse_algos_cpp cpp/bindings.cpp cpp/graph.cpp cpp/algorithms.cpp cpp/milp_solver.cpp)

install(TARGETS horse_algos_cpp DESTINATION horse_algos)

target_link_libraries(horse_algos_cpp PRIVATE pybind11::module ortools::ortools)
