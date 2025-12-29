/**
 * @file h3_utils.hpp
 * @brief H3 utility functions for hierarchical routing.
 */

#pragma once

#include <cstdint>
#include <vector>

namespace h3_utils {

/**
 * @brief Get resolution of an H3 cell.
 */
int get_resolution(uint64_t cell);

/**
 * @brief Get parent cell at target resolution.
 */
uint64_t cell_to_parent(uint64_t cell, int target_res);

/**
 * @brief Find lowest common ancestor of two H3 cells.
 */
uint64_t find_lca(uint64_t cell1, uint64_t cell2);

/**
 * @brief Find lowest common ancestor (Iterative Fallback).
 */
uint64_t find_lca_old(uint64_t cell1, uint64_t cell2);

/**
 * @brief Check if node_cell is within high_cell region.
 * @return true if node is within the high_cell ancestor
 */
bool parent_check(uint64_t node_cell, uint64_t high_cell, int high_res);

/**
 * @brief Convert lat/lng to H3 cell at given resolution.
 */
uint64_t latlng_to_cell(double lat, double lng, int res);

/**
 * @brief Get ring of cells at distance k from center.
 * @param center Center H3 cell
 * @param k Ring distance (0 = just center, 1 = immediate neighbors, etc.)
 * @return Vector of cell IDs in ring
 */
std::vector<uint64_t> grid_ring(uint64_t center, int k);

/**
 * @brief Get boundary polygon of an H3 cell.
 * @param cell H3 cell index
 * @return Vector of (lat, lon) pairs forming the polygon
 */
std::vector<std::pair<double, double>> cell_boundary(uint64_t cell);

}  // namespace h3_utils

