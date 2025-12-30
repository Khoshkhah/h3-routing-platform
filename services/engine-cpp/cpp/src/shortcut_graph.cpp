/**
 * @file shortcut_graph.cpp
 * @brief ShortcutGraph implementation - loading and query algorithms.
 */

#include "shortcut_graph.hpp"
#include "h3_utils.hpp"

#include <arrow/api.h>
#include <arrow/io/api.h>
#include <parquet/arrow/reader.h>

#ifdef HAVE_DUCKDB
#include <duckdb.hpp>
#endif

#include <fstream>
#include <iostream>
#include <queue>
#include <sstream>
#include <limits>
#include <algorithm>
#include <filesystem>
#include <unordered_set>
#include <functional>
#include <cmath>

namespace fs = std::filesystem;

// Priority queue entry (for classic)
struct PQEntry {
    double dist;
    uint32_t edge;
    bool operator>(const PQEntry& o) const { return dist > o.dist; }
};

// Priority queue entry with resolution (for pruned) - optimized: 1 byte vs 8 bytes
struct PQEntryWithRes {
    double dist;
    uint32_t edge;
    int8_t res;  // Resolution instead of full cell - much smaller!
    bool operator>(const PQEntryWithRes& o) const { return dist > o.dist; }
};

using MinHeap = std::priority_queue<PQEntry, std::vector<PQEntry>, std::greater<PQEntry>>;
using MinHeapWithRes = std::priority_queue<PQEntryWithRes, std::vector<PQEntryWithRes>, std::greater<PQEntryWithRes>>;

// Helper to load a single parquet file
static bool load_parquet_file(const std::string& filepath, 
                              std::vector<Shortcut>& shortcuts,
                              std::unordered_map<uint32_t, std::vector<size_t>>& fwd_adj,
                              std::unordered_map<uint32_t, std::vector<size_t>>& bwd_adj) {
    arrow::MemoryPool* pool = arrow::default_memory_pool();
    
    std::shared_ptr<arrow::io::ReadableFile> infile;
    PARQUET_ASSIGN_OR_THROW(infile, arrow::io::ReadableFile::Open(filepath, pool));
    
    std::unique_ptr<parquet::arrow::FileReader> reader;
    PARQUET_THROW_NOT_OK(parquet::arrow::OpenFile(infile, pool, &reader));
    
    std::shared_ptr<arrow::Table> table;
    PARQUET_THROW_NOT_OK(reader->ReadTable(&table));
    
    // Handle chunked columns
    auto from_chunked = table->GetColumnByName("from_edge");
    auto to_chunked = table->GetColumnByName("to_edge");
    auto cost_chunked = table->GetColumnByName("cost");
    auto via_chunked = table->GetColumnByName("via_edge");
    auto cell_chunked = table->GetColumnByName("cell");
    auto inside_chunked = table->GetColumnByName("inside");
    
    for (int chunk = 0; chunk < from_chunked->num_chunks(); ++chunk) {
        auto from_col = std::static_pointer_cast<arrow::Int32Array>(from_chunked->chunk(chunk));
        auto to_col = std::static_pointer_cast<arrow::Int32Array>(to_chunked->chunk(chunk));
        auto cost_col = std::static_pointer_cast<arrow::DoubleArray>(cost_chunked->chunk(chunk));
        auto via_col = std::static_pointer_cast<arrow::Int32Array>(via_chunked->chunk(chunk));
        auto cell_col = std::static_pointer_cast<arrow::Int64Array>(cell_chunked->chunk(chunk));
        auto inside_col = std::static_pointer_cast<arrow::Int8Array>(inside_chunked->chunk(chunk));
        
        for (int64_t i = 0; i < from_col->length(); ++i) {
            Shortcut sc;
            sc.from = static_cast<uint32_t>(from_col->Value(i));
            sc.to = static_cast<uint32_t>(to_col->Value(i));
            sc.cost = cost_col->Value(i);
            sc.via_edge = static_cast<uint32_t>(via_col->Value(i));
            sc.cell = static_cast<uint64_t>(cell_col->Value(i));
            sc.inside = inside_col->Value(i);
            // Precompute resolution (-1 if cell=0)
            sc.cell_res = (sc.cell == 0) ? -1 : static_cast<int8_t>(h3_utils::get_resolution(sc.cell));
            
            size_t idx = shortcuts.size();
            shortcuts.push_back(sc);
            fwd_adj[sc.from].push_back(idx);
            bwd_adj[sc.to].push_back(idx);
        }
    }
    
    return true;
}

bool ShortcutGraph::load_shortcuts(const std::string& path) {
    shortcuts_.clear();
    fwd_adj_.clear();
    bwd_adj_.clear();
    shortcut_lookup_.clear();
    
    if (fs::is_directory(path)) {
        // Load all .parquet files in directory
        for (const auto& entry : fs::directory_iterator(path)) {
            if (entry.path().extension() == ".parquet") {
                load_parquet_file(entry.path().string(), shortcuts_, fwd_adj_, bwd_adj_);
            }
        }
    } else {
        // Load single file
        load_parquet_file(path, shortcuts_, fwd_adj_, bwd_adj_);
    }
    
    // Build shortcut_lookup_ for path expansion: key = (from << 32 | to) -> shortcut index
    for (size_t idx = 0; idx < shortcuts_.size(); ++idx) {
        const auto& sc = shortcuts_[idx];
        const uint64_t key = (static_cast<uint64_t>(sc.from) << 32) | sc.to;
        // Keep first shortcut for each (from, to) pair
        if (shortcut_lookup_.find(key) == shortcut_lookup_.end()) {
            shortcut_lookup_[key] = idx;
        }
    }
    
    return !shortcuts_.empty();
}

