cmake_minimum_required(VERSION 3.14)
project(h3_toolkit)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(FetchContent)

FetchContent_Declare(
  h3
  GIT_REPOSITORY https://github.com/uber/h3.git
  GIT_TAG        v4.1.0 
)

FetchContent_MakeAvailable(h3)

# Boost.Geometry (header-only, used for polygon buffering)
find_package(Boost REQUIRED)

include_directories(${h3_SOURCE_DIR}/src/h3lib/include src/cpp/include)

add_library(h3_toolkit STATIC
    src/cpp/src/h3_toolkit.cpp
)

# Link against h3 target (h3 usually exposes 'h3' target) and Boost
target_link_libraries(h3_toolkit PUBLIC h3 Boost::headers)
target_include_directories(h3_toolkit PUBLIC src/cpp/include ${Boost_INCLUDE_DIRS})

# Tests
enable_testing()
add_executable(h3_toolkit_test tests/cpp/test_h3_toolkit.cpp)
target_link_libraries(h3_toolkit_test h3_toolkit )
add_test(NAME h3_toolkit_test COMMAND h3_toolkit_test)

# Benchmark
add_executable(bench_pure_cpp benchmarks/bench_pure_cpp.cpp)
target_link_libraries(bench_pure_cpp h3_toolkit)

# Verification
add_executable(verify_cpp benchmarks/verify_cpp.cpp)
target_link_libraries(verify_cpp h3_toolkit)

# Python bindings (pybind11)
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

pybind11_add_module(_h3_toolkit_cpp src/bindings/python_bindings.cpp)
target_link_libraries(_h3_toolkit_cpp PRIVATE h3_toolkit h3)
target_include_directories(_h3_toolkit_cpp PRIVATE src/cpp/include ${h3_SOURCE_DIR}/src/h3lib/include)

# Install to Python package directory
install(TARGETS _h3_toolkit_cpp DESTINATION ${CMAKE_SOURCE_DIR}/src/python/h3_toolkit)
message(STATUS "Building Python bindings with pybind11")
