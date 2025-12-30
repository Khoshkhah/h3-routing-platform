"""
Routing Algorithms Library

This module provides all routing algorithms for the H3 Routing Platform.

Algorithms:
- dijkstra_sp: Ground truth, no filtering
- bi_dijkstra_sp: Bidirectional Dijkstra (no filtering)
- bi_classic_sp: Bidirectional with inside filtering only
- bi_classic_alt_sp: Alternative path using penalty method (thread-safe)
- bi_dijkstra_alt_sp: Alternative path using standard bidirectional Dijkstra (no filtering)
- bi_lca_res_sp: Bidirectional with LCA resolution pruning
- uni_lca_sp: Unidirectional phase-based with LCA
- bi_lca_sp: Bidirectional phase-based with LCA (fastest)
- m2m_classic_sp: Many-to-many with inside filtering
- load_via_lookup: Load via_edge lookup table
- expand_path_sp: Expand shortcut path to base edges


Usage:
    from routing_algorithms_sp import dijkstra_sp, bi_lca_sp
    
    cost, path, success = dijkstra_sp(con, source, target)
    cost, path, success = bi_lca_sp(con, source, target)
"""

import heapq
from typing import Dict, List, Tuple, Optional, Set
import duckdb
import h3


# =============================================================================
# CONSTANTS
# =============================================================================

INF = float('inf')


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def compute_high_cell(con: duckdb.DuckDBPyConnection, source_edge: int, target_edge: int) -> Tuple[int, int]:
    """Compute the LCA (high cell) for source and target edges."""
    result = con.execute("""
        SELECT 
            e1.lca_res AS src_res,
            e1.to_cell AS src_cell,
            e2.lca_res AS tgt_res,
            e2.to_cell AS tgt_cell
        FROM edges e1, edges e2
        WHERE e1.id = ? AND e2.id = ?
    """, [source_edge, target_edge]).fetchone()
    
    if not result:
        return 0, -1
    
    src_res, src_cell, tgt_res, tgt_cell = result
    
    # Get cells at their LCA resolutions
    if src_cell and src_res >= 0:
        src_cell = h3.cell_to_parent(h3.int_to_str(src_cell), src_res)
    else:
        src_cell = None
        
    if tgt_cell and tgt_res >= 0:
        tgt_cell = h3.cell_to_parent(h3.int_to_str(tgt_cell), tgt_res)
    else:
        tgt_cell = None
    
    if not src_cell or not tgt_cell:
        return 0, -1
    
    # Find LCA
    lca = 0
    for res in range(15, -1, -1):
        p1 = h3.cell_to_parent(src_cell, res) if h3.get_resolution(src_cell) >= res else None
        p2 = h3.cell_to_parent(tgt_cell, res) if h3.get_resolution(tgt_cell) >= res else None
        if p1 and p2 and p1 == p2:
            lca = p1
            break
    
    if lca == 0:
        return 0, -1
    else:   
        return h3.str_to_int(lca), h3.get_resolution(lca)


def get_edge_cost(con: duckdb.DuckDBPyConnection, edge_id: int) -> float:
    """Get the cost of a single edge."""
    result = con.execute("SELECT cost FROM edges WHERE id = ?", [edge_id]).fetchone()
    return result[0] if result else 0.0


def get_edge_res(con: duckdb.DuckDBPyConnection, edge_id: int) -> int:
    """Get the lca_res of an edge."""
    result = con.execute("SELECT lca_res FROM edges WHERE id = ?", [edge_id]).fetchone()
    return result[0] if result else -1


def load_adjacency(con: duckdb.DuckDBPyConnection) -> Tuple[Dict, Dict]:
    """Load forward and backward adjacency lists from shortcuts table."""
    shortcuts_raw = con.execute("""
        SELECT from_edge, to_edge, cost, inside, cell
        FROM shortcuts
    """).fetchall()
    
    fwd_adj = {}
    bwd_adj = {}
    
    for from_e, to_e, cost, inside, cell in shortcuts_raw:
        try:
            cell_res = h3.get_resolution(h3.int_to_str(cell)) if cell and cell != 0 else -1
        except:
            cell_res = -1
        
        # Forward adjacency
        if from_e not in fwd_adj:
            fwd_adj[from_e] = []
        fwd_adj[from_e].append((to_e, cost, inside, cell_res))
        
        # Backward adjacency
        if to_e not in bwd_adj:
            bwd_adj[to_e] = []
        bwd_adj[to_e].append((from_e, cost, inside, cell_res))
    
    return fwd_adj, bwd_adj


def load_via_lookup(con: duckdb.DuckDBPyConnection) -> Dict[Tuple[int, int], int]:
    """Load via_edge lookup table from shortcuts table."""
    shortcuts_raw = con.execute("SELECT from_edge, to_edge, via_edge FROM shortcuts").fetchall()
    return {(f, t): v for f, t, v in shortcuts_raw}


def get_shortcut_base_edges(shortcut_id: int, via_lookup: Dict[Tuple[int, int], int], fwd_adj: Dict) -> List[int]:
    """Get all base edges that comprise a given shortcut ID."""
    # We need the (from, to) for the shortcut to look it up in via_lookup
    # This is slightly tricky since we only have the ID. 
    # But in this system, the ID *is* the edge.
    # However, to find its via_edge, we need its source and target nodes in the dual graph.
    # In the dual graph, an edge E is a node, so we need to know what E connects from/to.
    # Actually, the 'shortcuts' table has 'from_edge' and 'to_edge'.
    # For a shortcut ID to be in the via_lookup, it must be the 'via_edge' of something,
    # or it's a base edge.
    pass # Wait, let's use the recursive expansion logic instead.



