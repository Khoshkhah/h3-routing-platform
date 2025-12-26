"""
query_classic_trace - exact copy of query_classic with trace logging added.
Copy this into your notebook.
"""

def query_classic_trace(source_edge: int, target_edge: int):
    """Trace version of query_classic - exact same logic with logging."""
    
    # Compare with actual results first
    r_classic = query_classic(source_edge, target_edge)
    print(f"query_classic result: path={r_classic.path}, dist={r_classic.distance:.4f}")
    
    if source_edge == target_edge:
        return r_classic
    
    trace = []
    inf = float('inf')
    dist_fwd = {source_edge: 0.0}
    dist_bwd = {target_edge: get_edge_cost(target_edge)}
    parent_fwd = {source_edge: source_edge}
    parent_bwd = {target_edge: target_edge}
    
    pq_fwd = [(0.0, source_edge)]
    pq_bwd = [(dist_bwd[target_edge], target_edge)]
    
    best = inf
    meeting = None
    step = 0
    
    while pq_fwd or pq_bwd:
        step += 1
        
        # Forward step
        if pq_fwd:
            d, u = heappop(pq_fwd)
            
            # Exact same logic as query_classic
            if d > dist_fwd.get(u, inf):
                trace.append({'step': step, 'dir': 'FWD', 'edge': u, 'dist': d, 
                             'action': 'STALE', 'best': best, 'meeting': meeting})
            elif d < best:
                # Log expansion
                expanded = []
                for sc in fwd_adj.get(u, []):
                    if sc.inside != 1:
                        continue
                    v = sc.to_edge
                    nd = d + sc.cost
                    if nd < dist_fwd.get(v, inf):
                        dist_fwd[v] = nd
                        parent_fwd[v] = u
                        heappush(pq_fwd, (nd, v))
                        expanded.append(v)
                        if v in dist_bwd:
                            total = nd + dist_bwd[v]
                            if total < best:
                                best = total
                                meeting = v
                                trace.append({'step': step, 'dir': 'FWD', 'edge': u, 'dist': d,
                                             'action': f'MEETING at {v}', 'total': total,
                                             'fwd_dist': nd, 'bwd_dist': dist_bwd[v],
                                             'best': best, 'meeting': meeting})
                
                trace.append({'step': step, 'dir': 'FWD', 'edge': u, 'dist': d, 
                             'action': 'EXPAND', 'expanded': expanded, 
                             'best': best, 'meeting': meeting})
            else:
                trace.append({'step': step, 'dir': 'FWD', 'edge': u, 'dist': d, 
                             'action': 'd>=best', 'best': best, 'meeting': meeting})
        
        # Backward step
        if pq_bwd:
            d, u = heappop(pq_bwd)
            
            # Exact same logic as query_classic
            if d > dist_bwd.get(u, inf):
                trace.append({'step': step, 'dir': 'BWD', 'edge': u, 'dist': d, 
                             'action': 'STALE', 'best': best, 'meeting': meeting})
            elif d < best:
                # Log expansion
                expanded = []
                for sc in bwd_adj.get(u, []):
                    if sc.inside not in (-1, 0):
                        continue
                    prev = sc.from_edge
                    nd = d + sc.cost
                    if nd < dist_bwd.get(prev, inf):
                        dist_bwd[prev] = nd
                        parent_bwd[prev] = u
                        heappush(pq_bwd, (nd, prev))
                        expanded.append(prev)
                        if prev in dist_fwd:
                            total = dist_fwd[prev] + nd
                            if total < best:
                                best = total
                                meeting = prev
                                trace.append({'step': step, 'dir': 'BWD', 'edge': u, 'dist': d,
                                             'action': f'MEETING at {prev}', 'total': total,
                                             'fwd_dist': dist_fwd[prev], 'bwd_dist': nd,
                                             'best': best, 'meeting': meeting})
                
                trace.append({'step': step, 'dir': 'BWD', 'edge': u, 'dist': d, 
                             'action': 'EXPAND', 'expanded': expanded,
                             'best': best, 'meeting': meeting})
            else:
                trace.append({'step': step, 'dir': 'BWD', 'edge': u, 'dist': d, 
                             'action': 'd>=best', 'best': best, 'meeting': meeting})
        
        # Early termination
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best:
                trace.append({'step': step, 'action': 'EARLY_TERM', 'best': best, 'meeting': meeting})
                break
        elif not pq_fwd and not pq_bwd:
            break
        
        if step > 500:
            print("Trace limit reached")
            break
    
    print(f"Trace result: best={best:.4f}, meeting={meeting}")
    
    # Show meetings
    meetings = [t for t in trace if 'MEETING' in str(t.get('action', ''))]
    print(f"Meeting events: {len(meetings)}")
    for m in meetings:
        print(f"  {m}")
    
    return pd.DataFrame(trace)
