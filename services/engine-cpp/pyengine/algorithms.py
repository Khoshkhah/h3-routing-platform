import heapq
from typing import Dict, List, Tuple, Optional, Set, Any
from .core import Shortcut, ShortestPathData
from .utils import find_lca, get_resolution, cell_to_parent

INF = float('inf')

class HighCell:
    def __init__(self, cell: int, res: int):
        self.cell = cell
        self.res = res

def compute_high_cell(source_edge: int, target_edge: int, data: ShortestPathData) -> HighCell:
    src_meta = data.edge_meta.get(source_edge)
    dst_meta = data.edge_meta.get(target_edge)
    
    if not src_meta or not dst_meta:
        return HighCell(0, -1)
    
    src_cell = src_meta.get("to_cell", 0)
    dst_cell = dst_meta.get("to_cell", 0)
    src_res = src_meta.get("lca_res", -1)
    dst_res = dst_meta.get("lca_res", -1)
    
    # Match legacy logic: if res < 0 or cell == 0, treat as 0
    if src_cell == 0 or src_res < 0:
        src_cell_p = 0
    else:
        src_cell_p = cell_to_parent(src_cell, src_res)
        
    if dst_cell == 0 or dst_res < 0:
        dst_cell_p = 0
    else:
        dst_cell_p = cell_to_parent(dst_cell, dst_res)
        
    if src_cell_p == 0 or dst_cell_p == 0:
        return HighCell(0, -1)
        
    lca = find_lca(src_cell_p, dst_cell_p)
    res = get_resolution(lca) if lca != 0 else -1
    return HighCell(lca, res)

# =============================================================================
# Helper: Generic Dijkstra Reconstruct
# =============================================================================
def _reconstruct_uni(parent: Dict[int, int], end_node: int) -> List[int]:
    path = []
    curr = end_node
    while curr != parent[curr]:
        path.append(curr)
        curr = parent[curr]
    path.append(curr)
    path.reverse()
    return path

def _reconstruct_bi(parent_fwd: Dict[int, int], parent_bwd: Dict[int, int], meeting_node: int) -> List[int]:
    path = []
    curr = meeting_node
    while curr != parent_fwd[curr]:
        path.append(curr)
        curr = parent_fwd[curr]
    path.append(curr)
    path.reverse()
    
    curr = meeting_node
    while curr != parent_bwd[curr]:
        curr = parent_bwd[curr]
        path.append(curr)
    return path

# =============================================================================
# Algorithm 1: Unidirectional Dijkstra (uni_dijkstra)
# =============================================================================
def query_uni_dijkstra(source_edge: int, target_edge: int, data: ShortestPathData) -> Tuple[float, List[int], bool]:
    if source_edge == target_edge:
        cost = data.edge_meta.get(source_edge, {}).get("cost", 0.0)
        return cost, [source_edge], True
        
    dist = {source_edge: 0.0}
    parent = {source_edge: source_edge}
    pq = [(0.0, source_edge)]
    
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, INF): continue
        if u == target_edge:
            cost = d + data.edge_meta.get(target_edge, {}).get("cost", 0.0)
            return cost, _reconstruct_uni(parent, u), True
            
        for sc in data.fwd_adj.get(u, []):
            nd = d + sc.cost
            if nd < dist.get(sc.to_edge, INF):
                dist[sc.to_edge] = nd
                parent[sc.to_edge] = u
                heapq.heappush(pq, (nd, sc.to_edge))
                
    return -1.0, [], False