def expand_path_sp(shortcut_path: List[int], via_lookup: Dict[Tuple[int, int], int]) -> List[int]:
    """
    Expand a shortcut path to base edges using the via_lookup table.
    
    Algorithm:
    1. For each consecutive pair (u, v) in path, call expand_edge_pair(u, v)
    2. expand_edge_pair looks up (u, v) in table to get via_edge
    3. If via_edge == u or via_edge == v or via_edge == 0, return [u, v] (base pair)
    4. Otherwise, recursively expand (u, via) and (via, v), combine results
    """
    if not shortcut_path:
        return []
    if len(shortcut_path) == 1:
        return [shortcut_path[0]]
    
    def expand_edge_pair(u: int, v: int, visited: set) -> List[int]:
        """Expand a single edge pair (u, v) to base edges."""
        key = (u, v)
        
        # Cycle detection
        if key in visited:
            return [u, v]
        visited.add(key)
        
        # Look up via_edge for this pair
        via = via_lookup.get(key)
        
        # If no expansion found or via equals u or v or 0, it's a base pair
        if via is None or via == u or via == v or via == 0:
            return [u, v]
        
        # Recursively expand (u, via) and (via, v)
        left = expand_edge_pair(u, via, visited)
        right = expand_edge_pair(via, v, visited)
        
        # Combine: left ends with junction point, right starts with it
        # Avoid duplicating the junction
        if left and right and left[-1] == right[0]:
            return left + right[1:]
        else:
            return left + right

    # Expand each consecutive pair in the path
    result = []
    for i in range(len(shortcut_path) - 1):
        u, v = shortcut_path[i], shortcut_path[i + 1]
        visited = set()
        expanded = expand_edge_pair(u, v, visited)
        
        # Merge with previous result, avoiding duplicate junction
        if not result:
            result = expanded
        elif result and expanded and result[-1] == expanded[0]:
            result.extend(expanded[1:])
        else:
            result.extend(expanded)
    
    return result


# =============================================================================
# ALGORITHM 1: dijkstra - Ground truth (no filtering)
# =============================================================================

def dijkstra_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None
) -> Tuple[float, List[int], bool]:
    """
    Standard Dijkstra on shortcut graph (no inside filtering).
    Ground truth for correctness testing.
    
    Returns:
        Tuple of (cost, path, success)
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Load adjacency if not provided
    if fwd_adj is None:
        fwd_adj, _ = load_adjacency(con)
    
    # Standard Dijkstra
    dist: Dict[int, float] = {source_edge: 0.0}
    parent: Dict[int, int] = {source_edge: source_edge}
    pq = [(0.0, source_edge)]
    
    while pq:
        d, u = heapq.heappop(pq)
        
        if u == target_edge:
            # Reconstruct path
            path = []
            curr = u
            while curr != parent.get(curr):
                path.append(curr)
                curr = parent[curr]
            path.append(curr)
            path.reverse()
            return d + get_edge_cost(con, target_edge), path, True
        
        if d > dist.get(u, INF):
            continue
        
        if u not in fwd_adj:
            continue
        
        for to_edge, cost, inside, cell_res in fwd_adj[u]:
            nd = d + cost
            if to_edge not in dist or nd < dist[to_edge]:
                dist[to_edge] = nd
                parent[to_edge] = u
                heapq.heappush(pq, (nd, to_edge))
    
    return -1, [], False


# =============================================================================
# ALGORITHM 1.5: bi_dijkstra_sp - Bidirectional Dijkstra (no filtering)
# =============================================================================

def bi_dijkstra_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict = None,
    bwd_adj: Dict = None
) -> Tuple[float, List[int], bool]:
    """
    True Bidirectional Dijkstra (no inside filtering).
    Always expands from the side with the smaller minimum distance.
    Stops as soon as pq_fwd.min + pq_bwd.min >= best_cost.
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    if fwd_adj is None or bwd_adj is None:
        fwd_adj, bwd_adj = load_adjacency(con)
    
    dist_fwd: Dict[int, float] = {source_edge: 0.0}
    parent_fwd: Dict[int, int] = {source_edge: source_edge}
    pq_fwd = [(0.0, source_edge)]
    
    dist_bwd: Dict[int, float] = {target_edge: 0.0}
    parent_bwd: Dict[int, int] = {target_edge: target_edge}
    pq_bwd = [(0.0, target_edge)]
    
    best = INF
    meeting_edge = None
    
    while pq_fwd and pq_bwd:
        if pq_fwd[0][0] + pq_bwd[0][0] >= best:
            break
            
        if pq_fwd[0][0] <= pq_bwd[0][0]:
            d, u = heapq.heappop(pq_fwd)
            if d > dist_fwd.get(u, INF): continue
            for v, cost, inside, res in fwd_adj.get(u, []):
                nd = d + cost
                if nd < dist_fwd.get(v, INF):
                    dist_fwd[v], parent_fwd[v] = nd, u
                    heapq.heappush(pq_fwd, (nd, v))
                    if v in dist_bwd and nd + dist_bwd[v] < best:
                        best, meeting_edge = nd + dist_bwd[v], v
        else:
            d, u = heapq.heappop(pq_bwd)
            if d > dist_bwd.get(u, INF): continue
            for v, cost, inside, res in bwd_adj.get(u, []):
                nd = d + cost
                if nd < dist_bwd.get(v, INF):
                    dist_bwd[v], parent_bwd[v] = nd, u
                    heapq.heappush(pq_bwd, (nd, v))
                    if v in dist_fwd and dist_fwd[v] + nd < best:
                        best, meeting_edge = dist_fwd[v] + nd, v
    
    if best == INF: return -1, [], False
        
    path, curr = [], meeting_edge
    while curr != parent_fwd[curr]: path.append(curr); curr = parent_fwd[curr]
    path.append(curr); path.reverse(); curr = meeting_edge
    while curr != parent_bwd[curr]: curr = parent_bwd[curr]; path.append(curr)

    # Final cost calculation (sum of edge costs)
    final_cost = get_edge_cost(con, path[0])
    for j in range(len(path) - 1):
        found = False
        for n, c, i, r in fwd_adj.get(path[j], []):
            if n == path[j+1]: final_cost += c; found = True; break
        if not found: return -1, [], False

    return final_cost, path, True




