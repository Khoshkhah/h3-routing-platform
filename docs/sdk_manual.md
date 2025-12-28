---
layout: default
title: SDK Manual
nav_order: 6
---

# SDK Manual

This document provides a high-fidelity reference for the H3 Routing Platform client libraries.

## Python SDK

The Python SDK is the primary interface for interacting with the routing engine, supporting all features including dynamic dataset management and advanced routing modes.

### installation

```bash
pip install -e sdk/python
```

---

### RoutingClient

Constructor for the routing client.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `base_url` | `str` | `"http://localhost:8082"` | URL of the Routing Engine or API Gateway. |
| `config_path` | `str` | `None` | Optional path to `datasets.yaml` for local resolution. |

#### Usage
```python
from h3_routing_client import RoutingClient
client = RoutingClient(base_url="http://localhost:8082")
```

---

### health

Check the current status of the server and list loaded datasets.

#### Arguments
None.

#### Return Value
Returns a `dict` containing:
- `status`: String (e.g., "healthy").
- `datasets_loaded`: List of strings showing active datasets.

#### Usage
```python
status = client.health()
print(status['datasets_loaded'])
```

---

### route

Calculate the shortest path between two geographic points.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `dataset` | `str` | *required* | Target dataset name. |
| `start_lat`, `start_lng` | `float` | *required* | Origin coordinates. |
| `end_lat`, `end_lng` | `float` | *required* | Destination coordinates. |
| `mode` | `str` | `"knn"` | Nearest edge search mode (`knn`, `radius`, `one_to_one`). |
| `num_candidates` | `int` | `3` | Number of candidate edges for `knn` mode. |
| `algorithm` | `str` | `"pruned"` | Routing logic (`pruned`, `classic`, `dijkstra`). |

#### Return Value
Returns a `RouteResponse` object:
- `success`: `bool`
- `cost`: `float` (Alias for `distance`)
- `distance_meters`: `float` (Physical length)
- `runtime_ms`: `float`
- `path`: `List[int]` (Raw base edge IDs)
- `geojson`: `dict` (GeoJSON LineString)
- `error`: `str` (Optional error message)

#### Usage
```python
response = client.route("vancouver", 49.2, -123.1, 49.3, -123.2)
if response.success:
    print(f"Cost: {response.cost}")
```

---

### load_dataset

Dynamically load a dataset into the engine memory.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `name` | `str` | *required* | Dataset identifier. |
| `db_path` | `str` | `None` | Path to the DuckDB database (preferred). |
| `shortcuts_path` | `str` | `None` | Path to parquet shortcuts (Legacy). |
| `edges_path` | `str` | `None` | Path to edges metadata (Legacy). |

#### Return Value
Returns `True` if successfully loaded, `False` otherwise.

#### Usage
```python
client.load_dataset("burnaby", db_path="/path/to/burnaby.db")
```

---

### nearest_edges

Retrieve road segments closest to a specific coordinate.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `dataset` | `str` | *required* | Target dataset. |
| `lat`, `lon` | `float` | *required* | Query coordinates. |
| `k` | `int` | `5` | Maximum number of edges to return. |
| `radius_meters`| `float` | `100.0` | Maximum search radius. |

#### Return Value
Returns a `List[Dict]` where each dict contains:
- `edge_id`: `int`
- `distance`: `float` (Meters from point)
- `cost`: `float`

---

### route_by_edge (Debug)

Computes a route directly between two static edge IDs, skipping spatial lookup.

#### Arguments

| Name | Type | Description |
| :--- | :--- | :--- |
| `dataset` | `str` | Target dataset. |
| `source_edge` | `int` | Internal graph ID for source. |
| `target_edge` | `int` | Internal graph ID for destination. |

---

### route_by_edge_raw (Debug)

Similar to `route_by_edge`, but returns the raw shortcut-level path without expansion into base road edges. Useful for visualizing the CH hierarchy.

---

### route_raw (Debug)

Computes a route using coordinates but returns the unexpanded shortcut path.

---

### Internal Classes & Properties

#### RouteResponse
The object returned by routing methods contains several convenience properties.

- **`cost`**: Returns the total optimization weight of the path (alias for `distance`).
- **`distance_meters`**: Returns the physical length of the path in meters.
- **`path`**: Provides the ordered sequence of base road edge IDs.
- **`geojson`**: A standard GeoJSON LineString dictionary ready for visualization.

---

## C++ SDK

A header-only lightweight client designed for embedding into performance-critical services.

### routing::Client

Constructor for the C++ client.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `url` | `std::string` | `"http://localhost:8082"` | Base URL of the engine. |

---

### route

Executes a routing request.

#### Arguments

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `req` | `routing::RouteRequest` | *required*| Structure containing `dataset`, `start_lat`, `start_lng`, `end_lat`, `end_lng`, and `mode`. |

#### Return Value
Returns a `nlohmann::json` object containing the query results or an `error` key.

#### Usage
```cpp
routing::RouteRequest req = {"burnaby", 49.2, -123.1, 49.25, -123.15};
auto res = client.route(req);
```
