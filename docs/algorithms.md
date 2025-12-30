---
layout: default
title: Routing Algorithms
nav_order: 3
---

# Routing Algorithms

This document describes the routing algorithms implemented in the H3 Routing Platform.

## Overview

All algorithms find shortest paths on a **shortcut graph** built from H3 hierarchical cells. The graph has two key properties:

1. **Shortcuts:** Pre-computed paths between edges that skip intermediate nodes
2. **Inside values:** Each shortcut has an `inside` value indicating direction in the H3 hierarchy:
   - `inside = 1`: Upward (toward coarser cells/lower resolution)
   - `inside = 0`: Lateral (same level in hierarchy)
   - `inside = -1`: Downward (toward finer cells/higher resolution)
   - `inside = -2`: Base edge (outer-only)

## Unified API Naming

The system exposes a unified set of algorithm names via the Streamlit UI and API to ensure consistency across the Python and C++ engines.

| UI Display Name | API Value | Description | Internal Implementation (C++/Python) |
|---|---|---|---|
| **Bidirectional Pruned (Res)** | `pruned` | **Recommended**. Uses resolution-based pruning. | `query_pruned` / `query_bi_lca_res` |
| **Bidirectional Classic** | `classic` | Standard bidirectional Dijkstra (no pruning). | `query_classic` |
| **Unidirectional Phase-Based** | `unidirectional` | Unidirectional Phase-Based search. | `query_unidirectional` / `query_uni_lca` |
| **Bidirectional Phase-Based (LCA)** | `bi_lca` | Pruning based on LCA phases. | `query_bi_lca` (Python only*) |
| **Dijkstra (Baseline)** | `dijkstra` | Naive Unidirectional Dijkstra. **Slowest**. | `query_dijkstra` / `query_uni_dijkstra` |
| **Bi-Dijkstra (Baseline)** | `bidijkstra` | Naive Bidirectional Dijkstra. | `query_bidijkstra` / `query_bi_dijkstra` |
| **Many-to-Many (KNN)** | `m2m` | K-Nearest Neighbors search. | `query_multi` / `query_m2m` |

*\*Note: Phase-Based algorithms map to their Resolution-Based counterparts in the C++ engine if selected.*

## Algorithm Summary

| # | Name | Type | High Cell | Forward | Backward | Speed |
|---|------|------|-----------|---------|----------|-------|
| 1 | `dijkstra` | 1:1 | No | All | N/A | Baseline |
| 1.5 | `bi_dijkstra` | 1:1 | No | All | All | Fast |
| 2 | `bi_classic` | 1:1 | No | Up only | Up + Down | Faster |
| 3 | `bi_lca_res` | 1:1 | Yes | Toward LCA | Toward LCA | Fast |
| 4 | `uni_lca` | 1:1 | Yes | Phase-based | N/A | Fast |
| 5 | `bi_lca` | 1:1 | Yes | Phase-based | Phase-based | Fastest |
| 6 | `m2m_classic` | M:N | No | Up only | Up + Down | Fast |
| 7 | `m2m_lca` | M:N | Per-pair | Phase-based | Phase-based | TBD |

---

## Algorithm Details

### 1. Dijkstra (`dijkstra`)

**Standard Dijkstra** on the shortcut graph with no filtering.

- **Use case:** Ground truth for correctness testing
- **Filtering:** None (uses all shortcuts)
- **Optimality:** Always finds optimal path
- **Speed:** Slowest (explores entire graph)

```python
def dijkstra(source, target):
    # Standard Dijkstra - no inside filtering
    for shortcut in neighbors:
        explore(shortcut)  # All shortcuts allowed
```

---

### 1.5 Bidirectional Dijkstra (`bi_dijkstra`)

**Standard Bidirectional Dijkstra** with no filtering.

- **Use case:** Performance comparison baseline
- **Filtering:** None
- **Optimality:** Always finds optimal path (100% correct)
- **Speed:** Faster than unidirectional Dijkstra (usually 1.5-2x), but slower than filtered algorithms.

---

### 2. Bidirectional Classic (`bi_classic`)

**Bidirectional search** with asymmetric filtering based on `inside` values.

- **Use case:** Fast queries when no LCA is known
- **Forward filtering:** Only `inside = 1` (go UP in hierarchy)
- **Backward filtering:** `inside = -1` or `inside = 0` (go UP and lateral)
- **Meeting point:** Can meet anywhere in the graph

```
Forward:  source → up → up → up → ...
                                    ↘
                                     Meeting
                                    ↗
Backward: target → up → lateral → up → ...
```

**Key insight:** Forward can ONLY go up, so it will eventually reach coarse cells. Backward can also go down/lateral, allowing it to meet forward somewhere.

---

### 3. Bidirectional LCA Resolution (`bi_lca_res`)

**Bidirectional search** with LCA (Least Common Ancestor) targeting and resolution-based pruning.

