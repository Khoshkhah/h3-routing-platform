# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Data                                │
│  ┌─────────────────┐      ┌─────────────────┐              │
│  │ edges.csv       │      │ edge_graph.csv  │              │
│  │ (road network)  │      │ (connectivity)  │              │
│  └────────┬────────┘      └────────┬────────┘              │
└───────────┼────────────────────────┼────────────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    DuckDB Engine                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ edges table        │ shortcuts table                 │   │
│  │ - id               │ - from_edge                     │   │
│  │ - from_cell (H3)   │ - to_edge                       │   │
│  │ - to_cell (H3)     │ - cost                          │   │
│  │ - lca_res          │ - via_edge                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Algorithm Selection                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Pure    │  │  Scipy   │  │  Hybrid  │  │ Partitioned│ │
│  │ DuckDB   │  │          │  │          │  │            │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ shortcuts.parquet                                    │   │
│  │ - from_edge, to_edge, cost, via_edge                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Module Structure

```
src/
├── config.py                    # Configuration parameters
├── utilities.py                 # DuckDB helper functions
│   ├── initialize_duckdb()      # Create/connect to DB
│   ├── read_edges()             # Load edge data
│   ├── initial_shortcuts_table()# Create initial shortcuts
│   ├── assign_cell_forward()    # Assign cells (forward pass)
│   ├── assign_cell_backward()   # Assign cells (backward pass)
│   └── merge_shortcuts()        # Merge new shortcuts
│
├── logging_config.py            # Logging setup
│
├── generate_shortcuts_pure.py   # Pure DuckDB algorithm
│   └── compute_shortest_paths_pure_duckdb()
│
├── generate_shortcuts_scipy.py  # Scipy-based algorithm
│   ├── process_partition_scipy()
│   └── main()
│
├── generate_shortcuts_hybrid.py # Hybrid algorithm
│   └── main()
│
└── generate_shortcuts_partitioned.py  # Partitioned algorithm
    ├── partition_by_cell()
    ├── process_partition_forward()
    ├── process_partition_backward()
    ├── process_single_cell_forward()
    ├── process_single_cell_backward()
    └── main()
```

## Data Flow

### Forward Pass (Resolution 15 → -1)

1. Start with initial shortcuts (direct edge connections)
2. For each resolution (high to low):
   - Assign `current_cell` based on inner_cell
   - Filter active shortcuts (current_cell IS NOT NULL)
   - Compute shortest paths within each cell
   - Merge new shortcuts into main table

### Backward Pass (Resolution 0 → 15)

1. Start with shortcuts from forward pass
2. For each resolution (low to high):
   - Assign `current_cell` based on outer_cell
   - Filter active shortcuts (current_cell IS NOT NULL)
   - Compute shortest paths within each cell
   - Merge new shortcuts into main table

## DuckDB Tables

### `edges`
| Column | Type | Description |
|--------|------|-------------|
| id | INT | Edge ID |
| from_cell | BIGINT | H3 cell of start vertex |
| to_cell | BIGINT | H3 cell of end vertex |
| lca_res | INT | LCA resolution |

### `shortcuts`
| Column | Type | Description |
|--------|------|-------------|
| from_edge | INT | Starting edge |
| to_edge | INT | Ending edge |
| cost | DOUBLE | Path cost |
| via_edge | INT | First hop edge |

### `shortcuts_next` (temporary)
| Column | Type | Description |
|--------|------|-------------|
| from_edge | INT | Starting edge |
| to_edge | INT | Ending edge |
| cost | DOUBLE | Path cost |
| via_edge | INT | First hop edge |
| current_cell | BIGINT | Assigned H3 cell for this resolution |
