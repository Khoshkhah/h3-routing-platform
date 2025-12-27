# Shortcut Generator (DuckDB)

The core preprocessing tool that builds Contraction Hierarchies from road networks using H3 spatial partitioning.

## ⚡ Overview

This tool takes a road network (edges and graph connectivity) and produces a **Shortcut Database (`.db`)**. A hierarchical algorithm partitions the graph using H3 cells, computing shortcuts within and between cells to speed up routing queries.

## 🚀 Key Features

- **H3 Partitioning**: Uses H3 cells (resolutions 7-15) to parallelize shortest path computations.
- **DuckDB Storage**: Inputs and outputs are managed efficiently using DuckDB.
- **Robustness**: Handles turn restrictions and complex graph topology.
- **Variable Configuration**: Supports flexible path configurations.

## 📦 Usage

The tool is configured via YAML files in the `config/` directory.

### Quick Start

```bash
# Activate environment
conda activate h3-routing

# Run for a dataset (e.g., Burnaby)
python main.py --config config/burnaby.yaml
```

This will produce: `data/Burnaby.db`

### Configuration

Configs inherit from `config/default.yaml`. To add a new dataset:

1. Create `config/new_city.yaml`
2. Specify the district name and any overrides:
   ```yaml
   input:
     district: "New_City"
   
   duckdb:
     memory_limit: "16GB"
   ```

## 📊 Output Schema

The resulting `.db` file contains:

- **edges**: Road segments with geometry, length, and attributes.
- **shortcuts**: Pre-calculated shortcut edges for fast routing.
- **dataset_info**: Metadata including the boundary GeoJSON.

## 📁 Structure

- `main.py`: Entry point.
- `src/processor_parallel.py`: Main logic for parallel shortcut generation.
- `src/config_loader.py`: Handles YAML configuration and variable resolution.
- `config/`: Configuration files.