# =============================================================================
# ALGORITHM 2: bi_classic - Bidirectional with inside filtering
# =============================================================================

def bi_classic_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict = None,
    bwd_adj: Dict = None
) -> Tuple[float, List[int], bool]:
    """
    Bidirectional Dijkstra with inside filtering only.
    Forward: inside=1 only (go up)
    Backward: inside=-1 or 0 (go up and lateral)
    
    Returns:
        Tuple of (cost, path, success)
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Load adjacency if not provided
    if fwd_adj is None or bwd_adj is None:
        fwd_adj, bwd_adj = load_adjacency(con)
    
    dist_fwd: Dict[int, float] = {source_edge: 0.0}
    dist_bwd: Dict[int, float] = {}
    parent_fwd: Dict[int, int] = {source_edge: source_edge}
    parent_bwd: Dict[int, int] = {}
    
    pq_fwd = [(0.0, source_edge)]
    target_cost = get_edge_cost(con, target_edge)
    dist_bwd[target_edge] = target_cost
    parent_bwd[target_edge] = target_edge
    pq_bwd = [(target_cost, target_edge)]
    
    best = INF
    meeting_edge = None
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heapq.heappop(pq_fwd)
            
            if d > dist_fwd.get(u, INF) or d >= best:
                pass
            else:
                for to_edge, cost, inside, cell_res in fwd_adj.get(u, []):
                    if inside != 1:
                        continue
                    
                    nd = d + cost
                    if to_edge not in dist_fwd or nd < dist_fwd[to_edge]:
                        dist_fwd[to_edge] = nd
                        parent_fwd[to_edge] = u
                        heapq.heappush(pq_fwd, (nd, to_edge))
                        
                        if to_edge in dist_bwd:
                            total = nd + dist_bwd[to_edge]
                            if total < best:
                                best = total
                                meeting_edge = to_edge
        
        # Backward step
        if pq_bwd:
            d, u = heapq.heappop(pq_bwd)
            
            if d > dist_bwd.get(u, INF) or d >= best:
                pass
            else:
                for from_edge, cost, inside, cell_res in bwd_adj.get(u, []):
                    if inside != -1 and inside != 0:
                        continue
                    
                    nd = d + cost
                    if from_edge not in dist_bwd or nd < dist_bwd[from_edge]:
                        dist_bwd[from_edge] = nd
                        parent_bwd[from_edge] = u
                        heapq.heappush(pq_bwd, (nd, from_edge))
                        
                        if from_edge in dist_fwd:
                            total = dist_fwd[from_edge] + nd
                            if total < best:
                                best = total
                                meeting_edge = from_edge
        
        # Early termination
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best:
                break
        elif not pq_fwd and not pq_bwd:
            break
    
    if best == INF:
        return -1, [], False
    
    # Reconstruct path
    path = []
    curr = meeting_edge
    while curr != parent_fwd.get(curr):
        path.append(curr)
        curr = parent_fwd[curr]
    path.append(curr)
    path.reverse()
    
    curr = meeting_edge
    while parent_bwd.get(curr) != curr:
        curr = parent_bwd[curr]
        path.append(curr)
    
    return best, path, True


# =============================================================================
# ALGORITHM 2-ALT: bi_classic_alt_sp - Alternative path using penalty method
# =============================================================================

# =============================================================================
# ALGORITHM 2-ALT: bi_classic_alt_sp - Alternative path (Hierarchical)
# =============================================================================

# =============================================================================
# ALGORITHM 2-ALT: bi_classic_alt_sp - Alternative path (Hierarchical)
# =============================================================================

def bi_classic_alt_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    shortest_path: List[int],
    fwd_adj: Dict = None,
    bwd_adj: Dict = None,
    penalty_factor: float = 2.0,
    via_lookup: Dict = None
) -> Tuple[float, List[int], bool]:
    """Find alternative path using hierarchical filtering and simple node-based penalties."""
    if fwd_adj is None or bwd_adj is None: fwd_adj, bwd_adj = load_adjacency(con)
    
    # Penalize any node that was in the shortest path
    penalized_nodes = set(shortest_path)
    penalized_nodes.discard(source_edge)
    penalized_nodes.discard(target_edge)

    if source_edge == target_edge: return get_edge_cost(con, source_edge), [source_edge], True
    
    dist_fwd, dist_bwd = {source_edge: 0.0}, {target_edge: get_edge_cost(con, target_edge)}
    parent_fwd, parent_bwd = {source_edge: source_edge}, {target_edge: target_edge}
    pq_fwd, pq_bwd = [(0.0, source_edge)], [(dist_bwd[target_edge], target_edge)]
    best, meeting_edge = INF, None

    while pq_fwd or pq_bwd:
        if pq_fwd:
            d, u = heapq.heappop(pq_fwd)
            if d < dist_fwd.get(u, INF) and d < best:
                for v, cost, inside, res in fwd_adj.get(u, []):
                    if inside != 1: continue
                    eff_cost = cost * penalty_factor if v in penalized_nodes else cost
                    nd = d + eff_cost
                    if nd < dist_fwd.get(v, INF):
                        dist_fwd[v], parent_fwd[v] = nd, u
                        heapq.heappush(pq_fwd, (nd, v))
                        if v in dist_bwd and nd+dist_bwd[v] < best: best, meeting_edge = nd+dist_bwd[v], v
        if pq_bwd:
            d, u = heapq.heappop(pq_bwd)
            if d < dist_bwd.get(u, INF) and d < best:
                for v, cost, inside, res in bwd_adj.get(u, []):
                    if inside not in (-1, 0): continue
                    eff_cost = cost * penalty_factor if v in penalized_nodes else cost
                    nd = d + eff_cost
                    if nd < dist_bwd.get(v, INF):
                        dist_bwd[v], parent_bwd[v] = nd, u
                        heapq.heappush(pq_bwd, (nd, v))
                        if v in dist_fwd and dist_fwd[v]+nd < best: best, meeting_edge = dist_fwd[v]+nd, v
        if pq_fwd and pq_bwd and pq_fwd[0][0] >= best and pq_bwd[0][0] >= best: break

    if best == INF: return -1, [], False
    
    path, curr = [], meeting_edge
    while curr != parent_fwd[curr]: path.append(curr); curr = parent_fwd[curr]
    path.append(curr); path.reverse(); curr = meeting_edge
    while curr != parent_bwd[curr]: curr = parent_bwd[curr]; path.append(curr)
    
    # Calculate true cost (without penalties)
    true_cost_total = get_edge_cost(con, path[0])
    for j in range(len(path) - 1):
        found = False
        for n, c, i, r in fwd_adj.get(path[j], []):
            if n == path[j+1]: true_cost_total += c; found = True; break
        if not found: return -1, [], False
    return true_cost_total, path, True


# =============================================================================
# ALGORITHM 1.5-ALT: bi_dijkstra_alt_sp - Alternative path (No filtering)
# =============================================================================

def bi_dijkstra_alt_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    shortest_path: List[int],
    fwd_adj: Dict = None,
    bwd_adj: Dict = None,
    penalty_factor: float = 2.0,
    via_lookup: Dict = None
) -> Tuple[float, List[int], bool]:
    """
    True Bidirectional Dijkstra (no inside filtering) with node-based penalties.
    Always expands from the side with the smaller minimum distance.
    Stops as soon as pq_fwd.min + pq_bwd.min >= best_cost.
    """
    if fwd_adj is None or bwd_adj is None: fwd_adj, bwd_adj = load_adjacency(con)
    
    # Penalize any node that was in the shortest path
    penalized_nodes = set(shortest_path)
    penalized_nodes.discard(source_edge)
    penalized_nodes.discard(target_edge)

    if source_edge == target_edge: return get_edge_cost(con, source_edge), [source_edge], True
    
    dist_fwd, dist_bwd = {source_edge: 0.0}, {target_edge: 0.0}
    parent_fwd, parent_bwd = {source_edge: source_edge}, {target_edge: target_edge}
    pq_fwd, pq_bwd = [(0.0, source_edge)], [(0.0, target_edge)]
    best, meeting_edge = INF, None

    while pq_fwd and pq_bwd:
        # Termination condition
        if pq_fwd[0][0] + pq_bwd[0][0] >= best:
            break
            
        # Select side: expand smaller distance
        if pq_fwd[0][0] <= pq_bwd[0][0]:
            d, u = heapq.heappop(pq_fwd)
            if d > dist_fwd.get(u, INF): continue
            
            for v, cost, inside, res in fwd_adj.get(u, []):
                eff_cost = cost * penalty_factor if v in penalized_nodes else cost
                nd = d + eff_cost
                if nd < dist_fwd.get(v, INF):
                    dist_fwd[v], parent_fwd[v] = nd, u
                    heapq.heappush(pq_fwd, (nd, v))
                    if v in dist_bwd and nd + dist_bwd[v] < best:
                        best, meeting_edge = nd + dist_bwd[v], v
        else:
            d, u = heapq.heappop(pq_bwd)
            if d > dist_bwd.get(u, INF): continue
            
            for v, cost, inside, res in bwd_adj.get(u, []):
                eff_cost = cost * penalty_factor if v in penalized_nodes else cost
                nd = d + eff_cost
                if nd < dist_bwd.get(v, INF):
                    dist_bwd[v], parent_bwd[v] = nd, u
                    heapq.heappush(pq_bwd, (nd, v))
                    if v in dist_fwd and dist_fwd[v] + nd < best:
                        best, meeting_edge = dist_fwd[v] + nd, v

    if best == INF: return -1, [], False
    
    path, curr = [], meeting_edge
    while curr != parent_fwd[curr]: path.append(curr); curr = parent_fwd[curr]
    path.append(curr); path.reverse(); curr = meeting_edge
    while curr != parent_bwd[curr]: curr = parent_bwd[curr]; path.append(curr)
    
    # Calculate true cost (without penalties)
    true_cost_total = get_edge_cost(con, path[0])
    for j in range(len(path) - 1):
        found = False
        for n, c, i, r in fwd_adj.get(path[j], []):
            if n == path[j+1]: true_cost_total += c; found = True; break
        if not found: return -1, [], False
    return true_cost_total, path, True








# =============================================================================
# ALGORITHM 3: uni_lca - Unidirectional phase-based with LCA
# =============================================================================


def uni_lca_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None
) -> Tuple[float, List[int], bool]:
    """
    Unidirectional phase-based search with LCA targeting.
    
    Phases:
    - 0: Initial
    - 1: Ascending (inside=1 when cell_res > high_res)
    - 2: At peak (inside != 1)
    - 3: Descending (inside=-1 only)
    
    Returns:
        Tuple of (cost, path, success)
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Compute LCA
    high_cell, high_res = compute_high_cell(con, source_edge, target_edge)
    
    # Load adjacency if not provided
    if fwd_adj is None:
        fwd_adj, _ = load_adjacency(con)
    
    src_res = get_edge_res(con, source_edge)
    
    dist: Dict[int, float] = {source_edge: 0.0}
    parent: Dict[int, int] = {source_edge: source_edge}
    pq = [(0.0, source_edge, src_res, 0)]  # (dist, edge, res, phase)
    
    while pq:
        d, u, u_res, phase = heapq.heappop(pq)
        state_key = u
        
        if state_key in dist and d > dist[state_key]:
            continue
        
        if u == target_edge:
            path = []
            curr_key = state_key
            while curr_key != parent.get(curr_key):
                path.append(curr_key)
                curr_key = parent[curr_key]
            path.append(curr_key)
            path.reverse()
            target_cost = get_edge_cost(con, target_edge)
            return d + target_cost, path, True
        
        if u not in fwd_adj:
            continue
        
        for to_edge, cost, inside, cell_res in fwd_adj[u]:
            allowed = False
            next_phase = phase
            
            # Phase-based filtering
            if phase == 0 or phase == 1:
                if cell_res > high_res and inside == 1:
                    allowed = True
                    next_phase = 1
                elif cell_res <= high_res and inside == 1:
                    allowed = True
                    next_phase = 2
                elif inside != 1:
                    allowed = True
                    next_phase = 2
            elif phase == 2:
                if inside != 1:
                    allowed = True
                    next_phase = 3
            elif phase == 3:
                if inside == -1:
                    allowed = True
                    next_phase = 3
            
            if not allowed:
                continue
            
            nd = d + cost
            next_key = to_edge
            
            if next_key not in dist or nd < dist[next_key]:
                dist[next_key] = nd
                parent[next_key] = state_key
                heapq.heappush(pq, (nd, to_edge, cell_res, next_phase))
    
    return -1, [], False


