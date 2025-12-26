# Data Formats

Input data for the routing engine comes from the [road-to-shortcut-duckdb](../../road-to-shortcut-duckdb) project.

---

## Shortcuts Parquet

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `from_edge` | int32 | Starting edge ID |
| `to_edge` | int32 | Ending edge ID |
| `via_edge` | int32 | Intermediate edge for path expansion (0 for base edges) |
| `cost` | float64 | Total travel cost |
| `cell` | int64 | H3 cell for query filtering |
| `inside` | int8 | Direction indicator |

### Inside Values

| Value | Direction | Description |
|-------|-----------|-------------|
| **+1** | Upward | Forward search only |
| **0** | Lateral | Backward search (at LCA resolution) |
| **-1** | Downward | Backward search only |
| **-2** | Base edge | Elementary shortcut (via_edge = 0) |

---

## Edge Metadata CSV

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` or `edge_index` | int32 | Edge identifier |
| `to_cell` | int64 | H3 cell at edge end |
| `from_cell` | int64 | H3 cell at edge start |
| `lca_res` | int32 | LCA resolution |
| `length` | float64 | Edge length (meters) |
| `cost` | float64 | Edge traversal cost |

---

## Query Output

```python
@dataclass
class QueryResult:
    distance: float        # Total path cost
    path: list[int]        # Edge IDs (shortcut path)
    reachable: bool        # True if path found
```

---

## Path Expansion

The shortcut path returned by the query algorithms needs to be expanded to base edges for display.

### via_edge Semantics

| Shortcut Type | via_edge Value | Meaning |
|---------------|----------------|---------|
| **Base edge** | `via_edge = to_edge` | Direct connection, cannot expand further |
| **Composite** | `via_edge ≠ to_edge` | Expand through via_edge: `(u,v)` → `(u,via)` + `(via,v)` |

### Expansion Algorithm

```python
def expand_pair(u, v):
    via = lookup[(u, v)]
    
    if via == v:  # Base edge: via_edge equals to_edge
        return [u, v]
    else:  # Composite: expand recursively
        left = expand_pair(u, via)
        right = expand_pair(via, v)
        return left + right[1:]  # Avoid duplicate junction
```
