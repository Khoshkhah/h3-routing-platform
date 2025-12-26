# OSM to Road Conversion - Project Documentation

This document provides a detailed overview of the `osm-to-road` project, including its input/output data, processing pipeline, and key features.

## 1. Project Overview

The goal of this project is to convert raw OpenStreetMap (OSM) data into a highly optimized, graph-based road network suitable for routing algorithms. Unlike standard OSM tools, this project enriches the network with:
*   **H3 Spatial Indexing**: For efficient spatial lookups and hierarchical routing.
*   **Turn Restrictions**: Explicitly handling forbidden turns.
*   **Speed Prediction**: Inferring speed limits where missing.
*   **Shortcut Tables**: Pre-calculating costs for hierarchical routing.

## 2. Input Data

The primary input is **OpenStreetMap (OSM) data** in PBF format (`.osm.pbf`) and a **YAML configuration file**.

*   **Config**: Specified via `config/config.yaml`.
*   **Parameters**:
    *   `name`: The output identifier (e.g., "Somerset").
    *   `pbf_path`: Path to the OSM data file.

### Workflow
```bash
python main.py --config config/config.yaml
```

## 3. Output Data

The pipeline generates four key CSV files in the `data/output/` directory:

### A. Nodes File (`*_simplified_nodes.csv`)
Contains the vertices of the road network.
*   `id`: Unique node identifier.
*   `geometry`: Point geometry (Latitude/Longitude).

### B. Edges File (`*_simplified_edges_with_h3.csv`)
Contains the road segments connecting nodes.
*   `edge_index`: Unique sequential integer identifier (starts from 0).
*   `source`: ID of the starting node.
*   `target`: ID of the ending node.
*   `length`: Length of the segment in meters.
*   `maxspeed`: Speed limit in km/h.
*   `geometry`: LineString geometry.
*   `to_cell`: H3 cell index of the target node.
*   `from_cell`: H3 cell index of the source node.
*   `lca_res`: Resolution of the Lowest Common Ancestor H3 cell.
*   `cost`: Travel time cost (seconds).

### C. Edge Graph (`*_edge_graph.csv`)
Represents the connectivity *between edges*, essential for modeling turn restrictions.
*   `from_edge`: ID of the edge entering a node.
*   `to_edge`: ID of the edge leaving that node.
*   **Note**: Forbidden turns are excluded from this graph.

### D. Shortcut Table (`*_shortcut_table.csv`)
An optimized table for hierarchical routing algorithms.
*   `from_edge`: The edge being traversed.
*   `to_edge`: The subsequent edge.
*   `cost`: Cost to traverse the from_edge.
*   `via_cell`: H3 cell of the junction.
*   `lca_res`: Hierarchical level for routing decisions.

## 4. Pipeline Processing

The `main.py` script executes the following steps:

1.  **PBF Filtering (Optional)**: If a GeoJSON boundary is provided, the large source PBF is clipped to a localized area using `scripts/filter_pbf.py`.
2.  **Config Loading**: Parses `config/config.yaml` for name and file paths.
3.  **Build Graph**: Extracts the driving network using `pyrosm`.
4.  **Simplify**: Removes self-loops and simplifies network topology using `osmnx`.
5.  **Extract**: Converts the graph into Node and Edge DataFrames.
6.  **Process Speeds**:
    *   Parses existing `maxspeed` tags.
    *   Predicts missing speeds based on `highway` type.
7.  **Turn Restrictions**:
    *   Parses OSM relations to find "no_left_turn", "no_u_turn", etc.
    *   Identifies forbidden `(from_edge, to_edge)` pairs.
8.  **Build Edge Graph**: Constructs the dual graph, filtering out forbidden turns, with interactive progress bars.
9.  **H3 Indexing & LCA**:
    *   Converts node coordinates to H3 cells (Resolution 15).
    *   Calculates the Lowest Common Ancestor (LCA) resolution for edges.
10. **Calculate Costs**: Computes travel time based on length and speed.
11. **Create Shortcut Table**: Assembles the final routing table with `lca_res_from_edge` and `lca_res_to_edge` logic.
12. **Save**: Exports all datasets to CSV with sequential `edge_index` identifiers.

## 5. Special Features

### H3 Spatial Indexing
This project uniquely integrates **Uber's H3 Hexagonal Hierarchical Spatial Index**. By mapping nodes to H3 cells and calculating LCA resolutions, the network supports **hierarchical routing algorithms**. This allows routers to ignore lower-level roads when traversing large distances, significantly speeding up pathfinding.

### Robust Turn Restrictions
Many basic OSM converters ignore turn restrictions. This project explicitly extracts them from OSM relations and builds an **Edge Graph** (Dual Graph). This ensures that a route will never suggest an illegal turn, which is critical for realistic navigation.

### Intelligent Speed Inference
Raw OSM data often lacks speed limits. The `SpeedProcessor` module uses a heuristic dictionary to infer speed limits based on road types (`highway` tag), ensuring that cost calculations are reasonable even when data is missing.
