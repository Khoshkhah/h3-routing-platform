/**
 * @file csr_graph.cpp
 * @brief CSR Graph implementation - clean rewrite based on legacy shortcut_graph.cpp.
 */

#include "csr_graph.hpp"
#include "h3_utils.hpp"

#include <arrow/api.h>
#include <arrow/io/api.h>
#include <parquet/arrow/reader.h>

#include <filesystem>
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <queue>
#include <limits>
#include <cmath>
#include <unordered_set>

#ifdef HAVE_DUCKDB
#include <duckdb.hpp>
#endif

namespace fs = std::filesystem;

// ============================================================
// PRIORITY QUEUE ENTRIES
// ============================================================

struct PQEntry {
    double dist;
    uint32_t edge;
    bool operator>(const PQEntry& o) const { return dist > o.dist; }
};

struct PQEntryWithRes {
    double dist;
    uint32_t edge;
    int8_t res;
    bool operator>(const PQEntryWithRes& o) const { return dist > o.dist; }
};

struct PQEntryWithState {
    double dist;
    uint64_t state;
    bool operator>(const PQEntryWithState& o) const { return dist > o.dist; }
};

using MinHeap = std::priority_queue<PQEntry, std::vector<PQEntry>, std::greater<PQEntry>>;
using MinHeapWithRes = std::priority_queue<PQEntryWithRes, std::vector<PQEntryWithRes>, std::greater<PQEntryWithRes>>;
using MinHeapWithState = std::priority_queue<PQEntryWithState, std::vector<PQEntryWithState>, std::greater<PQEntryWithState>>;

// ============================================================
// LOADING - PARQUET
// ============================================================

// Temporary structure for building CSR
struct TempShortcut {
    uint32_t from;
    uint32_t to;
    float cost;
    uint32_t via_edge;
    uint64_t cell;
    int8_t inside;
    int8_t cell_res;
};

static bool load_parquet_file_csr(const std::string& filepath, std::vector<TempShortcut>& out_list) {
    auto result = arrow::io::ReadableFile::Open(filepath);
    if (!result.ok()) return false;
    
    std::unique_ptr<parquet::arrow::FileReader> reader;
    auto status = parquet::arrow::OpenFile(*result, arrow::default_memory_pool(), &reader);
    if (!status.ok()) return false;
    
    std::shared_ptr<arrow::Table> table;
    status = reader->ReadTable(&table);
    if (!status.ok()) return false;
    
    auto from_col = std::static_pointer_cast<arrow::Int32Array>(table->GetColumnByName("from_edge")->chunk(0));
    auto to_col = std::static_pointer_cast<arrow::Int32Array>(table->GetColumnByName("to_edge")->chunk(0));
    auto cost_col = std::static_pointer_cast<arrow::DoubleArray>(table->GetColumnByName("cost")->chunk(0));
    auto via_col = std::static_pointer_cast<arrow::Int32Array>(table->GetColumnByName("via_edge")->chunk(0));
    auto cell_col = std::static_pointer_cast<arrow::Int64Array>(table->GetColumnByName("cell")->chunk(0));
    auto inside_col = std::static_pointer_cast<arrow::Int8Array>(table->GetColumnByName("inside")->chunk(0));
    
    for (int64_t i = 0; i < table->num_rows(); ++i) {
        TempShortcut sc;
        sc.from = static_cast<uint32_t>(from_col->Value(i));
        sc.to = static_cast<uint32_t>(to_col->Value(i));
        sc.cost = cost_col->Value(i);
        sc.via_edge = static_cast<uint32_t>(via_col->Value(i));
        sc.cell = static_cast<uint64_t>(cell_col->Value(i));
        sc.inside = inside_col->Value(i);
        sc.cell_res = (sc.cell == 0) ? -1 : static_cast<int8_t>(h3_utils::get_resolution(sc.cell));
        out_list.push_back(sc);
    }
    return true;
}

