#include "h3_toolkit.hpp"
#include <h3api.h>
#include <iostream>
#include <chrono>
#include <set>

const int TARGET_RES = 15;

int main() {
    std::cout << "==================================================" << std::endl;
    std::cout << "PURE C++ Benchmark" << std::endl;
    std::cout << "==================================================" << std::endl;
    
    H3Index base_cells[122];
    getRes0Cells(base_cells);
    H3Index cell_res0 = base_cells[0];
    
    std::cout << "Base cell: " << std::hex << cell_res0 << std::dec << std::endl;
    std::cout << "Target resolution: " << TARGET_RES << std::endl;
    std::cout << std::endl;
    std::cout << "Computing..." << std::endl;
    
    std::set<int> all_faces = {1, 2, 3, 4, 5, 6};
    
    auto start = std::chrono::high_resolution_clock::now();
    auto result = h3_toolkit::children_on_boundary_faces(cell_res0, TARGET_RES, all_faces);
    auto end = std::chrono::high_resolution_clock::now();
    
    std::chrono::duration<double> elapsed = end - start;
    
    std::cout << "Count: " << result.size() << std::endl;
    std::cout << "Time:  " << elapsed.count() << " seconds" << std::endl;
    std::cout << "Rate:  " << (result.size() / elapsed.count()) << " cells/sec" << std::endl;
    
    return 0;
}
