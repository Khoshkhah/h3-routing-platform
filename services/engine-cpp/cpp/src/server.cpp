/**
 * @file server.cpp
 * @brief HTTP server for routing API using Crow framework.
 * 
 * Supports multiple named datasets, GeoJSON responses, and timing info.
 */

#include "shortcut_graph.hpp"
#include "h3_utils.hpp"
#include <crow.h>
#include <nlohmann/json.hpp>
#include <iostream>
#include <fstream>
#include <memory>
#include <chrono>
#include <mutex>

using json = nlohmann::json;

// Dataset with graph and metadata
struct Dataset {
    std::string name;
    ShortcutGraph graph;
    bool loaded = false;
};

// Global datasets map (thread-safe)
std::unordered_map<std::string, std::unique_ptr<Dataset>> g_datasets;
std::mutex g_datasets_mutex;

// Server configuration
struct ServerConfig {
    int port = 8080;
    std::string host = "0.0.0.0";
    std::string index_type = "h3";
};

ServerConfig g_config;

// Helper: Get dataset by name
Dataset* get_dataset(const std::string& name) {
    std::lock_guard<std::mutex> lock(g_datasets_mutex);
    auto it = g_datasets.find(name);
    return (it != g_datasets.end() && it->second->loaded) ? it->second.get() : nullptr;
}

// Helper: Build GeoJSON from path
json build_geojson(const Dataset& ds, const std::vector<uint32_t>& path) {
    json coords = json::array();
    
    for (uint32_t edge_id : path) {
        auto geom = ds.graph.get_edge_geometry(edge_id);
        if (geom) {
            for (const auto& [lon, lat] : *geom) {
                coords.push_back({lon, lat});
            }
        }
    }
    
    if (coords.empty()) {
        return nullptr;
    }
    
    return {
        {"type", "Feature"},
        {"geometry", {
            {"type", "LineString"},
            {"coordinates", coords}
        }},
        {"properties", {
            {"edge_count", path.size()}
        }}
    };
}

// Helper: Calculate total distance in meters from geometry
double calculate_distance_meters(const Dataset& ds, const std::vector<uint32_t>& path) {
    double total = 0.0;
    for (uint32_t edge_id : path) {
        const EdgeMeta* meta = ds.graph.get_edge_meta(edge_id);
        if (meta) {
            total += meta->length;
        }
    }
    return total;
}

// Helper: Build cell debug info with boundary
json build_cell_info(uint64_t cell) {
    if (cell == 0) return nullptr;
    
    int res = h3_utils::get_resolution(cell);
    auto boundary = h3_utils::cell_boundary(cell);
    
    json boundary_json = json::array();
    for (const auto& [lat, lon] : boundary) {
        // GeoJSON format: [lon, lat]
        boundary_json.push_back({lon, lat});
    }
    
    return {
        {"id", cell},
        {"res", res},
        {"boundary", boundary_json}
    };
}

// Helper: Point struct
struct Point { double lat, lon; };

// Helper: Squared distance
double distSq(Point p1, Point p2) {
    double dLat = p1.lat - p2.lat;
    double dLon = p1.lon - p2.lon;
    return dLat*dLat + dLon*dLon;
}

// Helper: Project point onto segment
Point project_on_segment(Point p, Point a, Point b) {
    double l2 = distSq(a, b);
    if (l2 == 0) return a;
    double t = ((p.lat - a.lat) * (b.lat - a.lat) + (p.lon - a.lon) * (b.lon - a.lon)) / l2;
    t = std::max(0.0, std::min(1.0, t));
    return {a.lat + t * (b.lat - a.lat), a.lon + t * (b.lon - a.lon)};
}

