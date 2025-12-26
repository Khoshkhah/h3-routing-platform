# Core Concepts (DuckDB)

This document defines the fundamental concepts used in the DuckDB-based shortcuts generation algorithm.

## Table of Contents

1. [Edge Model](#edge-model)
2. [H3 Cells](#h3-cells)
3. [Shortcuts](#shortcuts)
4. [Resolution and LCA](#resolution-and-lca)
5. [Algorithm Phases](#algorithm-phases)
6. [Cell Assignment Logic](#cell-assignment-logic)

---

## Edge Model

An **edge** represents a road segment in the network. Each edge has two H3 cells:

```
Edge: A road segment from point P1 to point P2

        P1 ──────────────▶ P2
     (start)    edge     (end)
        │                  │
        ▼                  ▼
    from_cell           to_cell
    (entry)             (exit)
```

### Definitions

| Term | Definition |
|------|------------|
| **from_cell** | The H3 cell where the edge **STARTS** |
| **to_cell** | The H3 cell where the edge **ENDS** |
| **from_edge** | In a shortcut A→B, edge A is the "from" edge |
| **to_edge** | In a shortcut A→B, edge B is the "to" edge |

### Direct Connection Rule

For shortcut (A, B) to be **direct** (A connects directly to B):
- `A.to_cell == B.from_cell`

---

## H3 Cells

H3 is a hierarchical hexagonal grid system. Each cell has a **resolution** from 0 (largest) to 15 (smallest).

### Special Values

| Value | Meaning |
|-------|---------|
| **Cell = 0** | Global scope (spans entire network) |
| **Resolution = -1** | Universal resolution for global shortcuts |

---

## Shortcuts

A **shortcut** represents a precomputed path between two edges. It can span multiple intermediate edges.

```
Shortcut: A precomputed PATH from edge A to edge B

  ┌─────────┐                           ┌─────────┐
  │ Edge A  │ ─ ─ ─ ─ (path) ─ ─ ─ ─ ─▶ │ Edge B  │
  │ (from)  │                           │  (to)   │
  └─────────┘                           └─────────┘
```

### Shortcut Columns

| Column | Type | Description |
|--------|------|-------------|
| `from_edge` | int | ID of the starting edge |
| `to_edge` | int | ID of the ending edge |
| `via_edge` | int | ID of the intermediate edge (for path reconstruction) |
| `cost` | float | Total travel cost from from_edge to to_edge |
| `cell` | long | H3 cell for query filtering |
| `inside` | byte | Direction: +1=upward, 0=lateral, -1=downward, -2=outer-only |

### Direction (`inside`) Logic

The `inside` column helps categorize the shortcut's relationship with the H3 hierarchy:

- **+1 (Upward)**: `lca_in > lca_out` (moving from finer to coarser cells)
- **0 (Lateral)**: `lca_in == lca_out` (moving between cells of same resolution)
- **-1 (Downward)**: `lca_in < lca_out` (moving from coarser to finer cells)
- **-2 (Outer-only)**: `lca_res > inner_res` (shortcut only exists at coarser resolutions than its junction)

---

## Resolution and LCA

### LCA (Lowest Common Ancestor)

The **LCA** of two cells is the coarsest cell that contains both.

### Shortcut Definitions

For a shortcut A→B:

1. **inner_cell**: LCA of `A.to_cell` and `B.from_cell` (The junction point)
2. **outer_cell**: LCA of `A.from_cell` and `B.to_cell` (The full extent)
3. **lca_res**: `max(lca_res_A, lca_res_B)` (The resolution where both edges first meet)

**Validity Rule:**
A shortcut is valid at resolution `R` if:
- `lca_res <= R` (shortcut is "active" at or above its join resolution)
- AND (`inner_res >= R` OR `outer_res >= R`) (shortcut exists within cells at this resolution)

**Deactivation Rule:**
If `lca_res > R`, the shortcut is considered "not yet active" for resolution `R`.
If both `inner_res < R` and `outer_res < R`, the shortcut is "deactivated" (too fine for this level).

---

## Algorithm Phases

The DuckDB implementation uses a **4-Phase Partitioned Approach** to handle large datasets in memory:

| Phase | Direction | Res Range | Strategy |
|-------|-----------|-----------|----------|
| **1. Local Forward** | 15 → 7 | Fine to Coarse | Partitioned by Res-7 cells |
| **2. Global Forward**| 6 → -1 | Coarse to Global| Hierarchical aggregation |
| **3. Global Backward**| 0 → 6 | Global to Coarse| Hierarchical expansion |
| **4. Local Backward** | 7 → 15 | Coarse to Fine | Partitioned by Res-7 cells |

---

## Cell Assignment Logic

### Forward Pass (Phases 1 & 2)

Assigns shortcuts to their parent H3 cells to find local optimal paths. 

```sql
-- Inner cell assignment
SELECT ... FROM ... WHERE lca_res <= res AND inner_parent IS NOT NULL

UNION ALL

-- Outer cell assignment (if different from inner)
SELECT ... FROM ... WHERE lca_res <= res AND outer_parent IS NOT NULL AND outer_parent != inner_parent

UNION ALL

-- Deactivation (beyond scope or not yet active)
SELECT NULL AS current_cell FROM ... WHERE (inner_res < res AND outer_res < res) OR lca_res > res
```

### Backward Pass (Phases 3 & 4)

Propagates global optimal costs down by expanding parent shortcuts into children. Uses a `LATERAL JOIN` to handle cases where a shortcut belongs to multiple child cells.

```sql
SELECT ... 
FROM parents
CROSS JOIN LATERAL (
    SELECT inner_parent AS current_cell WHERE inner_parent IN (child_list)
    UNION
    SELECT outer_parent WHERE outer_parent IN (child_list)
    UNION ALL
    SELECT NULL WHERE inner_parent NOT IN (child_list) AND outer_parent NOT IN (child_list)
) AS matched_cells
```

### Merging

After each resolution step, DuckDB performs a `GROUP BY (from_edge, to_edge)` and keeps the `MIN(cost)`, ensuring we always track the shortest possible path found so far.