bool CSRGraph::load_shortcuts(const std::string& path) {
    std::vector<TempShortcut> temp_list;
    
    // Load from single file or directory
    if (fs::is_directory(path)) {
        for (const auto& entry : fs::directory_iterator(path)) {
            if (entry.path().extension() == ".parquet") {
                load_parquet_file_csr(entry.path().string(), temp_list);
            }
        }
    } else {
        if (!load_parquet_file_csr(path, temp_list)) return false;
    }
    
    if (temp_list.empty()) return false;
    
    // Find max edge ID
    max_edge_id_ = 0;
    for (const auto& sc : temp_list) {
        max_edge_id_ = std::max(max_edge_id_, sc.from);
        max_edge_id_ = std::max(max_edge_id_, sc.to);
    }
    
    // Sort by source for forward CSR
    std::sort(temp_list.begin(), temp_list.end(), 
              [](const TempShortcut& a, const TempShortcut& b) { return a.from < b.from; });
    
    // Build forward CSR
    fwd_offsets_.assign(max_edge_id_ + 2, 0);
    
    // Count shortcuts per source
    std::vector<uint32_t> counts(max_edge_id_ + 1, 0);
    for (const auto& sc : temp_list) {
        counts[sc.from]++;
    }
    
    // Compute offsets (prefix sum)
    uint32_t offset = 0;
    for (size_t i = 0; i <= max_edge_id_; ++i) {
        fwd_offsets_[i] = offset;
        offset += counts[i];
    }
    fwd_offsets_[max_edge_id_ + 1] = offset;
    
    // Copy shortcuts
    shortcuts_.reserve(temp_list.size());
    for (const auto& t : temp_list) {
        CSRShortcut sc;
        sc.from = t.from;
        sc.to = t.to;
        sc.cost = t.cost;
        sc.via_edge = t.via_edge;
        sc.cell = t.cell;
        sc.inside = t.inside;
        shortcuts_.push_back(sc);
    }
    
    // Build backward CSR
    std::fill(counts.begin(), counts.end(), 0);
    for (const auto& sc : shortcuts_) {
        counts[sc.to]++;
    }
    
    bwd_offsets_.assign(max_edge_id_ + 2, 0);
    offset = 0;
    for (size_t i = 0; i <= max_edge_id_; ++i) {
        bwd_offsets_[i] = offset;
        offset += counts[i];
    }
    bwd_offsets_[max_edge_id_ + 1] = offset;
    
    // Fill backward indices
    std::vector<uint32_t> current_pos(bwd_offsets_.begin(), bwd_offsets_.end() - 1);
    bwd_indices_.resize(shortcuts_.size());
    for (size_t i = 0; i < shortcuts_.size(); ++i) {
        uint32_t target = shortcuts_[i].to;
        bwd_indices_[current_pos[target]++] = static_cast<uint32_t>(i);
    }
    
    std::cout << "CSR loaded: " << shortcuts_.size() << " shortcuts, max_edge=" << max_edge_id_ << std::endl;
    return true;
}

// ============================================================
// LOADING - EDGE METADATA
// ============================================================

bool CSRGraph::load_edge_metadata(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) return false;
    
    std::string line;
    std::getline(file, line); // Skip header
    
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        std::string token;
        
        std::vector<std::string> tokens;
        while (std::getline(ss, token, ',')) {
            tokens.push_back(token);
        }
        
        if (tokens.size() < 6) continue;
        
        uint32_t id = std::stoul(tokens[0]);
        CSREdgeMeta meta;
        meta.from_cell = std::stoull(tokens[1]);
        meta.to_cell = std::stoull(tokens[2]);
        meta.lca_res = std::stoll(tokens[3]);
        meta.length = std::stod(tokens[4]);
        meta.cost = std::stod(tokens[5]);
        
        // Parse geometry if present
        if (tokens.size() > 6) {
            std::string geom = tokens[6];
            // Handle quoted geometry
            for (size_t i = 7; i < tokens.size(); ++i) {
                geom += "," + tokens[i];
            }
            // Remove quotes
            if (!geom.empty() && geom.front() == '"') geom = geom.substr(1);
            if (!geom.empty() && geom.back() == '"') geom.pop_back();
            
            // Parse LINESTRING(lon lat, lon lat, ...)
            size_t start = geom.find('(');
            size_t end = geom.rfind(')');
            if (start != std::string::npos && end != std::string::npos && end > start) {
                std::string coords = geom.substr(start + 1, end - start - 1);
                std::istringstream cs(coords);
                std::string point;
                while (std::getline(cs, point, ',')) {
                    size_t first = point.find_first_not_of(" \t");
                    if (first == std::string::npos) continue;
                    point = point.substr(first);
                    std::istringstream ps(point);
                    double lon, lat;
                    if (ps >> lon >> lat) {
                        meta.geometry.push_back({lon, lat});
                    }
                }
                meta.geometry.shrink_to_fit();
            }
        }
        
        edge_meta_[id] = std::move(meta);
    }
    
    std::cout << "CSR loaded: " << edge_meta_.size() << " edges with metadata" << std::endl;
    return !edge_meta_.empty();
}

// ============================================================
// LOADING - DUCKDB
// ============================================================

#ifdef HAVE_DUCKDB

