# Quick Start Guide

Get up and running with the shortcut generation pipeline in 5 minutes.

## Prerequisites

- Python 3.10+
- ~8GB RAM minimum (16GB+ recommended for large datasets)
- Input data: edges with H3 indices + edge graph

## Installation

```bash
# Clone and enter directory
cd road-to-shortcut-duckdb

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

### Basic Usage

```bash
# Run with Burnaby dataset
python main.py --config config/burnaby.yaml

# Run with All Vancouver dataset
python main.py --config config/all_vancouver.yaml

# List available configs
python main.py --list
```

### Output

- **Shortcuts**: `output/{district}_shortcuts` (Parquet format)
- **Database**: `persist/{district}.db` (DuckDB, retained for resume)
- **Logs**: `logs/{district}_YYYYMMDD_HHMMSS.log`

## Configuration Quick Reference

Edit `config/burnaby.yaml` or create a new config:

```yaml
input:
  district: "Burnaby"

algorithm:
  sp_method: HYBRID      # Best overall
  partition_res: 7       # 6 for larger datasets

duckdb:
  memory_limit: "12GB"
  fresh_start: true      # Set false to resume

parallel:
  workers: 4             # Adjust based on RAM
  workers_phase1: 10     # Phase 1 is memory-friendly
  workers_phase4: 2      # Phase 4 scipy is hungry
```

## Understanding the Pipeline

The pipeline has 4 phases:

```
Phase 1: Forward (res 15→7)    │ Parallel by partition cells
Phase 2: Consolidation (6→0)   │ Hierarchical merge
Phase 3: Backward (0→6)        │ Hierarchical expand  
Phase 4: Backward (7→15)       │ Parallel by partition cells
```

## Example Run Output

```
Loading config: burnaby
Running algorithm: partitioned
  District: Burnaby
  Workers: 4 (parallel)

Statistics:
  Nodes: 14,408
  Edges: 35,217
  Initial Shortcuts: 99,497

PHASE 1: PARALLEL FORWARD (15 -> 7)
  [1/33] Chunk 608704929401405439 complete in 2.55s...
  ...
  
PHASE 4: PARALLEL BACKWARD (7 -> 15)
  [33/33] Cell 608704929434959871 complete in 2.06s...

FINALIZING
  Final Count: 4,173,086
  Total time: 4m26s
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Out of memory | Reduce `workers_phase4` to 1-2 |
| Lock errors | `rm -f persist/*.db.wal` |
| Slow phase 4 | Reduce `workers_phase4`, increase `partition_res` |
| Resume from crash | Set `fresh_start: false` |

## Next Steps

- [Configuration Reference](configuration.md) - All config options
- [Parallel Processing](parallel_processing.md) - Worker tuning
- [Algorithms](algorithms.md) - How it works
- [Architecture](architecture.md) - Code structure