// Helper: Trim GeoJSON coordinates based on start/end points
json trim_geojson_coords(const json& original_coords, double start_lat, double start_lon, double end_lat, double end_lon) {
    if (!original_coords.is_array() || original_coords.empty()) return original_coords;
    
    std::vector<Point> points;
    for (const auto& p : original_coords) {
        points.push_back({p[1], p[0]}); // GeoJSON is [lon, lat]
    }
    
    if (points.size() < 2) return original_coords;
    
    // Trim Start
    Point start_target = {start_lat, start_lon};
    size_t start_idx = 0;
    Point new_start = points[0];
    double min_start_dist = -1.0;
    
    // Look at first few segments (e.g. first 50 points or full first edge)
    // Since we don't know edge boundaries here, we scan until we find a reasonable projection?
    // Actually, simply finding the closest point on the ENTIRE path might be risky (loops).
    // Let's assume the user is near the START of the path.
    // Scan first 100 segments or 10% of path?
    size_t scan_limit = std::min((size_t)100, points.size() - 1);
    
    for (size_t i = 0; i < scan_limit; ++i) {
        Point p = project_on_segment(start_target, points[i], points[i+1]);
        double d = distSq(start_target, p);
        if (min_start_dist < 0 || d < min_start_dist) {
            min_start_dist = d;
            new_start = p;
            start_idx = i;
        }
    }
    
    // Trim End
    Point end_target = {end_lat, end_lon};
    size_t end_idx = points.size() - 1;
    Point new_end = points.back();
    double min_end_dist = -1.0;
    
    size_t end_scan_start = (points.size() > 100) ? points.size() - 100 : 0;
    // ensure end_scan_start is after start_idx? Not strictly necessary if path is long.
    
    for (size_t i = end_scan_start; i < points.size() - 1; ++i) {
        Point p = project_on_segment(end_target, points[i], points[i+1]);
        double d = distSq(end_target, p);
        if (min_end_dist < 0 || d < min_end_dist) {
            min_end_dist = d;
            new_end = p;
            end_idx = i; // Segment index
        }
    }
    
    // Rebuild coords
    json new_coords = json::array();
    
    // Start Point
    new_coords.push_back({new_start.lon, new_start.lat});
    
    // Middle Points
    // We keep points from start_idx + 1 up to end_idx
    // If start_idx == end_idx, we just add start and end points (segment replacement)
    for (size_t i = start_idx + 1; i <= end_idx; ++i) {
         if (i < points.size()) { // endpoint of segment i-1 is points[i]
             // Wait, segment i is points[i] to points[i+1].
             // We want to keep vertices BETWEEN the cut points.
             // If we cut segment 0 at t=0.5. We output new_start.
             // Next vertex is points[1].
             new_coords.push_back({points[i].lon, points[i].lat});
         }
    }
    
    // End Point
    // Check if new_end is different from last added point to avoid duplicates?
    // For simplicity, just add it.
    new_coords.push_back({new_end.lon, new_end.lat});
    
    return new_coords;
}

bool load_dataset(const std::string& name, const std::string& shortcuts_path, const std::string& edges_path) {
    std::cout << "Loading dataset '" << name << "'...\n";
    
    auto ds = std::make_unique<Dataset>();
    ds->name = name;
    
    std::cout << "  Shortcuts: " << shortcuts_path << "\n";
    if (!ds->graph.load_shortcuts(shortcuts_path)) {
        std::cerr << "  Failed to load shortcuts\n";
        return false;
    }
    
    std::cout << "  Edges: " << edges_path << "\n";
    if (!ds->graph.load_edge_metadata(edges_path)) {
        std::cerr << "  Failed to load edge metadata\n";
        return false;
    }
    
    std::cout << "  Building spatial index (" << g_config.index_type << ")...\n";
    if (g_config.index_type == "rtree") {
        ds->graph.build_spatial_index(SpatialIndexType::RTREE);
    } else {
        ds->graph.build_spatial_index(SpatialIndexType::H3);
    }
    
    ds->loaded = true;
    
    {
        std::lock_guard<std::mutex> lock(g_datasets_mutex);
        g_datasets[name] = std::move(ds);
    }
    
    std::cout << "  Dataset '" << name << "' loaded successfully\n";
    return true;
}

#ifdef HAVE_DUCKDB
// Load dataset from consolidated DuckDB database
bool load_dataset_duckdb(const std::string& name, const std::string& db_path) {
    std::cout << "Loading dataset '" << name << "' from DuckDB...\n";
    std::cout << "  Database: " << db_path << "\n";
    
    auto ds = std::make_unique<Dataset>();
    ds->name = name;
    
    if (!ds->graph.load_from_duckdb(db_path)) {
        std::cerr << "  Failed to load from DuckDB\n";
        return false;
    }
    
    std::cout << "  Building spatial index (" << g_config.index_type << ")...\n";
    if (g_config.index_type == "rtree") {
        ds->graph.build_spatial_index(SpatialIndexType::RTREE);
    } else {
        ds->graph.build_spatial_index(SpatialIndexType::H3);
    }
    
    ds->loaded = true;
    
    {
        std::lock_guard<std::mutex> lock(g_datasets_mutex);
        g_datasets[name] = std::move(ds);
    }
    
    std::cout << "  Dataset '" << name << "' loaded successfully from DuckDB\n";
    return true;
}
#endif