bool CSRGraph::load_from_duckdb(const std::string& db_path) {
    std::cout << "CSR loading from DuckDB: " << db_path << std::endl;
    
    try {
        duckdb::DBConfig config;
        config.options.access_mode = duckdb::AccessMode::READ_ONLY;
        duckdb::DuckDB db(db_path, &config);
        duckdb::Connection con(db);
        
        // Clear existing data
        shortcuts_.clear();
        fwd_offsets_.clear();
        bwd_offsets_.clear();
        bwd_indices_.clear();
        edge_meta_.clear();
        max_edge_id_ = 0;
        
        // Load shortcuts
        std::vector<TempShortcut> temp_list;
        auto result = con.Query("SELECT from_edge, to_edge, cost, via_edge, cell, inside FROM shortcuts");
        if (result->HasError()) {
            std::cerr << "Error loading shortcuts: " << result->GetError() << std::endl;
            return false;
        }
        
        while (auto chunk = result->Fetch()) {
            for (idx_t i = 0; i < chunk->size(); i++) {
                TempShortcut sc;
                sc.from = static_cast<uint32_t>(chunk->GetValue(0, i).GetValue<int32_t>());
                sc.to = static_cast<uint32_t>(chunk->GetValue(1, i).GetValue<int32_t>());
                sc.cost = chunk->GetValue(2, i).GetValue<double>();
                sc.via_edge = static_cast<uint32_t>(chunk->GetValue(3, i).GetValue<int32_t>());
                sc.cell = static_cast<uint64_t>(chunk->GetValue(4, i).GetValue<int64_t>());
                sc.inside = chunk->GetValue(5, i).GetValue<int8_t>();
                sc.cell_res = (sc.cell == 0) ? -1 : static_cast<int8_t>(h3_utils::get_resolution(sc.cell));
                
                max_edge_id_ = std::max(max_edge_id_, sc.from);
                max_edge_id_ = std::max(max_edge_id_, sc.to);
                temp_list.push_back(sc);
            }
        }
        std::cout << "  Loaded " << temp_list.size() << " shortcuts" << std::endl;
        
        if (temp_list.empty()) return false;
        
        // Sort and build CSR (same as load_shortcuts)
        std::sort(temp_list.begin(), temp_list.end(),
                  [](const TempShortcut& a, const TempShortcut& b) { return a.from < b.from; });
        
        fwd_offsets_.assign(max_edge_id_ + 2, 0);
        std::vector<uint32_t> counts(max_edge_id_ + 1, 0);
        for (const auto& sc : temp_list) counts[sc.from]++;
        
        uint32_t offset = 0;
        for (size_t i = 0; i <= max_edge_id_; ++i) {
            fwd_offsets_[i] = offset;
            offset += counts[i];
        }
        fwd_offsets_[max_edge_id_ + 1] = offset;
        
        shortcuts_.reserve(temp_list.size());
        for (const auto& t : temp_list) {
            CSRShortcut sc;
            sc.from = t.from; sc.to = t.to; sc.cost = t.cost;
            sc.via_edge = t.via_edge; sc.cell = t.cell;
            sc.inside = t.inside;
            shortcuts_.push_back(sc);
        }
        
        // Build backward CSR
        std::fill(counts.begin(), counts.end(), 0);
        for (const auto& sc : shortcuts_) counts[sc.to]++;
        
        bwd_offsets_.assign(max_edge_id_ + 2, 0);
        offset = 0;
        for (size_t i = 0; i <= max_edge_id_; ++i) {
            bwd_offsets_[i] = offset;
            offset += counts[i];
        }
        bwd_offsets_[max_edge_id_ + 1] = offset;
        
        std::vector<uint32_t> current_pos(bwd_offsets_.begin(), bwd_offsets_.end() - 1);
        bwd_indices_.resize(shortcuts_.size());
        for (size_t i = 0; i < shortcuts_.size(); ++i) {
            uint32_t target = shortcuts_[i].to;
            bwd_indices_[current_pos[target]++] = static_cast<uint32_t>(i);
        }
        
        // Load edges with geometry
        result = con.Query("SELECT id, from_cell, to_cell, lca_res, length, cost, geometry FROM edges");
        if (result->HasError()) {
            std::cerr << "Error loading edges: " << result->GetError() << std::endl;
            return false;
        }
        
        while (auto chunk = result->Fetch()) {
            for (idx_t i = 0; i < chunk->size(); i++) {
                uint32_t id = static_cast<uint32_t>(chunk->GetValue(0, i).GetValue<int64_t>());
                CSREdgeMeta meta;
                meta.from_cell = static_cast<uint64_t>(chunk->GetValue(1, i).GetValue<int64_t>());
                meta.to_cell = static_cast<uint64_t>(chunk->GetValue(2, i).GetValue<int64_t>());
                meta.lca_res = chunk->GetValue(3, i).GetValue<int64_t>();
                meta.length = chunk->GetValue(4, i).GetValue<double>();
                meta.cost = chunk->GetValue(5, i).GetValue<double>();
                
                std::string geom = chunk->GetValue(6, i).ToString();
                size_t start = geom.find('(');
                size_t end = geom.rfind(')');
                if (start != std::string::npos && end != std::string::npos && end > start) {
                    std::string coords = geom.substr(start + 1, end - start - 1);
                    std::istringstream ss(coords);
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
                    meta.geometry.shrink_to_fit();
                }
                edge_meta_[id] = std::move(meta);
            }
        }
        std::cout << "  Loaded " << edge_meta_.size() << " edges with geometry" << std::endl;
        
        return !shortcuts_.empty() && !edge_meta_.empty();
        
    } catch (const std::exception& e) {
        std::cerr << "DuckDB error: " << e.what() << std::endl;
        return false;
    }
}

#endif // HAVE_DUCKDB

// ============================================================
// ACCESSORS
// ============================================================

double CSRGraph::get_edge_cost(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    return (it != edge_meta_.end()) ? it->second.cost : 0.0;
}

uint64_t CSRGraph::get_edge_cell(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    return (it != edge_meta_.end()) ? it->second.to_cell : 0;
}

const CSREdgeMeta* CSRGraph::get_edge_meta(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    return (it != edge_meta_.end()) ? &it->second : nullptr;
}

const std::vector<std::pair<double, double>>* CSRGraph::get_edge_geometry(uint32_t edge_id) const {
    auto it = edge_meta_.find(edge_id);
    return (it != edge_meta_.end()) ? &it->second.geometry : nullptr;
}

