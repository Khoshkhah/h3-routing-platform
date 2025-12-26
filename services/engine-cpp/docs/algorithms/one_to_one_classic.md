# One-to-One Classic Algorithm

Bidirectional search on H3 spatial hierarchy shortcuts.

## Overview

This algorithm finds the shortest path between a single source edge and target edge using bidirectional search with `inside` directional filtering.

> [!NOTE]
> **H3-Based Hierarchical Routing**
> 
> This algorithm uses H3 spatial cells as the hierarchy instead of node contraction order.
> - **Forward search**: Only `inside=+1` (upward to coarser cells)
> - **Backward search**: Only `inside≤0` (downward/lateral)

```
         Source                              Target
           │                                   │
           ▼                                   ▼
    ┌──────────────┐                   ┌──────────────┐
    │ Forward      │                   │ Backward     │
    │ Search       │◄──── Meeting ────►│ Search       │
    │ (inside=+1)  │      Point        │ (inside≤0)   │
    └──────────────┘                   └──────────────┘
```

## Algorithm

### Initialization

```python
dist_fwd[source] = 0.0
dist_bwd[target] = target_edge_cost
pq_fwd.push((0.0, source))
pq_bwd.push((target_edge_cost, target))
```

### Forward Search
- Expand edges where `inside == +1` (upward to coarser H3 cells)
- Update distances and parent pointers
- Check for meeting with backward search

### Backward Search
- Expand edges where `inside == -1` (downward to finer cells)
- Also allow `inside == 0` (lateral) at high_cell
- Check for meeting with forward search

### Termination
Stop when both priority queues have top elements ≥ best found path.

## Pseudocode

```python
def query(source_edge, target_edge):
    dist_fwd = {source_edge: 0.0}
    dist_bwd = {target_edge: get_edge_cost(target_edge)}
    pq_fwd = [(0.0, source_edge)]
    pq_bwd = [(dist_bwd[target_edge], target_edge)]
    best = infinity
    meeting = None
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heappop(pq_fwd)
            if d >= best: continue
            
            for sc in fwd_adj[u]:
                if sc.inside != 1:
                    continue  # Only upward
                # ... expand
        
        # Backward step
        if pq_bwd:
            d, u = heappop(pq_bwd)
            if d >= best: continue
            
            for sc in bwd_adj[u]:
                if sc.inside not in (-1, 0):
                    continue  # Only downward/lateral
                # ... expand
    
    return reconstruct_path(meeting)
```

## Complexity

- **Time**: O((|E| + |V|) log |V|)
- **Space**: O(|V|) for distance arrays
