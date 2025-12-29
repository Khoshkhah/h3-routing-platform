# API Reference

This document provides a detailed specification for the H3 Routing Engine REST API.

## Core Endpoints

### POST /route
Finds the shortest path between two coordinate pairs using the platform's routing pipeline.

#### Request Parameters (JSON)
| Name | Type | Description |
| :--- | :--- | :--- |
| `dataset` | string | Name of the pre-loaded dataset to query. |
| `start_lat`, `start_lng` | float | Coordinates of the origin point. |
| `end_lat`, `end_lng` | float | Coordinates of the destination point. |
| `mode` | string | Search strategy: `knn`, `radius`, `one_to_one`, `one_to_one_v2`. |
| `algorithm` | string | Algorithm: `bi_classic_sp`, `bi_dijkstra_sp`, `bi_lca_res_sp`, `m2m_classic_sp`, etc. |
| `num_candidates` | integer | Number of nearest edges to consider (for `knn` mode). |

#### Response Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `success` | boolean | Indicates if a route was successfully computed. |
| `route.distance` | float | Total weight (cost) of the path. |
| `route.distance_meters`| float | Physical length of the path in meters. |
| `route.path` | array | Sequential list of base road edge IDs. |
| `route.geojson` | object | GeoJSON LineString representation of the path. |

#### Example
```bash
curl -X POST http://localhost:8082/route \
-H "Content-Type: application/json" \
-d '{"dataset": "vancouver", "start_lat": 49.2, "start_lng": -123.1, ...}'
```

---

### GET /nearest_edges
Retrieves the road edges closest to a specific geographic point.

#### Parameters (Query)
| Name | Type | Description |
| :--- | :--- | :--- |
| `lat`, `lon` | float | Geographic coordinates for the search. |
| `k` | integer | Maximum number of edges to return (default: 5). |
| `dataset` | string | Scope the search to this dataset. |

#### Response Example
```json
{
  "edges": [
    { "edge_id": 101, "distance": 5.2, "cost": 120.0 },
    { "edge_id": 102, "distance": 14.8, "cost": 150.0 }
  ]
}
```

---

### POST /load_dataset
Instructs the engine to load a new dataset into memory.

#### Request Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `dataset` | string | Unique identifier for the dataset. |
| `shortcuts_path` | string | File path to the augmented shortcut graph (.parquet). |
| `edges_path` | string | File path to the edge metadata (.csv). |

---

### POST /unload_dataset
Removes a dataset and frees associated physical memory via `malloc_trim`.

---

### GET /health
Returns the current server status and a list of all resident datasets.