// Unload dataset by name
bool unload_dataset(const std::string& name) {
    std::lock_guard<std::mutex> lock(g_datasets_mutex);
    auto it = g_datasets.find(name);
    if (it != g_datasets.end()) {
        g_datasets.erase(it);
        std::cout << "Dataset '" << name << "' unloaded\n";
        return true;
    }
    return false;
}

// Get list of loaded datasets
std::vector<std::string> get_loaded_datasets() {
    std::lock_guard<std::mutex> lock(g_datasets_mutex);
    std::vector<std::string> names;
    for (const auto& [name, ds] : g_datasets) {
        if (ds->loaded) names.push_back(name);
    }
    return names;
}

// Load config from JSON file
bool load_config(const std::string& config_path) {
    std::ifstream file(config_path);
    if (!file) {
        std::cerr << "Config file not found: " << config_path << "\n";
        return false;
    }
    
    try {
        json config = json::parse(file);
        
        // Server settings
        if (config.contains("port")) g_config.port = config["port"];
        if (config.contains("host")) g_config.host = config["host"];
        if (config.contains("index_type")) g_config.index_type = config["index_type"];
        
        // Load datasets
        if (config.contains("datasets")) {
            for (const auto& ds : config["datasets"]) {
                std::string name = ds.value("name", "");
                std::string shortcuts = ds.value("shortcuts_path", "");
                std::string edges = ds.value("edges_path", "");
                
                if (!name.empty() && !shortcuts.empty() && !edges.empty()) {
                    load_dataset(name, shortcuts, edges);
                }
            }
        }
        
        std::cout << "Loaded config from: " << config_path << "\n";
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Error parsing config: " << e.what() << "\n";
        return false;
    }
}

int main(int argc, char* argv[]) {
    std::cout << "=== Routing Engine HTTP Server ===\n\n";
    
    // Parse command line args
    std::string initial_name, initial_shortcuts, initial_edges;
    std::string initial_db_path;
    std::string config_path = "config/server.json";  // Default config path
    bool use_config = false;
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            g_config.port = std::stoi(argv[++i]);
        } else if (arg == "--config" && i + 1 < argc) {
            config_path = argv[++i];
            use_config = true;
        } else if (arg == "--db" && i + 1 < argc) {
            initial_db_path = argv[++i];
        } else if (arg == "--shortcuts" && i + 1 < argc) {
            initial_shortcuts = argv[++i];
        } else if (arg == "--edges" && i + 1 < argc) {
            initial_edges = argv[++i];
        } else if (arg == "--name" && i + 1 < argc) {
            initial_name = argv[++i];
        } else if (arg == "--index" && i + 1 < argc) {
            g_config.index_type = argv[++i];
        } else if (arg == "--help") {
            std::cout << "Usage: routing_server [options]\n"
                      << "  --config PATH      Config file (default: config/server.json)\n"
                      << "  --port PORT        Server port (default: 8080)\n"
                      << "  --db PATH          DuckDB database file (preferred)\n"
                      << "  --shortcuts PATH   Shortcuts Parquet directory (legacy)\n"
                      << "  --edges PATH       Edges CSV file (legacy)\n"
                      << "  --name NAME        Dataset name (default: 'default')\n"
                      << "  --index TYPE       Spatial index: h3 or rtree (default: h3)\n";
            return 0;
        }
    }
    
    // Only load config if explicitly specified with --config
    if (use_config) {
        std::ifstream config_check(config_path);
        if (config_check.good()) {
            config_check.close();
            load_config(config_path);
        }
    }
    
    // Load dataset from DuckDB (preferred) or files (legacy)
    if (initial_name.empty()) initial_name = "default";
    
#ifdef HAVE_DUCKDB
    if (!initial_db_path.empty()) {
        load_dataset_duckdb(initial_name, initial_db_path);
    } else
