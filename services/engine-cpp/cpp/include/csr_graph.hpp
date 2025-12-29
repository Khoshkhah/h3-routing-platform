/**
 * @file csr_graph.hpp
 * @brief CSR (Compressed Sparse Row) routing graph for memory-efficient routing.
 * 
 * This implementation uses CSR format instead of hash maps for adjacency,
 * providing better cache locality and lower memory overhead.
 * 
 * The API matches ShortcutGraph for drop-in replacement.
 */

#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>
#include <mutex>
#include <boost/geometry.hpp>
#include <boost/geometry/geometries/point.hpp>
#include <boost/geometry/geometries/box.hpp>
#include <boost/geometry/index/rtree.hpp>

namespace bg = boost::geometry;
namespace bgi = boost::geometry::index;

// Geometry types for R-tree
using CSRPoint2D = bg::model::point<double, 2, bg::cs::cartesian>;
using CSRBox2D = bg::model::box<CSRPoint2D>;
using CSRRTreeValue = std::pair<CSRBox2D, uint32_t>;

/**
 * @brief Result of a shortest path query.
 */
struct CSRQueryResult {
    double distance = -1.0;
    std::vector<uint32_t> path;
    bool reachable = false;
    std::string error;
};

/**
 * @brief H3 cell constraint for pruned search.
 */
struct CSRHighCell {
    uint64_t cell = 0;
    int res = -1;
};

/**
 * @brief Edge metadata.
 */
struct CSREdgeMeta {
    uint64_t to_cell = 0;
    uint64_t from_cell = 0;
    int64_t lca_res = -1;
    double length = 0.0;
    float cost = 0.0f;
    std::vector<std::pair<double, double>> geometry;
};

/**
 * @brief Shortcut edge stored in CSR arrays.
 */
struct CSRShortcut {
    uint64_t cell;
    float cost;
    uint32_t from;
    uint32_t to;
    uint32_t via_edge : 30;
    int32_t inside : 2;
    
    // Helper to get resolution from cell on the fly
    int8_t get_res() const {
        return (cell == 0) ? -1 : static_cast<int8_t>((cell >> 52) & 0xF);
    }
};
// Ensure size is exactly 24 bytes
static_assert(sizeof(CSRShortcut) == 24, "CSRShortcut must be 24 bytes");

/**
 * @brief Spatial index type.
 */
enum class CSRSpatialIndexType {
    H3,
    RTREE
};

/**
 * @brief CSR-based routing graph.
 * 
 * Memory layout for CSR forward adjacency:
 *   fwd_offsets_[u] to fwd_offsets_[u+1] is the range of shortcuts from edge u
 *   shortcuts_ stores the actual shortcut data
 * 
 * For backward adjacency:
 *   bwd_offsets_[v] to bwd_offsets_[v+1] is the range of indices into shortcuts_
 *   bwd_indices_ stores indices into shortcuts_ array
 */
class CSRGraph {
public:
    // ========== LOADING ==========
    
    bool load_shortcuts(const std::string& path);
    bool load_edge_metadata(const std::string& path);

#ifdef HAVE_DUCKDB
    bool load_from_duckdb(const std::string& db_path);
#endif

    // ========== SPATIAL INDEX ==========
    
    void build_spatial_index(CSRSpatialIndexType type = CSRSpatialIndexType::RTREE);
    
    std::vector<std::pair<uint32_t, double>> find_nearest_edges(
        double lat, double lng,
        int max_candidates = 5,
        double radius_meters = 500.0
    ) const;

    // ========== QUERIES ==========
    
    CSRQueryResult query_classic(uint32_t source_edge, uint32_t target_edge) const;
    CSRQueryResult query_bidijkstra(uint32_t source_edge, uint32_t target_edge) const;
    CSRQueryResult query_pruned(uint32_t source_edge, uint32_t target_edge) const;
    CSRQueryResult query_unidirectional(uint32_t source_edge, uint32_t target_edge) const;
    CSRQueryResult query_dijkstra(uint32_t source_edge, uint32_t target_edge) const;
    CSRQueryResult query_multi(
        const std::vector<uint32_t>& source_edges,
        const std::vector<double>& source_dists,
        const std::vector<uint32_t>& target_edges,
        const std::vector<double>& target_dists
    ) const;

    // ========== PATH EXPANSION ==========
    
    std::vector<uint32_t> expand_path(const std::vector<uint32_t>& shortcut_path) const;

    // ========== ACCESSORS ==========
    
    double get_edge_cost(uint32_t edge_id) const;
    uint64_t get_edge_cell(uint32_t edge_id) const;
    const CSREdgeMeta* get_edge_meta(uint32_t edge_id) const;
    const std::vector<std::pair<double, double>>* get_edge_geometry(uint32_t edge_id) const;
    CSRHighCell compute_high_cell(uint32_t source_edge, uint32_t target_edge) const;
    
    size_t shortcut_count() const { return shortcuts_.size(); }
    size_t edge_count() const { return edge_meta_.size(); }
    bool has_spatial_index() const { return spatial_index_built_; }
    size_t memory_usage() const;

private:
    // ========== HELPER METHODS ==========
    
    // Check if edge ID is valid for CSR access
    bool is_valid_edge(uint32_t edge_id) const {
        return edge_id <= max_edge_id_ && 
               edge_id + 1 < fwd_offsets_.size() &&
               edge_id + 1 < bwd_offsets_.size();
    }
    
    // Get forward neighbors range (start, end indices into shortcuts_)
    std::pair<uint32_t, uint32_t> get_fwd_range(uint32_t edge_id) const {
        if (!is_valid_edge(edge_id)) return {0, 0};
        return {fwd_offsets_[edge_id], fwd_offsets_[edge_id + 1]};
    }
    
    // Get backward neighbors range (start, end indices into bwd_indices_)
    std::pair<uint32_t, uint32_t> get_bwd_range(uint32_t edge_id) const {
        if (!is_valid_edge(edge_id)) return {0, 0};
        return {bwd_offsets_[edge_id], bwd_offsets_[edge_id + 1]};
    }
    
    // Find shortcut index for path expansion
    int find_shortcut_index(uint32_t u, uint32_t v) const;

    // ========== CSR DATA STRUCTURES ==========
    
    // Shortcuts stored contiguously, sorted by source edge
    std::vector<CSRShortcut> shortcuts_;
    
    // Forward adjacency: fwd_offsets_[u] to fwd_offsets_[u+1] indexes into shortcuts_
    std::vector<uint32_t> fwd_offsets_;
    
    // Backward adjacency: bwd_offsets_[v] to bwd_offsets_[v+1] indexes into bwd_indices_
    std::vector<uint32_t> bwd_offsets_;
    std::vector<uint32_t> bwd_indices_;  // Indices into shortcuts_
    
    // Maximum edge ID (used for bounds checking)
    uint32_t max_edge_id_ = 0;
    
    // Edge metadata (still uses map since it's sparse)
    std::unordered_map<uint32_t, CSREdgeMeta> edge_meta_;
    
    // ========== SPATIAL INDEX ==========
    
    bool spatial_index_built_ = false;
    CSRSpatialIndexType spatial_index_type_ = CSRSpatialIndexType::RTREE;
    std::unordered_map<uint64_t, std::vector<uint32_t>> h3_index_;
    int h3_index_res_ = 9;
    std::unique_ptr<bgi::rtree<CSRRTreeValue, bgi::quadratic<16>>> rtree_;
    
    // Thread safety for concurrent queries (mutable for const methods)
    mutable std::mutex query_mutex_;
};
