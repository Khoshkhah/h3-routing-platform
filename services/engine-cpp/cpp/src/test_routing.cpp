/**
 * @file test_routing.cpp
 * @brief Test suite validating routing against ground truth from scipy.
 * 
 * Usage:
 *   1. Generate ground truth: python scripts/generate_test_data.py ...
 *   2. Run test: ./cpp/build/test_routing --shortcuts PATH --edges PATH --truth PATH
 */

#include "shortcut_graph.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>
#include <cmath>
#include <vector>
#include <iomanip>

struct TestCase {
    uint32_t source;
    uint32_t target;
    double expected;
};

struct TestResult {
    int total = 0;
    int passed = 0;
    int mismatches = 0;
    int close_matches = 0;  // Within 1% but not exact
    double total_ms = 0;
};

std::vector<TestCase> load_test_cases(const std::string& path) {
    std::vector<TestCase> cases;
    std::ifstream file(path);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open " << path << "\n";
        return cases;
    }
    
    std::string line;
    std::getline(file, line);  // Skip header
    
    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string cell;
        std::vector<std::string> row;
        while (std::getline(ss, cell, ',')) {
            row.push_back(cell);
        }
        if (row.size() >= 3) {
            TestCase tc;
            tc.source = std::stoul(row[0]);
            tc.target = std::stoul(row[1]);
            tc.expected = std::stod(row[2]);
            cases.push_back(tc);
        }
    }
    return cases;
}

void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " [options]\n"
              << "Options:\n"
              << "  --shortcuts PATH   Path to shortcuts Parquet\n"
              << "  --edges PATH       Path to edge metadata CSV\n"
              << "  --truth PATH       Path to ground truth CSV (from generate_test_data.py)\n"
              << "  --algorithm ALG    Algorithm: classic, pruned (default: pruned)\n"
              << "  --verbose          Print each query result\n"
              << "  --help             Show this help\n";
}

int main(int argc, char* argv[]) {
    std::string shortcuts_path, edges_path, truth_path;
    std::string algorithm = "pruned";
    bool verbose = false;
    double tolerance = 0.01;  // 1% tolerance
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--shortcuts" && i + 1 < argc) {
            shortcuts_path = argv[++i];
        } else if (arg == "--edges" && i + 1 < argc) {
            edges_path = argv[++i];
        } else if (arg == "--truth" && i + 1 < argc) {
            truth_path = argv[++i];
        } else if (arg == "--algorithm" && i + 1 < argc) {
            algorithm = argv[++i];
        } else if (arg == "--verbose") {
            verbose = true;
        } else if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
    }
    
    if (shortcuts_path.empty() || edges_path.empty() || truth_path.empty()) {
        print_usage(argv[0]);
        return 1;
    }
    
    // Load graph
    ShortcutGraph graph;
    
    std::cout << "Loading shortcuts: " << shortcuts_path << "\n";
    auto t0 = std::chrono::steady_clock::now();
    if (!graph.load_shortcuts(shortcuts_path)) {
        std::cerr << "Failed to load shortcuts\n";
        return 1;
    }
    auto t1 = std::chrono::steady_clock::now();
    std::cout << "Loaded " << graph.shortcut_count() << " shortcuts in "
              << std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count() << " ms\n";
    
    std::cout << "Loading edges: " << edges_path << "\n";
    if (!graph.load_edge_metadata(edges_path)) {
        std::cerr << "Failed to load edges\n";
        return 1;
    }
    std::cout << "Loaded " << graph.edge_count() << " edges\n\n";
    
    // Load test cases
    std::cout << "Loading test cases: " << truth_path << "\n";
    auto test_cases = load_test_cases(truth_path);
    if (test_cases.empty()) {
        std::cerr << "No test cases loaded\n";
        return 1;
    }
    std::cout << "Loaded " << test_cases.size() << " test cases\n\n";
    
    // Run tests
    TestResult result;
    result.total = test_cases.size();
    
    std::cout << "Running tests with algorithm: " << algorithm << "\n";
    std::cout << std::string(50, '-') << "\n";
    
    for (const auto& tc : test_cases) {
        auto t0 = std::chrono::steady_clock::now();
        QueryResult r;
        if (algorithm == "classic") {
            r = graph.query_classic(tc.source, tc.target);
        } else {
            r = graph.query_pruned(tc.source, tc.target);
        }
        auto t1 = std::chrono::steady_clock::now();
        result.total_ms += std::chrono::duration<double, std::milli>(t1 - t0).count();
        
        double actual = r.reachable ? r.distance : -1;
        
        // Check match
        bool exact_match = false;
        bool close_match = false;
        
        if (tc.expected < 0 && actual < 0) {
            exact_match = true;  // Both unreachable
        } else if (tc.expected >= 0 && actual >= 0) {
            double diff = std::abs(actual - tc.expected);
            double rel_diff = diff / std::max(tc.expected, 0.001);
            exact_match = (diff < 0.001);
            close_match = (rel_diff < tolerance);
        }
        
        if (exact_match) {
            result.passed++;
        } else if (close_match) {
            result.close_matches++;
            if (verbose) {
                std::cout << tc.source << " -> " << tc.target 
                          << ": expected=" << tc.expected << " got=" << actual 
                          << " (close)\n";
            }
        } else {
            result.mismatches++;
            if (result.mismatches <= 20 || verbose) {
                std::cerr << "MISMATCH: " << tc.source << " -> " << tc.target 
                          << " expected=" << tc.expected << " got=" << actual << "\n";
            }
        }
    }
    
    // Print results
    std::cout << std::string(50, '=') << "\n";
    std::cout << "RESULTS:\n";
    std::cout << "  Total:          " << result.total << "\n";
    std::cout << "  Exact match:    " << result.passed 
              << " (" << std::fixed << std::setprecision(1) 
              << (100.0 * result.passed / result.total) << "%)\n";
    std::cout << "  Close match:    " << result.close_matches 
              << " (" << (100.0 * result.close_matches / result.total) << "%)\n";
    std::cout << "  Mismatches:     " << result.mismatches 
              << " (" << (100.0 * result.mismatches / result.total) << "%)\n";
    std::cout << "\n";
    std::cout << "PERFORMANCE:\n";
    std::cout << "  Total time:     " << result.total_ms << " ms\n";
    std::cout << "  Avg per query:  " << (result.total_ms / result.total) << " ms\n";
    
    int status = (result.mismatches == 0) ? 0 : 1;
    if (status == 0) {
        std::cout << "\n✓ ALL TESTS PASSED\n";
    } else {
        std::cout << "\n✗ " << result.mismatches << " TESTS FAILED\n";
    }
    
    return status;
}