#endif
    if (!initial_shortcuts.empty() && !initial_edges.empty()) {
        load_dataset(initial_name, initial_shortcuts, initial_edges);
    }
    
    // Create Crow app
    crow::SimpleApp app;
    
    // ============================================================
    // HEALTH ENDPOINT
    // ============================================================
    CROW_ROUTE(app, "/health")([]() {
        json response = {
            {"status", "healthy"},
            {"datasets_loaded", get_loaded_datasets()}
        };
        return crow::response(200, response.dump());
    });
    
    // ============================================================
    // LOAD DATASET
    // ============================================================
    CROW_ROUTE(app, "/load_dataset").methods("POST"_method)([](const crow::request& req) {
        try {
            auto body = json::parse(req.body);
            std::string name = body.value("dataset", body.value("name", "default"));
            
#ifdef HAVE_DUCKDB
            // Prefer DuckDB path if provided
            std::string db_path = body.value("db_path", "");
            if (!db_path.empty()) {
                bool success = load_dataset_duckdb(name, db_path);
                json response = {
                    {"success", success},
                    {"dataset", name},
                    {"source", "duckdb"}
                };
                return crow::response(success ? 200 : 500, response.dump());
            }
#endif
            
            // Fallback to separate files
            std::string shortcuts = body.value("shortcuts_path", "");
            std::string edges = body.value("edges_path", "");
            
            if (shortcuts.empty() || edges.empty()) {
                return crow::response(400, R"({"success": false, "error": "db_path or (shortcuts_path + edges_path) required"})");
            }
            
            bool success = load_dataset(name, shortcuts, edges);
            json response = {
                {"success", success},
                {"dataset", name},
                {"source", "files"}
            };
            return crow::response(success ? 200 : 500, response.dump());
            
        } catch (const std::exception& e) {
            json response = {{"success", false}, {"error", e.what()}};
            return crow::response(400, response.dump());
        }
    });
    
    // ============================================================
    // UNLOAD DATASET
    // ============================================================
    CROW_ROUTE(app, "/unload_dataset").methods("POST"_method)([](const crow::request& req) {
        try {
            auto body = json::parse(req.body);
            std::string name = body.value("dataset", body.value("name", ""));
            
            if (name.empty()) {
                return crow::response(400, R"({"success": false, "error": "dataset name required"})");
            }
            
            bool was_loaded = unload_dataset(name);
            json response = {
                {"success", true},
                {"dataset", name},
                {"was_loaded", was_loaded}
            };
            return crow::response(200, response.dump());
            
        } catch (const std::exception& e) {
            json response = {{"success", false}, {"error", e.what()}};
            return crow::response(400, response.dump());
        }
    });
    
#ifdef HAVE_DUCKDB
    // ============================================================
    // GET BOUNDARY - Return dataset boundary as GeoJSON
    // ============================================================
    CROW_ROUTE(app, "/boundary").methods("GET"_method)([](const crow::request& req) {
        try {
            std::string dataset_name = req.url_params.get("dataset") ? req.url_params.get("dataset") : "default";
            
            Dataset* ds = get_dataset(dataset_name);
            if (!ds) {
                return crow::response(404, R"({"error": "Dataset not found"})");
            }
            
            std::string boundary = ds->graph.get_dataset_info("boundary_geojson");
            if (boundary.empty()) {
                return crow::response(404, R"({"error": "No boundary GeoJSON stored for this dataset"})");
            }
            
            // Return raw GeoJSON
            auto resp = crow::response(200, boundary);
            resp.set_header("Content-Type", "application/geo+json");
            return resp;
            
        } catch (const std::exception& e) {
            json response = {{"error", e.what()}};
            return crow::response(500, response.dump());
        }
    });
