# One-to-One Pruned Algorithm

Enhanced bidirectional search with H3 spatial hierarchy pruning.

## Overview

This algorithm extends the classic approach by adding **H3 spatial pruning**. Before searching, it computes the **high cell** — the lowest common ancestor (LCA) of source and target H3 cells — and prunes nodes outside this region.

> [!NOTE]
> **H3-Based Hierarchical Routing**
> 
> The hierarchy comes from H3 hexagonal grid resolutions (0-15). Coarser cells (lower resolution) are "higher" in the hierarchy.

## H3 Resolution Semantics

> [!IMPORTANT]
> **Resolution Comparison Rule**
> 
> **Higher resolution = Smaller cell = Deeper in hierarchy**
> 
> - Resolution 0: Largest cells (~4,000 km²)
> - Resolution 15: Smallest cells (~1 m²)
> 
> When checking if a node is "inside" a high cell:
> ```
> node_res >= high_res  →  node could be inside high cell
> ```
> 
> For example: If high_res=6 and node_res=8, the node cell (res 8) is smaller 
> and could be a child of the high cell (res 6).

## Key Difference from Classic

| Classic | Pruned |
|---------|--------|
| Only `inside` filtering | `inside` + `parent_check` on popped node |
| Searches entire graph | Restricted to high_cell region |
| More edges explored | Fewer edges, faster queries |

## Inside Values

| Value | Meaning | Direction |
|-------|---------|-----------|
| `+1` | Upward shortcut (to coarser cell) | Forward only |
| `0` | Lateral shortcut (same level) | At high_cell or global |
| `-1` | Downward shortcut (to finer cell) | Backward with check |
| `-2` | Edge shortcut (direct edge) | Backward when global |

## Algorithm

### 1. Compute High Cell

```python
def compute_high_cell(source_edge, target_edge):
    src_meta = edge_metadata[source_edge]
    dst_meta = edge_metadata[target_edge]
    
    src_cell = h3.cell_to_parent(src_meta.to_cell, src_meta.lca_res)
    dst_cell = h3.cell_to_parent(dst_meta.to_cell, dst_meta.lca_res)
    
    # Handle global edges (cell=0)
    if src_cell == 0 or dst_cell == 0:
        return HighCell(cell=0, res=-1)  # Disable pruning
    
    lca = find_lca(src_cell, dst_cell)
    return HighCell(cell=lca, res=h3.get_resolution(lca))
```

### 2. Parent Check

Applied to the **popped node** (not the shortcut being expanded):

```python
def parent_check(node_cell, high_cell, high_res):
    """Return True if node is within the high_cell region."""
    if high_cell == 0 or high_res < 0:
        return True  # Pruning disabled
    if node_cell == 0:
        return False  
    
    parent = h3.cell_to_parent(node_cell, high_res)
    return parent == high_cell
```

#### Fast Resolution-Based Check (Optimized)

Instead of storing full cells (8 bytes), store just resolution (1 byte):

```python
def parent_check_fast(node_res, high_res):
    """Fast check using resolution only - no H3 calls needed."""
    if high_res < 0:
        return True   # No pruning constraint
    if node_res < 0:
        return False  # Node has no valid cell
    return node_res >= high_res  # Node at same or finer resolution
```

## Pseudocode

```python
def query_pruned(source_edge, target_edge):
    high = compute_high_cell(source_edge, target_edge)
    
    dist_fwd = {source_edge: 0.0}
    dist_bwd = {target_edge: get_edge_cost(target_edge)}
    pq_fwd = [(0.0, source_edge, src_cell)]
    pq_bwd = [(dist_bwd[target_edge], target_edge, tgt_cell)]
    
    best = inf
    meeting = None
    min_arrival_fwd = inf
    min_arrival_bwd = inf
    
    while pq_fwd or pq_bwd:
        # === FORWARD STEP ===
        if pq_fwd:
            d, u, u_cell = heappop(pq_fwd)
            
            # Check for meeting BEFORE other checks
            if u in dist_bwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                if d + dist_bwd[u] <= best:
                    best = d + dist_bwd[u]
                    meeting = u
            
            if d >= best: continue
            if d > dist_fwd[u]: continue  # stale
            
            # PRUNING: Check popped node against high_cell
            if not parent_check(u_cell, high.cell, high.res):
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                continue
            
            if u_cell == high.cell:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
            
            for sc in fwd_adj[u]:
                if sc.inside != 1:
                    continue
                # ... expand shortcut
        
        # === BACKWARD STEP ===
        if pq_bwd:
            d, u, u_cell = heappop(pq_bwd)
            
            # Check for meeting BEFORE other checks
            if u in dist_fwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                if dist_fwd[u] + d < best:
                    best = dist_fwd[u] + d
                    meeting = u
            
            if d > dist_bwd[u]: continue  # stale
            if d >= best: continue
            
            # PRUNING: Check popped node against high_cell
            check = parent_check(u_cell, high.cell, high.res)
            
            if u_cell == high.cell or (not check):
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
            
            at_high_cell = (u_cell == high.cell)
            
            for sc in bwd_adj[u]:
                # Backward filtering rules:
                # inside == -1: Downward, only when parent_check passes
                # inside == 0:  Lateral, at high_cell OR when check fails (global)
                # inside == -2: Edge shortcut, only when check fails (global)
                if sc.inside == -1 and check:
                    pass  # Downward allowed when check passes
                elif sc.inside == 0 and (at_high_cell or (not check)):
                    pass  # Lateral at high_cell or global edge
                elif sc.inside == -2 and (not check):
                    pass  # Edge shortcuts when global
                else:
                    continue
                
                # ... expand shortcut
        
        # === EARLY TERMINATION ===
        if best < inf:
            bound_fwd = min(min_arrival_fwd, pq_fwd[0][0]) if pq_fwd else min_arrival_fwd
            bound_bwd = min(min_arrival_bwd, pq_bwd[0][0]) if pq_bwd else min_arrival_bwd
            
            fwd_good = pq_fwd and (pq_fwd[0][0] + bound_bwd < best)
            bwd_good = pq_bwd and (pq_bwd[0][0] + bound_fwd < best)
            if not fwd_good and not bwd_good:
                break
    
    return reconstruct_path(meeting)
```

## Key Points

1. **Meeting check FIRST**: Update best/meeting BEFORE checking stale/d>=best
2. **parent_check on popped node**: Prune when node is outside high_cell region
3. **Global edge handling**: Edges with `cell=0` or failed `parent_check`:
   - Update `min_arrival` bounds
   - Allow `inside=0` (lateral) and `inside=-2` (edge shortcuts)
4. **Forward**: Only `inside == +1` shortcuts
5. **Backward**: 
   - `inside == -1` when check passes (normal downward)
   - `inside == 0` (lateral) at high_cell OR when check fails
   - `inside == -2` when check fails (global edges)

## Early Termination

The algorithm uses bounds-based early termination:
- `min_arrival_fwd/bwd`: Minimum distance at which each direction has "arrived" at the meeting region
- Terminate when neither direction can improve `best`

## Complexity

- **Time**: O((|E'| + |V'|) log |V'|) where E', V' are in high_cell region
- **Speedup**: Typically 1.3-2x faster than classic for local queries
- Speedup depends on how localized the query is (higher high_res = better pruning)
