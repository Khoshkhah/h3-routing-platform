# Road-to-Shortcut DuckDB

DuckDB-based shortcut generation for road networks using H3 spatial indexing.

## Overview

This project computes shortcut paths in road networks using a hierarchical forward-backward algorithm with H3-based spatial partitioning. It provides both parallel and sequential implementations optimized for performance.

## Performance (Burnaby Dataset: 4,173,086 shortcuts)

| Version | Time | Description |
|---------|------|-------------|
| **Parallel** | **5m 9s** | 4 workers, recommended |
| Sequential | 12m 9s | Single-threaded |

### Phase Breakdown (Parallel)

| Phase | Time | Description |
|-------|------|-------------|
| Phase 1 | 55s | Forward pass 15→7 (33 parallel chunks) |
| Phase 2 | 31s | Hierarchical consolidation 6→-1 |
| Phase 3 | 2m 53s | Backward consolidation -1→7 |
| Phase 4 | 50s | Backward chunked 7→15 (parallel) |

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run parallel version (recommended)
python src/generate_shortcuts_parallel.py --district Burnaby

# Run sequential version
python src/generate_shortcuts_partitioned.py --district Burnaby
```

## Configuration

Edit `src/config.py`:

| Setting | Description |
|---------|-------------|
| `DISTRICT_NAME` | Dataset to process (e.g., "Burnaby") |
| `EDGES_FILE` | Path to edges CSV with H3 indices |
| `GRAPH_FILE` | Path to edge connectivity graph |
| `DUCKDB_MEMORY_LIMIT` | Memory limit (default: 12GB) |

## Algorithm

The algorithm uses a 4-phase hierarchical approach:

1. **Phase 1 (Forward Chunked)**: Process each H3 cell at resolution 7 independently, running shortest paths from res 15→7
2. **Phase 2 (Forward Consolidation)**: Merge child cells into parents, continuing from res 6→-1 (global)
3. **Phase 3 (Backward Consolidation)**: Split from global back down to res 7, running SP at each level
4. **Phase 4 (Backward Chunked)**: Process each res-7 cell independently from res 8→15

### Key Optimizations

- **H3 Metadata Pre-calculation**: `lca_res`, `inner_cell`, `outer_cell`, `inner_res`, `outer_res` computed once
- **Parallel Processing**: Phase 1 and 4 use Python multiprocessing
- **Smart SP Skipping**: Skip shortest path when no shortcuts are newly activated
- **Hash Join Partitioning**: Efficient cell assignment using temp tables

## Documentation

- [Core Concepts](docs/core_concepts.md) - Edge model, H3 logic, activation rules
- [Algorithm Overview](docs/algorithms.md) - Detailed phase breakdown
- [Architecture](docs/architecture.md) - System design
- [Configuration](docs/configuration.md) - Setup guide

## Project Structure

```
road-to-shortcut-duckdb/
├── src/
│   ├── generate_shortcuts_parallel.py   # Main entry (parallel)
│   ├── generate_shortcuts_partitioned.py # Core algorithm (sequential)
│   ├── config.py                         # Configuration
│   ├── utilities.py                      # DuckDB utilities & H3 UDFs
│   └── logging_config.py                 # Logging setup
├── docs/                                 # Documentation
├── archive/                              # Legacy/debug scripts
├── logs/                                 # Log files (gitignored)
├── output/                               # Generated shortcuts (gitignored)
└── requirements.txt
```

## License

MIT