bool ShortcutGraph::load_edge_metadata(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) return false;
    
    std::string header_line;
    std::getline(file, header_line);  // Read header
    
    // Parse header to find column indices
    std::vector<std::string> cols;
    std::stringstream ss(header_line);
    std::string cell;
    while (std::getline(ss, cell, ',')) {
        // Trim whitespace, CR, quotes
        cell.erase(0, cell.find_first_not_of(" \t\r\n\"'")); // Left trim
        cell.erase(cell.find_last_not_of(" \t\r\n\"'") + 1); // Right trim
        cols.push_back(cell);
    }
    
    std::cout << "DEBUG: CSV Headers: ";
    for (const auto& c : cols) std::cout << "'" << c << "' ";
    std::cout << std::endl;
    
    int idx_length = -1;
    int idx_geometry = -1;
    int idx_cost = -1;
    int idx_to_cell = -1;
    int idx_from_cell = -1;
    int idx_lca_res = -1;
    int idx_id = -1;
    
    for (int i = 0; i < (int)cols.size(); ++i) {
        if (cols[i] == "length") idx_length = i;
        else if (cols[i] == "geometry") idx_geometry = i;
        else if (cols[i] == "cost") idx_cost = i;
        else if (cols[i] == "incoming_cell" || cols[i] == "from_cell") idx_from_cell = i; // Note: csv has incoming/outgoing
        else if (cols[i] == "outgoing_cell" || cols[i] == "to_cell") idx_to_cell = i; // Mapping varies?
        else if (cols[i] == "lca_res") idx_lca_res = i;
        else if (cols[i] == "id" || cols[i] == "edge_index") idx_id = i;
    }
    
    // Fallback if ID is missing (assume 0 if not found, but better to fail)
    if (idx_id == -1) idx_id = 0; // Legacy assumption? Or fatal error.
    
    // If incoming/outgoing names differ:
    // CSV Header: length,maxspeed,geometry,highway,cost,incoming_cell,outgoing_cell,lca_res,id
    // Code mappings:
    if (idx_from_cell == -1) {
        for (int i=0; i<(int)cols.size(); ++i) if (cols[i] == "incoming_cell") idx_from_cell = i; 
    }
    if (idx_to_cell == -1) {
        for (int i=0; i<(int)cols.size(); ++i) if (cols[i] == "outgoing_cell") idx_to_cell = i;
    }
    int min_cols = 9;
    
    edge_meta_.clear();
    std::string line;
    while (std::getline(file, line)) {
        // Parse CSV with quote handling
        std::vector<std::string> row;
        std::string field;
        bool in_quotes = false;
        
        for (char c : line) {
            if (c == '"') {
                in_quotes = !in_quotes;
            } else if (c == ',' && !in_quotes) {
                row.push_back(field);
                field.clear();
            } else {
                field += c;
            }
        }
        row.push_back(field);  // Last field
        
        if (static_cast<int>(row.size()) >= min_cols) {
            try {
                uint32_t id = std::stoul(row[idx_id]);
                EdgeMeta meta;
                meta.to_cell = std::stoull(row[idx_to_cell]);
                meta.from_cell = std::stoull(row[idx_from_cell]);
                meta.lca_res = std::stoi(row[idx_lca_res]);
                meta.length = std::stod(row[idx_length]);
                meta.cost = std::stod(row[idx_cost]);
                
                // Parse geometry (WKT LINESTRING)
                if (static_cast<int>(row.size()) > idx_geometry) {
                    std::string& geom = row[idx_geometry];
                    // Parse "LINESTRING (lon1 lat1, lon2 lat2, ...)"
                    size_t start = geom.find('(');
                    size_t end = geom.rfind(')');
                    if (start != std::string::npos && end != std::string::npos && end > start) {
                        std::string coords = geom.substr(start + 1, end - start - 1);
                        std::stringstream ss(coords);
                        std::string point;
                        while (std::getline(ss, point, ',')) {
                            // Trim whitespace
                            size_t first = point.find_first_not_of(" \t");
                            if (first == std::string::npos) continue;
                            point = point.substr(first);
                            
                            // Parse "lon lat"
                            std::istringstream ps(point);
                            double lon, lat;
                            if (ps >> lon >> lat) {
                                meta.geometry.push_back({lon, lat});
                            }
                        }
                    }
                }
                
                edge_meta_[id] = std::move(meta);
            } catch (...) {
                // Skip malformed rows
            }
        }
    }
    
    std::cout << "Loaded " << edge_meta_.size() << " edges with geometry\n";
    return !edge_meta_.empty();
}

double ShortcutGraph::get_edge_cost(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    return (it != edge_meta_.end()) ? it->second.cost : 0.0;
}

uint64_t ShortcutGraph::get_edge_cell(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    return (it != edge_meta_.end()) ? it->second.to_cell : 0;
}

const EdgeMeta* ShortcutGraph::get_edge_meta(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    return (it != edge_meta_.end()) ? &it->second : nullptr;
}

HighCell ShortcutGraph::compute_high_cell(uint32_t source_edge, uint32_t target_edge) const {
    auto src_it = edge_meta_.find(source_edge);
    auto dst_it = edge_meta_.find(target_edge);
    
    if (src_it == edge_meta_.end() || dst_it == edge_meta_.end()) {
        return {0, -1};
    }
    
    uint64_t src_cell = src_it->second.to_cell;
    uint64_t dst_cell = dst_it->second.to_cell;
    int src_res = src_it->second.lca_res;
    int dst_res = dst_it->second.lca_res;
    
    // Match Python: if res < 0 or cell == 0, treat as 0
    if (src_cell == 0 || src_res < 0) {
        src_cell = 0;
    } else {
        src_cell = h3_utils::cell_to_parent(src_cell, src_res);
    }
    
    if (dst_cell == 0 || dst_res < 0) {
        dst_cell = 0;
    } else {
        dst_cell = h3_utils::cell_to_parent(dst_cell, dst_res);
    }
    
    // If either cell is 0, return 0
    if (src_cell == 0 || dst_cell == 0) {
        return {0, -1};
    }
    
    uint64_t lca = h3_utils::find_lca(src_cell, dst_cell);
    int res = (lca != 0) ? h3_utils::get_resolution(lca) : -1;
    return {lca, res};
}

