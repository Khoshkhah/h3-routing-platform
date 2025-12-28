/**
 * @file benchmark_memory.cpp
 * @brief Benchmark tool to compare memory usage of ShortcutGraph and CSRGraph.
 */

#include "shortcut_graph.hpp"
#include "csr_graph.hpp"

#include <iostream>
#include <fstream>
#include <unistd.h>
#include <sys/resource.h>
#include <iomanip>
#include <chrono>

// Helper to get current RSS memory usage in MB
double get_memory_usage_mb() {
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        return usage.ru_maxrss / 1024.0; // Linux: ru_maxrss is in KB
    }
    return 0.0;
}

void print_separator() {
    std::cout << std::string(60, '-') << "\n";
}

int main(int argc, char* argv[]) {
    std::string shortcuts_path;
    
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--shortcuts" && i + 1 < argc) {
            shortcuts_path = argv[++i];
        }
    }
    
    if (shortcuts_path.empty()) {
        std::cerr << "Usage: " << argv[0] << " --shortcuts <path>\n";
        return 1;
    }
    
    std::cout << "Starting Memory Benchmark\n";
    std::cout << "Target File: " << shortcuts_path << "\n";
    print_separator();
    
    double baseline_mem = get_memory_usage_mb();
    std::cout << "Baseline Memory: " << std::fixed << std::setprecision(2) << baseline_mem << " MB\n";
    print_separator();
    
    // TEST 1: Original ShortcutGraph
    /*
    {
        std::cout << "[TEST 1] Loading ShortcutGraph (OriginalMap)...\n";
        auto t0 = std::chrono::high_resolution_clock::now();
        
        ShortcutGraph* graph = new ShortcutGraph();
        if (!graph->load_shortcuts(shortcuts_path)) {
            std::cerr << "Failed to load shortcuts\n";
            return 1;
        }
        
        auto t1 = std::chrono::high_resolution_clock::now();
        double dt = std::chrono::duration<double>(t1 - t0).count();
        double current_mem = get_memory_usage_mb();
        double graph_mem = current_mem - baseline_mem;
        
        std::cout << "Loaded " << graph->shortcut_count() << " shortcuts.\n";
        std::cout << "Time: " << dt << " s\n";
        std::cout << "Total RSS: " << current_mem << " MB\n";
        std::cout << "Approx Graph Size: " << graph_mem << " MB\n";
        
        print_separator();
        
        delete graph; 
        std::cout << "Cleaned up ShortcutGraph.\n";
        double after_cleanup = get_memory_usage_mb();
        std::cout << "Memory after cleanup: " << after_cleanup << " MB (May not drop immediately due to allocator)\n";
        print_separator();
    }
    */
    
    // TEST 2: New CSRGraph
    {
        std::cout << "[TEST 2] Loading CSRGraph (Proposed)...\n";
        auto t0 = std::chrono::high_resolution_clock::now();
        
        CSRGraph* graph = new CSRGraph();
        if (!graph->load_shortcuts(shortcuts_path)) {
            std::cerr << "Failed to load shortcuts\n";
            return 1;
        }
        
        auto t1 = std::chrono::high_resolution_clock::now();
        double dt = std::chrono::duration<double>(t1 - t0).count();
        double current_mem = get_memory_usage_mb();
        
        // Note: previous cleanup might not have returned pages to OS, so comparison is tricky.
        // But the peak RSS is reliable if we assume the previous run fragmentation is reused.
        // Actually, for fairer comparison, we should probably check the difference carefully.
        // However, Linux allocators usually reuse freed memory.
        
        std::cout << "Loaded " << graph->shortcut_count() << " shortcuts.\n";
        std::cout << "Time: " << dt << " s\n";
        std::cout << "Total RSS: " << current_mem << " MB\n";
        std::cout << "Internal Structural Size: " << (graph->memory_usage() / 1024.0 / 1024.0) << " MB\n";
        
        print_separator();
        delete graph;
    }
    
    return 0;
}
