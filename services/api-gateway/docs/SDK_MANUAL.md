# Routing SDK Manual

The `routing-pipeline` project includes a Python SDK for interacting with the high-performance C++ Routing Server.

## 📦 Installation

The SDK is part of the `routing-pipeline` package. Ensure dependencies are installed:

```bash
cd routing-pipeline
pip install -r api/requirements.txt
```

## 🚀 Quick Start

### 1. Connect to the Server

Use the `CHQueryEngineFactory` to create a client connected to your running `routing-server` (default implementation uses HTTP).

```python
from api.ch_query import CHQueryEngineFactory

# Connect to local server (default port 8080)
factory = CHQueryEngineFactory(server_url="http://localhost:8080")
```

### 2. Register a Dataset

While the server handles the actual data loading, you register the dataset name in the client factory to facilitate engine creation.

```python
# Create an engine for a specific dataset
# Note: The dataset must be loaded/configured on the server side
dataset_name = "Burnaby"
factory.register_dataset(dataset_name)

engine = factory.get_engine(dataset_name)
```

### 3. Compute a Route

Use `compute_route_latlon` to find the shortest path between two coordinates. The server handles:
1.  **Map Matching**: Finding the nearest road edges to your coordinates.
2.  **Pathfinding**: Running the bidirectional Dijkstra algorithm.
3.  **Geometry**: Returning the full path geometry.

```python
result = engine.compute_route_latlon(
    start_lat=49.2827, start_lng=-122.9781,
    end_lat=49.2500, end_lng=-122.9500
)

if result.success:
    print(f"Distance: {result.distance:.1f} cost units")
    print(f"Physical Distance: {result.distance_meters:.1f} meters")
    print(f"Path: {len(result.path)} edges")
    print(f"Runtime: {result.runtime_ms:.2f} ms")
    # result.geojson contains the full LineString geometry
else:
    print(f"Error: {result.error}")
```

### 4. Search Modes

The SDK supports multiple search modes for different use cases:

```python
# KNN Mode (default): Use K nearest edges as candidates
result = engine.compute_route_latlon(
    start_lat=49.28, start_lng=-122.98,
    end_lat=49.25, end_lng=-122.95,
    search_mode="knn",
    num_candidates=5  # Try 5 nearest edges at each end
)

# Radius Mode: Find all edges within radius
result = engine.compute_route_latlon(
    start_lat=49.28, start_lng=-122.98,
    end_lat=49.25, end_lng=-122.95,
    search_mode="radius",
    search_radius=500.0  # 500 meters
)

# One-to-One Mode: Single source/target (fastest, uses classic algorithm)
result = engine.compute_route_latlon(
    start_lat=49.28, start_lng=-122.98,
    end_lat=49.25, end_lng=-122.95,
    search_mode="one_to_one"
)

# One-to-One v2: Single source/target with pruning optimization
result = engine.compute_route_latlon(
    start_lat=49.28, start_lng=-122.98,
    end_lat=49.25, end_lng=-122.95,
    search_mode="one_to_one_v2"  # Uses H3 cell pruning
)
```

### 5. Timing Breakdown

Get detailed timing information for each phase of the routing computation:

```python
result = engine.compute_route_latlon(...)

if result.timing_breakdown:
    tb = result.timing_breakdown
    print(f"Find Nearest Edges: {tb['find_nearest_us']:.0f} µs")
    print(f"CH Search: {tb['search_us']:.0f} µs")
    print(f"Path Expansion: {tb['expand_us']:.0f} µs")
    print(f"GeoJSON Build: {tb['geojson_us']:.0f} µs")
    print(f"Total: {tb['total_ms']:.2f} ms")
```

### 6. Find Nearest Edges

You can query just for the nearest road edge(s).

**Single Nearest Edge:**
```python
result = engine.find_nearest_edge(lat=49.25, lon=-122.95)
if result['success']:
    print(f"Nearest Edge: {result['edge_id']} ({result['distance_meters']:.1f}m away)")
```

**Multiple Candidates (KNN):**
```python
# Find top 5 edges within 500 meters
result = engine.find_nearest_edges(
    lat=49.25, lon=-122.95,
    radius=500.0, max_candidates=5
)
if result['success']:
    for edge in result['edges']:
        print(f"Edge {edge['id']}: {edge['distance']:.1f}m")
```

## 📚 API Reference

### `CHQueryEngineFactory`

*   `__init__(server_url: str = "http://localhost:8080")`
    *   Initialize the factory pointing to the C++ server.
    
*   `register_dataset(name: str)`
    *   Register a known dataset name.
    
*   `get_engine(name: str) -> CHQueryEngine`
    *   Get a reusable engine instance for the specified dataset. Engines are cached for performance.

*   `check_health() -> dict`
    *   Check server status and get list of loaded datasets.
    *   **Returns**: `{"status": "healthy", "datasets_loaded": [...]}`

### `CHQueryEngine`

*   `compute_route_latlon(start_lat, start_lng, end_lat, end_lng, search_mode="knn", num_candidates=3, search_radius=100.0) -> QueryResult`
    *   Computes the shortest path between two points.
    *   **Parameters**:
        - `start_lat, start_lng`: Source coordinates
        - `end_lat, end_lng`: Destination coordinates
        - `search_mode`: `"knn"`, `"radius"`, `"one_to_one"`, or `"one_to_one_v2"`
        - `num_candidates`: Number of candidate edges for KNN mode (1-10)
        - `search_radius`: Search radius in meters for radius mode
    *   **Returns**: `QueryResult` object.

*   `find_nearest_edge(lat, lon) -> dict`
    *   Find the single nearest edge to coordinates.

*   `find_nearest_edges(lat, lon, radius, max_candidates) -> dict`
    *   Find multiple nearest edges within radius.

### `QueryResult`

Data class containing the routing response.

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | True if route was found |
| `distance` | float | Route cost (optimization metric, e.g., travel time) |
| `distance_meters` | float | Physical route length in meters |
| `runtime_ms` | float | Total server-side processing time |
| `path` | List[int] | List of base Edge IDs in the path |
| `geojson` | dict | GeoJSON Feature with LineString geometry |
| `timing_breakdown` | dict | Detailed timing per phase (see below) |
| `debug` | dict | Debug info (H3 cells for source/target/high) |
| `error` | str | Error message if `success` is False |

### `timing_breakdown` Fields

| Field | Unit | Description |
|-------|------|-------------|
| `find_nearest_us` | microseconds | Time to find nearest edges for source and target |
| `search_us` | microseconds | Time for CH bidirectional search |
| `expand_us` | microseconds | Time to expand shortcuts to base edges |
| `geojson_us` | microseconds | Time to build GeoJSON geometry |
| `total_ms` | milliseconds | Total end-to-end time |