# =============================================================================
# Algorithm 1.5: Bidirectional Dijkstra (bi_dijkstra)
# Matches C++ query_bidijkstra (lines 1041-1152)
# =============================================================================
def query_bi_dijkstra(source_edge: int, target_edge: int, data: ShortestPathData) -> Tuple[float, List[int], bool]:
    """Bidirectional Dijkstra without inside filtering. Matches C++ query_bidijkstra."""
    if source_edge == target_edge:
        cost = data.edge_meta.get(source_edge, {}).get("cost", 0.0)
        return cost, [source_edge], True
    
    dist_fwd = {source_edge: 0.0}
    parent_fwd = {source_edge: source_edge}
    pq_fwd = [(0.0, source_edge)]
    
    tgt_cost = data.edge_meta.get(target_edge, {}).get("cost", 0.0)
    dist_bwd = {target_edge: tgt_cost}
    parent_bwd = {target_edge: target_edge}
    pq_bwd = [(tgt_cost, target_edge)]
    
    best = INF
    meeting = None
    
    while pq_fwd and pq_bwd:
        if pq_fwd[0][0] + pq_bwd[0][0] >= best: break
        
        # Alternating: process queue with smaller top distance
        if pq_fwd[0][0] <= pq_bwd[0][0]:
            d, u = heapq.heappop(pq_fwd)
            if d > dist_fwd.get(u, INF): continue
            
            for sc in data.fwd_adj.get(u, []):
                nd = d + sc.cost
                if nd < dist_fwd.get(sc.to_edge, INF):
                    dist_fwd[sc.to_edge] = nd
                    parent_fwd[sc.to_edge] = u
                    heapq.heappush(pq_fwd, (nd, sc.to_edge))
                    
                    if sc.to_edge in dist_bwd:
                        total = nd + dist_bwd[sc.to_edge]
                        if total < best: best = total; meeting = sc.to_edge
        else:
            d, u = heapq.heappop(pq_bwd)
            if d > dist_bwd.get(u, INF): continue
            
            for sc in data.bwd_adj.get(u, []):
                nd = d + sc.cost
                if nd < dist_bwd.get(sc.from_edge, INF):
                    dist_bwd[sc.from_edge] = nd
                    parent_bwd[sc.from_edge] = u
                    heapq.heappush(pq_bwd, (nd, sc.from_edge))
                    
                    if sc.from_edge in dist_fwd:
                        total = dist_fwd[sc.from_edge] + nd
                        if total < best: best = total; meeting = sc.from_edge
    
    if meeting is None: return -1.0, [], False
    return best, _reconstruct_bi(parent_fwd, parent_bwd, meeting), True

# =============================================================================
# Algorithm 2: bi_classic - Bidirectional Hierarchical (classic)
# Matches C++ query_classic (lines 734-866)
# =============================================================================
def query_classic(source_edge: int, target_edge: int, data: ShortestPathData) -> Tuple[float, List[int], bool]:
    """Bidirectional Dijkstra with inside filtering. Matches C++ query_classic."""
    if source_edge == target_edge:
        cost = data.edge_meta.get(source_edge, {}).get("cost", 0.0)
        return cost, [source_edge], True
    
    dist_fwd = {source_edge: 0.0}
    parent_fwd = {source_edge: source_edge}
    pq_fwd = [(0.0, source_edge)]
    
    tgt_cost = data.edge_meta.get(target_edge, {}).get("cost", 0.0)
    dist_bwd = {target_edge: tgt_cost}
    parent_bwd = {target_edge: target_edge}
    pq_bwd = [(tgt_cost, target_edge)]
    
    best = INF
    meeting = None
    
    # Main loop: process BOTH queues per iteration (matching C++)
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heapq.heappop(pq_fwd)
            
            if d > dist_fwd.get(u, INF): pass  # Skip stale
            elif d >= best: pass  # Per-node pruning
            else:
                for sc in data.fwd_adj.get(u, []):
                    if sc.inside != 1: continue  # Inside filter
                    
                    nd = d + sc.cost
                    if nd < dist_fwd.get(sc.to_edge, INF):
                        dist_fwd[sc.to_edge] = nd
                        parent_fwd[sc.to_edge] = u
                        heapq.heappush(pq_fwd, (nd, sc.to_edge))
                        
                        if sc.to_edge in dist_bwd:
                            total = nd + dist_bwd[sc.to_edge]
                            if total < best: best = total; meeting = sc.to_edge
        
        # Backward step
        if pq_bwd:
            d, u = heapq.heappop(pq_bwd)
            
            if d > dist_bwd.get(u, INF): pass
            elif d >= best: pass
            else:
                for sc in data.bwd_adj.get(u, []):
                    if sc.inside not in [-1, 0]: continue  # Inside filter
                    
                    nd = d + sc.cost
                    if nd < dist_bwd.get(sc.from_edge, INF):
                        dist_bwd[sc.from_edge] = nd
                        parent_bwd[sc.from_edge] = u
                        heapq.heappush(pq_bwd, (nd, sc.from_edge))
                        
                        if sc.from_edge in dist_fwd:
                            total = dist_fwd[sc.from_edge] + nd
                            if total < best: best = total; meeting = sc.from_edge
        
        # Early termination
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best: break
        elif not pq_fwd and not pq_bwd:
            break
    
    if meeting is None: return -1.0, [], False
    return best, _reconstruct_bi(parent_fwd, parent_bwd, meeting), True

