cmake_minimum_required(VERSION 3.20)
project(routing_engine VERSION 1.0.0 LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Suppress FindBoost warning for CMake 4.x
if(POLICY CMP0167)
    cmake_policy(SET CMP0167 NEW)
endif()

# Find packages
find_package(Arrow REQUIRED)
find_package(Parquet REQUIRED)
find_package(Boost REQUIRED COMPONENTS system filesystem)

# H3 - try to find, or use local install
find_library(H3_LIBRARY NAMES h3 HINTS ${CMAKE_PREFIX_PATH}/lib $ENV{CONDA_PREFIX}/lib)
find_path(H3_INCLUDE_DIR NAMES h3/h3api.h HINTS ${CMAKE_PREFIX_PATH}/include $ENV{CONDA_PREFIX}/include)

if(NOT H3_LIBRARY OR NOT H3_INCLUDE_DIR)
    message(FATAL_ERROR "H3 library not found. Run: ./scripts/install_h3.sh")
endif()

# DuckDB - find library
find_library(DUCKDB_LIBRARY NAMES duckdb HINTS ${CMAKE_PREFIX_PATH}/lib $ENV{CONDA_PREFIX}/lib /usr/local/lib)
find_path(DUCKDB_INCLUDE_DIR NAMES duckdb.hpp HINTS ${CMAKE_PREFIX_PATH}/include $ENV{CONDA_PREFIX}/include /usr/local/include)

if(NOT DUCKDB_LIBRARY OR NOT DUCKDB_INCLUDE_DIR)
    message(WARNING "DuckDB library not found. DuckDB loading will be disabled.")
    set(HAVE_DUCKDB OFF)
else()
    set(HAVE_DUCKDB ON)
    message(STATUS "Found DuckDB: ${DUCKDB_LIBRARY}")
endif()

message(STATUS "Found Arrow: ${Arrow_DIR}")
message(STATUS "Found Parquet: ${Parquet_DIR}")
message(STATUS "Found H3: ${H3_LIBRARY}")
message(STATUS "Found Boost: ${Boost_INCLUDE_DIRS}")

# Create routing library (core algorithms)
add_library(routing_lib STATIC
    src/shortcut_graph.cpp
    src/h3_utils.cpp
)

target_include_directories(routing_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/crow/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/json/include
    ${H3_INCLUDE_DIR}
    ${Boost_INCLUDE_DIRS}
)

if(HAVE_DUCKDB)
    target_include_directories(routing_lib PUBLIC ${DUCKDB_INCLUDE_DIR})
    target_compile_definitions(routing_lib PUBLIC HAVE_DUCKDB)
endif()

target_link_libraries(routing_lib PUBLIC
    Arrow::arrow_shared
    Parquet::parquet_shared
    ${H3_LIBRARY}
    Boost::system
    Boost::filesystem
)

if(HAVE_DUCKDB)
    target_link_libraries(routing_lib PUBLIC ${DUCKDB_LIBRARY})
endif()

# CLI executable
add_executable(routing_engine src/main.cpp)
target_link_libraries(routing_engine PRIVATE routing_lib)

# HTTP Server executable
add_executable(routing_server src/server.cpp)
target_link_libraries(routing_server PRIVATE routing_lib)

# Test executable
add_executable(test_routing src/test_routing.cpp)
target_link_libraries(test_routing PRIVATE routing_lib)

# Install
install(TARGETS routing_engine routing_server test_routing RUNTIME DESTINATION bin)

