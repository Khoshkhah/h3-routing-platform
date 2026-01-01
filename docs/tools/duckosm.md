---
layout: default
title: duckOSM
parent: Tools
nav_order: 2
---

# duckOSM

**High-performance OSM to DuckDB road network converter.**

duckOSM converts OpenStreetMap PBF files to routing-ready DuckDB databases using pure SQL processing.

## Quick Start

```bash
cd tools/duckOSM
python main.py --config config/burnaby.yaml
```

## Features

- **Pure SQL Processing** - Uses DuckDB spatial extension
- **Multi-Mode Support** - Driving, walking, cycling in separate schemas
- **H3 Indexing** - Automatic spatial indexing for fast queries
- **Graph Simplification** - Contracts degree-2 nodes, merges geometries
- **Turn Restrictions** - Extracts and applies from OSM relations

## Configuration

```yaml
# config/my_region.yaml
name: "my_region"
pbf_path: "data/maps/region.osm.pbf"
output_path: "../../data"

# Optional boundary filter
boundary_path: "data/boundaries/region.geojson"

options:
  simplify: true
  h3_resolution: 8
  
modes:
  - driving
  - walking
  - cycling
```

## Output Schema

Each mode creates its own schema (e.g., `driving`, `walking`, `cycling`).

### `edges` Table
| Column | Type | Description |
|--------|------|-------------|
| `edge_id` | INTEGER | Unique edge ID |
| `source` | BIGINT | Source node ID |
| `target` | BIGINT | Target node ID |
| `length_m` | FLOAT | Length in meters |
| `cost_s` | FLOAT | Travel time (seconds) |
| `geometry` | GEOMETRY | LineString geometry |
| `from_cell` | UBIGINT | Source H3 cell |
| `to_cell` | UBIGINT | Target H3 cell |
| `lca_res` | TINYINT | LCA resolution for shortcuts |

### `edge_graph` Table
| Column | Type | Description |
|--------|------|-------------|
| `from_edge` | INTEGER | Incoming edge |
| `to_edge` | INTEGER | Outgoing edge |
| `via_edge` | INTEGER | Same as to_edge |
| `cost` | FLOAT | Travel cost |

## Usage Examples

```bash
# Import with config
python main.py --config config/metro_vancouver.yaml

# Query the results
duckdb data/metro_vancouver.duckdb -c "SELECT COUNT(*) FROM driving.edges"
```

## Integration

duckOSM output is directly consumed by the [shortcut-generator](shortcut-generator.md):

```yaml
# shortcut-generator config
input:
  name: "metro_vancouver"
  database_path: "/path/to/metro_vancouver.duckdb"
  input_schema: "driving"
```

## Documentation

- [Architecture](../../../tools/duckOSM/docs/architecture.md)
- [Data Dictionary](../../../tools/duckOSM/docs/data_dictionary.md)
- [Query Cookbook](../../../tools/duckOSM/docs/query_cookbook.md)
