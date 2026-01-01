---
layout: default
title: Shortcut Generator
parent: Tools
nav_order: 3
---

# Shortcut Generator (DuckDB)

The core preprocessing tool that builds Contraction Hierarchies from road networks using H3 spatial partitioning.

## ⚡ Overview

This tool takes a road network from duckOSM and produces hierarchical **shortcuts** stored in the same DuckDB database. A 4-phase algorithm partitions the graph using H3 cells, computing shortcuts within and between cells to speed up routing queries.

## 🚀 Key Features

- **DuckDB Integration**: Reads directly from duckOSM output (input_schema)
- **H3 Partitioning**: Uses H3 cells (resolutions 0-15) for parallelization
- **Parallel Processing**: Multi-core shortcut generation in Phase 1 and 4
- **Memory Efficient**: Streams results to avoid OOM on large datasets

## 📦 Usage

### Quick Start

```bash
# Activate environment
conda activate h3-routing

# Run for a DuckDB dataset
python tools/shortcut-generator/main.py --config config/metro_vancouver_duckdb.yaml
```

### Configuration (DuckDB mode)

```yaml
# config/metro_vancouver_duckdb.yaml
input:
  name: "metro_vancouver"
  database_path: "/path/to/metro_vancouver.duckdb"
  input_schema: "driving"

algorithm:
  sp_method: "HYBRID"
  partition_res: 7
  hybrid_res: 10

parallel:
  workers: 10
```

## 📊 Output Schema

Shortcuts are added to the `shortcuts` schema in the same DuckDB database:

- **shortcuts**: Pre-calculated shortcut edges with `from_edge`, `to_edge`, `cost`, `via_edge`, `cell`, `inside`
- **edges**: Copy of input edges with routing-specific columns
- **elementary_shortcuts**: Initial shortcuts before hierarchical merging
- **dataset_info**: Metadata including boundary GeoJSON

## 🔄 Workflow

1. **Phase 1**: Forward pass - partition at fine resolution, parallel shortest paths
2. **Phase 2**: Hierarchical consolidation - merge up to coarse resolution
3. **Phase 3**: Backward pass - assign cells to shortcuts
4. **Phase 4**: Parallel finalization per H3 cell