# =============================================================================
# ALGORITHM 4: bi_lca - Bidirectional phase-based with LCA (fastest)
# =============================================================================

def bi_lca_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None,
    bwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None
) -> Tuple[float, List[int], bool]:
    """
    Bidirectional phase-based search with LCA targeting.
    This is the fastest algorithm with 100% correctness.
    
    Forward: Phase-based filtering (inside=1 up, then inside=-1 down)
    Backward: Mirror of forward (swap inside values)
    
    Returns:
        Tuple of (cost, path, success)
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Compute LCA
    high_cell, high_res = compute_high_cell(con, source_edge, target_edge)
    
    # Load adjacency if not provided
    if fwd_adj is None or bwd_adj is None:
        fwd_adj, bwd_adj = load_adjacency(con)
    
    src_res = get_edge_res(con, source_edge)
    tgt_res = get_edge_res(con, target_edge)
    
    # Initialize forward
    dist_fwd: Dict[int, float] = {source_edge: 0.0}
    parent_fwd: Dict[int, int] = {source_edge: source_edge}
    
    # Initialize backward
    dist_bwd: Dict[int, float] = {}
    parent_bwd: Dict[int, int] = {}
    target_cost = get_edge_cost(con, target_edge)
    dist_bwd[target_edge] = target_cost
    parent_bwd[target_edge] = target_edge
    
    # Priority queues: (distance, edge, u_res, phase)
    pq_fwd = [(0.0, source_edge, src_res, 0)]
    pq_bwd = [(target_cost, target_edge, tgt_res, 0)]
    
    best = INF
    meeting_edge = None
    
    visited_fwd: Set[int] = set()
    visited_bwd: Set[int] = set()
    
    alternate = True
    
    while pq_fwd or pq_bwd:
        # Decide which direction to expand
        if not pq_fwd:
            expand_forward = False
        elif not pq_bwd:
            expand_forward = True
        elif alternate:
            expand_forward = True
        else:
            expand_forward = False
        alternate = not alternate
        
        if expand_forward:
            # Forward step
            d, u, u_res, phase = heapq.heappop(pq_fwd)
            
            if u in dist_fwd and d > dist_fwd[u]:
                continue
            if d >= best:
                continue
            
            visited_fwd.add(u)
            
            # Check for meeting
            if u in visited_bwd:
                total = d + dist_bwd[u]
                if total < best:
                    best = total
                    meeting_edge = u
            
            if u in fwd_adj:
                for to_edge, cost, inside, cell_res in fwd_adj[u]:
                    allowed = False
                    next_phase = phase
                    
                    # Forward filtering
                    if phase == 0 or phase == 1:
                        if cell_res > high_res and inside == 1:
                            allowed = True
                            next_phase = 1
                        elif cell_res <= high_res and inside == 1:
                            allowed = True
                            next_phase = 2
                        elif inside != 1:
                            allowed = True
                            next_phase = 2
                    elif phase == 2:
                        if inside != 1:
                            allowed = True
                            next_phase = 3
                    elif phase == 3:
                        if inside == -1:
                            allowed = True
                            next_phase = 3
                    
                    if not allowed:
                        continue
                    
                    nd = d + cost
                    
                    if to_edge not in dist_fwd or nd < dist_fwd[to_edge]:
                        dist_fwd[to_edge] = nd
                        parent_fwd[to_edge] = u
                        heapq.heappush(pq_fwd, (nd, to_edge, cell_res, next_phase))
                        
                        # Check for meeting when ADDING to heap
                        if to_edge in dist_bwd:
                            total = nd + dist_bwd[to_edge]
                            if total < best:
                                best = total
                                meeting_edge = to_edge
        
        else:
            # Backward step
            if not pq_bwd:
                continue
            d, u, u_res, phase = heapq.heappop(pq_bwd)
            
            if u in dist_bwd and d > dist_bwd[u]:
                continue
            if d >= best:
                continue
            
            visited_bwd.add(u)
            
            # Check for meeting
            if u in visited_fwd:
                total = dist_fwd[u] + d
                if total < best:
                    best = total
                    meeting_edge = u
            
            if u in bwd_adj:
                for from_edge, cost, inside, cell_res in bwd_adj[u]:
                    allowed = False
                    next_phase = phase
                    
                    # Backward filtering: swap 1↔-1
                    if phase == 0 or phase == 1:
                        if cell_res > high_res and inside == -1:
                            allowed = True
                            next_phase = 1
                        elif cell_res <= high_res and inside == -1:
                            allowed = True
                            next_phase = 2
                        elif inside != -1:
                            allowed = True
                            next_phase = 2
                    elif phase == 2:
                        if inside != -1:
                            allowed = True
                            next_phase = 3
                    elif phase == 3:
                        if inside == 1:
                            allowed = True
                            next_phase = 3
                    
                    if not allowed:
                        continue
                    
                    nd = d + cost
                    
                    if from_edge not in dist_bwd or nd < dist_bwd[from_edge]:
                        dist_bwd[from_edge] = nd
                        parent_bwd[from_edge] = u
                        heapq.heappush(pq_bwd, (nd, from_edge, cell_res, next_phase))
                        
                        # Check for meeting when ADDING to heap
                        if from_edge in dist_fwd:
                            total = dist_fwd[from_edge] + nd
                            if total < best:
                                best = total
                                meeting_edge = from_edge
    
    if best == INF:
        return -1, [], False
    
    # Reconstruct path
    path = []
    curr = meeting_edge
    while curr != parent_fwd.get(curr):
        path.append(curr)
        curr = parent_fwd[curr]
    path.append(curr)
    path.reverse()
    
    curr = meeting_edge
    while parent_bwd.get(curr) != curr:
        curr = parent_bwd[curr]
        path.append(curr)
    
    return best, path, True


# =============================================================================
# ALGORITHM 5: bi_lca_res - Bidirectional with LCA resolution pruning
# =============================================================================

def bi_lca_res_sp(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None,
    bwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None
) -> Tuple[float, List[int], bool]:
    """
    Bidirectional Dijkstra with LCA resolution-based pruning.
    Uses resolution comparison (u_res vs high_res) for pruning.
    
    Ported from cpp_algorithms.py query_pruned.
    
    Returns:
        Tuple of (cost, path, success)
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Compute LCA
    high_cell, high_res = compute_high_cell(con, source_edge, target_edge)
    
    # Load adjacency if not provided
    if fwd_adj is None or bwd_adj is None:
        fwd_adj, bwd_adj = load_adjacency(con)
    
    src_res = get_edge_res(con, source_edge)
    tgt_res = get_edge_res(con, target_edge)
    
    dist_fwd: Dict[int, float] = {source_edge: 0.0}
    dist_bwd: Dict[int, float] = {}
    parent_fwd: Dict[int, int] = {source_edge: source_edge}
    parent_bwd: Dict[int, int] = {}
    
    # Priority queues: (distance, edge, resolution)
    pq_fwd = [(0.0, source_edge, src_res)]
    target_cost = get_edge_cost(con, target_edge)
    dist_bwd[target_edge] = target_cost
    parent_bwd[target_edge] = target_edge
    pq_bwd = [(target_cost, target_edge, tgt_res)]
    
    best = INF
    meeting_edge = None
    min_arrival_fwd = INF
    min_arrival_bwd = INF
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u, u_res = heapq.heappop(pq_fwd)
            
            # Check meeting
            if u in dist_bwd:
                min_arrival_fwd = min(dist_fwd.get(u, INF), min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd[u], min_arrival_bwd)
                total = d + dist_bwd[u]
                if total < best:
                    best = total
                    meeting_edge = u
            
            if u in dist_fwd and d > dist_fwd[u]:
                pass  # stale
            elif d >= best:
                pass  # pruned
            else:
                # Resolution-based pruning
                if u_res < high_res:
                    min_arrival_fwd = min(dist_fwd.get(u, INF), min_arrival_fwd)
                else:
                    if u_res == high_res:
                        min_arrival_fwd = min(dist_fwd.get(u, INF), min_arrival_fwd)
                    
                    for to_edge, cost, inside, cell_res in fwd_adj.get(u, []):
                        if inside != 1:
                            continue
                        
                        nd = d + cost
                        if to_edge not in dist_fwd or nd < dist_fwd[to_edge]:
                            dist_fwd[to_edge] = nd
                            parent_fwd[to_edge] = u
                            heapq.heappush(pq_fwd, (nd, to_edge, cell_res))
                            
                            # Check meeting when adding
                            if to_edge in dist_bwd:
                                total = nd + dist_bwd[to_edge]
                                if total < best:
                                    best = total
                                    meeting_edge = to_edge
        
        # Backward step
        if pq_bwd:
            d, u, u_res = heapq.heappop(pq_bwd)
            
            # Check meeting
            if u in dist_fwd:
                min_arrival_fwd = min(dist_fwd[u], min_arrival_fwd)
                min_arrival_bwd = min(dist_bwd.get(u, INF), min_arrival_bwd)
                total = dist_fwd[u] + d
                if total < best:
                    best = total
                    meeting_edge = u
            
            if u in dist_bwd and d > dist_bwd[u]:
                continue  # stale
            if d >= best:
                continue
            
            # Resolution-based check
            check = (u_res >= high_res)
            
            if u_res == high_res or not check:
                min_arrival_bwd = min(dist_bwd.get(u, INF), min_arrival_bwd)
            
            for from_edge, cost, inside, cell_res in bwd_adj.get(u, []):
                # Resolution-based filtering
                allowed = False
                if inside == -1 and check:
                    allowed = True
                elif inside == 0 and u_res <= high_res:
                    allowed = True
                elif inside == -2 and not check:
                    allowed = True
                
                if not allowed:
                    continue
                
                nd = d + cost
                if from_edge not in dist_bwd or nd < dist_bwd[from_edge]:
                    dist_bwd[from_edge] = nd
                    parent_bwd[from_edge] = u
                    heapq.heappush(pq_bwd, (nd, from_edge, cell_res))
                    
                    # Check meeting when adding
                    if from_edge in dist_fwd:
                        total = dist_fwd[from_edge] + nd
                        if total < best:
                            best = total
                            meeting_edge = from_edge
        
        # Early termination
        if best < INF:
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
    
    if best == INF:
        return -1, [], False
    
    # Reconstruct path
    path = []
    curr = meeting_edge
    while curr != parent_fwd.get(curr):
        path.append(curr)
        curr = parent_fwd[curr]
    path.append(curr)
    path.reverse()
    
    curr = meeting_edge
    while parent_bwd.get(curr) != curr:
        curr = parent_bwd[curr]
        path.append(curr)
    
    return best, path, True