QueryResult ShortcutGraph::query_classic(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }

    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge " + std::to_string(source_edge) + " not found in graph"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge " + std::to_string(target_edge) + " not found in graph"};
    }
    
    std::unordered_map<uint32_t, double> dist_fwd, dist_bwd;
    std::unordered_map<uint32_t, uint32_t> parent_fwd, parent_bwd;
    MinHeap pq_fwd, pq_bwd;
    
    dist_fwd[source_edge] = 0.0;
    parent_fwd[source_edge] = source_edge;
    pq_fwd.push({0.0, source_edge});
    
    double target_cost = get_edge_cost(target_edge);
    dist_bwd[target_edge] = target_cost;
    parent_bwd[target_edge] = target_edge;
    pq_bwd.push({target_cost, target_edge});
    
    double best = INF;
    uint32_t meeting = 0;
    bool found = false;
    
    while (!pq_fwd.empty() || !pq_bwd.empty()) {
        // Forward step
        if (!pq_fwd.empty()) {
            auto [d, u] = pq_fwd.top(); pq_fwd.pop();
            
            auto it = dist_fwd.find(u);
            if (it != dist_fwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto adj_it = fwd_adj_.find(u);
            if (adj_it != fwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    if (sc.inside != 1) continue;
                    
                    double nd = d + sc.cost;
                    auto v_it = dist_fwd.find(sc.to);
                    if (v_it == dist_fwd.end() || nd < v_it->second) {
                        dist_fwd[sc.to] = nd;
                        parent_fwd[sc.to] = u;
                        pq_fwd.push({nd, sc.to});
                        
                        auto bwd_it = dist_bwd.find(sc.to);
                        if (bwd_it != dist_bwd.end()) {
                            double total = nd + bwd_it->second;
                            if (total < best) {
                                best = total;
                                meeting = sc.to;
                                found = true;
                            }
                        }
                    }
                }
            }
        }
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto adj_it = bwd_adj_.find(u);
            if (adj_it != bwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    if (sc.inside != -1 && sc.inside != 0) continue;
                    
                    double nd = d + sc.cost;
                    auto prev_it = dist_bwd.find(sc.from);
                    if (prev_it == dist_bwd.end() || nd < prev_it->second) {
                        dist_bwd[sc.from] = nd;
                        parent_bwd[sc.from] = u;
                        pq_bwd.push({nd, sc.from});
                        
                        auto fwd_it = dist_fwd.find(sc.from);
                        if (fwd_it != dist_fwd.end()) {
                            double total = fwd_it->second + nd;
                            if (total < best) {
                                best = total;
                                meeting = sc.from;
                                found = true;
                            }
                        }
                    }
                }
            }
        }
        
        // Early termination
        if (!pq_fwd.empty() && !pq_bwd.empty()) {
            if (pq_fwd.top().dist >= best && pq_bwd.top().dist >= best) break;
        } else if (pq_fwd.empty() && pq_bwd.empty()) {
            break;
        }
    }
    
    if (!found) return {-1, {}, false, "No path found between source and target"};
    
    // Reconstruct path - use iterators to avoid inserting default values
    std::vector<uint32_t> path;
    uint32_t curr = meeting;
    
    // Forward path: meeting -> source
    while (true) {
        path.push_back(curr);
        auto it = parent_fwd.find(curr);
        if (it == parent_fwd.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    // Backward path: meeting -> target
    curr = meeting;
    while (true) {
        auto it = parent_bwd.find(curr);
        if (it == parent_bwd.end() || it->second == curr) break;
        curr = it->second;
        path.push_back(curr);
    }
    
    return {best, path, true, ""};
}

QueryResult ShortcutGraph::query_classic_alt(
    uint32_t source_edge, 
    uint32_t target_edge,
    const std::vector<uint32_t>& penalized_nodes,
    double penalty_factor
) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }

    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge " + std::to_string(source_edge) + " not found in graph"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge " + std::to_string(target_edge) + " not found in graph"};
    }

    // Build set for O(1) penalty check
    std::unordered_set<uint32_t> penalty_set(penalized_nodes.begin(), penalized_nodes.end());
    // Never penalize endpoints
    penalty_set.erase(source_edge);
    penalty_set.erase(target_edge);
    
    std::unordered_map<uint32_t, double> dist_fwd, dist_bwd;
    std::unordered_map<uint32_t, uint32_t> parent_fwd, parent_bwd;
    MinHeap pq_fwd, pq_bwd;
    
    dist_fwd[source_edge] = 0.0;
    parent_fwd[source_edge] = source_edge;
    pq_fwd.push({0.0, source_edge});
    
    double target_cost = get_edge_cost(target_edge);
    dist_bwd[target_edge] = target_cost;
    parent_bwd[target_edge] = target_edge;
    pq_bwd.push({target_cost, target_edge});
    
    double best = INF;
    uint32_t meeting = 0;
    bool found = false;
    
    while (!pq_fwd.empty() || !pq_bwd.empty()) {
        // Forward step
        if (!pq_fwd.empty()) {
            auto [d, u] = pq_fwd.top(); pq_fwd.pop();
            
            auto it = dist_fwd.find(u);
            if (it != dist_fwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto adj_it = fwd_adj_.find(u);
            if (adj_it != fwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    if (sc.inside != 1) continue;
                    
                    double cost = sc.cost;
                    if (penalty_set.count(sc.to)) {
                        cost *= penalty_factor;
                    }
                    
                    double nd = d + cost;
                    auto v_it = dist_fwd.find(sc.to);
                    if (v_it == dist_fwd.end() || nd < v_it->second) {
                        dist_fwd[sc.to] = nd;
                        parent_fwd[sc.to] = u;
                        pq_fwd.push({nd, sc.to});
                        
                        auto bwd_it = dist_bwd.find(sc.to);
                        if (bwd_it != dist_bwd.end()) {
                            double total = nd + bwd_it->second;
                            if (total < best) {
                                best = total;
                                meeting = sc.to;
                                found = true;
                            }
                        }
                    }
                }
            }
        }
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto adj_it = bwd_adj_.find(u);
            if (adj_it != bwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    if (sc.inside != -1 && sc.inside != 0) continue;
                    
                    double cost = sc.cost;
                    if (penalty_set.count(sc.from)) {
                        cost *= penalty_factor;
                    }
                    
                    double nd = d + cost;
                    auto prev_it = dist_bwd.find(sc.from);
                    if (prev_it == dist_bwd.end() || nd < prev_it->second) {
                        dist_bwd[sc.from] = nd;
                        parent_bwd[sc.from] = u;
                        pq_bwd.push({nd, sc.from});
                        
                        auto fwd_it = dist_fwd.find(sc.from);
                        if (fwd_it != dist_fwd.end()) {
                            double total = fwd_it->second + nd;
                            if (total < best) {
                                best = total;
                                meeting = sc.from;
                                found = true;
                            }
                        }
                    }
                }
            }
        }
        
        // Early termination
        if (!pq_fwd.empty() && !pq_bwd.empty()) {
            if (pq_fwd.top().dist >= best && pq_bwd.top().dist >= best) break;
        } else if (pq_fwd.empty() && pq_bwd.empty()) {
            break;
        }
    }
    
    if (!found) return {-1, {}, false, "No path found between source and target"};
    
    // Reconstruct path
    std::vector<uint32_t> path;
    uint32_t curr = meeting;
    
    while (true) {
        path.push_back(curr);
        auto it = parent_fwd.find(curr);
        if (it == parent_fwd.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    curr = meeting;
    while (true) {
        auto it = parent_bwd.find(curr);
        if (it == parent_bwd.end() || it->second == curr) break;
        curr = it->second;
        path.push_back(curr);
    }
    
    // Calculate true cost (without penalties)
    double true_total = get_edge_cost(path[0]);
    for (size_t i = 1; i < path.size(); ++i) {
        // Find cost of segment path[i-1] -> path[i]
        bool seg_found = false;
        auto adj_it = fwd_adj_.find(path[i-1]);
        if (adj_it != fwd_adj_.end()) {
            for (size_t idx : adj_it->second) {
                if (shortcuts_[idx].to == path[i]) {
                    true_total += shortcuts_[idx].cost;
                    seg_found = true;
                    break;
                }
            }
        }
        if (!seg_found) return {-1, {}, false, "Path reconstruction error"};
    }
    
    return {true_total, path, true, ""};
}

QueryResult ShortcutGraph::query_bidijkstra(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }

    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge " + std::to_string(source_edge) + " not found in graph"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge " + std::to_string(target_edge) + " not found in graph"};
    }
    
    std::unordered_map<uint32_t, double> dist_fwd, dist_bwd;
    std::unordered_map<uint32_t, uint32_t> parent_fwd, parent_bwd;
    MinHeap pq_fwd, pq_bwd;
    
    dist_fwd[source_edge] = 0.0;
    parent_fwd[source_edge] = source_edge;
    pq_fwd.push({0.0, source_edge});
    
    dist_bwd[target_edge] = 0.0;
    parent_bwd[target_edge] = target_edge;
    pq_bwd.push({0.0, target_edge});
    
    double best = INF;
    uint32_t meeting = 0;
    bool found = false;
    
    while (!pq_fwd.empty() && !pq_bwd.empty()) {
        if (pq_fwd.top().dist + pq_bwd.top().dist >= best) break;

        if (pq_fwd.top().dist <= pq_bwd.top().dist) {
            auto [d, u] = pq_fwd.top(); pq_fwd.pop();
            if (d > dist_fwd[u]) continue;
            
            auto adj_it = fwd_adj_.find(u);
            if (adj_it != fwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    double nd = d + sc.cost;
                    auto v_it = dist_fwd.find(sc.to);
                    if (v_it == dist_fwd.end() || nd < v_it->second) {
                        dist_fwd[sc.to] = nd;
                        parent_fwd[sc.to] = u;
                        pq_fwd.push({nd, sc.to});
                        
                        auto b_it = dist_bwd.find(sc.to);
                        if (b_it != dist_bwd.end()) {
                            if (nd + b_it->second < best) {
                                best = nd + b_it->second;
                                meeting = sc.to;
                                found = true;
                            }
                        }
                    }
                }
            }
        } else {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            if (d > dist_bwd[u]) continue;
            
            auto adj_it = bwd_adj_.find(u);
            if (adj_it != bwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    double nd = d + sc.cost;
                    auto v_it = dist_bwd.find(sc.from);
                    if (v_it == dist_bwd.end() || nd < v_it->second) {
                        dist_bwd[sc.from] = nd;
                        parent_bwd[sc.from] = u;
                        pq_bwd.push({nd, sc.from});
                        
                        auto f_it = dist_fwd.find(sc.from);
                        if (f_it != dist_fwd.end()) {
                            if (f_it->second + nd < best) {
                                best = f_it->second + nd;
                                meeting = sc.from;
                                found = true;
                            }
                        }
                    }
                }
            }
        }
    }
    
    if (!found) return {-1, {}, false, "No path found between source and target"};
    
    std::vector<uint32_t> path;
    uint32_t curr = meeting;
    while (true) {
        path.push_back(curr);
        auto it = parent_fwd.find(curr);
        if (it == parent_fwd.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    curr = meeting;
    while (true) {
        auto it = parent_bwd.find(curr);
        if (it == parent_bwd.end() || it->second == curr) break;
        curr = it->second;
        path.push_back(curr);
    }
    
    // Final cost: cost of first edge + sum of transitions
    double final_cost = get_edge_cost(path[0]) + best;
    return {final_cost, path, true, ""};
}


QueryResult ShortcutGraph::query_pruned(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }
    
    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge " + std::to_string(source_edge) + " not found in graph"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge " + std::to_string(target_edge) + " not found in graph"};
    }
    
    HighCell high = compute_high_cell(source_edge, target_edge);
    
    std::unordered_map<uint32_t, double> dist_fwd, dist_bwd;
    std::unordered_map<uint32_t, uint32_t> parent_fwd, parent_bwd;
    MinHeapWithRes pq_fwd, pq_bwd;
    
    // Get initial resolutions from edge metadata (already stored as lca_res)
    int8_t src_res = -1, tgt_res = -1;
    auto src_it = edge_meta_.find(source_edge);
    if (src_it != edge_meta_.end()) {
        src_res = static_cast<int8_t>(src_it->second.lca_res);
    }
    auto tgt_it = edge_meta_.find(target_edge);
    if (tgt_it != edge_meta_.end()) {
        tgt_res = static_cast<int8_t>(tgt_it->second.lca_res);
    }
    
    dist_fwd[source_edge] = 0.0;
    parent_fwd[source_edge] = source_edge;
    pq_fwd.push({0.0, source_edge, src_res});
    
    double target_cost = get_edge_cost(target_edge);
    dist_bwd[target_edge] = target_cost;
    parent_bwd[target_edge] = target_edge;
    pq_bwd.push({target_cost, target_edge, tgt_res});
    
    double best = INF;
    uint32_t meeting = 0;
    bool found = false;
    double min_arrival_fwd = INF;  // Track min arrival in forward direction
    double min_arrival_bwd = INF;  // Track min arrival in backward direction
    
    while (!pq_fwd.empty() || !pq_bwd.empty()) {
        // Forward step
        if (!pq_fwd.empty()) {
            auto [d, u, u_res] = pq_fwd.top(); pq_fwd.pop();
            
            // Check meeting
            auto bwd_it = dist_bwd.find(u);
            if (bwd_it != dist_bwd.end()) {
                min_arrival_fwd = std::min(dist_fwd[u], min_arrival_fwd);
                min_arrival_bwd = std::min(bwd_it->second, min_arrival_bwd);
                double total = d + bwd_it->second;
                if (total < best) {
                    best = total;
                    meeting = u;
                    found = true;
                }
            }
            
            auto it = dist_fwd.find(u);
            if (it != dist_fwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            // FAST PRUNING: simple resolution comparison (no H3 calls!)
            if (u_res < high.res) {
                min_arrival_fwd = std::min(dist_fwd[u], min_arrival_fwd);
                continue;
            }
            
            // At high resolution level - update min_arrival
            if (u_res == high.res) {
                min_arrival_fwd = std::min(dist_fwd[u], min_arrival_fwd);
            }
            
            auto adj_it = fwd_adj_.find(u);
            if (adj_it != fwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    if (sc.inside != 1) continue;
                    
                    double nd = d + sc.cost;
                    auto v_it = dist_fwd.find(sc.to);
                    if (v_it == dist_fwd.end() || nd < v_it->second) {
                        dist_fwd[sc.to] = nd;
                        parent_fwd[sc.to] = u;
                        pq_fwd.push({nd, sc.to, sc.cell_res});
                    }
                }
            }
        }
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u, u_res] = pq_bwd.top(); pq_bwd.pop();
            
            // Check meeting
            auto fwd_it = dist_fwd.find(u);
            if (fwd_it != dist_fwd.end()) {
                min_arrival_fwd = std::min(fwd_it->second, min_arrival_fwd);
                min_arrival_bwd = std::min(dist_bwd[u], min_arrival_bwd);
                double total = fwd_it->second + d;
                if (total < best) {
                    best = total;
                    meeting = u;
                    found = true;
                }
            }
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            // FAST PRUNING: check = (u_res >= high.res)
            bool check = (u_res >= high.res);
            
            // Update min_arrival when at high res or outside scope
            if (u_res == high.res || !check) {
                min_arrival_bwd = std::min(dist_bwd[u], min_arrival_bwd);
            }
            
            auto adj_it = bwd_adj_.find(u);
            if (adj_it != bwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    
                    // FAST resolution-based filtering
                    bool allowed = false;
                    if (sc.inside == -1 && check) allowed = true;
                    else if (sc.inside == 0 && u_res <= high.res) allowed = true;
                    else if (sc.inside == -2 && !check) allowed = true;
                    
                    if (!allowed) continue;
                    
                    double nd = d + sc.cost;
                    auto prev_it = dist_bwd.find(sc.from);
                    if (prev_it == dist_bwd.end() || nd < prev_it->second) {
                        dist_bwd[sc.from] = nd;
                        parent_bwd[sc.from] = u;
                        pq_bwd.push({nd, sc.from, sc.cell_res});
                    }
                }
            }
        }
        
        // Early termination - check if both directions can improve
        if (best < INF) {
            double bound_fwd = min_arrival_fwd;
            double bound_bwd = min_arrival_bwd;
            if (!pq_fwd.empty()) bound_fwd = std::min(bound_fwd, pq_fwd.top().dist);
            if (!pq_bwd.empty()) bound_bwd = std::min(bound_bwd, pq_bwd.top().dist);
            
            bool fwd_good = !pq_fwd.empty() && (pq_fwd.top().dist + bound_bwd < best);
            bool bwd_good = !pq_bwd.empty() && (pq_bwd.top().dist + bound_fwd < best);
            if (!fwd_good && !bwd_good) break;
        }
    }
    
    if (!found) return {-1, {}, false, "No path found between source and target (pruned)"};
    
    // Reconstruct path - use iterators to avoid inserting default values
    std::vector<uint32_t> path;
    uint32_t curr = meeting;
    
    // Forward path: meeting -> source
    while (true) {
        path.push_back(curr);
        auto it = parent_fwd.find(curr);
        if (it == parent_fwd.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    // Backward path: meeting -> target  
    curr = meeting;
    while (true) {
        auto it = parent_bwd.find(curr);
        if (it == parent_bwd.end() || it->second == curr) break;
        curr = it->second;
        path.push_back(curr);
    }
    
    return {best, path, true, ""};
}

// Struct for Unidirectional Pruned Dijkstra
struct PQEntryUni {
    double dist;
    uint32_t edge;
    int u_res;
    int counter;
    bool used_minus1;
    
    bool operator>(const PQEntryUni& o) const { return dist > o.dist; }
};

QueryResult ShortcutGraph::query_unidirectional(uint32_t source_edge, uint32_t target_edge) const {
    if (source_edge == target_edge) {
         return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }

    HighCell high = compute_high_cell(source_edge, target_edge);
    const int MAX_USES = 2;
    constexpr double INF = std::numeric_limits<double>::infinity();

    // Priority Queue
    std::priority_queue<PQEntryUni, std::vector<PQEntryUni>, std::greater<PQEntryUni>> pq;

    // Distances and Parents map
    // Key packing: (u << 4) | (counter << 1) | used_minus1
    using StateKey = uint64_t;
    std::unordered_map<StateKey, double> dist;
    std::unordered_map<StateKey, StateKey> parent;

    auto pack_key = [](uint32_t u, int counter, bool used_minus1) -> StateKey {
        return (static_cast<uint64_t>(u) << 4) | (static_cast<uint64_t>(counter) << 1) | (used_minus1 ? 1 : 0);
    };

    // Initialize source
    int src_res = -1;
    auto meta_it = edge_meta_.find(source_edge);
    if (meta_it != edge_meta_.end()) {
        src_res = meta_it->second.lca_res;
    }

    StateKey start_key = pack_key(source_edge, 0, false);
    dist[start_key] = 0.0;
    parent[start_key] = start_key;
    
    pq.push({0.0, source_edge, src_res, 0, false});

    double best = INF;
    StateKey final_state_key = 0;
    bool found = false;

    while (!pq.empty()) {
        auto [d, u, u_res, counter, used_minus1] = pq.top();
        pq.pop();

        StateKey current_key = pack_key(u, counter, used_minus1);
        
        auto it = dist.find(current_key);
        if (it != dist.end() && d > it->second) continue;

        if (u == target_edge) {
            if (d < best) {
                best = d;
                final_state_key = current_key;
                found = true;
                break;
            }
        }

        auto adj_it = fwd_adj_.find(u);
        if (adj_it == fwd_adj_.end()) continue;

        for (size_t idx : adj_it->second) {
            const Shortcut& sc = shortcuts_[idx];
            
            bool allowed = false;
            int next_counter = counter;
            bool next_used_minus1 = used_minus1;

            if (u_res > high.res) {
                // ABOVE PEAK
                if (sc.inside == 1 && !used_minus1) allowed = true;
                else if (sc.inside == -1 && used_minus1) allowed = true;
            } else {
                // AT OR BELOW PEAK
                if (used_minus1) {
                    if (sc.inside == -1) allowed = true;
                } else {
                    if ((sc.inside == 0 || sc.inside == -2) && counter < MAX_USES) {
                        allowed = true;
                        next_counter = counter + 1;
                        next_used_minus1 = true;
                    } else if (sc.inside == -1) {
                        allowed = true;
                        next_used_minus1 = true;
                    }
                }
            }

            if (!allowed) continue;

            double nd = d + sc.cost;
            StateKey next_key = pack_key(sc.to, next_counter, next_used_minus1);

            auto dist_it = dist.find(next_key);
            if (dist_it == dist.end() || nd < dist_it->second) {
                dist[next_key] = nd;
                parent[next_key] = current_key;
                
                int next_res = -1;
                auto next_meta = edge_meta_.find(sc.to);
                if (next_meta != edge_meta_.end()) {
                    next_res = next_meta->second.lca_res;
                }
                
                pq.push({nd, sc.to, next_res, next_counter, next_used_minus1});
            }
        }
    }

    if (!found) return {-1, {}, false, "No path found"};

    std::vector<uint32_t> path;
    StateKey curr = final_state_key;
    while (true) {
        uint32_t edge_id = static_cast<uint32_t>(curr >> 4);
        path.push_back(edge_id);
        
        auto it = parent.find(curr);
        if (it == parent.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    return {best, path, true, ""};
}

QueryResult ShortcutGraph::query_multi(
    const std::vector<uint32_t>& source_edges,
    const std::vector<double>& source_dists,
    const std::vector<uint32_t>& target_edges,
    const std::vector<double>& target_dists
) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    std::unordered_map<uint32_t, double> dist_fwd, dist_bwd;
    std::unordered_map<uint32_t, uint32_t> parent_fwd, parent_bwd;
    MinHeap pq_fwd, pq_bwd;
    
    // Create sets for quick lookup during path reconstruction
    std::unordered_set<uint32_t> source_set(source_edges.begin(), source_edges.end());
    std::unordered_set<uint32_t> target_set(target_edges.begin(), target_edges.end());
    
    // Initialize from all sources - start at 0.0 like query_classic
    for (size_t i = 0; i < source_edges.size(); ++i) {
        uint32_t src = source_edges[i];
        if (edge_meta_.find(src) != edge_meta_.end()) {
            dist_fwd[src] = 0.0;
            parent_fwd[src] = src;
            pq_fwd.push({0.0, src});
        }
    }
    
    // Initialize from all targets - start at target_cost like query_classic
    for (size_t i = 0; i < target_edges.size(); ++i) {
        uint32_t tgt = target_edges[i];
        double target_cost = get_edge_cost(tgt);
        if (edge_meta_.find(tgt) != edge_meta_.end()) {
            dist_bwd[tgt] = target_cost;
            parent_bwd[tgt] = tgt;
            pq_bwd.push({target_cost, tgt});
        }
    }
    
    double best = INF;
    uint32_t meeting = 0;
    bool found = false;
    
   while (!pq_fwd.empty() || !pq_bwd.empty()) {
        // Forward step
        if (!pq_fwd.empty()) {
            auto [d, u] = pq_fwd.top(); pq_fwd.pop();
            
            auto it = dist_fwd.find(u);
            if (it != dist_fwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto adj_it = fwd_adj_.find(u);
            if (adj_it != fwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    if (sc.inside != 1) continue;
                    
                    double nd = d + sc.cost;
                    auto v_it = dist_fwd.find(sc.to);
                    if (v_it == dist_fwd.end() || nd < v_it->second) {
                        dist_fwd[sc.to] = nd;
                        parent_fwd[sc.to] = u;
                        pq_fwd.push({nd, sc.to});
                        
                        auto bwd_it = dist_bwd.find(sc.to);
                        if (bwd_it != dist_bwd.end()) {
                            double total = nd + bwd_it->second;
                            if (total < best) {
                                best = total;
                                meeting = sc.to;
                                found = true;
                            }
                        }
                    }
                }
            }
        }
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto adj_it = bwd_adj_.find(u);
            if (adj_it != bwd_adj_.end()) {
                for (size_t idx : adj_it->second) {
                    const Shortcut& sc = shortcuts_[idx];
                    if (sc.inside != -1 && sc.inside != 0) continue;
                    
                    double nd = d + sc.cost;
                    auto prev_it = dist_bwd.find(sc.from);
                    if (prev_it == dist_bwd.end() || nd < prev_it->second) {
                        dist_bwd[sc.from] = nd;
                        parent_bwd[sc.from] = u;
                        pq_bwd.push({nd, sc.from});
                        
                        auto fwd_it = dist_fwd.find(sc.from);
                        if (fwd_it != dist_fwd.end()) {
                            double total = fwd_it->second + nd;
                            if (total < best) {
                                best = total;
                                meeting = sc.from;
                                found = true;
                            }
                        }
                    }
                }
            }
        }
        
        // Early termination
        if (!pq_fwd.empty() && !pq_bwd.empty()) {
            if (pq_fwd.top().dist >= best && pq_bwd.top().dist >= best) break;
        } else if (pq_fwd.empty() && pq_bwd.empty()) {
            break;
        }
    }
    
    if (!found) return {-1, {}, false};
    
    // Reconstruct path 
    std::vector<uint32_t> path;
    uint32_t curr = meeting;
    
    // Forward path: meeting -> source
    while (true) {
        path.push_back(curr);
        auto it = parent_fwd.find(curr);
        if (it == parent_fwd.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    // Backward path: meeting -> target
    curr = meeting;
    while (true) {
        auto it = parent_bwd.find(curr);
        if (it == parent_bwd.end() || it->second == curr) break;
        curr = it->second;
        path.push_back(curr);
    }
    
    return {best, path, true};
}
// ============================================================
// SPATIAL INDEXING METHODS
// ============================================================

void ShortcutGraph::build_spatial_index(SpatialIndexType type) {
    spatial_index_type_ = type;
    
    if (type == SpatialIndexType::H3) {
        // Build H3 cell-based index
        h3_index_.clear();
        for (const auto& [edge_id, meta] : edge_meta_) {
            if (meta.to_cell == 0) continue;
            
            // Use to_cell at index resolution
            uint64_t cell = h3_utils::cell_to_parent(meta.to_cell, h3_index_res_);
            if (cell != 0) {
                h3_index_[cell].push_back(edge_id);
            }
        }
        std::cout << "Built H3 index with " << h3_index_.size() << " cells at res " << h3_index_res_ << "\n";
    } else {
        // Build R-tree index
        rtree_ = std::make_unique<bgi::rtree<RTreeValue, bgi::quadratic<16>>>();
        
        for (const auto& [edge_id, meta] : edge_meta_) {
            if (meta.geometry.empty()) continue;
            
            // Compute bounding box from geometry
            double min_x = std::numeric_limits<double>::max();
            double min_y = std::numeric_limits<double>::max();
            double max_x = std::numeric_limits<double>::lowest();
            double max_y = std::numeric_limits<double>::lowest();
            
            for (const auto& [lon, lat] : meta.geometry) {
                min_x = std::min(min_x, lon);
                min_y = std::min(min_y, lat);
                max_x = std::max(max_x, lon);
                max_y = std::max(max_y, lat);
            }
            
            Box2D bbox(Point2D(min_x, min_y), Point2D(max_x, max_y));
            rtree_->insert({bbox, edge_id});
        }
        std::cout << "Built R-tree index with " << rtree_->size() << " entries\n";
    }
    
    spatial_index_built_ = true;
}

// Helper: Haversine distance in meters
static double haversine_distance(double lat1, double lon1, double lat2, double lon2) {
    const double R = 6371000.0;  // Earth radius in meters
    double dLat = (lat2 - lat1) * M_PI / 180.0;
    double dLon = (lon2 - lon1) * M_PI / 180.0;
    double a = sin(dLat/2) * sin(dLat/2) +
               cos(lat1 * M_PI / 180.0) * cos(lat2 * M_PI / 180.0) *
               sin(dLon/2) * sin(dLon/2);
    double c = 2 * atan2(sqrt(a), sqrt(1-a));
    return R * c;
}

// Helper: Distance from point to linestring
static double point_to_line_distance(double lat, double lng, 
                                     const std::vector<std::pair<double, double>>& line) {
    if (line.empty()) return std::numeric_limits<double>::max();
    if (line.size() == 1) return haversine_distance(lat, lng, line[0].second, line[0].first);
    
    double min_dist = std::numeric_limits<double>::max();
    for (size_t i = 0; i < line.size() - 1; ++i) {
        double lon1 = line[i].first, lat1 = line[i].second;
        double lon2 = line[i+1].first, lat2 = line[i+1].second;
        
        // Project point onto segment (simplified Cartesian approximation)
        double dx = lon2 - lon1;
        double dy = lat2 - lat1;
        double t = 0.0;
        if (dx != 0 || dy != 0) {
            t = ((lng - lon1) * dx + (lat - lat1) * dy) / (dx * dx + dy * dy);
            t = std::max(0.0, std::min(1.0, t));
        }
        double proj_lon = lon1 + t * dx;
        double proj_lat = lat1 + t * dy;
        double dist = haversine_distance(lat, lng, proj_lat, proj_lon);
        min_dist = std::min(min_dist, dist);
    }
    return min_dist;
}

std::vector<std::pair<uint32_t, double>> ShortcutGraph::find_nearest_edges(
    double lat, double lng, int max_candidates, double radius_meters) const {
    
    std::vector<std::pair<uint32_t, double>> results;
    
    if (!spatial_index_built_) {
        std::cerr << "Warning: Spatial index not built. Call build_spatial_index() first.\n";
        return results;
    }
    
    if (spatial_index_type_ == SpatialIndexType::H3) {
        // H3-based search
        uint64_t center_cell = h3_utils::latlng_to_cell(lat, lng, h3_index_res_);
        if (center_cell == 0) return results;
        
        // Collect candidates from expanding rings
        // We need to collect MORE than max_candidates, then sort and take top k
        std::unordered_set<uint32_t> seen;
        int k = 0;
        int min_rings = 2;  // Always check at least 2 rings to ensure we find nearby edges
        
        // Keep expanding until we have enough candidates OR exhausted reasonable area
        while (k < 5) {
            std::vector<uint64_t> ring = h3_utils::grid_ring(center_cell, k);
            for (uint64_t cell : ring) {
                auto it = h3_index_.find(cell);
                if (it != h3_index_.end()) {
                    for (uint32_t edge_id : it->second) {
                        if (seen.count(edge_id)) continue;
                        seen.insert(edge_id);
                        
                        auto meta_it = edge_meta_.find(edge_id);
                        if (meta_it == edge_meta_.end()) continue;
                        
                        double dist = point_to_line_distance(lat, lng, meta_it->second.geometry);
                        if (dist <= radius_meters) {
                            results.push_back({edge_id, dist});
                        }
                    }
                }
            }
            ++k;
            // Only stop early after minimum rings AND we have plenty of candidates
            if (k >= min_rings && results.size() >= static_cast<size_t>(max_candidates * 2)) {
                break;
            }
        }
    } else {
        // R-tree-based search
        if (!rtree_) return results;
        
        Point2D query_point(lng, lat);
        std::vector<RTreeValue> candidates;
        rtree_->query(bgi::nearest(query_point, max_candidates * 2), std::back_inserter(candidates));
        
        for (const auto& [bbox, edge_id] : candidates) {
            auto meta_it = edge_meta_.find(edge_id);
            if (meta_it == edge_meta_.end()) continue;
            
            double dist = point_to_line_distance(lat, lng, meta_it->second.geometry);
            if (dist <= radius_meters) {
                results.push_back({edge_id, dist});
            }
        }
    }
    
    // Sort by distance and limit
    std::sort(results.begin(), results.end(), 
              [](const auto& a, const auto& b) { return a.second < b.second; });
    if (results.size() > static_cast<size_t>(max_candidates)) {
        results.resize(max_candidates);
    }
    
    return results;
}

std::vector<uint32_t> ShortcutGraph::expand_path(const std::vector<uint32_t>& shortcut_path) const {
    if (shortcut_path.empty()) return {};
    if (shortcut_path.size() == 1) return {shortcut_path[0]};
    
    // Helper lambda to recursively expand a pair (u, v)
    std::function<std::vector<uint32_t>(uint32_t, uint32_t, std::unordered_set<uint64_t>&)> expand_pair;
    expand_pair = [this, &expand_pair](uint32_t u, uint32_t v, std::unordered_set<uint64_t>& visited) -> std::vector<uint32_t> {
        const uint64_t key = (static_cast<uint64_t>(u) << 32) | v;
        
        // Cycle detection
        if (visited.count(key)) {
            return {u, v};
        }
        visited.insert(key);
        
        // Look up the shortcut
        auto it = shortcut_lookup_.find(key);
        if (it == shortcut_lookup_.end()) {
            // No shortcut entry, these are consecutive base edges
            return {u, v};
        }
        
        const auto& sc = shortcuts_[it->second];
        const uint32_t via = sc.via_edge;
        
        // Base edge check: via_edge equals to_edge means it's a direct edge
        // We also check via == u to prevent infinite recursion on self-loops
        // Base edge check: via equal to source/target means loop or invalid (if 0 was treated as edge)
        // User requested removing via == 0 check to allow expansion through edge 0
        if (via == u || via == v) {
            // Base edge (via equals source/target)
            return {u, v};
        }
        
        // Recursively expand: u -> via and via -> v
        auto left = expand_pair(u, via, visited);
        auto right = expand_pair(via, v, visited);
        
        // Merge, avoiding duplicate at the junction
        if (!right.empty() && !left.empty() && right[0] == left.back()) {
            left.insert(left.end(), right.begin() + 1, right.end());
        } else {
            left.insert(left.end(), right.begin(), right.end());
        }
        return left;
    };
    
    // Expand each consecutive pair and merge
    std::vector<uint32_t> base_edges;
    for (size_t i = 0; i + 1 < shortcut_path.size(); ++i) {
        std::unordered_set<uint64_t> visited;
        auto expanded = expand_pair(shortcut_path[i], shortcut_path[i + 1], visited);
        
        // For first pair, add all edges
        if (base_edges.empty()) {
            base_edges = expanded;
        } else {
            // For subsequent pairs, skip the first edge (already in base_edges as last edge)
            if (!expanded.empty() && !base_edges.empty() && expanded[0] == base_edges.back()) {
                base_edges.insert(base_edges.end(), expanded.begin() + 1, expanded.end());
            } else {
                base_edges.insert(base_edges.end(), expanded.begin(), expanded.end());
            }
        }
    }
    
    return base_edges;
}

const std::vector<std::pair<double, double>>* ShortcutGraph::get_edge_geometry(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    if (it != edge_meta_.end()) {
        return &it->second.geometry;
    }
    return nullptr;
}

#ifdef HAVE_DUCKDB

bool ShortcutGraph::load_from_duckdb(const std::string& db_path) {
    std::cout << "Loading data from DuckDB: " << db_path << std::endl;
    
    try {
        // Open in read-only mode to avoid lock conflicts with Python processes
        duckdb::DBConfig config;
        config.options.access_mode = duckdb::AccessMode::READ_ONLY;
        duckdb::DuckDB db(db_path, &config);
        duckdb::Connection con(db);
        
        // Clear existing data
        shortcuts_.clear();
        fwd_adj_.clear();
        bwd_adj_.clear();
        shortcut_lookup_.clear();
        edge_meta_.clear();
        dataset_info_.clear();
        
        // 1. Load shortcuts
        auto result = con.Query("SELECT from_edge, to_edge, cost, via_edge, cell, inside FROM shortcuts");
        if (result->HasError()) {
            std::cerr << "Error loading shortcuts: " << result->GetError() << std::endl;
            return false;
        }
        
        while (auto chunk = result->Fetch()) {
            for (idx_t i = 0; i < chunk->size(); i++) {
                Shortcut sc;
                sc.from = static_cast<uint32_t>(chunk->GetValue(0, i).GetValue<int32_t>());
                sc.to = static_cast<uint32_t>(chunk->GetValue(1, i).GetValue<int32_t>());
                sc.cost = chunk->GetValue(2, i).GetValue<double>();
                sc.via_edge = static_cast<uint32_t>(chunk->GetValue(3, i).GetValue<int32_t>());
                sc.cell = static_cast<uint64_t>(chunk->GetValue(4, i).GetValue<int64_t>());
                sc.inside = static_cast<int8_t>(chunk->GetValue(5, i).GetValue<int8_t>());
                sc.cell_res = (sc.cell == 0) ? -1 : static_cast<int8_t>(h3_utils::get_resolution(sc.cell));
                
                size_t idx = shortcuts_.size();
                shortcuts_.push_back(sc);
                fwd_adj_[sc.from].push_back(idx);
                bwd_adj_[sc.to].push_back(idx);
            }
        }
        std::cout << "  Loaded " << shortcuts_.size() << " shortcuts" << std::endl;
        
        // Build shortcut lookup
        for (size_t idx = 0; idx < shortcuts_.size(); ++idx) {
            const auto& sc = shortcuts_[idx];
            const uint64_t key = (static_cast<uint64_t>(sc.from) << 32) | sc.to;
            if (shortcut_lookup_.find(key) == shortcut_lookup_.end()) {
                shortcut_lookup_[key] = idx;
            }
        }
        
        // 2. Load edges with geometry
        result = con.Query("SELECT id, from_cell, to_cell, lca_res, length, cost, geometry FROM edges");
        if (result->HasError()) {
            std::cerr << "Error loading edges: " << result->GetError() << std::endl;
            return false;
        }
        
        while (auto chunk = result->Fetch()) {
            for (idx_t i = 0; i < chunk->size(); i++) {
                uint32_t id = static_cast<uint32_t>(chunk->GetValue(0, i).GetValue<int64_t>());
                EdgeMeta meta;
                meta.from_cell = static_cast<uint64_t>(chunk->GetValue(1, i).GetValue<int64_t>());
                meta.to_cell = static_cast<uint64_t>(chunk->GetValue(2, i).GetValue<int64_t>());
                meta.lca_res = chunk->GetValue(3, i).GetValue<int64_t>();
                meta.length = chunk->GetValue(4, i).GetValue<double>();
                meta.cost = chunk->GetValue(5, i).GetValue<double>();
                
                // Parse geometry (WKT LINESTRING)
                std::string geom = chunk->GetValue(6, i).ToString();
                size_t start = geom.find('(');
                size_t end = geom.rfind(')');
                if (start != std::string::npos && end != std::string::npos && end > start) {
                    std::string coords = geom.substr(start + 1, end - start - 1);
                    std::stringstream ss(coords);
                    std::string point;
                    while (std::getline(ss, point, ',')) {
                        size_t first = point.find_first_not_of(" \t");
                        if (first == std::string::npos) continue;
                        point = point.substr(first);
                        std::istringstream ps(point);
                        double lon, lat;
                        if (ps >> lon >> lat) {
                            meta.geometry.push_back({lon, lat});
                        }
                    }
                }
                
                edge_meta_[id] = std::move(meta);
            }
        }
        std::cout << "  Loaded " << edge_meta_.size() << " edges with geometry" << std::endl;
        
        // 3. Load dataset_info
        result = con.Query("SELECT key, value FROM dataset_info");
        if (!result->HasError()) {
            while (auto chunk = result->Fetch()) {
                for (idx_t i = 0; i < chunk->size(); i++) {
                    std::string key = chunk->GetValue(0, i).ToString();
                    std::string value = chunk->GetValue(1, i).ToString();
                    dataset_info_[key] = value;
                }
            }
            std::cout << "  Loaded " << dataset_info_.size() << " dataset info entries" << std::endl;
        }
        
        std::cout << "DuckDB loading complete." << std::endl;
        return !shortcuts_.empty() && !edge_meta_.empty();
        
    } catch (const std::exception& e) {
        std::cerr << "DuckDB error: " << e.what() << std::endl;
        return false;
    }
}

std::string ShortcutGraph::get_dataset_info(const std::string& key) const {
    auto it = dataset_info_.find(key);
    if (it != dataset_info_.end()) {
        return it->second;
    }
    return "";
}

#endif // HAVE_DUCKDB
