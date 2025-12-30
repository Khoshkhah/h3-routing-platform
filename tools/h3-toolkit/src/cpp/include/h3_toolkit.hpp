#pragma once

#include <h3api.h>
#include <set>
#include <vector>

namespace h3_toolkit {

/**
 * Traces which of the given input_faces the target H3 cell lies on for an ancestor
 * cell at a coarser resolution.
 * 
 * @param h Target H3 cell index.
 * @param input_faces Subset of face numbers {1-6}.
 * @param res_parent Resolution of the ancestor cell.
 * @return Set of face numbers (1-6) at the ancestor's boundary.
 */
std::set<int> trace_cell_to_ancestor_faces(H3Index h, const std::set<int>& input_faces, int res_parent);

/**
 * Convenience overload that defaults to parent resolution (res - 1).
 */
std::set<int> trace_cell_to_parent_faces(H3Index h, const std::set<int>& input_faces);

/**
 * Returns all children of 'parent' at 'target_res' that lie on the parent's
 * specified boundary faces.
 * 
 * @param parent Parent H3 cell index.
 * @param target_res Resolution to descend to (must be > parent resolution).
 * @param input_faces Set of face numbers {1-6} to filter by.
 * @return Vector of child H3 cells on those boundary faces.
 */
std::vector<H3Index> children_on_boundary_faces(H3Index parent, int target_res, const std::set<int>& input_faces = {1,2,3,4,5,6});

/**
 * Finds the coarsest ancestor (lowest resolution) such that h still lies on at least
 * one of the specified input_faces.
 */
H3Index cell_to_coarsest_ancestor_on_faces(H3Index h, const std::set<int>& input_faces = {1,2,3,4,5,6});

/**
 * Returns the cell boundary as a vector of (lon, lat) pairs.
 */
std::vector<std::pair<double, double>> cell_boundary(H3Index cell);

/**
 * Returns the merged boundary polygon of all boundary children at target_res.
 * @param parent Parent H3 cell
 * @param target_res Resolution for boundary children
 * @return Vector of (lon, lat) pairs representing the merged boundary polygon
 */
std::vector<std::pair<double, double>> cell_boundary_from_children(H3Index parent, int target_res);

/**
 * Returns a buffered polygon of a single cell (simple buffer, no children).
 * @param cell H3 cell index
 * @param buffer_meters Buffer distance in meters. If < 0, auto-calculates.
 * @return Vector of (lon, lat) pairs representing the buffered polygon
 */
std::vector<std::pair<double, double>> get_buffered_h3_polygon(H3Index cell, double buffer_meters = -1.0);

/**
 * Returns a buffered polygon that is guaranteed to contain all res 15 children.
 * Uses Boost.Geometry for polygon buffering.
 * 
 * @param cell H3 cell index.
 * @param intermediate_res Resolution for initial boundary computation (default: 10).
 * @param buffer_meters Buffer distance in meters. If < 0, auto-calculates as 100% of intermediate edge length.
 * @param use_convex_hull If true, use fast convex hull. If false, union cells for accurate boundary.
 * @return Vector of (longitude, latitude) pairs representing the buffered polygon vertices.
 */
std::vector<std::pair<double, double>> get_buffered_boundary_polygon(
    H3Index cell,
    int intermediate_res = 10,
    double buffer_meters = -1.0,
    bool use_convex_hull = true
);

} // namespace h3_toolkit