# =============================================================================
# Algorithm 3: uni_lca - Unidirectional LCA-targeted
# =============================================================================
def query_uni_lca(source_edge: int, target_edge: int, data: ShortestPathData) -> Tuple[float, List[int], bool]:
    if source_edge == target_edge:
        cost = data.edge_meta.get(source_edge, {}).get("cost", 0.0)
        return cost, [source_edge], True
        
    high = compute_high_cell(source_edge, target_edge, data)
    src_res = data.edge_meta.get(source_edge, {}).get("lca_res", -1)
    
    dist = {source_edge: 0.0}
    parent = {source_edge: source_edge}
    pq = [(0.0, source_edge, src_res, 0)] # (dist, edge, res, phase)
    
    while pq:
        d, u, u_res, phase = heapq.heappop(pq)
        if d > dist.get(u, INF): continue
        if u == target_edge:
            return d + data.edge_meta.get(target_edge, {}).get("cost", 0.0), _reconstruct_uni(parent, u), True
            
        for sc in data.fwd_adj.get(u, []):
            allowed = False
            next_phase = phase
            if phase == 0 or phase == 1:
                if sc.lca_res > high.res and sc.inside == 1: allowed = True; next_phase = 1
                elif sc.lca_res <= high.res and sc.inside == 1: allowed = True; next_phase = 2
                elif sc.inside != 1: allowed = True; next_phase = 2
            elif phase == 2:
                if sc.inside != 1: allowed = True; next_phase = 3
            elif phase == 3:
                if sc.inside == -1: allowed = True; next_phase = 3
                    
            if not allowed: continue
            
            nd = d + sc.cost
            if nd < dist.get(sc.to_edge, INF):
                dist[sc.to_edge] = nd
                parent[sc.to_edge] = u
                heapq.heappush(pq, (nd, sc.to_edge, sc.lca_res, next_phase))
                
    return -1.0, [], False

# =============================================================================
# Algorithm 4: bi_lca - Bidirectional LCA-targeted
# =============================================================================
def query_bi_lca(source_edge: int, target_edge: int, data: ShortestPathData) -> Tuple[float, List[int], bool]:
    if source_edge == target_edge:
        cost = data.edge_meta.get(source_edge, {}).get("cost", 0.0)
        return cost, [source_edge], True
        
    high = compute_high_cell(source_edge, target_edge, data)
    src_res = data.edge_meta.get(source_edge, {}).get("lca_res", -1)
    tgt_res = data.edge_meta.get(target_edge, {}).get("lca_res", -1)
    
    pq_fwd = [(0.0, source_edge, src_res, 0)]
    tgt_cost = data.edge_meta.get(target_edge, {}).get("cost", 0.0)
    pq_bwd = [(tgt_cost, target_edge, tgt_res, 0)]
    
    dist_fwd = {source_edge: 0.0}
    dist_bwd = {target_edge: tgt_cost}
    
    parent_fwd = {source_edge: source_edge}
    parent_bwd = {target_edge: target_edge}
    
    best_total = INF
    meeting_node = None
    
    while pq_fwd and pq_bwd:
        if pq_fwd[0][0] + pq_bwd[0][0] >= best_total: break
        
        # Forward step
        if pq_fwd[0][0] <= pq_bwd[0][0]:
            d, u, u_res, phase = heapq.heappop(pq_fwd)
            if d > dist_fwd.get(u, INF): continue
            for sc in data.fwd_adj.get(u, []):
                allowed = False
                next_phase = phase
                if phase == 0 or phase == 1:
                    if sc.lca_res > high.res and sc.inside == 1: allowed = True; next_phase = 1
                    elif sc.lca_res <= high.res and sc.inside == 1: allowed = True; next_phase = 2
                    elif sc.inside != 1: allowed = True; next_phase = 2
                elif phase == 2:
                    if sc.inside != 1: allowed = True; next_phase = 3
                elif phase == 3:
                    if sc.inside == -1: allowed = True; next_phase = 3
                
                if not allowed: continue
                nd = d + sc.cost
                if nd < dist_fwd.get(sc.to_edge, INF):
                    dist_fwd[sc.to_edge] = nd
                    parent_fwd[sc.to_edge] = u
                    heapq.heappush(pq_fwd, (nd, sc.to_edge, sc.lca_res, next_phase))
                    if sc.to_edge in dist_bwd:
                        total = nd + dist_bwd[sc.to_edge]
                        if total < best_total: best_total = total; meeting_node = sc.to_edge
        # Backward step
        else:
            d, u, u_res, phase = heapq.heappop(pq_bwd)
            if d > dist_bwd.get(u, INF): continue
            for sc in data.bwd_adj.get(u, []):
                allowed = False
                next_phase = phase
                if phase == 0 or phase == 1:
                    if sc.lca_res > high.res and sc.inside == -1: allowed = True; next_phase = 1
                    elif sc.lca_res <= high.res and sc.inside == -1: allowed = True; next_phase = 2
                    elif sc.inside != -1: allowed = True; next_phase = 2
                elif phase == 2:
                    if sc.inside != -1: allowed = True; next_phase = 3
                elif phase == 3:
                    if sc.inside == 1: allowed = True; next_phase = 3
                
                if not allowed: continue
                nd = d + sc.cost
                if nd < dist_bwd.get(sc.from_edge, INF):
                    dist_bwd[sc.from_edge] = nd
                    parent_bwd[sc.from_edge] = u
                    heapq.heappush(pq_bwd, (nd, sc.from_edge, sc.lca_res, next_phase))
                    if sc.from_edge in dist_fwd:
                        total = nd + dist_fwd[sc.from_edge]
                        if total < best_total: best_total = total; meeting_node = sc.from_edge
                        
    if meeting_node is None: return -1.0, [], False
    return best_total, _reconstruct_bi(parent_fwd, parent_bwd, meeting_node), True

