# C++ Routing Engine: Deep Dive

This document explains the low-level technical architecture of the routing engine C++ backend.

## 1. The "Stateful" Server Model

Unlike a typical PHP or stateless Python script that starts up, handles one request, and dies, this C++ engine is a **Long-Running Stateful Process**.

### How it stays in memory:
1.  **Heap Allocation**: When you start the server, it allocates a massive block of RAM (the Heap).
2.  **Global Object**: There is a global object (or a long-lived object in `main()`) that holds the entire graph data structure.
3.  **Event Loop**: After loading data, the `main()` function doesn't exit. It enters an infinite loop (the HTTP Server loop provided by `Crow`), waiting for incoming TCP connections.

```cpp
// Simplified Mental Model
int main() {
   // 1. ALLOCATION: Create the graph object in memory
   ShortcutGraph graph; 
   
   // 2. LOADING: Read 100MB of parquet data into RAM
   graph.load_shortcuts("data.parquet"); 
   
   // 3. LISTEN: Enter infinite loop (blocking)
   while(true) {
       Request req = wait_for_request();
       // Graph is ALREADY in memory! Zero latency to access it.
       Response res = graph.query(req); 
       send(res);
   }
}
```

## 2. In-Memory Data Structures

The "Graph" isn't just a generic blob. It is a set of highly optimized C++ STL containers residing in RAM.

### The `ShortcutGraph` Class
This is the heart of the engine. It holds:

1.  **`shortcuts_` (Vector)**: A contiguous array of `Shortcut` structs.
    *   *Why Vector?* O(1) random access by index. CPU cache friendly.
    *   *Size*: ~20 bytes per shortcut * Millions of shortcuts.
2.  **`fwd_adj_` / `bwd_adj_` (Adjacency Lists)**: Maps an Edge ID to a list of outgoing Shortcuts.
    *   *Structure*: `vector<vector<ShortcutIndex>>` or `FlatMap`.
    *   *Purpose*: When Dijkstra is at Edge A, it asks "Where can I go?". This list answers instantly.
3.  **`shortcut_lookup_` (Hash Map)**: Maps pair `(u, v)` to a Shortcut ID.
    *   *Purpose*: Used during path expansion. "I am at u, going to v, is there a shortcut?".
4.  **`edge_meta_` (Hash Map)**: Stores metadata like Geometry (lat/lons) and H3 cells for every edge.

## 3. The Query Lifecycle (Technical)

When a request hits `http://localhost:8082/route`:

1.  **Thread Pool**: `Crow` (the web framework) assigns the request to a worker thread.
2.  **Pointer Access**: The worker thread gets a pointer to the global `dataset` object.
    *   *Note*: Since we only READ the graph during routing, multiple threads can access the same memory simultaneously without locks (Thread-Safe Reading).
3.  **Spatial Index (Bitwise Ops)**:
    *   The `H3` index is just math (bitwise operations on 64-bit integers). It's extremely fast.
    *   It converts `(lat, lon)` -> `H3 Cell ID (uint64_t)`.
    *   It looks up which edges are in that cell bucket.
### 4. Hierarchy Algorithm (Heap Operations):
    *   Uses a `std::priority_queue`.
    *   Pops an Edge ID.
    *   Accesses `fwd_adj_[edge_id]` in RAM to get neighbors.
    *   *Crucial*: No disk I/O happens here. It's all pointer chasing in RAM.
5.  **Path Expansion (Recursion)**:
    *   The result is a `vector<uint32_t>` of shortcut IDs.
    *   The `expand_path` function recursively walks this vector, looking up `via_edges` in the `shortcut_lookup_` map, and building a new vector of base edges.

## 4. Why is it fast?

1.  **Zero I/O**: The disk is touched only once (at startup).
2.  **Pre-Calculation**: Contraction Hierarchies do the hard work (scanning the whole graph) offline. The query only scans a tiny "upward" subgraph.
3.  **Data Locality**: Vectors keep data close together in memory, maximizing CPU cache hits.
4.  **Compiled Code**: C++ compiles to machine code. There is no interpreter overhead (like Python VM) for the tight loops in Dijkstra.

## 5. Spatial Index Configuration

The engine supports two spatial index types for finding the nearest edge to a coordinate:

### Index Types

| Type | Enum Value | Best For | Description |
|------|------------|----------|-------------|
| **H3** | `SpatialIndexType::H3` | Dense urban networks | Uses H3 hexagonal grid for O(1) cell lookup. Searches expanding rings around query location. |
| **R-tree** | `SpatialIndexType::RTREE` | Long highways, sparse areas | Uses Boost R-tree. Handles edges that span multiple H3 cells better. |

### Configuration Options

**1. Command Line:**
```bash
./routing_server --port 8082 --index-type rtree
./routing_server --port 8082 --index-type h3    # default
```

**2. Config File (JSON):**
```json
{
  "port": 8082,
  "index_type": "h3"
}
```

### When to Use Each

| Scenario | Recommended Index |
|----------|-------------------|
| City center with dense street grid | H3 (faster) |
| Rural/highway heavy network | R-tree (more accurate) |
| Mixed urban + highway | R-tree |

### API Response

The current index type is returned in the `/dataset-info` endpoint:
```json
{
  "name": "burnaby",
  "index_type": "h3",
  "shortcut_count": 4173086
}
```