CSRHighCell CSRGraph::compute_high_cell(uint32_t source_edge, uint32_t target_edge) const {
    auto src = edge_meta_.find(source_edge);
    auto tgt = edge_meta_.find(target_edge);
    if (src == edge_meta_.end() || tgt == edge_meta_.end()) return {0, -1};
    
    uint64_t src_cell = src->second.to_cell;
    uint64_t tgt_cell = tgt->second.to_cell;
    if (src_cell == 0 || tgt_cell == 0) return {0, -1};
    
    uint64_t lca = h3_utils::find_lca(src_cell, tgt_cell);
    int res = (lca != 0) ? h3_utils::get_resolution(lca) : -1;
    return {lca, res};
}

int CSRGraph::find_shortcut_index(uint32_t u, uint32_t v) const {
    auto range = get_fwd_range(u);
    for (uint32_t i = range.first; i < range.second; ++i) {
        if (shortcuts_[i].to == v) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

size_t CSRGraph::memory_usage() const {
    size_t total = 0;
    total += shortcuts_.capacity() * sizeof(CSRShortcut);
    total += fwd_offsets_.capacity() * sizeof(uint32_t);
    total += bwd_offsets_.size() * sizeof(uint32_t);
    total += bwd_indices_.capacity() * sizeof(uint32_t);
    
    // Maps and their content
    total += edge_meta_.size() * (sizeof(uint32_t) + sizeof(CSREdgeMeta) + 32);
    for (const auto& [id, meta] : edge_meta_) {
        total += meta.geometry.capacity() * sizeof(std::pair<double, double>);
    }
    
    if (spatial_index_type_ == CSRSpatialIndexType::H3) {
        total += h3_index_.size() * (sizeof(uint64_t) + sizeof(std::vector<uint32_t>) + 32);
        for (const auto& [cell, list] : h3_index_) {
            total += list.capacity() * sizeof(uint32_t);
        }
    } else if (rtree_) {
        // Approximate R-tree overhead
        total += rtree_->size() * sizeof(CSRRTreeValue) * 1.2;
    }
    
    return total;
}

// ============================================================
// SPATIAL INDEXING
// ============================================================

static double haversine(double lat1, double lon1, double lat2, double lon2) {
    constexpr double R = 6371000.0;
    double dlat = (lat2 - lat1) * M_PI / 180.0;
    double dlon = (lon2 - lon1) * M_PI / 180.0;
    double a = std::sin(dlat / 2) * std::sin(dlat / 2) +
               std::cos(lat1 * M_PI / 180.0) * std::cos(lat2 * M_PI / 180.0) *
               std::sin(dlon / 2) * std::sin(dlon / 2);
    return R * 2 * std::atan2(std::sqrt(a), std::sqrt(1 - a));
}

static double point_to_line_distance(double lat, double lng, 
                                     const std::vector<std::pair<double, double>>& line) {
    if (line.empty()) return std::numeric_limits<double>::infinity();
    if (line.size() == 1) return haversine(lat, lng, line[0].second, line[0].first);
    
    double min_dist = std::numeric_limits<double>::infinity();
    for (size_t i = 0; i + 1 < line.size(); ++i) {
        double x0 = lng, y0 = lat;
        double x1 = line[i].first, y1 = line[i].second;
        double x2 = line[i+1].first, y2 = line[i+1].second;
        
        double dx = x2 - x1, dy = y2 - y1;
        double len_sq = dx * dx + dy * dy;
        
        double t = 0.0;
        if (len_sq > 1e-12) {
            t = std::max(0.0, std::min(1.0, ((x0 - x1) * dx + (y0 - y1) * dy) / len_sq));
        }
        
        double proj_x = x1 + t * dx;
        double proj_y = y1 + t * dy;
        double dist = haversine(lat, lng, proj_y, proj_x);
        min_dist = std::min(min_dist, dist);
    }
    return min_dist;
}

void CSRGraph::build_spatial_index(CSRSpatialIndexType type) {
    spatial_index_type_ = type;
    h3_index_.clear();
    rtree_.reset();
    
    if (type == CSRSpatialIndexType::RTREE) {
        std::vector<CSRRTreeValue> items;
        items.reserve(edge_meta_.size());
        
        for (const auto& [edge_id, meta] : edge_meta_) {
            if (meta.geometry.empty()) continue;
            
            double min_lon = 180, max_lon = -180, min_lat = 90, max_lat = -90;
            for (const auto& [lon, lat] : meta.geometry) {
                min_lon = std::min(min_lon, lon);
                max_lon = std::max(max_lon, lon);
                min_lat = std::min(min_lat, lat);
                max_lat = std::max(max_lat, lat);
            }
            
            CSRBox2D box(CSRPoint2D(min_lon, min_lat), CSRPoint2D(max_lon, max_lat));
            items.push_back({box, edge_id});
        }
        
        rtree_ = std::make_unique<bgi::rtree<CSRRTreeValue, bgi::quadratic<16>>>(items.begin(), items.end());
        std::cout << "CSR R-tree built with " << items.size() << " edges" << std::endl;
    } else {
        // H3 index
        for (const auto& [edge_id, meta] : edge_meta_) {
            uint64_t cell1 = meta.from_cell, cell2 = meta.to_cell;
            if (cell1 != 0) {
                uint64_t indexed = h3_utils::cell_to_parent(cell1, h3_index_res_);
                h3_index_[indexed].push_back(edge_id);
            }
            if (cell2 != 0 && cell2 != cell1) {
                uint64_t indexed = h3_utils::cell_to_parent(cell2, h3_index_res_);
                h3_index_[indexed].push_back(edge_id);
            }
        }
        std::cout << "CSR H3 index built with " << h3_index_.size() << " cells" << std::endl;
    }
    
    spatial_index_built_ = true;
}

std::vector<std::pair<uint32_t, double>> CSRGraph::find_nearest_edges(
    double lat, double lng, int max_candidates, double radius_meters) const {
    
    std::vector<std::pair<uint32_t, double>> results;
    if (!spatial_index_built_) return results;
    
    std::unordered_set<uint32_t> seen;
    
    if (spatial_index_type_ == CSRSpatialIndexType::RTREE && rtree_) {
        // Convert radius to degrees (approximate)
        double deg_radius = radius_meters / 111000.0;
        CSRBox2D query_box(
            CSRPoint2D(lng - deg_radius, lat - deg_radius),
            CSRPoint2D(lng + deg_radius, lat + deg_radius)
        );
        
        std::vector<CSRRTreeValue> candidates;
        rtree_->query(bgi::intersects(query_box), std::back_inserter(candidates));
        
        for (const auto& [box, edge_id] : candidates) {
            if (seen.count(edge_id)) continue;
            seen.insert(edge_id);
            
            auto it = edge_meta_.find(edge_id);
            if (it == edge_meta_.end()) continue;
            
            double dist = point_to_line_distance(lat, lng, it->second.geometry);
            if (dist <= radius_meters) {
                results.push_back({edge_id, dist});
            }
        }
    } else {
        // H3 search
        uint64_t origin = h3_utils::latlng_to_cell(lat, lng, h3_index_res_);
        if (origin == 0) return results;
        
        int k_max = std::min(5, static_cast<int>(radius_meters / 400.0) + 1);
        
        std::vector<uint64_t> cells;
        cells.push_back(origin);
        for (int k = 1; k <= k_max; ++k) {
            auto ring = h3_utils::grid_ring(origin, k);
            cells.insert(cells.end(), ring.begin(), ring.end());
        }
        
        for (uint64_t cell : cells) {
            auto it = h3_index_.find(cell);
            if (it == h3_index_.end()) continue;
            
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
    
    // Sort by distance and limit results
    std::sort(results.begin(), results.end(),
              [](const auto& a, const auto& b) { return a.second < b.second; });
    
    if (results.size() > static_cast<size_t>(max_candidates)) {
        results.resize(max_candidates);
    }
    
    return results;
}

// ============================================================
// PATH EXPANSION
// ============================================================

std::vector<uint32_t> CSRGraph::expand_path(const std::vector<uint32_t>& shortcut_path) const {
    if (shortcut_path.size() <= 1) return shortcut_path;
    
    std::vector<uint32_t> result;
    
    std::function<void(uint32_t, uint32_t, int)> expand = [&](uint32_t u, uint32_t v, int depth) {
        if (depth > 50) {
            result.push_back(u);
            return;
        }
        
        int idx = find_shortcut_index(u, v);
        if (idx < 0 || idx >= static_cast<int>(shortcuts_.size())) {
            result.push_back(u);
            return;
        }
        
        uint32_t via = shortcuts_[idx].via_edge;
        if (via == u || via == v || via == 0) {
            result.push_back(u);
            return;
        }
        
        expand(u, via, depth + 1);
        expand(via, v, depth + 1);
    };
    
    for (size_t i = 0; i + 1 < shortcut_path.size(); ++i) {
        expand(shortcut_path[i], shortcut_path[i + 1], 0);
    }
    
    if (!shortcut_path.empty()) {
        result.push_back(shortcut_path.back());
    }
    
    return result;
}

// ============================================================
// QUERY: CLASSIC BIDIRECTIONAL DIJKSTRA
// ============================================================

CSRQueryResult CSRGraph::query_classic(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }
    
    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge not found"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge not found"};
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
            
            auto [start, end] = get_fwd_range(u);
            for (uint32_t i = start; i < end && i < shortcuts_.size(); ++i) {
                const auto& sc = shortcuts_[i];
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
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto [start, end] = get_bwd_range(u);
            for (uint32_t k = start; k < end && k < bwd_indices_.size(); ++k) {
                uint32_t idx = bwd_indices_[k];
                if (idx >= shortcuts_.size()) continue;
                
                const auto& sc = shortcuts_[idx];
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
        
        // Early termination
        if (!pq_fwd.empty() && !pq_bwd.empty()) {
            if (pq_fwd.top().dist >= best && pq_bwd.top().dist >= best) break;
        } else if (pq_fwd.empty() && pq_bwd.empty()) {
            break;
        }
    }
    
    if (!found) return {-1, {}, false, "No path found"};
    
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
    
    return {best, path, true, ""};
}

CSRQueryResult CSRGraph::query_classic_alt(
    uint32_t source_edge, 
    uint32_t target_edge,
    const std::vector<uint32_t>& penalized_nodes,
    double penalty_factor
) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }

    if (!is_valid_edge(source_edge)) {
        return {-1, {}, false, "Source edge " + std::to_string(source_edge) + " not found in graph"};
    }
    if (!is_valid_edge(target_edge)) {
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
            
            auto [start, end] = get_fwd_range(u);
            for (uint32_t i = start; i < end && i < shortcuts_.size(); ++i) {
                const auto& sc = shortcuts_[i];
                if (sc.inside != 1) continue;
                
                double cost = sc.cost;
                if (penalty_set.count(sc.to) || 
                    (sc.via_edge != 0 && penalty_set.count(sc.via_edge))) {
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
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto [start, end] = get_bwd_range(u);
            for (uint32_t k = start; k < end && k < bwd_indices_.size(); ++k) {
                uint32_t idx = bwd_indices_[k];
                if (idx >= shortcuts_.size()) continue;
                
                const auto& sc = shortcuts_[idx];
                if (sc.inside != -1 && sc.inside != 0) continue;
                
                double cost = sc.cost;
                if (penalty_set.count(sc.from) ||
                    (sc.via_edge != 0 && penalty_set.count(sc.via_edge))) {
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
        
        // Early termination
        if (!pq_fwd.empty() && !pq_bwd.empty()) {
            if (pq_fwd.top().dist >= best && pq_bwd.top().dist >= best) break;
        } else if (pq_fwd.empty() && pq_bwd.empty()) {
            break;
        }
    }
    
    if (!found) return {-1, {}, false, "No path found"};
    
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
        auto [start, end] = get_fwd_range(path[i-1]);
        for (uint32_t k = start; k < end && k < shortcuts_.size(); ++k) {
            if (shortcuts_[k].to == path[i]) {
                true_total += shortcuts_[k].cost;
                seg_found = true;
                break;
            }
        }
        if (!seg_found) return {-1, {}, false, "Path reconstruction error"};
    }
    
    return {true_total, path, true, ""};
}

CSRQueryResult CSRGraph::query_bidijkstra(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }
    
    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge not found"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge not found"};
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
    
    while (!pq_fwd.empty() && !pq_bwd.empty()) {
        if (pq_fwd.top().dist + pq_bwd.top().dist >= best) break;

        if (pq_fwd.top().dist <= pq_bwd.top().dist) {
            auto [d, u] = pq_fwd.top(); pq_fwd.pop();
            if (d > dist_fwd[u]) continue;
            
            auto [start, end] = get_fwd_range(u);
            for (uint32_t i = start; i < end && i < shortcuts_.size(); ++i) {
                const auto& sc = shortcuts_[i];
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
        } else {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            if (d > dist_bwd[u]) continue;
            
            auto [start, end] = get_bwd_range(u);
            for (uint32_t k = start; k < end && k < bwd_indices_.size(); ++k) {
                uint32_t idx = bwd_indices_[k];
                if (idx >= shortcuts_.size()) continue;
                
                const auto& sc = shortcuts_[idx];
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
    double final_cost = best;
    return {final_cost, path, true, ""};
}


// ============================================================
// QUERY: PRUNED BIDIRECTIONAL DIJKSTRA
// ============================================================

CSRQueryResult CSRGraph::query_pruned(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }
    
    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge not found"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge not found"};
    }
    
    CSRHighCell high = compute_high_cell(source_edge, target_edge);
    
    std::unordered_map<uint32_t, double> dist_fwd, dist_bwd;
    std::unordered_map<uint32_t, uint32_t> parent_fwd, parent_bwd;
    MinHeapWithRes pq_fwd, pq_bwd;
    
    auto src_meta = edge_meta_.find(source_edge);
    auto tgt_meta = edge_meta_.find(target_edge);
    int8_t src_res = (src_meta != edge_meta_.end()) ? static_cast<int8_t>(src_meta->second.lca_res) : -1;
    int8_t tgt_res = (tgt_meta != edge_meta_.end()) ? static_cast<int8_t>(tgt_meta->second.lca_res) : -1;
    
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
    double min_arrival_fwd = INF, min_arrival_bwd = INF;
    
    while (!pq_fwd.empty() || !pq_bwd.empty()) {
        // Forward step
        if (!pq_fwd.empty()) {
            auto [d, u, u_res] = pq_fwd.top(); pq_fwd.pop();
            
            auto bwd_it = dist_bwd.find(u);
            if (bwd_it != dist_bwd.end()) {
                min_arrival_fwd = std::min(dist_fwd[u], min_arrival_fwd);
                min_arrival_bwd = std::min(bwd_it->second, min_arrival_bwd);
                if (d + bwd_it->second < best) {
                    best = d + bwd_it->second;
                    meeting = u;
                    found = true;
                }
            }
            
            auto it = dist_fwd.find(u);
            if (it != dist_fwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            if (u_res < high.res) {
                min_arrival_fwd = std::min(dist_fwd[u], min_arrival_fwd);
                continue;
            }
            if (u_res == high.res) min_arrival_fwd = std::min(dist_fwd[u], min_arrival_fwd);
            
            auto [start, end] = get_fwd_range(u);
            for (uint32_t i = start; i < end && i < shortcuts_.size(); ++i) {
                const auto& sc = shortcuts_[i];
                if (sc.inside != 1) continue;
                
                double nd = d + sc.cost;
                auto v_it = dist_fwd.find(sc.to);
                if (v_it == dist_fwd.end() || nd < v_it->second) {
                    dist_fwd[sc.to] = nd;
                    parent_fwd[sc.to] = u;
                    pq_fwd.push({nd, sc.to, sc.get_res()});
                }
            }
        }
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u, u_res] = pq_bwd.top(); pq_bwd.pop();
            
            auto fwd_it = dist_fwd.find(u);
            if (fwd_it != dist_fwd.end()) {
                min_arrival_fwd = std::min(fwd_it->second, min_arrival_fwd);
                min_arrival_bwd = std::min(dist_bwd[u], min_arrival_bwd);
                if (fwd_it->second + d < best) {
                    best = fwd_it->second + d;
                    meeting = u;
                    found = true;
                }
            }
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            bool check = (u_res >= high.res);
            if (u_res == high.res || !check) min_arrival_bwd = std::min(dist_bwd[u], min_arrival_bwd);
            
            auto [start, end] = get_bwd_range(u);
            for (uint32_t k = start; k < end && k < bwd_indices_.size(); ++k) {
                uint32_t idx = bwd_indices_[k];
                if (idx >= shortcuts_.size()) continue;
                
                const auto& sc = shortcuts_[idx];
                
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
                    pq_bwd.push({nd, sc.from, sc.get_res()});
                }
            }
        }
        
        // Early termination
        if (best < INF) {
            double bound_fwd = min_arrival_fwd;
            double bound_bwd = min_arrival_bwd;
            if (!pq_fwd.empty()) bound_fwd = std::min(bound_fwd, static_cast<double>(pq_fwd.top().dist));
            if (!pq_bwd.empty()) bound_bwd = std::min(bound_bwd, static_cast<double>(pq_bwd.top().dist));
            
            bool fwd_good = !pq_fwd.empty() && (pq_fwd.top().dist + bound_bwd < best);
            bool bwd_good = !pq_bwd.empty() && (pq_bwd.top().dist + bound_fwd < best);
            if (!fwd_good && !bwd_good) break;
        }
    }
    
    if (!found) return {-1, {}, false, "No path found"};
    
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
    
    return {best, path, true, ""};
}


// ============================================================
// QUERY: UNIDIRECTIONAL PRUNED
// ============================================================

CSRQueryResult CSRGraph::query_unidirectional(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }
    
    // Validate edges
    if (!is_valid_edge(source_edge)) return {-1, {}, false, "Source edge not found"};
    if (!is_valid_edge(target_edge)) return {-1, {}, false, "Target edge not found"};
    
    CSRHighCell high = compute_high_cell(source_edge, target_edge);
    
    // Priority queue storing (dist, state)
    MinHeapWithState pq;
    
    // Map: state -> dist
    std::unordered_map<uint64_t, double> dist_map;
    // Map: state -> parent_state (for path reconstruction)
    std::unordered_map<uint64_t, uint64_t> parent_map;
    
    // Initial state: (source_edge, phase=0)
    // Packing: (edge << 4) | phase
    uint64_t start_state = (static_cast<uint64_t>(source_edge) << 4) | 0;
    
    double src_cost = 0;
    dist_map[start_state] = src_cost;
    parent_map[start_state] = start_state; // root points to self
    pq.push({src_cost, start_state});
    
    double best_dist = INF;
    uint64_t best_end_state = 0;
    bool found = false;
    
    while (!pq.empty()) {
        auto [d, curr_packed] = pq.top(); pq.pop();
        
        // Unpack state
        uint32_t u = static_cast<uint32_t>(curr_packed >> 4);
        int phase = static_cast<int>(curr_packed & 0xF); // Use 4 bits for phase just in case/consistency
        
        if (d > dist_map[curr_packed]) continue;
        if (d >= best_dist) continue;
        
        // Target check
        if (u == target_edge) {
            best_dist = d + get_edge_cost(target_edge);
            best_end_state = curr_packed;
            found = true;
            break; 
        }
        
        // Explore neighbors
        auto [start, end] = get_fwd_range(u);
        for (uint32_t i = start; i < end; ++i) {
            if (i >= shortcuts_.size()) break;
            const auto& sc = shortcuts_[i];
            
            bool allowed = false;
            int next_phase = phase;
            
            // Logic matching query_uni_lca in algorithms.py
            if (phase == 0 || phase == 1) {
                if (sc.get_res() > high.res && sc.inside == 1) { allowed = true; next_phase = 1; }
                else if (sc.get_res() <= high.res && sc.inside == 1) { allowed = true; next_phase = 2; }
                else if (sc.inside != 1) { allowed = true; next_phase = 2; }
            } else if (phase == 2) {
                if (sc.inside != 1) { allowed = true; next_phase = 3; }
            } else if (phase == 3) {
                if (sc.inside == -1) { allowed = true; next_phase = 3; }
            }
            
            if (!allowed) continue;
            
            // Relaxation
            double new_dist = d + sc.cost;
            uint64_t next_state = (static_cast<uint64_t>(sc.to) << 4) | next_phase;
            
            auto it = dist_map.find(next_state);
            if (it == dist_map.end() || new_dist < it->second) {
                dist_map[next_state] = new_dist;
                parent_map[next_state] = curr_packed;
                pq.push({new_dist, next_state});
            }
        }
    }
    
    if (!found) {
        return {-1, {}, false, "No path found"};
    }
    
    // Reconstruct path
    std::vector<uint32_t> path;
    uint64_t curr = best_end_state;
    
    while (true) {
        uint32_t u = static_cast<uint32_t>(curr >> 4);
        path.push_back(u);
        
        auto it = parent_map.find(curr);
        if (it == parent_map.end() || it->second == curr) break;
        curr = it->second;
    }
    std::reverse(path.begin(), path.end());
    
    // Add target edge cost to total (consistent with other query methods)
    double total_distance = best_dist;
    
    return {total_distance, path, true, ""};
}