# =============================================================================
# ALGORITHM 6: m2m_classic_sp - Many-to-many with inside filtering
# =============================================================================

def m2m_classic_sp(
    con: duckdb.DuckDBPyConnection,
    source_edges: List[int],
    target_edges: List[int],
    fwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None,
    bwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None
) -> Tuple[float, List[int], bool]:
    """
    Many-to-many bidirectional Dijkstra with inside filtering.
    Same filtering logic as bi_classic_sp but with multiple sources and targets.
    
    Args:
        con: DuckDB connection
        source_edges: List of source edge IDs
        target_edges: List of target edge IDs
        fwd_adj: Forward adjacency dict
        bwd_adj: Backward adjacency dict
    
    Returns:
        Tuple of (cost, path, success) for the best source-target pair
    """
    if not source_edges or not target_edges:
        return -1, [], False
    
    # Load adjacency if not provided
    if fwd_adj is None or bwd_adj is None:
        fwd_adj, bwd_adj = load_adjacency(con)
    
    # Initialize forward from all sources at distance 0.0
    dist_fwd: Dict[int, float] = {}
    parent_fwd: Dict[int, int] = {}
    pq_fwd = []
    
    for src in source_edges:
        dist_fwd[src] = 0.0
        parent_fwd[src] = src
        heapq.heappush(pq_fwd, (0.0, src))
    
    # Initialize backward from all targets at edge_cost
    dist_bwd: Dict[int, float] = {}
    parent_bwd: Dict[int, int] = {}
    pq_bwd = []
    
    for tgt in target_edges:
        tgt_cost = get_edge_cost(con, tgt)
        dist_bwd[tgt] = tgt_cost
        parent_bwd[tgt] = tgt
        heapq.heappush(pq_bwd, (tgt_cost, tgt))
    
    best = INF
    meeting_edge = None
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heapq.heappop(pq_fwd)
            
            if d > dist_fwd.get(u, INF) or d >= best:
                pass
            else:
                for to_edge, cost, inside, cell_res in fwd_adj.get(u, []):
                    if inside != 1:
                        continue
                    
                    nd = d + cost
                    if to_edge not in dist_fwd or nd < dist_fwd[to_edge]:
                        dist_fwd[to_edge] = nd
                        parent_fwd[to_edge] = u
                        heapq.heappush(pq_fwd, (nd, to_edge))
                        
                        # Check for meeting point
                        if to_edge in dist_bwd:
                            total = nd + dist_bwd[to_edge]
                            if total < best:
                                best = total
                                meeting_edge = to_edge
        
        # Backward step
        if pq_bwd:
            d, u = heapq.heappop(pq_bwd)
            
            if d > dist_bwd.get(u, INF) or d >= best:
                pass
            else:
                for from_edge, cost, inside, cell_res in bwd_adj.get(u, []):
                    if inside != -1 and inside != 0:
                        continue
                    
                    nd = d + cost
                    if from_edge not in dist_bwd or nd < dist_bwd[from_edge]:
                        dist_bwd[from_edge] = nd
                        parent_bwd[from_edge] = u
                        heapq.heappush(pq_bwd, (nd, from_edge))
                        
                        # Check for meeting point
                        if from_edge in dist_fwd:
                            total = dist_fwd[from_edge] + nd
                            if total < best:
                                best = total
                                meeting_edge = from_edge
        
        # Early termination
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best:
                break
        elif not pq_fwd and not pq_bwd:
            break
    
    if best == INF:
        return -1, [], False
    
    # Reconstruct path
    path = []
    curr = meeting_edge
    while curr != parent_fwd.get(curr):
        path.append(curr)
        curr = parent_fwd[curr]
    path.append(curr)
    path.reverse()
    
    curr = meeting_edge
    while parent_bwd.get(curr) != curr:
        curr = parent_bwd[curr]
        path.append(curr)
    
    return best, path, True


