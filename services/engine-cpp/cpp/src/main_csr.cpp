/**
 * @file main_csr.cpp
 * @brief CLI entry point for CSR routing engine.
 */

#include "csr_graph.hpp"
#include <iostream>
#include <chrono>
#include <cstring>

void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " [options]\n"
              << "Options:\n"
              << "  --shortcuts PATH   Path to shortcuts Parquet directory\n"
              << "  --edges PATH       Path to edge metadata CSV\n"
              << "  --source ID        Source edge ID\n"
              << "  --target ID        Target edge ID\n"
              << "  --algorithm ALG    Algorithm: classic, pruned (default: pruned)\n"
              << "  --help             Show this help\n";
}

int main(int argc, char* argv[]) {
    std::string shortcuts_path, edges_path;
    uint32_t source = 0, target = 0;
    std::string algorithm = "pruned";
    
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--shortcuts") == 0 && i + 1 < argc) {
            shortcuts_path = argv[++i];
        } else if (std::strcmp(argv[i], "--edges") == 0 && i + 1 < argc) {
            edges_path = argv[++i];
        } else if (std::strcmp(argv[i], "--source") == 0 && i + 1 < argc) {
            source = std::stoul(argv[++i]);
        } else if (std::strcmp(argv[i], "--target") == 0 && i + 1 < argc) {
            target = std::stoul(argv[++i]);
        } else if (std::strcmp(argv[i], "--algorithm") == 0 && i + 1 < argc) {
            algorithm = argv[++i];
        } else if (std::strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        }
    }
    
    if (shortcuts_path.empty() || edges_path.empty()) {
        std::cerr << "Error: --shortcuts and --edges are required\n";
        print_usage(argv[0]);
        return 1;
    }
    
    CSRGraph graph;
    
    std::cout << "Loading shortcuts from: " << shortcuts_path << "\n";
    auto t0 = std::chrono::steady_clock::now();
    if (!graph.load_shortcuts(shortcuts_path)) {
        std::cerr << "Error: Failed to load shortcuts\n";
        return 1;
    }
    auto t1 = std::chrono::steady_clock::now();
    auto load_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
    std::cout << "Loaded " << graph.shortcut_count() << " shortcuts in " << load_ms << " ms\n";
    
    std::cout << "Loading edges from: " << edges_path << "\n";
    if (!graph.load_edge_metadata(edges_path)) {
        std::cerr << "Error: Failed to load edge metadata\n";
        return 1;
    }
    std::cout << "Loaded " << graph.edge_count() << " edges\n\n";
    
    if (source == 0 && target == 0) {
        std::cout << "No query specified. Use --source and --target.\n";
        return 0;
    }
    
    std::cout << "Query: " << source << " -> " << target << " (" << algorithm << ")\n";
    
    t0 = std::chrono::steady_clock::now();
    CSRQueryResult result;
    if (algorithm == "classic") {
        result = graph.query_classic(source, target);
    } else {
        result = graph.query_pruned(source, target);
    }
    t1 = std::chrono::steady_clock::now();
    
    auto query_us = std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count();
    
    if (result.reachable) {
        std::cout << "Distance: " << result.distance << "\n";
        std::cout << "Path length: " << result.path.size() << " edges\n";
        std::cout << "Query time: " << query_us / 1000.0 << " ms\n";
        
        std::cout << "Path: ";
        for (size_t i = 0; i < std::min(result.path.size(), size_t(10)); ++i) {
            std::cout << result.path[i];
            if (i < result.path.size() - 1) std::cout << " -> ";
        }
        if (result.path.size() > 10) std::cout << " ...";
        std::cout << "\n";
    } else {
        std::cout << "No path found\n";
        std::cout << "Query time: " << query_us / 1000.0 << " ms\n";
    }
    
    return 0;
}
