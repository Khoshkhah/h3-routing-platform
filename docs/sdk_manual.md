---
layout: default
title: SDK Manual
nav_order: 6
---

# SDK Manual

This document is the official developer guide for the H3 Routing Platform client libraries.

## Python SDK

The Python SDK provides a high-level, asynchronous-ready interface for interacting with the routing engine.

### Installation
```bash
pip install -e sdk/python
```

### Core Client: RoutingClient
`RoutingClient(base_url="http://localhost:8082")`

#### Methods

**`route(dataset, start_lat, start_lng, end_lat, end_lng, mode="knn", algorithm="pruned")`**  
Computes a shortest path between two coordinates.  
- **Returns**: `RouteResponse` object.

**`nearest_edges(dataset, lat, lon, k=5)`**  
Finds the road segments closest to a specific location.

**`load_dataset(name, shortcuts_path, edges_path)`**  
Dynamically loads a graph into the engine memory.

**`unload_dataset(name)`**  
Frees memory by removing a dataset from the engine.

### Response Object: RouteResponse
| Field | Type | Description |
| :--- | :--- | :--- |
| `success` | bool | Boolean reflecting query status. |
| `cost` | float | Total weight (e.g. travel time). |
| `distance_meters`| float | Physical length in meters. |
| `path` | list | List of raw base edge IDs. |
| `geojson` | dict | GeoJSON LineString feature. |

## C++ SDK

A header-only lightweight client designed for integration into C++ performance-critical applications.

### Requirements
- libcurl
- nlohmann/json

### Quick Integration
```cpp
#include "routing_client.hpp"

routing::Client client("http://localhost:8082");
routing::RouteRequest req = { "vancouver", 49.2, -123.1, 49.3, -123.2 };
auto response = client.route(req);
```

### Reference: routing::RouteRequest
| Member | Type | Default |
| :--- | :--- | :--- |
| `dataset` | string | *required* |
| `start_lat`, `start_lng` | double | *required* |
| `end_lat`, `end_lng` | double | *required* |
| `mode` | string | "knn" |

---

### Memory Efficiency

The CSR engine is highly optimized for large-scale networks. 
- **Compact Storage**: Road graphs are stored in 24-byte contiguous blocks, using bitfields to minimize padding.
- **Active Reclamation**: The server aggressively releases memory back to the OS using `malloc_trim` after dataset unloads and loads.
- **Scaling**: A metropolitan area with 55M shortcuts (like Metro Vancouver) fits in approximately 1.6 GB of RSS.

---

## Error Handling

### Python
```python
response = client.route(...)
if not response.success:
    if "not loaded" in response.error:
        # Dataset not loaded
        client.load_dataset("burnaby", "/path/to/db", "/path/to/edges")
    else:
        print(f"Route failed: {response.error}")
```

### C++
```cpp
auto response = client.route(req);
if (!response.contains("success") || !response["success"]) {
    std::cerr << "Error: " << response.value("error", "Unknown") << "\n";
}
```

---

## Debug Methods

These methods are for testing and development. They provide lower-level access to the routing engine.

### `route_by_edge(dataset, source_edge, target_edge) -> Dict`

Route between two edge IDs. **Returns expanded path** (base edge IDs).
Bypasses nearest-edge lookup - useful when you already know the edge IDs.

```python
result = client.route_by_edge("burnaby", source_edge=1500, target_edge=2900)
if result["success"]:
    print(f"Path: {result['route']['path']}")  # Expanded base edges
    print(f"Distance: {result['route']['distance_meters']}m")
```

---

### `route_by_edge_raw(dataset, source_edge, target_edge) -> Dict`

Route between two edge IDs. **Returns shortcut-level path** (not expanded).
Useful for debugging the contraction hierarchy structure.

```python
result = client.route_by_edge_raw("burnaby", source_edge=1500, target_edge=2900)
if result["success"]:
    print(f"Shortcut path: {result.get('shortcut_path', [])}")
```

> **Note**: Requires `expand=False` support in C++ engine.

---

### `route_raw(dataset, start_lat, start_lng, end_lat, end_lng) -> Dict`

Route by coordinates. **Returns shortcut-level path** (not expanded).
Useful for debugging the contraction hierarchy structure.

```python
result = client.route_raw("burnaby", 49.25, -123.12, 49.28, -123.11)
if result["success"]:
    print(f"Shortcut path: {result.get('shortcut_path', [])}")
```

> **Note**: Requires `expand=False` support in C++ engine.
