# Configuration Reference

This document explains all configuration options for the shortcut generation pipeline.

## Configuration Files

Configuration uses YAML files in the `config/` directory:
- `default.yaml` - Base defaults
- `burnaby.yaml`, `all_vancouver.yaml` - District-specific overrides

Run with: `python main.py --config config/burnaby.yaml`

## Configuration Sections

### Input

```yaml
input:
  edges_file: "/path/to/{district}_edges_with_h3.csv"
  graph_file: "/path/to/{district}_edge_graph.csv"
  district: "Burnaby"
```

| Field | Description |
|-------|-------------|
| `edges_file` | Path to edge data with H3 indices. `{district}` is replaced. |
| `graph_file` | Path to edge connectivity graph |
| `district` | District name for file paths and output naming |

### Output

```yaml
output:
  directory: "output"
  shortcuts_file: "{district}_shortcuts"
  persist_dir: "persist"
```

| Field | Description |
|-------|-------------|
| `directory` | Output directory for shortcuts parquet |
| `shortcuts_file` | Output filename (without extension) |
| `persist_dir` | Directory for DuckDB persistent database |

### Algorithm

```yaml
algorithm:
  name: "partitioned"      # Algorithm to use
  sp_method: "HYBRID"      # Shortest path method
  hybrid_res: 10           # Resolution threshold for HYBRID
  partition_res: 7         # Partition resolution for phases 1 & 4
  min_res: 0               # Minimum H3 resolution
  max_res: 15              # Maximum H3 resolution
```

| Field | Values | Description |
|-------|--------|-------------|
| `name` | `partitioned` | Algorithm type (currently only partitioned) |
| `sp_method` | `SCIPY`, `PURE`, `HYBRID` | Shortest path computation method |
| `hybrid_res` | 0-15 | Threshold: PURE for res >= this, SCIPY below |
| `partition_res` | 5-8 | Cell resolution for chunking phases 1 & 4 |

### DuckDB

```yaml
duckdb:
  memory_limit: "12GB"
  threads: null            # null = auto-detect
  fresh_start: true        # Delete existing DB before run
```

| Field | Description |
|-------|-------------|
| `memory_limit` | Maximum memory for DuckDB operations |
| `threads` | CPU threads (null = auto) |
| `fresh_start` | If true, delete existing database on startup |

### Parallel

```yaml
parallel:
  workers: 4               # Default workers for all phases
  workers_phase1: 10       # Override for Phase 1
  workers_phase4: 2        # Override for Phase 4
```

| Field | Description |
|-------|-------------|
| `workers` | Default worker count |
| `workers_phase1` | Workers for Phase 1 (forward chunked) |
| `workers_phase2` | Workers for Phase 2 SP calls |
| `workers_phase3` | Workers for Phase 3 SP calls |
| `workers_phase4` | Workers for Phase 4 (backward chunked) |

See [parallel_processing.md](parallel_processing.md) for memory considerations.

### Logging

```yaml
logging:
  level: "INFO"            # Log level
  verbose: true            # Extra detail in logs
```

## Example Configurations

### Small Dataset (Testing)
```yaml
input:
  district: "Burnaby"
algorithm:
  sp_method: HYBRID
  hybrid_res: 10
  partition_res: 7
parallel:
  workers: 1
```

### Large Dataset (Production)
```yaml
input:
  district: "All_Vancouver"
algorithm:
  sp_method: HYBRID
  hybrid_res: 10
  partition_res: 6
duckdb:
  memory_limit: "24GB"
parallel:
  workers: 4
  workers_phase1: 10
  workers_phase4: 2
```

## Input File Formats

### edges_with_h3.csv

| Column | Type | Description |
|--------|------|-------------|
| id | INT | Unique edge identifier |
| from_cell | BIGINT | H3 cell of edge start |
| to_cell | BIGINT | H3 cell of edge end |
| lca_res | INT | LCA resolution of from/to cells |
| cost | FLOAT | Edge traversal cost |

### edge_graph.csv

| Column | Type | Description |
|--------|------|-------------|
| from_edge | INT | Source edge ID |
| to_edge | INT | Target edge ID |

Represents connectivity: a row means you can traverse from `from_edge` to `to_edge`.

## Output Format

Output is a Parquet file with columns:
- `from_edge`: Source edge ID
- `to_edge`: Destination edge ID  
- `cost`: Total cost of optimal path
- `via_edge`: First intermediate edge (for path reconstruction)