# =============================================================================
# Algorithm 5: bi_lca_res - Bidirectional with resolution pruning
# =============================================================================
def query_bi_lca_res(source_edge: int, target_edge: int, data: ShortestPathData) -> Tuple[float, List[int], bool]:
    if source_edge == target_edge:
        cost = data.edge_meta.get(source_edge, {}).get("cost", 0.0)
        return cost, [source_edge], True

    high = compute_high_cell(source_edge, target_edge, data)
    src_res = data.edge_meta.get(source_edge, {}).get("lca_res", -1)
    tgt_res = data.edge_meta.get(target_edge, {}).get("lca_res", -1)
    
    dist_fwd = {source_edge: 0.0}
    parent_fwd = {source_edge: source_edge}
    pq_fwd = [(0.0, source_edge, src_res)]
    
    tgt_cost = data.edge_meta.get(target_edge, {}).get("cost", 0.0)
    dist_bwd = {target_edge: tgt_cost}
    parent_bwd = {target_edge: target_edge}
    pq_bwd = [(tgt_cost, target_edge, tgt_res)]
    
    best = INF
    meeting_node = None
    min_arrival_fwd = INF
    min_arrival_bwd = INF
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u, u_res = heapq.heappop(pq_fwd)
            if u in dist_bwd:
                min_arrival_fwd = min(dist_fwd.get(u, INF), min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                total = d + dist_bwd[u]
                if total < best: best = total; meeting_node = u
            
            if d > dist_fwd.get(u, INF) or d >= best: pass
            else:
                if u_res < high.res:
                    min_arrival_fwd = min(dist_fwd.get(u, INF), min_arrival_fwd)
                else:
                    if u_res == high.res: min_arrival_fwd = min(dist_fwd.get(u, INF), min_arrival_fwd)
                    for sc in data.fwd_adj.get(u, []):
                        if sc.inside != 1: continue
                        nd = d + sc.cost
                        if nd < dist_fwd.get(sc.to_edge, INF):
                            dist_fwd[sc.to_edge] = nd
                            parent_fwd[sc.to_edge] = u
                            heapq.heappush(pq_fwd, (nd, sc.to_edge, sc.lca_res))
                            if sc.to_edge in dist_bwd:
                                total = nd + dist_bwd[sc.to_edge]
                                if total < best: best = total; meeting_node = sc.to_edge
        
        # Backward step
        if pq_bwd:
            d, u, u_res = heapq.heappop(pq_bwd)
            if u in dist_fwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd.get(u, INF), min_arrival_bwd)
                total = dist_fwd[u] + d
                if total < best: best = total; meeting_node = u
                
            if d > dist_bwd.get(u, INF) or d >= best: continue
            
            check = (u_res >= high.res)
            if u_res == high.res or not check: min_arrival_bwd = min(dist_bwd.get(u, INF), min_arrival_bwd)
            
            for sc in data.bwd_adj.get(u, []):
                allowed = False
                if sc.inside == -1 and check: allowed = True
                elif sc.inside == 0 and u_res <= high.res: allowed = True
                elif sc.inside == -2 and not check: allowed = True
                
                if not allowed: continue
                nd = d + sc.cost
                if nd < dist_bwd.get(sc.from_edge, INF):
                    dist_bwd[sc.from_edge] = nd
                    parent_bwd[sc.from_edge] = u
                    heapq.heappush(pq_bwd, (nd, sc.from_edge, sc.lca_res))
                    if sc.from_edge in dist_fwd:
                        total = dist_fwd[sc.from_edge] + nd
                        if total < best: best = total; meeting_node = sc.from_edge
                        
        # Early termination
        if best < INF:
            b_fwd = min(min_arrival_fwd, pq_fwd[0][0] if pq_fwd else INF)
            b_bwd = min(min_arrival_bwd, pq_bwd[0][0] if pq_bwd else INF)
            if (pq_fwd and pq_fwd[0][0] + b_bwd >= best) and (pq_bwd and pq_bwd[0][0] + b_fwd >= best):
                break
                
    if meeting_node is None: return -1.0, [], False
    return best, _reconstruct_bi(parent_fwd, parent_bwd, meeting_node), True

