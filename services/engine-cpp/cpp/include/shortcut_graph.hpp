/**
 * @file shortcut_graph.hpp
 * @brief H3-based hierarchical routing graph and query engine.
 */

#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>
#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point.hpp>
#include <boost/geometry/geometries/box.hpp>
#include <boost/geometry/geometries/linestring.hpp>
#include <boost/geometry/index/rtree.hpp>

namespace bg = boost::geometry;
namespace bgi = boost::geometry::index;

// Geometry types for R-tree
using Point2D = bg::model::point<double, 2, bg::cs::cartesian>;
using Box2D = bg::model::box<Point2D>;
using RTreeValue = std::pair<Box2D, uint32_t>;  // bbox + edge_id

/**
 * @brief Result of a shortest path query.
 */
struct QueryResult {
    double distance;              ///< Total path cost
    std::vector<uint32_t> path;   ///< Sequence of edge IDs
    bool reachable;               ///< True if a path was found
    std::string error;            ///< Error description if not reachable
};

/**
 * @brief H3 cell constraint for pruned search.
 */
struct HighCell {
    uint64_t cell = 0;  ///< H3 cell ID
    int res = -1;       ///< Cell resolution
};

/**
 * @brief Edge metadata for H3-based routing.
 */
struct EdgeMeta {
    uint64_t to_cell = 0;
    uint64_t from_cell = 0;
    int lca_res = -1;
    double length = 0.0;
    double cost = 0.0;
    // Geometry as sequence of (lon, lat) points
    std::vector<std::pair<double, double>> geometry;
};

/**
 * @brief Shortcut edge in the graph.
 */
struct Shortcut {
    uint32_t from;       ///< Source edge ID
    uint32_t to;         ///< Target edge ID
    double cost;         ///< Traversal cost
    uint32_t via_edge;   ///< Intermediate edge (0 if direct)
    uint64_t cell;       ///< H3 cell bounding this shortcut
    int8_t inside;       ///< Direction: +1 up, 0 lateral, -1 down, -2 edge
    int8_t cell_res;     ///< Resolution of cell (-1 if cell=0)
};

/**
 * @brief Spatial index type.
 */
enum class SpatialIndexType {
    H3,      ///< H3 cell-based index (O(1) lookup)
    RTREE    ///< Boost R-tree index (handles long edges better)
};

/**
 * @brief H3-based hierarchical routing graph.
 */
class ShortcutGraph {
public:
    /**
     * @brief Load shortcuts from Parquet directory.
     * @param path Path to Parquet files
     * @return true if successful
     */
    bool load_shortcuts(const std::string& path);

    /**
     * @brief Load edge metadata from CSV.
     * @param path Path to CSV file
     * @return true if successful
     */
    bool load_edge_metadata(const std::string& path);

#ifdef HAVE_DUCKDB
    /**
     * @brief Load all data from consolidated DuckDB database.
     * Loads edges (with geometry), shortcuts, and dataset_info in one call.
     * @param db_path Path to DuckDB database file
     * @return true if successful
     */
    bool load_from_duckdb(const std::string& db_path);

    /**
     * @brief Get dataset info value by key.
     * @param key Key name (e.g., "name", "boundary_geojson")
     * @return Value string, or empty if not found
     */
    std::string get_dataset_info(const std::string& key) const;
#endif

    /**
     * @brief Build spatial index for nearest edge search.
     * @param type Index type (H3 or RTREE)
     */
    void build_spatial_index(SpatialIndexType type = SpatialIndexType::H3);

    /**
     * @brief Find nearest edges to a coordinate.
     * @param lat Latitude
     * @param lng Longitude
     * @param max_candidates Maximum results
     * @param radius_meters Search radius (for H3, determines ring expansion)
     * @return Vector of (edge_id, distance_meters)
     */
    std::vector<std::pair<uint32_t, double>> find_nearest_edges(
        double lat, double lng,
        int max_candidates = 5,
        double radius_meters = 500.0
    ) const;

    /**
     * @brief Expand shortcut path to real edge sequence.
     * @param shortcut_path Path from query (may contain shortcuts)
     * @return Expanded path with only real edges
     */
    std::vector<uint32_t> expand_path(const std::vector<uint32_t>& shortcut_path) const;

    /**
     * @brief Classic bidirectional Dijkstra with inside filtering.
     */
    QueryResult query_classic(uint32_t source_edge, uint32_t target_edge) const;

    /**
     * @brief Pruned bidirectional Dijkstra with H3 parent_check.
     */
    QueryResult query_pruned(uint32_t source_edge, uint32_t target_edge) const;

    /**
     * @brief Unidirectional pruned Dijkstra with complex state machine.
     * Matches the Python prototype logic for 'inside' flag transitions.
     */
    QueryResult query_unidirectional(uint32_t source_edge, uint32_t target_edge) const;

    /**
     * @brief Multi-source/target bidirectional search.
     */
    QueryResult query_multi(
        const std::vector<uint32_t>& source_edges,
        const std::vector<double>& source_dists,
        const std::vector<uint32_t>& target_edges,
        const std::vector<double>& target_dists
    ) const;

    /**
     * @brief Get edge cost.
     */
    double get_edge_cost(uint32_t edge_id) const;

    /**
     * @brief Get edge H3 cell.
     */
    uint64_t get_edge_cell(uint32_t edge_id) const;

    /**
     * @brief Get edge metadata (for cell visualization).
     */
    const EdgeMeta* get_edge_meta(uint32_t edge_id) const;

    /**
     * @brief Get edge geometry.
     */
    const std::vector<std::pair<double, double>>* get_edge_geometry(uint32_t edge_id) const;

    /**
     * @brief Compute high cell (LCA) for source and target edges.
     */
    HighCell compute_high_cell(uint32_t source_edge, uint32_t target_edge) const;

    /**
     * @brief Get number of shortcuts loaded.
     */
    size_t shortcut_count() const { return shortcuts_.size(); }

    /**
     * @brief Get number of edges with metadata.
     */
    size_t edge_count() const { return edge_meta_.size(); }

    /**
     * @brief Check if spatial index is built.
     */
    bool has_spatial_index() const { return spatial_index_built_; }

private:

    // Core data
    std::vector<Shortcut> shortcuts_;
    std::unordered_map<uint32_t, std::vector<size_t>> fwd_adj_;
    std::unordered_map<uint32_t, std::vector<size_t>> bwd_adj_;
    std::unordered_map<uint32_t, EdgeMeta> edge_meta_;

    // Spatial indexing
    bool spatial_index_built_ = false;
    SpatialIndexType spatial_index_type_ = SpatialIndexType::H3;
    
    // H3 index: h3_cell -> [edge_ids]
    std::unordered_map<uint64_t, std::vector<uint32_t>> h3_index_;
    int h3_index_res_ = 10;  ///< H3 resolution for indexing
    
    // R-tree index
    std::unique_ptr<bgi::rtree<RTreeValue, bgi::quadratic<16>>> rtree_;
    
    // Shortcut lookup: key = (from << 32 | to) -> shortcut index
    std::unordered_map<uint64_t, size_t> shortcut_lookup_;
    
    // Dataset info from DuckDB (key -> value)
    std::unordered_map<std::string, std::string> dataset_info_;
};