#endif
    
    // ============================================================
    // NEAREST EDGES - Return KNN candidate edges for a location
    // ============================================================
    CROW_ROUTE(app, "/nearest_edges").methods("GET"_method, "POST"_method)([](const crow::request& req) {
        try {
            std::string dataset_name;
            double lat, lng;
            int k = 5;
            
            if (req.method == "GET"_method) {
                dataset_name = req.url_params.get("dataset") ? req.url_params.get("dataset") : "default";
                lat = req.url_params.get("lat") ? std::stod(req.url_params.get("lat")) : 0;
                lng = req.url_params.get("lon") ? std::stod(req.url_params.get("lon")) : 0;
                k = req.url_params.get("k") ? std::stoi(req.url_params.get("k")) : 5;
            } else {
                auto body = json::parse(req.body);
                dataset_name = body.value("dataset", "default");
                lat = body.value("lat", 0.0);
                lng = body.value("lon", 0.0);
                k = body.value("k", 5);
            }
            
            Dataset* ds = get_dataset(dataset_name);
            if (!ds) {
                return crow::response(404, R"({"error": "Dataset not found"})");
            }
            
            // Get nearest edges
            auto edges = ds->graph.find_nearest_edges(lat, lng, k);
            
            json result = json::array();
            for (const auto& [edge_id, dist] : edges) {
                const EdgeMeta* meta = ds->graph.get_edge_meta(edge_id);
                json edge_info = {
                    {"edge_id", edge_id},
                    {"distance", dist}
                };
                if (meta) {
                    edge_info["cost"] = meta->cost;
                    edge_info["length"] = meta->length;
                    edge_info["to_cell"] = meta->to_cell;
                    edge_info["from_cell"] = meta->from_cell;
                    edge_info["lca_res"] = meta->lca_res;
                }
                result.push_back(edge_info);
            }
            
            json response = {
                {"dataset", dataset_name},
                {"lat", lat},
                {"lon", lng},
                {"k", k},
                {"edges", result},
                {"index_type", ds->graph.has_spatial_index() ? "h3" : "none"}
            };
            
            return crow::response(200, response.dump());
            
        } catch (const std::exception& e) {
            json response = {{"error", e.what()}};
            return crow::response(400, response.dump());
        }
    });
    
    // ============================================================
    // ROUTE (coordinates) - GET and POST
    // ============================================================
    auto handle_route = [](const crow::request& req) {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        try {
            std::string dataset_name;
            double start_lat, start_lng, end_lat, end_lng;
            int max_candidates = 5;
            double radius = 500.0;
            std::string algorithm = "pruned";
            std::string mode = "knn";
            
            if (req.method == "GET"_method) {
                // GET parameters
                dataset_name = req.url_params.get("dataset") ? req.url_params.get("dataset") : "default";
                start_lat = req.url_params.get("source_lat") ? std::stod(req.url_params.get("source_lat")) :
                           (req.url_params.get("start_lat") ? std::stod(req.url_params.get("start_lat")) : 0);
                start_lng = req.url_params.get("source_lon") ? std::stod(req.url_params.get("source_lon")) :
                           (req.url_params.get("start_lng") ? std::stod(req.url_params.get("start_lng")) : 0);
                end_lat = req.url_params.get("target_lat") ? std::stod(req.url_params.get("target_lat")) :
                         (req.url_params.get("end_lat") ? std::stod(req.url_params.get("end_lat")) : 0);
                end_lng = req.url_params.get("target_lon") ? std::stod(req.url_params.get("target_lon")) :
                         (req.url_params.get("end_lng") ? std::stod(req.url_params.get("end_lng")) : 0);
                if (req.url_params.get("num_candidates")) max_candidates = std::stoi(req.url_params.get("num_candidates"));
                if (req.url_params.get("max_candidates")) max_candidates = std::stoi(req.url_params.get("max_candidates"));
                if (req.url_params.get("search_radius")) radius = std::stod(req.url_params.get("search_radius"));
                if (req.url_params.get("search_mode")) mode = req.url_params.get("search_mode");
            } else {
                // POST body
                auto body = json::parse(req.body);
                dataset_name = body.value("dataset", "default");
                start_lat = body.value("start_lat", body.value("source_lat", 0.0));
                start_lng = body.value("start_lng", body.value("source_lon", 0.0));
                end_lat = body.value("end_lat", body.value("target_lat", 0.0));
                end_lng = body.value("end_lng", body.value("target_lon", 0.0));
                max_candidates = body.value("max_candidates", body.value("num_candidates", 5));
                radius = body.value("search_radius", body.value("radius", 500.0));
                algorithm = body.value("algorithm", "pruned");
                mode = body.value("mode", body.value("search_mode", "knn"));
            }
            
            // Check expand param (default true for backward compatibility)
            bool expand_path = true;
            if (req.method == "POST"_method) {
                auto body = json::parse(req.body);
                expand_path = body.value("expand", true);
            }
            
            Dataset* ds = get_dataset(dataset_name);
            if (!ds) {
                json response = {{"success", false}, {"error", "Dataset '" + dataset_name + "' not loaded"}};
                return crow::response(503, response.dump());
            }
            
            // Timing: Find nearest edges
            auto t_nearest_start = std::chrono::high_resolution_clock::now();
            auto start_edges = ds->graph.find_nearest_edges(start_lat, start_lng, max_candidates, radius);
            auto end_edges = ds->graph.find_nearest_edges(end_lat, end_lng, max_candidates, radius);
            auto t_nearest_end = std::chrono::high_resolution_clock::now();
            double nearest_us = std::chrono::duration<double, std::micro>(t_nearest_end - t_nearest_start).count();
            
            if (start_edges.empty()) {
                return crow::response(400, R"({"success": false, "error": "No edges found near start"})");
            }
            if (end_edges.empty()) {
                return crow::response(400, R"({"success": false, "error": "No edges found near end"})");
            }
            
            // Timing: CH search
            auto t_search_start = std::chrono::high_resolution_clock::now();
            QueryResult result;
            if (mode == "one_to_one" || mode == "one_to_one_v2") {
                // one_to_one modes use single source/target query
                uint32_t source = start_edges[0].first;
                uint32_t target = end_edges[0].first;
                // one_to_one = classic, one_to_one_v2 = pruned
                if (mode == "one_to_one_v2" || algorithm == "pruned") {
                    result = ds->graph.query_pruned(source, target);
                } else if (algorithm == "unidirectional") {
                    result = ds->graph.query_unidirectional(source, target);
                } else if (algorithm == "bidijkstra") {
                    result = ds->graph.query_bidijkstra(source, target);
                } else {
                    result = ds->graph.query_classic(source, target);
                }
            } else {
                // KNN/radius modes always use multi-source/target query
                std::vector<uint32_t> sources, targets;
                std::vector<double> src_dists, tgt_dists;
                for (const auto& [eid, dist] : start_edges) {
                    sources.push_back(eid);
                    src_dists.push_back(dist);
                }
                for (const auto& [eid, dist] : end_edges) {
                    targets.push_back(eid);
                    tgt_dists.push_back(dist);
                }
                result = ds->graph.query_multi(sources, src_dists, targets, tgt_dists);
            }
            auto t_search_end = std::chrono::high_resolution_clock::now();
            double search_us = std::chrono::duration<double, std::micro>(t_search_end - t_search_start).count();
            
            auto end_time = std::chrono::high_resolution_clock::now();
            double runtime_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
            
            json response;
            if (result.reachable) {
                // Get source/target edges for debug info
                uint32_t source_edge = start_edges[0].first;
                uint32_t target_edge = end_edges[0].first;
                
                // Helper: resolve cell at proper resolution (matching routing-server)
                auto resolve_cell = [&ds](uint32_t edge_id) -> std::pair<uint64_t, int> {
                    const EdgeMeta* meta = ds->graph.get_edge_meta(edge_id);
                    if (!meta) return {0, -1};
                    
                    uint64_t cell = meta->to_cell;
                    if (cell == 0) cell = meta->from_cell;
                    
                    int res = meta->lca_res;
                    if (res == -1) res = 8;  // Default to res 8
                    
                    // Reduce cell to target resolution if needed
                    if (cell != 0 && h3_utils::get_resolution(cell) > res) {
                        cell = h3_utils::cell_to_parent(cell, res);
                    }
                    
                    return {cell, res};
                };
                
                auto [src_cell, src_res] = resolve_cell(source_edge);
                auto [tgt_cell, tgt_res] = resolve_cell(target_edge);
                
                // Compute high cell using graph's method
                HighCell high = ds->graph.compute_high_cell(source_edge, target_edge);
                
                // Conditionally expand path based on expand param
                std::vector<uint32_t> expanded_path;
                json geojson = nullptr;
                double expand_us = 0.0;
                double geojson_us = 0.0;
                double distance_meters = 0.0;
                
                if (expand_path) {
                    // Timing: Expand shortcut path to base edges
                    auto t_expand_start = std::chrono::high_resolution_clock::now();
                    expanded_path = ds->graph.expand_path(result.path);
                    auto t_expand_end = std::chrono::high_resolution_clock::now();
                    expand_us = std::chrono::duration<double, std::micro>(t_expand_end - t_expand_start).count();
                    
                    // Timing: Build GeoJSON
                    auto t_geojson_start = std::chrono::high_resolution_clock::now();
                    geojson = build_geojson(*ds, expanded_path);
                    
                    // Trim GeoJSON to match query coordinates
                    if (geojson != nullptr && geojson.contains("geometry")) {
                        auto trimmed = trim_geojson_coords(geojson["geometry"]["coordinates"], start_lat, start_lng, end_lat, end_lng);
                        geojson["geometry"]["coordinates"] = trimmed;
                    }
                    
                    auto t_geojson_end = std::chrono::high_resolution_clock::now();
                    geojson_us = std::chrono::duration<double, std::micro>(t_geojson_end - t_geojson_start).count();
                    distance_meters = calculate_distance_meters(*ds, expanded_path);
                }
                
                response["success"] = true;
                response["dataset"] = dataset_name;
                response["route"] = {
                    {"distance", result.distance},
                    {"distance_meters", distance_meters},
                    {"runtime_ms", runtime_ms},
                    {"path", expand_path ? json(expanded_path) : json(nullptr)},
                    {"shortcut_path", result.path},
                    {"geojson", geojson}
                };
                response["timing_breakdown"] = {
                    {"find_nearest_us", nearest_us},
                    {"search_us", search_us},
                    {"expand_us", expand_us},
                    {"geojson_us", geojson_us},
                    {"total_ms", runtime_ms}
                };
                response["debug"] = {
                    {"cells", {
                        {"source", build_cell_info(src_cell)},
                        {"target", build_cell_info(tgt_cell)},
                        {"high", build_cell_info(high.cell)}
                    }}
                };
            } else {
                response["success"] = false;
                response["error"] = "No path found";
                response["runtime_ms"] = runtime_ms;
            }
            
            return crow::response(200, response.dump());
            
        } catch (const std::exception& e) {
            json response = {{"success", false}, {"error", e.what()}};
            return crow::response(400, response.dump());
        }
    };
    
    CROW_ROUTE(app, "/route").methods("GET"_method, "POST"_method)(handle_route);
    
    // ============================================================
    // ROUTE BY EDGE IDs
    // ============================================================
    CROW_ROUTE(app, "/route_by_edge").methods("POST"_method)([](const crow::request& req) {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        try {
            auto body = json::parse(req.body);
            std::string dataset_name = body.value("dataset", "default");
            uint32_t source = body["source_edge"];
            uint32_t target = body["target_edge"];
            std::string algorithm = body.value("algorithm", "pruned");
            
            Dataset* ds = get_dataset(dataset_name);
            if (!ds) {
                json response = {{"success", false}, {"error", "Dataset '" + dataset_name + "' not loaded"}};
                return crow::response(503, response.dump());
            }
            
            QueryResult result;
            if (algorithm == "classic") {
                result = ds->graph.query_classic(source, target);
            } else if (algorithm == "unidirectional") {
                result = ds->graph.query_unidirectional(source, target);
            } else {
                result = ds->graph.query_pruned(source, target);
            }
            
            auto end_time = std::chrono::high_resolution_clock::now();
            double runtime_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
            
            json response;
            if (result.reachable) {
                // Expand shortcut path to base edges
                auto expanded_path = ds->graph.expand_path(result.path);
                
                response["success"] = true;
                response["route"] = {
                    {"distance", result.distance},
                    {"distance_meters", calculate_distance_meters(*ds, expanded_path)},
                    {"runtime_ms", runtime_ms},
                    {"path", expanded_path},
                    {"shortcut_path", result.path},
                    {"geojson", build_geojson(*ds, expanded_path)}
                };
            } else {
                response["success"] = false;
                response["error"] = "No path found";
                response["runtime_ms"] = runtime_ms;
            }
            
            return crow::response(200, response.dump());
            
        } catch (const std::exception& e) {
            json response = {{"success", false}, {"error", e.what()}};
            return crow::response(400, response.dump());
        }
    });
    
    std::cout << "\nStarting server on " << g_config.host << ":" << g_config.port << "\n";
    app.port(g_config.port).bindaddr(g_config.host).multithreaded().run();
    
    return 0;
}
