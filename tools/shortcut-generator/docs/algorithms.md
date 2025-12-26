# Algorithm Overview

This document describes the shortcut generation algorithms implemented in this project.

## Problem Statement

Given a road network represented as edges with H3 spatial indices, compute all-pairs shortest paths between connected edges. The result is a set of "shortcuts" that precompute optimal routes.

## H3 Hierarchical Approach

The algorithms use H3 hexagonal grid system to partition the problem:

1. **Resolution Levels**: H3 provides resolutions 0-15, where higher resolutions have smaller cells
2. **Forward Pass** (Res 15 → -1): Aggregate shortcuts from fine to coarse resolution
3. **Backward Pass** (Res 0 → 15): Expand shortcuts from coarse to fine resolution

### Cell Assignment

For each shortcut (from_edge → to_edge), we compute:
- **inner_cell**: LCA (Lowest Common Ancestor) of `from_edge.to_cell` and `to_edge.from_cell`
- **outer_cell**: LCA of `from_edge.from_cell` and `to_edge.to_cell`
- **lca_res**: Maximum of the two edge's LCA resolutions

A shortcut is "active" at resolution R if:
- `lca_res <= R` AND `inner_res >= R` (forward pass)
- `lca_res <= R` AND `outer_res >= R` (backward pass)

## Algorithms

### 1. Pure DuckDB (`generate_shortcuts_pure.py`)

All-SQL implementation using iterative self-joins:

```sql
-- Geometric expansion
SELECT L.from_edge, R.to_edge, L.cost + R.cost, L.to_edge AS via_edge
FROM paths L JOIN paths R
ON L.to_edge = R.from_edge AND L.current_cell = R.current_cell
WHERE L.from_edge != R.to_edge
```

**Pros**: Simple, no external dependencies
**Cons**: Memory-intensive for large cells

### 2. Scipy (`generate_shortcuts_scipy.py`)

Uses `scipy.sparse.csgraph.shortest_path` (Dijkstra/Floyd-Warshall):

1. Build sparse adjacency matrix from shortcuts
2. Compute all-pairs shortest paths
3. Convert back to shortcuts with path reconstruction

**Pros**: Very fast for dense graphs
**Cons**: Requires Python/NumPy overhead

### 3. Hybrid (`generate_shortcuts_hybrid.py`)

Combines both algorithms based on resolution:
- **High resolutions (10-15)**: Pure DuckDB (smaller, sparser cells)
- **Low resolutions (-1 to 9)**: Scipy (larger, denser cells)

**Pros**: Best of both worlds
**Cons**: More complex orchestration

### 4. Partitioned (`main.py` with `processor_parallel.py`)

Memory-efficient 4-phase approach with optional parallelism:

| Phase | Direction | Resolution Range | Strategy | Parallel |
|-------|-----------|------------------|----------|----------|
| 1 | Forward | 15 → partition_res | Partition by cells | ✅ Yes |
| 2 | Forward | partition_res-1 → 0 | Hierarchical aggregation | Sequential |
| 3 | Backward | 0 → partition_res-1 | Hierarchical expansion | Sequential |
| 4 | Backward | partition_res → 15 | Process cells individually | ✅ Yes |

**Parallel Phases (1 & 4)**: Each cell processed independently in separate workers using in-memory DuckDB instances. Data passed as DataFrames.

**Sequential Phases (2 & 3)**: Parent cells depend on children, so processed hierarchically. Uses SCIPY or PURE internally based on `hybrid_res`.

**Pros**: Constant memory per worker, scales to any dataset size
**Cons**: More complex orchestration

## Complexity Analysis

| Algorithm | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Pure DuckDB | O(V³ × R) | O(V²) |
| Scipy | O(V² log V × R) | O(V²) |
| Partitioned | O(V² log V × R / P) | O(V² / P) |

Where V = vertices (edges), R = resolutions, P = partitions
