# Routing Engine API Reference

This document details the HTTP endpoints exposed by the C++ Routing Engine (default port: `8082`).

## Base URL
`http://localhost:8082`

---

## 1. Health Check
**Endpoint**: `GET /health`
*   **Description**: Checks server status and lists loaded datasets.
*   **Usage**: Used by Python middleware to wait for server readiness.

### Response
```json
{
  "status": "healthy",
  "datasets_loaded": ["burnaby", "vancouver"]
}
```

---

## 2. Route (Coordinates)
**Endpoint**: `POST /route`
*   **Description**: Finds the shortest path between two coordinate pairs using the full pipeline (Index Lookup -> CH Query -> Path Expansion -> GeoJSON).

### Request
```json
{
  "dataset": "burnaby",
  "start_lat": 49.246292,
  "start_lng": -123.116226,
  "end_lat": 49.262292,
  "end_lng": -123.126226,
  "mode": "knn",           // "knn", "radius", "one_to_one"
  "num_candidates": 3,     // Edges to consider near start/end
  "algorithm": "pruned"    // "pruned" (default) or "classic"
}
```

### Response
```json
{
  "success": true,
  "dataset": "burnaby",
  "route": {
    "distance": 845.2,         // Total cost
    "distance_meters": 845.2,  // Metric length
    "runtime_ms": 1.2,
    "path": [101, 102, 103],   // Base Edge IDs
    "geojson": { ... }         // FeatureCollection LineString
  },
  "timing_breakdown": {
    "find_nearest_us": 45.0,
    "search_us": 250.0,
    "expand_us": 15.0,
    "geojson_us": 20.0
  }
}
```

---

## 3. Nearest Edges
**Endpoint**: `GET /nearest_edges`
*   **Description**: Finds graph edges closest to a location. Useful for debugging or snapping.

### Parameters
*   `lat`, `lon`: Coordinates
*   `k`: Number of edges to return (default: 5)
*   `dataset`: Dataset name

### Response
```json
{
  "edges": [
    {
      "edge_id": 1502,
      "distance": 12.5,  // Meters from query point
      "length": 50.0,    // Edge length
      "cost": 50.0
    }
  ]
}
```

---

## 4. Load Dataset
**Endpoint**: `POST /load_dataset`
*   **Description**: Trigger the engine to load a new dataset from disk into memory.

### Request
```json
{
  "dataset": "new_city",
  "shortcuts_path": "/abs/path/to/shortcuts.parquet",
  "edges_path": "/abs/path/to/edges.csv"
}
```

---

## 6. Unload Dataset
**Endpoint**: `POST /unload_dataset`
*   **Description**: Free up memory by unloading a dataset.

### Request
```json
{
  "dataset": "dataset_name"
}
```

---

## 7. Route by Edge ID (Debug)
**Endpoint**: `POST /route_by_edge`
*   **Description**: Skip spatial lookup and route directly between graph edge IDs.

### Request
```json
{
  "dataset": "burnaby",
  "source_edge": 1500,
  "target_edge": 2900
}
```
