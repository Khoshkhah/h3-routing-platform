# H3 Routing Engine: Optimized CSR Data Structure

This document describes the memory-optimized **Compressed Sparse Row (CSR)** architecture used in the C++ routing engine. These optimizations allow the engine to handle massive road networks (e.g., 55M+ shortcuts) with a minimal memory footprint.

## 1. Core CSR Layout

The graph is stored using a standard forward and backward CSR representation. This layout eliminates the need for expensive adjacency lists (vectors of vectors) or hash maps for edge discovery.

*   **`shortcuts_`**: A single contiguous `std::vector<CSRShortcut>` containing all edges and shortcuts.
*   **`fwd_offsets_`**: Indices into `shortcuts_`, where `fwd_offsets_[u]` to `fwd_offsets_[u+1]` define the range of outgoing edges from node `u`.
*   **`bwd_offsets_` / `bwd_indices_`**: Similar mapping for incoming edges, used during bidirectional search.

## 2. CSRShortcut Compaction (24-Byte Struct)

The `CSRShortcut` struct is the most numerous object in memory. It has been manually packed and aligned to exactly **24 bytes**.

| Field | Type | Size | Notes |
| :--- | :--- | :--- | :--- |
| `cell` | `uint64_t` | 8B | H3 Index (contains resolution in top bits) |
| `cost` | `float` | 4B | 32-bit precision for travel time/weight |
| `from` | `uint32_t` | 4B | Source edge ID |
| `to` | `uint32_t` | 4B | Target edge ID |
| `via_edge` | `bitfield` | 30 bits | Parent edge ID for path expansion |
| `inside` | `bitfield` | 2 bits | Query constraint: -1 (entry), 0 (core), 1 (exit) |

### Key Optimizations:
- **Bitfield Packing**: `via_edge` and `inside` share a single 32-bit word.
- **On-the-fly Resolution**: Redundant `cell_res` field was removed. The resolution is extracted from the H3 index using `get_res()` (shifting the top bits), saving 1-4 bytes per struct across 55M objects.
- **Float Precision**: Switching `cost` from `double` to `float` allowed the struct to fit within a 24-byte alignment boundary (avoiding 8 bytes of compiler padding).

## 3. Map Removal & Local Scanning

A major memory bottleneck (consuming ~2.6 GB for Vancouver) was the global endpoint lookup map. This map was replaced by a **Local Linear Scan**.

Because CSR stores neighbors contiguously:
1.  We look up the source edge `u` in `fwd_offsets_`.
2.  We perform a simple `for` loop over the small range of neighbors (typically 2-10).
3.  Since these neighbors are contiguous in memory, they are pulled into the **CPU L1 Cache** in a single fetch, making the scan faster than a hash map lookup in most real-world scenarios due to reduced "cache misses."

## 4. Memory Reclamation

To combat heap fragmentation and OS caching:
*   **`malloc_trim(0)`**: Called immediately after loading and unloading datasets. This forces the GLIBC allocator to release free pages back to the kernel.
*   **`shrink_to_fit()`**: Extensively used on geometry vectors and temporary loading structures to minimize peak Resident Set Size (RSS).

## 5. Performance Metrics

| Metric | Legacy Engine | CSR (Optimized) | Improvement |
| :--- | :--- | :--- | :--- |
| **Vancouver Memory** | 7.45 GB | **1.64 GB** | **78% Reduction** |
| **Vancouver Load Time**| ~120 s | **~15 s** | **8x Faster** |
| **Lookup Speed** | Hash Map | local L1 Cache Scan | Lower Latency |
