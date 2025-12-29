---
layout: default
title: OSM Importer
parent: Tools
nav_order: 2
---

# OSM to Road Network Converter

A high-performance Python pipeline to convert OpenStreetMap (OSM) PBF data into a structured road network compatible with C++ routing engines. It features H3 spatial indexing, turn restriction handling, and PBF filtering.

## Key Features

*   **Config-Driven Pipeline**: Manage multiple datasets easily using `config/config.yaml`.
*   **PBF Filtering**: High-performance clipping of large OSM files using `osmium-tool`.
*   **Turn Restrictions**: Full support for OSM turn restrictions (No-Left, No-U-Turn, etc.).
*   **H3 Spatial Indexing**: Level 15 H3 indexing for every road segment.
*   **Visual Feedback**: Interactive `tqdm` progress bars and timestamped logging.
*   **Auto-Indexing**: Sequential `edge_index` generation for rapid C++ graph loading.


---

## Installation

### 1. System Dependencies
Install `osmium-tool` for PBF filtering:
```bash
sudo apt-get update && sudo apt-get install -y osmium-tool
```

### 2. Python Setup
```bash
# Use main environment
conda activate h3-routing
pip install -r tools/osm-importer/requirements.txt
```

---

## Usage

### 1. Filtering a PBF (Optional)
If you have a large PBF (e.g., Kentucky) and want to clip it to a specific district (e.g., Somerset):
```bash
python tools/osm-importer/scripts/filter_pbf.py \
    --input data/maps/kentucky-latest.osm.pbf \
    --boundary data/boundaries/somerset.geojson \
    --output data/maps/somerset.osm.pbf
```

### 2. Running the Pipeline
Configure your input in `config/config.yaml`. Then run the converter:
```bash
python tools/osm-importer/main.py --config config/config.yaml
```

---

## Output Data Structure

The pipeline generates the following files in the `output_dir`:

*   **`*_simplified_edges_with_h3.csv`**: Road segments with `edge_index`, `from_cell`, `to_cell`, and costs.
*   **`*_edge_graph.csv`**: Connectivity between edges (for turn restrictions).
*   **`*_shortcut_table.csv`**: Pre-calculated shortcuts for hierarchical routing.
*   **`*_simplified_nodes.csv`**: Node coordinates.
