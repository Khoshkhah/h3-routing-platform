# Parallel Processing Guide

This document explains the parallel processing features and how to configure them for optimal performance.

## Overview

The shortcut generation pipeline supports per-phase worker configuration to balance speed vs memory usage.

## Phase Architecture

| Phase | Direction | Description | Parallelizable |
|-------|-----------|-------------|----------------|
| Phase 1 | Forward (15→7) | Process chunks at partition_res | ✅ Yes |
| Phase 2 | Forward (6→0) | Hierarchical consolidation | Sequential* |
| Phase 3 | Backward (0→6) | Backward consolidation | Sequential* |
| Phase 4 | Backward (7→15) | Process cells back to finest | ✅ Yes |

*Phase 2 and 3 are hierarchically dependent but use parallel SP internally.

## Configuration

In your YAML config file:

```yaml
parallel:
  workers: 4           # Default for all phases
  workers_phase1: 10   # Override: Phase 1 uses more memory-efficient ops
  workers_phase4: 2    # Override: Phase 4 scipy is memory-hungry
```

### Per-Phase Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `workers` | 1 | Default worker count for all phases |
| `workers_phase1` | `workers` | Workers for Phase 1 (forward chunked) |
| `workers_phase2` | `workers` | Workers for Phase 2 SP calls |
| `workers_phase3` | `workers` | Workers for Phase 3 SP calls |
| `workers_phase4` | `workers` | Workers for Phase 4 (backward chunked) |

## Memory Considerations

### Phase 1 (Forward)
- Each worker loads edges (~few MB) + chunk shortcuts (~depends on chunk)
- Uses in-memory DuckDB per worker
- **Safe to use 8-10 workers** on most systems

### Phase 4 (Backward)
- Uses `scipy` shortest path which is memory-intensive
- Scipy allocates dense matrices proportional to cell size
- **Recommended: 2-4 workers** to avoid OOM

### Example Configurations

**Small Dataset (Burnaby ~35K edges)**
```yaml
parallel:
  workers: 1  # Sequential is often faster due to lower overhead
```

**Large Dataset (All Vancouver ~200K edges)**
```yaml
parallel:
  workers: 4
  workers_phase1: 10  # Phase 1 is memory-friendly
  workers_phase4: 2   # Phase 4 scipy needs more RAM per worker
```

**High-Memory Server (64GB+ RAM)**
```yaml
parallel:
  workers: 8
  workers_phase1: 16
  workers_phase4: 6
```

## Log Output

With per-cell timing enabled, you'll see:

```
[INFO] PHASE 1: PARALLEL FORWARD (15 -> 7)
[INFO]   Processing 33 chunks in parallel (max 10 workers)...
[INFO]   [1/33] Chunk 608704929401405439 complete in 2.55s. 36876 active, 67860 deactivated
[INFO]   [2/33] Chunk 608704897709244415 complete in 5.87s. 114948 active, 165926 deactivated
```

## SCIPY vs PURE Methods

The `algorithm.sp_method` setting controls shortest path computation:

| Method | Best For | Memory | Speed |
|--------|----------|--------|-------|
| `PURE` | Small/sparse cells (res 10-15) | Low | Moderate |
| `SCIPY` | Large/dense cells (res 0-9) | High | Fast |
| `HYBRID` | All cases | Balanced | Best overall |

With `HYBRID`, the pipeline automatically switches:
- `res >= hybrid_res`: Use PURE
- `res < hybrid_res`: Use SCIPY

```yaml
algorithm:
  sp_method: HYBRID
  hybrid_res: 10
```

## Troubleshooting

### Out of Memory (OOM)
1. Reduce `workers_phase4` to 2 or 1
2. Increase `duckdb.memory_limit`
3. Consider lowering `partition_res` (fewer, larger chunks)

### Slow Performance
1. Increase workers for Phase 1 (it's memory-friendly)
2. Ensure you're using `HYBRID` sp_method
3. Check log timing breakdowns

### Lock Errors
If you see "Conflicting lock" errors:
1. Kill any zombie Python processes: `pkill -f "python3 main.py"`
2. Delete stale WAL files: `rm -f persist/*.db.wal`
