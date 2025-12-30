#include "h3_toolkit.hpp"
#include <h3api.h>
#include <iostream>
#include <chrono>
#include <set>

int main() {
    // Get a resolution 0 cell (base cell)
    // Get first base cell
    int num_base_cells = 122;
    H3Index base_cells[122];
    getRes0Cells(base_cells);
    
    H3Index cell_res0 = base_cells[0];
    
    std::cout << "Base cell: " << std::hex << cell_res0 << std::dec << std::endl;
    std::cout << "Resolution: " << getResolution(cell_res0) << std::endl;
    std::cout << std::endl;
    
    int target_res = 15;
    
    std::cout << "Computing boundary children from res 0 to res " << target_res << "..." << std::endl;
    std::cout << "This may take a while..." << std::endl;
    std::cout << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    std::set<int> all_faces = {1, 2, 3, 4, 5, 6};
    auto boundary_children = h3_toolkit::children_on_boundary_faces(cell_res0, target_res, all_faces);
    
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end - start;
    
    std::cout << "Results:" << std::endl;
    std::cout << "  Number of boundary children: " << boundary_children.size() << std::endl;
    std::cout << "  Time elapsed: " << elapsed.count() << " seconds" << std::endl;
    std::cout << "  Rate: " << (boundary_children.size() / elapsed.count()) << " cells/second" << std::endl;
    
    return 0;
}