# =============================================================================
# Algorithm 6: Many-to-Many Classic (m2m)
# =============================================================================
def query_m2m(source_edges: List[int], target_edges: List[int], data: ShortestPathData) -> Tuple[float, List[int], bool]:
    return _m2m_classic(source_edges, target_edges, data, inside_filter=True)

# =============================================================================
# Algorithm 7: Alternative Path (penalty method using uni_lca base)
# =============================================================================
def query_alternative(
    source_edge: int,
    target_edge: int,
    data: ShortestPathData,
    penalty_factor: float = 2.0,
    shortest_path_expanded: List[int] = None
) -> Tuple[float, List[int], bool]:
    """
    Find alternative path using uni_lca-based traversal with penalties.
    Uses phase-based approach for better path diversity.
    """
    if shortest_path_expanded is None:
        _, sp, success = query_uni_lca(source_edge, target_edge, data)
        if not success: return -1.0, [], False
        from .core import expand_path
        shortest_path_expanded = expand_path(sp, data.via_lookup)
    
    if source_edge == target_edge:
        cost = data.edge_meta.get(source_edge, {}).get("cost", 0.0)
        return cost, [source_edge], True
    
    # Build penalty set, excluding endpoints
    penalty_set = set(shortest_path_expanded)
    penalty_set.discard(source_edge)
    penalty_set.discard(target_edge)
    
    high = compute_high_cell(source_edge, target_edge, data)
    src_res = data.edge_meta.get(source_edge, {}).get("lca_res", -1)
    
    dist = {source_edge: 0.0}
    parent = {source_edge: source_edge}
    pq = [(0.0, source_edge, src_res, 0)]  # (dist, edge, res, phase)
    
    while pq:
        d, u, u_res, phase = heapq.heappop(pq)
        if d > dist.get(u, INF): continue
        
        if u == target_edge:
            return d + data.edge_meta.get(target_edge, {}).get("cost", 0.0), _reconstruct_uni(parent, u), True
            
        for sc in data.fwd_adj.get(u, []):
            allowed = False
            next_phase = phase
            
            # Phase transitions (same as query_uni_lca)
            if phase == 0 or phase == 1:
                if sc.lca_res > high.res and sc.inside == 1: allowed = True; next_phase = 1
                elif sc.lca_res <= high.res and sc.inside == 1: allowed = True; next_phase = 2
                elif sc.inside != 1: allowed = True; next_phase = 2
            elif phase == 2:
                if sc.inside != 1: allowed = True; next_phase = 3
            elif phase == 3:
                if sc.inside == -1: allowed = True; next_phase = 3
                    
            if not allowed: continue
            
            # Apply penalty to edges overlapping with shortest path
            cost = sc.cost
            if sc.to_edge in penalty_set:
                cost *= penalty_factor
            elif sc.via_edge != 0 and sc.via_edge in penalty_set:
                cost *= penalty_factor
            elif u in penalty_set:
                cost *= penalty_factor
            
            nd = d + cost
            if nd < dist.get(sc.to_edge, INF):
                dist[sc.to_edge] = nd
                parent[sc.to_edge] = u
                heapq.heappush(pq, (nd, sc.to_edge, sc.lca_res, next_phase))
                
    return -1.0, [], False

