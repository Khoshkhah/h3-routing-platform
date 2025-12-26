"""
Resolution-based pruning optimization for query_pruned.

Instead of propagating full 8-byte cell through queue, we use 1-byte resolution.
Parent check becomes a simple integer comparison: node_res >= high_res means "in scope"
"""

# No get_cell_res needed - cell_res is precomputed in Shortcut dataclass

def query_pruned_fast(source_edge: int, target_edge: int):
    """
    Optimized pruned search using resolution instead of cell.
    
    Key optimization: parent_check is now just `node_res >= high_res`
    - 1 byte resolution instead of 8 byte cell
    - Simple integer comparison instead of H3 library calls
    """
    if source_edge == target_edge:
        return QueryResult(get_edge_cost(source_edge), [source_edge], True)
    
    high = compute_high_cell(source_edge, target_edge)
    
    inf = float('inf')
    dist_fwd = {source_edge: 0.0}
    dist_bwd = {target_edge: get_edge_cost(target_edge)}
    parent_fwd = {source_edge: source_edge}
    parent_bwd = {target_edge: target_edge}
    
    # Calculate initial resolutions from edge's lca_res
    src_meta = edge_meta[source_edge]
    src_res = src_meta['lca_res']  # Already a resolution!
    tgt_meta = edge_meta[target_edge]
    tgt_res = tgt_meta['lca_res']
    
    # Heap entries: (distance, edge_id, resolution) - 1 byte vs 8 bytes!
    pq_fwd = [(0.0, source_edge, src_res)]
    pq_bwd = [(dist_bwd[target_edge], target_edge, tgt_res)]
    
    best = inf
    meeting = None
    min_arrival_fwd = inf  # Track min arrival distance in forward direction
    min_arrival_bwd = inf  # Track min arrival distance in backward direction
      
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u, u_res = heappop(pq_fwd)
            
            if u in dist_bwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                total = d + dist_bwd[u]
                if total < best:
                    best = total
                    meeting = u
                    
            if d >= best:
                continue
            if d > dist_fwd.get(u, inf):
                continue  # stale
            
            # FAST PRUNING: simple resolution comparison
            if u_res < high.res:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                continue
            
            # At high resolution level - update min_arrival
            if u_res == high.res:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)

            for sc in fwd_adj.get(u, []):
                if sc.inside != 1:
                    continue
                v = sc.to_edge
                nd = d + sc.cost
                if nd < dist_fwd.get(v, inf):
                    dist_fwd[v] = nd
                    parent_fwd[v] = u
                    # Use precomputed cell_res from shortcut
                    heappush(pq_fwd, (nd, v, sc.cell_res))
                    
        # Backward step
        if pq_bwd:
            d, u, u_res = heappop(pq_bwd)
            
            if u in dist_fwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                total = dist_fwd[u] + d
                if total < best:
                    best = total
                    meeting = u
                    
            if d > dist_bwd.get(u, inf):
                continue  # stale
            if d >= best:
                continue
           
            # FAST PRUNING: check = (u_res >= high.res)
            check = (u_res >= high.res)
            
            # Update min_arrival when at high res or outside scope
            if u_res == high.res or (not check):
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
            
            for sc in bwd_adj.get(u, []):
                if sc.inside == -1 and check:
                    pass
                elif sc.inside == 0 and (u_res <= high.res):
                    pass
                elif sc.inside == -2 and (not check):
                    pass
                else:
                    continue
                
                prev = sc.from_edge
                nd = d + sc.cost
                if nd < dist_bwd.get(prev, inf):
                    dist_bwd[prev] = nd
                    parent_bwd[prev] = u
                    # Use precomputed cell_res from shortcut
                    heappush(pq_bwd, (nd, prev, sc.cell_res))
                   
        # Early termination - check if both directions can improve
        if best < inf:
            bound_fwd = min_arrival_fwd
            bound_bwd = min_arrival_bwd
            if pq_fwd:
                bound_fwd = min(bound_fwd, pq_fwd[0][0])
            if pq_bwd:
                bound_bwd = min(bound_bwd, pq_bwd[0][0])
                
            fwd_good = pq_fwd and (pq_fwd[0][0] + bound_bwd < best)
            bwd_good = pq_bwd and (pq_bwd[0][0] + bound_fwd < best)
            if not fwd_good and not bwd_good:
                break

    if meeting is None or best == inf:
        return QueryResult(-1, [], False)
    
    # Reconstruct path
    path = []
    curr = meeting
    while curr != source_edge:
        path.append(curr)
        curr = parent_fwd[curr]
    path.append(source_edge)
    path.reverse()
    
    curr = meeting
    while curr != target_edge:
        curr = parent_bwd[curr]
        path.append(curr)
    
    return QueryResult(best, path, True)


# Test the optimization
print("Testing resolution-based pruning optimization...")
print()

# Test cases
test_cases = [(100, 200), (216, 1000), (2006, 1828)]

for src, tgt in test_cases:
    result_orig = query_pruned(src, tgt)
    result_fast = query_pruned_fast(src, tgt)
    
    match = abs(result_orig.distance - result_fast.distance) < 0.001
    print(f"{src} -> {tgt}:")
    print(f"  Original: {result_orig.distance:.4f}")
    print(f"  Fast:     {result_fast.distance:.4f}")
    print(f"  Match: {'✓' if match else 'FAIL'}")
    print()
