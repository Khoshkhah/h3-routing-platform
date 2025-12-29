---
layout: default
title: SDK Manual
nav_order: 6
---

# SDK Manual

This document provides a high-fidelity reference for the H3 Routing Platform Python SDK.

## Python SDK

The Python SDK is the primary interface for interacting with the routing engine. It supports dynamic dataset management, advanced routing modes, and spatial queries.

### Installation

```bash
pip install -e sdk/python
```

---

### Import & Initialization

The package is named `h3_routing_client`.

```python
from h3_routing_client import RoutingClient

# Initialize with the address of your C++ Engine or API Gateway
client = RoutingClient(base_url="http://localhost:8082")
```

---

### health

Check the current status of the server and list loaded datasets.

#### Return Value
Returns a `dict` containing:
- `status`: String (e.g., `"healthy"`)
- `datasets_loaded`: List of strings showing active datasets.

#### Usage Example
```python
status = client.health()
print(f"Server Status: {status['status']}")
print(f"Active Datasets: {status['datasets_loaded']}")
```

---

### load_dataset

Dynamically load a dataset into engine memory.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` | *required* | Dataset identifier (e.g., "vancouver"). |
| `db_path` | `str` | `None` | Path to the DuckDB database (preferred). |
| `shortcuts_path` | `str` | `None` | Path to parquet shortcuts (Legacy). |
| `edges_path` | `str` | `None` | Path to edges metadata (Legacy). |

#### Return Value
Returns `True` if successfully loaded, `False` otherwise.

#### Usage Example
```python
# Preferred way (DuckDB)
success = client.load_dataset(
    name="burnaby", 
    db_path="/data/burnaby.db"
)

# Legacy way (Separate files)
success = client.load_dataset(
    name="metro_van",
    shortcuts_path="/data/shortcuts/",
    edges_path="/data/edges.csv"
)
```

---

### unload_dataset

Remove a dataset from memory to free system resources.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` | *required* | Identifier of the dataset to unload. |

#### Return Value
Returns `True` if successfully unloaded, `False` otherwise.

#### Usage Example
```python
if client.unload_dataset("burnaby"):
    print("Memory freed successfully.")
```

---

### route

Calculate the shortest path between two points.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `dataset` | `str` | *required* | Target dataset. |
| `start_lat`, `start_lng` | `float` | *required* | Source coordinates. |
| `end_lat`, `end_lng` | `float` | *required* | Target coordinates. |
| `mode` | `str` | `"knn"` | Lookup mode: `knn`, `radius`, `one_to_one`. |
| `num_candidates` | `int` | `3` | Candidates for `knn` mode. |
| `algorithm` | `str` | `"bi_lca_res_sp"` | Algorithm: `bi_classic_sp`, `bi_dijkstra_sp`, `m2m_classic_sp`, etc. |

#### Return Value
Returns a `RouteResponse` object.

#### Usage Example
```python
response = client.route(
    dataset="vancouver",
    start_lat=49.2, start_lng=-123.1,
    end_lat=49.3, end_lng=-123.2,
    algorithm="pruned"
)

if response.success:
    print(f"Travel Cost: {response.cost}")
    print(f"Length (meters): {response.distance_meters}")
    print(f"Path Edges: {len(response.path)}")
```

---

### nearest_edges

Retrieve road segments closest to a specific coordinate.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `dataset` | `str` | *required* | Target dataset. |
| `lat`, `lon` | `float` | *required* | Query coordinates. |
| `k` | `int` | `5` | Max edges to return. |
| `radius_meters` | `float` | `100.0` | Max search radius. |

#### Return Value
Returns a `List[Dict]` containing `edge_id`, `distance`, and `cost`.

#### Spatial Index Note
By default, the server uses an **H3-based spatial index** for this query. This can be changed to an **R-tree** via the server command-line argument `--index rtree` or in the `server.json` configuration.

#### Usage Example
```python
edges = client.nearest_edges("vancouver", 49.25, -123.12, k=3)
for edge in edges:
    print(f"Edge {edge['edge_id']} is {edge['distance']:.1f}m away.")
```

---

### Debug & Advanced Methods

#### route_by_edge

Direct routing between internal Edge IDs, skipping coordinate lookup.

```python
# Useful for testing the graph structure directly
res = client.route_by_edge("vancouver", source_edge=501, target_edge=902)
```

#### route_by_edge_raw / route_raw

Returns the shortcut-level path (CH hierarchy) without expanding it into base road segments.

```python
# Useful for visualizing how the Contraction Hierarchies algorithm works
res = client.route_raw("vancouver", 49.2, -123.1, 49.3, -123.2)
print(f"Shortcut IDs: {res['route']['shortcut_path']}")
```

---

### Classes & Properties

#### RouteResponse

| Property | Type | Description |
| :--- | :--- | :--- |
| `success` | `bool` | `True` if a path was found. |
| `cost` | `float` | Total optimization weight (alias for `distance`). |
| `distance_meters`| `float` | Physical length in meters. |
| `runtime_ms` | `float` | Time taken by the engine. |
| `path` | `List[int]` | Ordered list of base road edge IDs. |
| `geojson` | `dict` | GeoJSON LineString dictionary. |
| `error` | `str` | Error message if `success` is `False`. |
