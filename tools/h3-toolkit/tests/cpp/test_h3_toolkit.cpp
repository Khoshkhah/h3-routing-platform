#include "h3_toolkit.hpp"
#include <h3api.h>
#include <iostream>
#include <cassert>
#include <set>
#include <vector>

void test_trace_to_parent() {
    // Helper to get H3 from lat/lng
    H3Index h = 0;
    // latLngToCell(const LatLng *g, int res, H3Index *out)
    // 37.775938728915946, -122.41795063018799 @ res 6
    LatLng g;
    g.lat = degsToRads(37.775938728915946);
    g.lng = degsToRads(-122.41795063018799);
    latLngToCell(&g, 6, &h);
    
    std::set<int> input = {1, 2, 3, 4, 5, 6};
    std::set<int> result = h3_toolkit::trace_cell_to_parent_faces(h, input);
    
    std::cout << "Trace to parent result size: " << result.size() << std::endl;
    // Just verify it runs and returns a subset
    for (int f : result) {
        assert(f >= 1 && f <= 6);
    }
}

void test_trace_to_ancestor() {
    LatLng g;
    g.lat = degsToRads(37.775938728915946);
    g.lng = degsToRads(-122.41795063018799);
    H3Index h;
    latLngToCell(&g, 6, &h);

    std::set<int> input = {1, 2};
    std::set<int> result = h3_toolkit::trace_cell_to_ancestor_faces(h, input, 4);
    
    std::cout << "Trace to ancestor (res 4) result size: " << result.size() << std::endl;
}

int main() {
    try {
        test_trace_to_parent();
        test_trace_to_ancestor();
        std::cout << "All C++ tests passed!" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Test failed: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
