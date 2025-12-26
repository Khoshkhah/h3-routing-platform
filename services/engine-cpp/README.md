# Routing Engine

H3-based hierarchical routing engine with HTTP API, implemented in C++.

## Features

- **Bidirectional Dijkstra** with H3 hierarchical pruning
- **HTTP REST API** for routing queries
- **Spatial indexing** (H3 and R-tree) for coordinate-based routing
- **Path expansion** - Shortcut paths to base edge sequences
- **Multi-source/target** queries for KNN routing

## Quick Start

### Build

```bash
# Activate environment
conda activate routing-engine
conda install -c conda-forge cmake ninja compilers arrow-cpp boost asio h3-py

# Build
./scripts/build.sh
```

### Run Server

```bash
# Start server (no dataset loaded)
./scripts/start_server.sh

# Start with dataset
./scripts/start_server.sh --shortcuts /path/to/shortcuts --edges /path/to/edges.csv --port 8082

# Stop server
./scripts/stop_server.sh
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server status, loaded datasets |
| `/route` | POST | Route from coordinates (lat/lng) |
| `/route_by_edge` | POST | Route by edge IDs |
| `/nearest_edges` | GET/POST | Find edges near coordinates |
| `/load_dataset` | POST | Load a new dataset |

### Example Requests

```bash
# Health check
curl http://localhost:8082/health

# Route by coordinates
curl -X POST http://localhost:8082/route \
  -H "Content-Type: application/json" \
  -d '{"start_lat": 37.09, "start_lng": -84.60, "end_lat": 37.10, "end_lng": -84.59}'

# Route by edge IDs
curl -X POST http://localhost:8082/route_by_edge \
  -H "Content-Type: application/json" \
  -d '{"source_edge": 100, "target_edge": 200}'

# Find nearest edges
curl "http://localhost:8082/nearest_edges?lat=37.09&lng=-84.60&max=5"
```

## Project Structure

```
routing-engine/
├── cpp/
│   ├── src/
│   │   ├── shortcut_graph.cpp   # Query algorithms + path expansion
│   │   ├── server.cpp           # HTTP server (Crow)
│   │   ├── h3_utils.cpp         # H3 helper functions
│   │   ├── main.cpp             # CLI tool
│   │   └── test_routing.cpp     # Test suite
│   ├── include/
│   │   ├── shortcut_graph.hpp
│   │   └── h3_utils.hpp
│   └── third_party/
│       ├── crow/                # HTTP framework
│       └── json/                # JSON library
├── docs/
│   ├── data_formats.md          # Input data schemas
│   └── algorithms/              # Algorithm documentation
│       ├── one_to_one_classic.md
│       ├── one_to_one_pruned.md
│       └── many_to_many.md
├── scripts/
│   ├── build.sh                 # Build project
│   ├── start_server.sh          # Start HTTP server
│   └── stop_server.sh           # Stop server
└── notebooks/
    └── cpp_algorithms.py        # Python algorithm implementations
```

## Algorithms

| Algorithm | Description | Use Case |
|-----------|-------------|----------|
| **Classic** | Bidirectional Dijkstra with `inside` filtering | General routing |
| **Pruned** | + H3 resolution-based hierarchy pruning | Local queries (faster) |
| **Multi** | Multi-source/target initialization | KNN routing |

## Data Formats

### Shortcuts Parquet

| Column | Type | Description |
|--------|------|-------------|
| `from_edge` | int32 | Starting edge ID |
| `to_edge` | int32 | Ending edge ID |
| `via_edge` | int32 | Intermediate edge (0 = base edge) |
| `cost` | float64 | Travel cost |
| `cell` | int64 | H3 cell |
| `inside` | int8 | Direction: +1=up, 0=lateral, -1=down, -2=base |

### Edge Metadata CSV

| Column | Type | Description |
|--------|------|-------------|
| `id` | int32 | Edge identifier |
| `to_cell` | int64 | H3 cell at edge end |
| `lca_res` | int32 | LCA resolution |
| `cost` | float64 | Edge traversal cost |

## Dependencies

- **Arrow/Parquet** - Reading shortcut files
- **H3** - Spatial hierarchy
- **Boost** - Geometry, filesystem
- **Crow** - HTTP server
- **ASIO** - Networking

## Related Projects

| Project | Role |
|---------|------|
| [osm-to-road](../osm-to-road) | OSM → Road graph |
| [road-to-shortcut-duckdb](../road-to-shortcut-duckdb) | Graph → Shortcuts |
| [routing-pipeline](../routing-pipeline) | API wrapper + Streamlit UI |
| **routing-engine** (this) | C++ query engine + HTTP API |
