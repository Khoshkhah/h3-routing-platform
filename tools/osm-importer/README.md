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
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### 1. Filtering a PBF (Optional)
If you have a large PBF (e.g., Kentucky) and want to clip it to a specific district (e.g., Somerset):
```bash
python scripts/filter_pbf.py \
    --input data/maps/kentucky-latest.osm.pbf \
    --boundary data/boundaries/somerset.geojson \
    --output data/maps/somerset.osm.pbf
```

### 2. Running the Pipeline
Configure your input in `config/config.yaml`:
```yaml
name: "Somerset"
pbf_path: "data/maps/somerset.osm.pbf"
output_dir: "data/output"
```

Then run the converter:
```bash
python main.py --config config/config.yaml
```

```

### 3. Extracting by H3 Cell
To clip a PBF file to a specific H3 cell (with buffer) using `h3-toolkit`:
```bash
python scripts/extract_cell_pbf.py \
    --input data/maps/large_region.osm.pbf \
    --cell 86283082fffffff \
    --output data/maps/cell_extract.osm.pbf
```

---

## Output Data Structure

The pipeline generates the following files in the `output_dir`:

*   **`*_simplified_edges_with_h3.csv`**: Road segments with `edge_index`, `from_cell`, `to_cell`, and costs.
*   **`*_edge_graph.csv`**: Connectivity between edges (for turn restrictions).
*   **`*_shortcut_table.csv`**: Pre-calculated shortcuts for hierarchical routing.
*   **`*_simplified_nodes.csv`**: Node coordinates.

---

## Logging
Logs are automatically saved to the `logs/` folder:
*   `logs/pipeline.log`: Main conversion details.
*   `logs/filter.log`: PBF filtering details.

---

## Contributing
Contributions are welcome! Please ensure you update the `requirements.txt` if you add new dependencies.