CSRQueryResult CSRGraph::query_multi(
    const std::vector<uint32_t>& source_edges,
    const std::vector<double>& source_dists,
    const std::vector<uint32_t>& target_edges,
    const std::vector<double>& target_dists
) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    std::unordered_map<uint32_t, double> dist_fwd, dist_bwd;
    std::unordered_map<uint32_t, uint32_t> parent_fwd, parent_bwd;
    MinHeap pq_fwd, pq_bwd;
    
    // Initialize from all sources
    for (size_t i = 0; i < source_edges.size(); ++i) {
        uint32_t src = source_edges[i];
        if (edge_meta_.find(src) != edge_meta_.end()) {
            dist_fwd[src] = 0.0;
            parent_fwd[src] = src;
            pq_fwd.push({0.0, src});
        }
    }
    
    // Initialize from all targets
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
            
            auto [start, end] = get_fwd_range(u);
            for (uint32_t i = start; i < end && i < shortcuts_.size(); ++i) {
                const auto& sc = shortcuts_[i];
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
        
        // Backward step
        if (!pq_bwd.empty()) {
            auto [d, u] = pq_bwd.top(); pq_bwd.pop();
            
            auto it = dist_bwd.find(u);
            if (it != dist_bwd.end() && d > it->second) continue;
            if (d >= best) continue;
            
            auto [start, end] = get_bwd_range(u);
            for (uint32_t k = start; k < end && k < bwd_indices_.size(); ++k) {
                uint32_t idx = bwd_indices_[k];
                if (idx >= shortcuts_.size()) continue;
                
                const auto& sc = shortcuts_[idx];
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
        
        // Early termination
        if (!pq_fwd.empty() && !pq_bwd.empty()) {
            if (pq_fwd.top().dist >= best && pq_bwd.top().dist >= best) break;
        } else if (pq_fwd.empty() && pq_bwd.empty()) {
            break;
        }
    }
    
    if (!found) return {-1, {}, false, "No path found"};
    
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
    
    return {best, path, true, ""};
}

// ============================================================
// QUERY: NORMAL DIJKSTRA (No CH)
// ============================================================

CSRQueryResult CSRGraph::query_dijkstra(uint32_t source_edge, uint32_t target_edge) const {
    constexpr double INF = std::numeric_limits<double>::infinity();
    
    if (source_edge == target_edge) {
        return {get_edge_cost(source_edge), {source_edge}, true, ""};
    }
    
    if (edge_meta_.find(source_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Source edge not found"};
    }
    if (edge_meta_.find(target_edge) == edge_meta_.end()) {
        return {-1, {}, false, "Target edge not found"};
    }
    
    std::unordered_map<uint32_t, double> dist;
    std::unordered_map<uint32_t, uint32_t> parent;
    MinHeap pq;
    
    dist[source_edge] = 0.0;
    parent[source_edge] = source_edge;
    pq.push({0.0, source_edge});
    
    double best_dist = INF;
    bool found = false;
    
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        
        if (d > dist[u]) continue;
        
        if (u == target_edge) {
            best_dist = d;
            found = true;
            break;
        }
        
        auto [start, end] = get_fwd_range(u);
        for (uint32_t i = start; i < end && i < shortcuts_.size(); ++i) {
            const auto& sc = shortcuts_[i];
            
            double nd = d + sc.cost;
            auto it = dist.find(sc.to);
            if (it == dist.end() || nd < it->second) {
                dist[sc.to] = nd;
                parent[sc.to] = u;
                pq.push({nd, sc.to});
            }
        }
    }
    
    if (!found) {
        return {-1, {}, false, "Path not found"};
    }
    
    // Reconstruct path
    std::vector<uint32_t> path;
    uint32_t curr = target_edge;
    while (curr != source_edge) {
        path.push_back(curr);
        curr = parent[curr];
    }
    path.push_back(source_edge);
    std::reverse(path.begin(), path.end());
    
    // Add target edge cost to final distance
    double final_cost = best_dist + get_edge_cost(target_edge);
    
    return {final_cost, path, true, ""};
}
