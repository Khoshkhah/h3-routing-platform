---
layout: default
title: Data Processing Workflow
nav_order: 4
---

# Data Processing Workflow

The H3 Routing Platform includes a robust pipeline for converting raw OpenStreetMap (OSM) data into the optimized format required by the C++ engine.

## 1. Map Data Ingestion (OSM to DuckDB)

The process begins by extracting road network data from OSM PBF or XML files.

- **Tool**: `osm-to-road` (or equivalent processor).
- **Format**: Data is normalized into a relational structure (Nodes and Edges) inside a **DuckDB** database.
- **Attributes**: Every edge is enriched with properties like `highway` type, `speed_limit`, and `cost` (travel time).

## 2. Contraction Hierarchy Generation

Once the base graph is ready, we run the shortcut generation process.

- **Deduplication**: Ensures no redundant edges exist between nodes.
- **Node Contraction**: Nodes are iteratively removed, and shortcuts are added to maintain connectivity.
- **H3 Enrichment**: Every shortcut is assigned an H3 cell and resolution to support spatial pruning.
- **Output**: 
  - `shortcuts.parquet`: The augmented graph containing both base edges and pre-computed shortcuts.
  - `edges.csv`: Detailed metadata (geometry, names, types) for the expanded path rendering.

## 3. Deployment to Engine

The generated data is then loaded into the **Routing Engine**.

- **Registration**: Datasets are defined in `datasets.yaml` or loaded dynamically via the API.
- **Memory Optimization**: During load, the engine compacts the data into the 24-byte CSR format and releases temporary peak memory using `malloc_trim`.
- **Validation**: The engine performs an internal consistency check to ensure all `via_edge` pointers are valid.

---

### Workflow Diagram

```mermaid
graph TD
    A[Raw OSM PBF] -->|Processing| B[Road Graph (DuckDB)]
    B -->|Preprocessing| C[Shortcut Generation]
    C -->|Output| D[shortcuts.parquet]
    C -->|Output| E[edges.csv]
    D -->|Load| F[C++ CSR Engine]
    E -->|Load| F
    F -->|Ready| G[Routing API]
```