- **Use case:** Fast queries with known LCA
- **High cell:** Computed as LCA of source and target cells
- **Forward filtering:** `inside = 1` (go toward LCA)
- **Backward filtering:** Based on `u_res >= high_res` comparison
- **Pruning:** Skip shortcuts whose cell resolution is below LCA

```
          High Cell (LCA)
             /\
      UP    /  \    UP
           /    \
      Source    Target
```

**Key property:** Both searches go TOWARD the LCA cell, meeting at or near it.

---

### 4. Unidirectional LCA (`uni_lca`)

**Unidirectional phase-based search** with LCA targeting.

- **Use case:** Reference implementation, testing
- **High cell:** Computed as LCA of source and target
- **Phases:**
  - Phase 0/1: Ascending (`inside = 1` when `cell_res > high_res`)
  - Phase 2: At peak (`inside != 1`)
  - Phase 3: Descending (`inside = -1` only)

```
Path structure:

    Phase 0/1    Phase 2    Phase 3
    (ascending)  (peak)     (descending)
         ↗         →          ↘
    source    high_cell    target
```

**Phase transitions:**
```python
if phase == 0 or phase == 1:
    if cell_res > high_res and inside == 1:
        next_phase = 1  # Continue ascending
    elif cell_res <= high_res and inside == 1:
        next_phase = 2  # Reached peak
    elif inside != 1:
        next_phase = 2  # At peak level
elif phase == 2:
    if inside != 1:
        next_phase = 3  # Start descending
elif phase == 3:
    if inside == -1:
        next_phase = 3  # Continue descending
```

---

### 5. Bidirectional LCA (`bi_lca`)

**Bidirectional phase-based search** - the fastest algorithm.

- **Use case:** Production queries
- **High cell:** Computed as LCA of source and target
- **Forward filtering:** Same as `uni_lca`
- **Backward filtering:** Mirror of forward (swap `inside` values)
- **Meeting detection:** Check when adding to heap AND when popping

```
Forward:   source → (phase 0) → (phase 1) → (phase 2) → ...
                                                         ↘
                                                          Meeting
                                                         ↗
Backward:  target → (phase 0) → (phase 1) → (phase 2) → ...
```

**Critical fix:** Meeting point is checked when ADDING edges to heap, not just when popping:

```python
# When pushing to forward heap:
if to_edge in dist_bwd:
    total = nd + dist_bwd[to_edge]
    if total < best:
        best = total
        meeting_edge = to_edge
```

---

### 6. Many-to-Many Classic (`m2m_classic`)

**Many-to-many version** of `bi_classic`.

- **Use case:** Distance matrices, batch queries
- **Sources:** Multiple source edges
- **Targets:** Multiple target edges
- **Filtering:** Same as `bi_classic` (inside-based)

```python
def m2m_classic(sources: List[int], targets: List[int]):
    # Initialize forward from ALL sources
    for src in sources:
        heappush(pq_fwd, (0, src))
    
    # Initialize backward from ALL targets
    for tgt in targets:
        heappush(pq_bwd, (edge_cost[tgt], tgt))
    
    # Run bidirectional search
    # Return distance matrix: sources × targets
```

---

### 7. Many-to-Many LCA (`m2m_lca`) - *Future*

**Many-to-many version** of `bi_lca` with phase-based filtering.

- **Challenge:** Each (source, target) pair has a different LCA
- **Approach:** TBD (may need per-pair tracking or no global LCA filter)

---

## Performance Comparison

| Algorithm | Correctness | Speed | Memory |
|-----------|-------------|-------|--------|
| `dijkstra` | 100% | 1x (baseline) | Low |
| `bi_dijkstra` | 100% | ~2x | Low |
| `bi_classic` | 100% | 5-10x | Low |
| `bi_lca_res` | 100% | 10-20x | Low |
| `uni_lca` | 100% | 10x | Low |
| `bi_lca` | 100% | 15-20x | Low |

*Note: Speeds are approximate and depend on graph size and structure.*

---

## Key Concepts

### H3 Hierarchy

```
Resolution 0: Coarsest (122 base cells)
     ↓
Resolution N: Finer
     ↓
Resolution 15: Finest
```

- Each cell has **1 parent** (unique path going UP)
- Each cell has **7 children** (multiple paths going DOWN)

### LCA (Least Common Ancestor)

The LCA of source and target is the coarsest cell containing both:

```python
def compute_lca(source_cell, target_cell):
    for res in range(min_res, -1, -1):
        if parent(source_cell, res) == parent(target_cell, res):
            return parent(source_cell, res)
```

### Phases

The phase-based algorithms track search progress:

- **Phase 0:** Initial (just started)
- **Phase 1:** Ascending (going UP toward LCA)
- **Phase 2:** At peak (reached LCA level)
- **Phase 3:** Descending (going DOWN toward target)

```
                     ┌─ Phase 2 ─┐
Phase 0 → Phase 1 ───┤           ├─── Phase 3
        (ascending)  └───────────┘   (descending)
                        (peak)
```