# =============================================================================
# ALGORITHM 7: m2m_lca - Many-to-many phase-based
# =============================================================================

# TODO: Implement many-to-many version of bi_lca


# =============================================================================
# MAIN - Testing
# =============================================================================

if __name__ == "__main__":
    import sys
    import random
    
    if len(sys.argv) < 2:
        print("Usage: python routing_algorithms.py <db_path> [source] [target] [--batch N]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    con = duckdb.connect(db_path, read_only=True)
    
    # Load adjacency once
    print("Loading shortcuts...")
    fwd_adj, bwd_adj = load_adjacency(con)
    print(f"Loaded {sum(len(v) for v in fwd_adj.values())} shortcuts")
    
    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        n_samples = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 100
        
        print(f"\nBatch testing {n_samples} samples...")
        
        edges = list(fwd_adj.keys())
        random.seed(42)
        
        matches = {"dijkstra": 0, "bi_classic_sp": 0, "uni_lca_sp": 0, "bi_lca_sp": 0}
        
        for i in range(n_samples):
            src = random.choice(edges)
            tgt = random.choice(edges)
            while src == tgt:
                tgt = random.choice(edges)
            
            dij_cost, _, dij_ok = dijkstra_sp(con, src, tgt, fwd_adj)
            
            for name, func in [("bi_classic_sp", bi_classic_sp), ("uni_lca_sp", uni_lca_sp), ("bi_lca_sp", bi_lca_sp)]:
                if name == "bi_classic_sp":
                    cost, _, ok = func(con, src, tgt, fwd_adj, bwd_adj)
                elif name == "uni_lca_sp":
                    cost, _, ok = func(con, src, tgt, fwd_adj)
                else:
                    cost, _, ok = func(con, src, tgt, fwd_adj, bwd_adj)
                
                if ok and dij_ok and abs(cost - dij_cost) < 0.01:
                    matches[name] += 1
            
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{n_samples}: bi_classic_sp={matches['bi_classic_sp']}, uni_lca_sp={matches['uni_lca_sp']}, bi_lca_sp={matches['bi_lca_sp']}")
        
        print(f"\nResults (vs Dijkstra):")
        for name, count in matches.items():
            if name != "dijkstra":
                print(f"  {name}: {count}/{n_samples} ({100*count/n_samples:.1f}%)")

    
    elif len(sys.argv) >= 4:
        source = int(sys.argv[2])
        target = int(sys.argv[3])
        
        print(f"\nRouting: {source} -> {target}")
        
        dij_cost, dij_path, _ = dijkstra_sp(con, source, target, fwd_adj)
        print(f"\n[Dijkstra] Cost: {dij_cost:.4f}, Path: {len(dij_path)} edges")
        
        bi_cost, bi_path, _ = bi_lca_sp(con, source, target, fwd_adj, bwd_adj)
        print(f"[bi_lca]   Cost: {bi_cost:.4f}, Path: {len(bi_path)} edges")
        
        if abs(dij_cost - bi_cost) < 0.01:
            print("\n✓ MATCH")
        else:
            print(f"\n✗ MISMATCH: diff={abs(dij_cost - bi_cost):.4f}")
    
    con.close()
