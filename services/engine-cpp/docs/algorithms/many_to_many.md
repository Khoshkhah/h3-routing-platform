# Many-to-Many Algorithm

Multi-source/multi-target bidirectional search for KNN routing.

## Overview

This algorithm handles multiple candidate source and target edges simultaneously. Used when the exact source/target edges are unknown, such as:
- **KNN routing**: Find nearest road edges to a GPS coordinate
- **Multi-modal**: Multiple entry/exit points

```
     Sources                                    Targets
    ┌───────┐                                  ┌───────┐
    │ S1    │──┐                          ┌────│ T1    │
    │ S2    │──┼── Forward ◄── Meeting ──►┼────│ T2    │
    │ S3    │──┘   Search      Point      └────│ T3    │
    └───────┘                                  └───────┘
         │                                          │
    source_distances                         target_distances
    (approach costs)                         (egress costs)
```

## Algorithm

### Initialization

Initialize forward search from **all** source edges:

```python
for i, (src, dist) in enumerate(zip(source_edges, source_distances)):
    dist_fwd[src] = dist  # Approach distance from query point
    pq_fwd.push((dist, src))
```

Initialize backward search from **all** target edges:

```python
for j, (tgt, dist) in enumerate(zip(target_edges, target_distances)):
    edge_cost = get_edge_cost(tgt)
    init_dist = edge_cost + dist  # Edge cost + egress distance
    dist_bwd[tgt] = init_dist
    pq_bwd.push((init_dist, tgt))
```

### Search

Same as classic bidirectional, but:
- `inside == +1` for forward
- `inside == -1` or `inside == 0` for backward

> **Note**: H3 `parent_check` pruning is NOT used because there's no single high_cell when sources/targets span multiple regions.

### Termination Caveat

The standard early termination (`pq_fwd.top + pq_bwd.top >= best`) does **NOT** work correctly with multiple targets. The backward queue's top might be from a different target than optimal.

**Solution**: Disable early termination for multi-target, or use only for single-source single-target.

## Pseudocode

```python
def query_multi(source_edges, target_edges, source_dists, target_dists):
    # Initialize from all sources
    dist_fwd = {}
    pq_fwd = []
    for src, d in zip(source_edges, source_dists):
        dist_fwd[src] = d
        heappush(pq_fwd, (d, src))
    
    # Initialize from all targets
    dist_bwd = {}
    pq_bwd = []
    for tgt, d in zip(target_edges, target_dists):
        edge_cost = get_edge_cost(tgt)
        init = edge_cost + d
        dist_bwd[tgt] = init
        heappush(pq_bwd, (init, tgt))
    
    best = infinity
    meeting = None
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heappop(pq_fwd)
            if d >= best: continue
            
            for sc in fwd_adj[u]:
                if sc.inside != 1:
                    continue
                v = sc.to
                new_d = d + sc.cost
                if new_d < dist_fwd.get(v, inf):
                    dist_fwd[v] = new_d
                    heappush(pq_fwd, (new_d, v))
                    if v in dist_bwd:
                        total = new_d + dist_bwd[v]
                        if total < best:
                            best = total
                            meeting = v
        
        # Backward step
        if pq_bwd:
            d, u = heappop(pq_bwd)
            if d >= best: continue
            
            for sc in bwd_adj[u]:
                if sc.inside not in (-1, 0):
                    continue
                prev = sc.from_edge
                new_d = d + sc.cost
                if new_d < dist_bwd.get(prev, inf):
                    dist_bwd[prev] = new_d
                    heappush(pq_bwd, (new_d, prev))
                    if prev in dist_fwd:
                        total = dist_fwd[prev] + new_d
                        if total < best:
                            best = total
                            meeting = prev
        
        # No early termination for multi-target!
        # Must explore until both queues exceed best
        if not pq_fwd and not pq_bwd:
            break
        if pq_fwd and pq_fwd[0][0] >= best:
            pq_fwd = []
        if pq_bwd and pq_bwd[0][0] >= best:
            pq_bwd = []
    
    return reconstruct_path(meeting)
```

## Complexity

- **Time**: O((|S| + |T| + |E|) log |V|)
- **Space**: O(|V|)

Where S = source edges, T = target edges, E = edges explored
