# Alternative Path Approach: Physical Segment Penalties

This document explains the "Physical Segment Penalty" approach for finding alternative paths. This strategy is **algorithm-agnostic**: it works equally well with unidirectional Dijkstra, bidirectional Dijkstra, or any shortcut-based routing engine.

## The Problem: Shortcut Overlap
In a hierachical routing engine (like one using Contraction Hierarchies or Shortcuts), multiple different "shortcuts" can represent almost identical physical routes. 

If we only penalize the **shortcut IDs** used in the shortest path:
1. The secondary search might simply pick a different shortcut ID that covers 99% of the same physical roads.
2. The result is an "alternative" path that looks identical to the shortest path on a map.

## The Solution: Physical Segment Penalties

The new approach shifts from penalizing technical IDs to penalizing physical reality.

### 1. Shortest Path Expansion
Instead of using the raw shortcut path, we call `expand_path_sp` immediately after finding the shortest route. This expands the sequence of high-level shortcuts into the full set of **base edges** (the actual physical road segments).

### 2. Physical Junction Penalties
We build a penalty set from every single node/edge in that **expanded path**.
- **Edge/Node Penalties**: We store the expanded path elements in a set for $O(1)$ lookup.
- **On-the-fly Penalty**: During the secondary search, whenever we consider a segment $u \to v$, we check if the physical destination $v$ is part of the expanded shortest path.

### 3. Why it works
Because we penalize based on the **expanded physical segments**, the algorithm cannot "cheat" by picking a different shortcut that lands on the same physical road. 

If a shortcut leads to a road segment you've already used, it gets penalized. This forces the Dijkstra search to veer away from the primary route's "gravity well" and explore truly distinct corridors in the road network.

## Why it gets good results
- **Physical Accuracy**: It accounts for the underlying geography, not just the graph topology.
- **High Diversity**: By avoiding any road used in the first trip, the second trip is often a completely different commute option.
- **Balance**: We don't penalize the source and target edges, ensuring the search can still start and end at the correct locations without penalty.

## Performance
Despite the expansion step, the approach remains extremely efficient:
1. **Search 1**: Finds shortest path (any algorithm).
2. **Expansion**: Fast lookup in `via` tables (sub-ms).
3. **Search 2**: Finds alternative with on-the-fly penalty checks.

The result is a production-ready approach that provides human-meaningful route choices regardless of the underlying search implementation.
