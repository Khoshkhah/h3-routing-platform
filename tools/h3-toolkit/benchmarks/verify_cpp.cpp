#include "h3_toolkit.hpp"
#include <h3api.h>
#include <iostream>
#include <iomanip>
#include <set>

int main() {
    // Get first base cell (same as Python)
    H3Index base_cells[122];
    getRes0Cells(base_cells);
    H3Index cell_res0 = base_cells[0];
    
    std::cout << "Base cell: " << std::hex << cell_res0 << std::dec << std::endl;
    
    int target_res = 8;  // Same as Python verify script
    
    std::cout << "Getting boundary children at res " << target_res << "..." << std::endl;
    
    std::set<int> all_faces = {1, 2, 3, 4, 5, 6};
    auto children = h3_toolkit::children_on_boundary_faces(cell_res0, target_res, all_faces);
    
    std::cout << "Found " << children.size() << " boundary children" << std::endl;
    std::cout << std::endl;
    
    std::cout << "First 10 boundary children (hex):" << std::endl;
    int count = 0;
    for (auto child : children) {
        if (count >= 10) break;
        std::cout << "  " << (count + 1) << ". " << std::hex << child << std::dec << "fffff" << std::endl;
        count++;
    }
    
    return 0;
}