def _m2m_classic(
    sources: List[int],
    targets: List[int],
    data: ShortestPathData,
    inside_filter: bool = True,
    penalty_set: Optional[Set[int]] = None,
    penalty_factor: float = 2.0
) -> Tuple[float, List[int], bool]:
    """
    Bidirectional Dijkstra matching C++ query_classic structure.
    
    Key differences from previous implementation:
    - Processes BOTH queues per iteration (not alternating)
    - Uses `or` termination (continues if EITHER queue has work)
    - Has per-node `d >= best` pruning
    """
    pq_fwd = []
    dist_fwd = {}
    parent_fwd = {}
    for s in sources:
        pq_fwd.append((0.0, s))
        dist_fwd[s] = 0.0
        parent_fwd[s] = s
    heapq.heapify(pq_fwd)
    
    pq_bwd = []
    dist_bwd = {}
    parent_bwd = {}
    for t in targets:
        tc = data.edge_meta.get(t, {}).get("cost", 0.0)
        pq_bwd.append((tc, t))
        dist_bwd[t] = tc
        parent_bwd[t] = t
    heapq.heapify(pq_bwd)
    
    best = INF
    meeting = None
    
    # Check source/target overlap
    common = set(sources) & set(targets)
    if common:
        for n in common:
            c = data.edge_meta.get(n, {}).get("cost", 0.0)
            if c < best: best = c; meeting = n
            
    # Main loop: process BOTH queues per iteration (matching C++)
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heapq.heappop(pq_fwd)
            
            if d > dist_fwd.get(u, INF): pass  # Skip stale entry
            elif d >= best: pass  # Per-node pruning (C++ line 772)
            else:
                for sc in data.fwd_adj.get(u, []):
                    if inside_filter and sc.inside != 1: continue
                    
                    cost = sc.cost
                    if penalty_set and (sc.to_edge in penalty_set or (sc.via_edge != 0 and sc.via_edge in penalty_set)):
                        cost *= penalty_factor
                    
                    nd = d + cost
                    if nd < dist_fwd.get(sc.to_edge, INF):
                        dist_fwd[sc.to_edge] = nd
                        parent_fwd[sc.to_edge] = u
                        heapq.heappush(pq_fwd, (nd, sc.to_edge))
                        
                        if sc.to_edge in dist_bwd:
                            total = nd + dist_bwd[sc.to_edge]
                            if total < best: best = total; meeting = sc.to_edge
        
        # Backward step
        if pq_bwd:
            d, u = heapq.heappop(pq_bwd)
            
            if d > dist_bwd.get(u, INF): pass  # Skip stale entry
            elif d >= best: pass  # Per-node pruning (C++ line 805)
            else:
                for sc in data.bwd_adj.get(u, []):
                    if inside_filter and sc.inside not in [-1, 0]: continue
                    
                    cost = sc.cost
                    if penalty_set and (sc.from_edge in penalty_set or (sc.via_edge != 0 and sc.via_edge in penalty_set)):
                        cost *= penalty_factor
                    
                    nd = d + cost
                    if nd < dist_bwd.get(sc.from_edge, INF):
                        dist_bwd[sc.from_edge] = nd
                        parent_bwd[sc.from_edge] = u
                        heapq.heappush(pq_bwd, (nd, sc.from_edge))
                        
                        if sc.from_edge in dist_fwd:
                            total = dist_fwd[sc.from_edge] + nd
                            if total < best: best = total; meeting = sc.from_edge
        
        # Early termination (C++ lines 836-840)
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best: break
        elif not pq_fwd and not pq_bwd:
            break
                        
    if meeting is None: return -1.0, [], False
    return best, _reconstruct_bi(parent_fwd, parent_bwd, meeting), True

# Aliases
def query_pruned(s, t, d): return query_bi_lca_res(s, t, d)
