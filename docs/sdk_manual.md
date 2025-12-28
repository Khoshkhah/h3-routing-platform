# SDK Manual

This guide documents the client libraries available for interacting with the **H3 Routing Platform**.

## Python SDK

The Python SDK provides a user-friendly wrapper around the HTTP API.

### Installation

```bash
# Development mode (editable)
pip install -e sdk/python

# Or copy the module
cp -r sdk/python/h3_routing_client your_project/
```

### Quick Start

```python
from h3_routing_client import RoutingClient

client = RoutingClient(base_url="http://localhost:8082")

# Check if engine is online
health = client.health()
print(f"Status: {health['status']}")
print(f"Loaded datasets: {health['datasets_loaded']}")

# Calculate a route
response = client.route(
    dataset="burnaby",
    start_lat=49.25, start_lng=-123.12,
    end_lat=49.28, end_lng=-123.11
)

if response.success:
    print(f"Distance: {response.distance_meters} meters")
    print(f"Runtime: {response.runtime_ms} ms")
else:
    print(f"Error: {response.error}")
```

---

### API Reference

#### `RoutingClient(base_url)`

Initialize the client.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | `http://localhost:8082` | URL of the C++ Routing Engine |

---

#### `client.health() -> Dict`

Check server status and list loaded datasets.

**Returns:**
```python
{
    "status": "healthy",
    "datasets_loaded": ["burnaby", "vancouver"]
}
```

---

#### `client.route(...) -> RouteResponse`

Calculate the shortest path between two points.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset` | str | *required* | Dataset name (e.g., "burnaby") |
| `start_lat` | float | *required* | Origin latitude |
| `start_lng` | float | *required* | Origin longitude |
| `end_lat` | float | *required* | Destination latitude |
| `end_lng` | float | *required* | Destination longitude |
| `mode` | str | `"knn"` | `"knn"`, `"one_to_one"`, `"one_to_one_v2"`, `"radius"` |
| `num_candidates` | int | `3` | Edges to check at start/end |
| `algorithm` | str | `"pruned"` | `"pruned"`, `"classic"`, `"dijkstra"` |

> [!NOTE]
> **Dijkstra Mode**: While significantly slower than CH (~40x), Dijkstra mode provides an exact shortest path ground-truth by searching the entire shortcut graph without CH constraints.

**Returns `RouteResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether route was found |
| `distance` | float | Total cost (typically travel time in seconds) |
| `distance_meters` | float | Route length in meters |
| `cost` | float | Alias for `distance` |
| `runtime_ms` | float | Query time in milliseconds |
| `path` | List[int] | List of base edge IDs |
| `geojson` | Dict | GeoJSON FeatureCollection for visualization |
| `error` | str | Error message if `success=False` |

---

#### `client.load_dataset(name, shortcuts_path, edges_path) -> bool`

Dynamically load a dataset into the engine.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Unique dataset identifier |
| `shortcuts_path` | str | Absolute path to shortcuts parquet/db |
| `edges_path` | str | Absolute path to edges CSV |

**Returns:** `True` if loaded successfully.

---

#### `client.unload_dataset(name) -> bool`

Unload a dataset from engine memory.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Dataset name to unload |

**Returns:** `True` if unloaded successfully.

---

#### `client.nearest_edges(dataset, lat, lon, k=5, radius_meters=100) -> List[Dict]`

Find the nearest graph edges to a location. Useful for debugging or manual edge snapping.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset` | str | *required* | Dataset name |
| `lat` | float | *required* | Query latitude |
| `lon` | float | *required* | Query longitude |
| `k` | int | `5` | Number of edges to return |
| `radius_meters` | float | `100.0` | Maximum search radius |

**Returns:** List of edge dictionaries:
```python
[
    {"edge_id": 1502, "distance": 12.5, "length": 50.0, "cost": 50.0},
    {"edge_id": 1503, "distance": 18.2, "length": 32.0, "cost": 32.0}
]
```

**Example:**
```python
edges = client.nearest_edges("burnaby", lat=49.25, lon=-123.12, k=3)
for edge in edges:
    print(f"Edge {edge['edge_id']}: {edge['distance']:.1f}m away")
```

The C++ SDK is a lightweight header-only library using `libcurl` for HTTP requests.

### Requirements
- `libcurl` (for HTTP)
- `nlohmann/json.hpp` (for JSON parsing)

### Installation

**CMake:**
```cmake
include_directories(${PROJECT_DIR}/sdk/cpp)
target_link_libraries(my_app curl)
```

**Include:**
```cpp
#include "routing_client.hpp"
```

---

### API Reference

#### `routing::Client(base_url)`

| Parameter | Type | Default |
|-----------|------|---------|
| `base_url` | std::string | `"http://localhost:8082"` |

---

#### `routing::RouteRequest`

```cpp
struct RouteRequest {
    std::string dataset;        // Required: dataset name
    double start_lat, start_lng; // Required: origin
    double end_lat, end_lng;     // Required: destination
    std::string mode = "knn";    // Optional: "knn", "one_to_one"
};
```

---

#### `client.route(RouteRequest) -> nlohmann::json`

Sends a routing request and returns the raw JSON response.

**Example:**
```cpp
#include "routing_client.hpp"
#include <iostream>

int main() {
    routing::Client client("http://localhost:8082");

    routing::RouteRequest req;
    req.dataset = "burnaby";
    req.start_lat = 49.25;
    req.start_lng = -123.12;
    req.end_lat = 49.28;
    req.end_lng = -123.11;

    auto response = client.route(req);

    if (response.contains("success") && response["success"]) {
        auto route = response["route"];
        std::cout << "Distance: " << route["distance_meters"] << " m\n";
        std::cout << "Path edges: " << route["path"].size() << "\n";
    } else {
        std::cerr << "Error: " << response["error"] << "\n";
    }

    return 0;
}
```

**Response fields:**
- `success` (bool): Whether route found
- `route.distance` (float): Cost
- `route.distance_meters` (float): Length in meters
- `route.path` (array): Edge IDs
- `route.geojson` (object): GeoJSON geometry
- `error` (string): Error message if failed

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
