/**
 * @file h3_utils.cpp
 * @brief H3 utility functions implementation.
 */

#include "h3_utils.hpp"
#include <h3/h3api.h>
#include <unordered_set>
#include <cmath>

namespace h3_utils {

int get_resolution(uint64_t cell) {
    if (cell == 0) return -1;
    return getResolution(cell);
}

uint64_t cell_to_parent(uint64_t cell, int target_res) {
    if (cell == 0 || target_res < 0) return 0;
    
    int current_res = getResolution(cell);
    if (target_res >= current_res) return cell;
    
    H3Index parent = 0;
    if (cellToParent(cell, target_res, &parent) != E_SUCCESS) {
        return 0;
    }
    return parent;
}

uint64_t find_lca(uint64_t cell1, uint64_t cell2) {
    if (cell1 == 0 || cell2 == 0) return 0;
    
    int res1 = getResolution(cell1);
    int res2 = getResolution(cell2);
    int min_res = (res1 < res2) ? res1 : res2;
    
    uint64_t c1 = (res1 > min_res) ? cell_to_parent(cell1, min_res) : cell1;
    uint64_t c2 = (res2 > min_res) ? cell_to_parent(cell2, min_res) : cell2;
    
    while (c1 != c2 && min_res > 0) {
        min_res--;
        c1 = cell_to_parent(c1, min_res);
        c2 = cell_to_parent(c2, min_res);
    }
    
    return (c1 == c2) ? c1 : 0;
}

bool parent_check(uint64_t node_cell, uint64_t high_cell, int high_res) {
    if (high_cell == 0 || high_res < 0) return true;
    if (node_cell == 0) return false;
    
    int node_res = getResolution(node_cell);
    if (high_res > node_res) return false;
    
    uint64_t parent = cell_to_parent(node_cell, high_res);
    return parent == high_cell;
}

uint64_t latlng_to_cell(double lat, double lng, int res) {
    if (res < 0 || res > 15) return 0;
    
    LatLng ll;
    ll.lat = lat * M_PI / 180.0;  // Convert to radians
    ll.lng = lng * M_PI / 180.0;
    
    H3Index cell = 0;
    if (latLngToCell(&ll, res, &cell) != E_SUCCESS) {
        return 0;
    }
    return cell;
}

std::vector<uint64_t> grid_ring(uint64_t center, int k) {
    std::vector<uint64_t> result;
    if (center == 0 || k < 0) return result;
    
    if (k == 0) {
        result.push_back(center);
        return result;
    }
    
    // Get disk size
    int64_t disk_size = 0;
    if (maxGridDiskSize(k, &disk_size) != E_SUCCESS) {
        return result;
    }
    
    // Get cells in disk
    std::vector<H3Index> disk(disk_size, 0);
    if (gridDisk(center, k, disk.data()) != E_SUCCESS) {
        return result;
    }
    
    // For k>0, we want just the ring, not the full disk
    // Get cells in inner disk (k-1)
    std::unordered_set<uint64_t> inner;
    if (k > 0) {
        int64_t inner_size = 0;
        maxGridDiskSize(k - 1, &inner_size);
        std::vector<H3Index> inner_disk(inner_size, 0);
        if (gridDisk(center, k - 1, inner_disk.data()) == E_SUCCESS) {
            for (auto c : inner_disk) {
                if (c != 0) inner.insert(c);
            }
        }
    }
    
    // Return only cells in disk but not in inner disk
    for (auto c : disk) {
        if (c != 0 && inner.find(c) == inner.end()) {
            result.push_back(c);
        }
    }
    
    return result;
}

std::vector<std::pair<double, double>> cell_boundary(uint64_t cell) {
    std::vector<std::pair<double, double>> boundary;
    if (cell == 0) return boundary;
    
    CellBoundary cb;
    if (cellToBoundary(cell, &cb) != E_SUCCESS) {
        return boundary;
    }
    
    // Convert radians to degrees and store as (lat, lon)
    for (int i = 0; i < cb.numVerts; ++i) {
        double lat = cb.verts[i].lat * 180.0 / M_PI;
        double lon = cb.verts[i].lng * 180.0 / M_PI;
        boundary.push_back({lat, lon});
    }
    
    // Close the polygon by repeating first point
    if (!boundary.empty()) {
        boundary.push_back(boundary[0]);
    }
    
    return boundary;
}

}  // namespace h3_utils
