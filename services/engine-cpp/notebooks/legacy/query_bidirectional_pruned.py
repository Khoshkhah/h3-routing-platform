"""
Bidirectional Pruned Search Algorithm (Python Prototype)

This implements a bidirectional hierarchy search that:
1. Forward: Starts from source, ascending through hierarchy
2. Backward: Starts from target, descending through hierarchy
3. Meeting: Detects when both frontiers meet
4. Termination: Stops when lower bounds prove optimality

The filtering rules are symmetric:
- Forward: inside=1 for ascending, inside=-1 after transition
- Backward: inside=-1 for descending, inside=1 after transition

Usage:
    python query_bidirectional_pruned.py <db_path> <source_edge> <target_edge>
    python query_bidirectional_pruned.py <db_path> --batch [num_samples]
"""

import heapq
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set

import duckdb
import h3


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
    lca = 0 #h3.cell_to_parent(src_cell, 0)  # Start at res 0
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


def query_bidirectional_pruned(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None,
    bwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None
) -> Tuple[float, List[int], bool]:
    """
    Bidirectional pruned search algorithm.
    
    Forward rules (source to LCA):
        u_res > high_res: inside=1 if !used, inside=-1 if used
        u_res <= high_res: inside={0,-2,-1} with counter
        
    Backward rules (target to LCA) - swap inside -1 <-> 1:
        u_res > high_res: inside=-1 if !used, inside=1 if used
        u_res <= high_res: inside={0,-2,1} with counter
    
    Args:
        con: DuckDB connection
        source_edge: Starting edge ID
        target_edge: Destination edge ID
        fwd_adj: Optional pre-loaded forward adjacency
        bwd_adj: Optional pre-loaded backward adjacency
        
    Returns:
        (cost, path, success)
    """
    INF = float('inf')
    MAX_USES = 2
    
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Step 1: Compute LCA resolution
    high_cell, high_res = compute_high_cell(con, source_edge, target_edge)
    
    # Step 2: Load shortcuts if not provided
    if fwd_adj is None or bwd_adj is None:
        shortcuts_raw = con.execute("""
            SELECT from_edge, to_edge, cost, inside, cell
            FROM shortcuts
        """).fetchall()
        
        fwd_adj = {}
        bwd_adj = {}
        for from_e, to_e, cost, inside, cell in shortcuts_raw:
            cell_res = h3.get_resolution(h3.int_to_str(cell)) if cell and cell != 0 else -1
            
            # Forward adjacency
            if from_e not in fwd_adj:
                fwd_adj[from_e] = []
            fwd_adj[from_e].append((to_e, cost, inside, cell_res))
            
            # Backward adjacency (reverse edge direction, SAME inside as C++ engine)
            # C++ engine uses original inside values for backward, not negated
            if to_e not in bwd_adj:
                bwd_adj[to_e] = []
            bwd_adj[to_e].append((from_e, cost, inside, cell_res))
    
    # Step 3: Initialize both directions
    # Use edge-only keys for dist/parent, phase is only in heap
    src_res = get_edge_res(con, source_edge)
    tgt_res = get_edge_res(con, target_edge)
    
    # Forward: dist_fwd[edge] -> distance (edge-only key)
    dist_fwd: Dict[int, float] = {}
    parent_fwd: Dict[int, int] = {}
    
    # Backward: dist_bwd[edge] -> distance (edge-only key)
    dist_bwd: Dict[int, float] = {}
    parent_bwd: Dict[int, int] = {}
    
    # Initialize forward
    dist_fwd[source_edge] = 0.0
    parent_fwd[source_edge] = source_edge
    
    # Initialize backward (start with target edge cost included)
    target_cost = get_edge_cost(con, target_edge)
    dist_bwd[target_edge] = target_cost
    parent_bwd[target_edge] = target_edge
    
    # Priority queues: (distance, edge, u_res, phase)
    # Phase: 0=initial, 1=ascending(inside=1), 2=at_peak(inside=0/-2), 3=descending(inside=-1)
    pq_fwd = [(0.0, source_edge, src_res, 0)]
    pq_bwd = [(target_cost, target_edge, tgt_res, 0)]
    
    best = INF
    meeting_edge = None
    
    # Track which edges have been visited by each direction
    visited_fwd: Set[int] = set()
    visited_bwd: Set[int] = set()
    
    alternate = True  # Start with forward
    
    # Step 4: Bidirectional search - TRUE ALTERNATING
    while pq_fwd or pq_bwd:
        # Termination check
        fwd_min = pq_fwd[0][0] if pq_fwd else INF
        bwd_min = pq_bwd[0][0] if pq_bwd else INF
        if best < INF and fwd_min + bwd_min >= best:
            break
        
        # TRUE ALTERNATING: switch between forward and backward
        if alternate and pq_fwd:
            expand_forward = True
        elif not alternate and pq_bwd:
            expand_forward = False
        elif pq_fwd:
            expand_forward = True
        else:
            expand_forward = False
        alternate = not alternate
        
        if expand_forward:
            # Forward step
            d, u, u_res, phase = heapq.heappop(pq_fwd)
            
            # Skip if already visited with better distance
            if u in dist_fwd and d > dist_fwd[u]:
                continue
            if d >= best:
                continue  # Prune by bound
            
            # Track visit
            visited_fwd.add(u)
            
            # Check for meeting with backward
            if u in visited_bwd:
                total = d + dist_bwd[u]
                if total < best:
                    best = total
                    meeting_edge = u
            
            # Expand forward neighbors
            if u in fwd_adj:
                for to_edge, cost, inside, cell_res in fwd_adj[u]:
                    allowed = False
                    next_phase = phase
                    
                    # Forward filtering: same as unidirectional phase logic
                    # ========== FILTERING LOGIC ==========
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
                    # =====================================
                    
                    if not allowed:
                        continue
                    
                    nd = d + cost
                    
                    # Use edge-only key for dist/parent
                    if to_edge not in dist_fwd or nd < dist_fwd[to_edge]:
                        dist_fwd[to_edge] = nd
                        parent_fwd[to_edge] = u
                        heapq.heappush(pq_fwd, (nd, to_edge, cell_res, next_phase))
                        
                        # Check for meeting when ADDING to heap (not just when popping)
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
            
            # Skip if already visited with better distance
            if u in dist_bwd and d > dist_bwd[u]:
                continue
            if d >= best:
                continue  # Prune by bound
            
            # Track visit
            visited_bwd.add(u)
            
            # Check for meeting with forward
            if u in visited_fwd:
                total = dist_fwd[u] + d
                if total < best:
                    best = total
                    meeting_edge = u
            
            # Expand backward neighbors (reverse edges)
            if u in bwd_adj:
                for from_edge, cost, inside, cell_res in bwd_adj[u]:
                    allowed = False
                    next_phase = phase
                    
                    # Backward filtering: SAME as forward (LCA is same for both directions)
                    # ========== FILTERING LOGIC ==========
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
                    # =====================================
                    
                    if not allowed:
                        continue
                    
                    nd = d + cost
                    
                    # Use edge-only key for dist/parent
                    if from_edge not in dist_bwd or nd < dist_bwd[from_edge]:
                        dist_bwd[from_edge] = nd
                        parent_bwd[from_edge] = u
                        heapq.heappush(pq_bwd, (nd, from_edge, cell_res, next_phase))
                        
                        # Check for meeting when ADDING to heap (not just when popping)
                        if from_edge in dist_fwd:
                            total = dist_fwd[from_edge] + nd
                            if total < best:
                                best = total
                                meeting_edge = from_edge

    
    if best == INF:
        return -1, [], False
    
    # Reconstruct path using edge-only keys
    # Forward part: source -> meeting
    path_fwd = []
    curr = meeting_edge
    while curr != parent_fwd.get(curr, curr):
        path_fwd.append(curr)
        curr = parent_fwd[curr]
    path_fwd.append(curr)
    path_fwd.reverse()
    
    # Backward part: meeting -> target (excluding meeting point, already in fwd)
    path_bwd = []
    curr = meeting_edge
    while curr != parent_bwd.get(curr, curr):
        next_edge = parent_bwd[curr]
        if next_edge != meeting_edge:  # Avoid duplicating meeting point
            path_bwd.append(next_edge)
        curr = next_edge
    
    path = path_fwd + path_bwd
    
    return best, path, True


def query_dijkstra(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int
) -> Tuple[float, List[int], bool]:
    """General Dijkstra (ground truth)."""
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    shortcuts = con.execute("SELECT from_edge, to_edge, cost FROM shortcuts").fetchall()
    
    fwd_adj = {}
    for from_e, to_e, cost in shortcuts:
        if from_e not in fwd_adj:
            fwd_adj[from_e] = []
        fwd_adj[from_e].append((to_e, cost))
    
    dist = {source_edge: 0.0}
    parent = {source_edge: source_edge}
    pq = [(0.0, source_edge)]
    
    while pq:
        d, u = heapq.heappop(pq)
        if u in dist and d > dist[u]:
            continue
        if u == target_edge:
            path = []
            curr = u
            while curr != parent.get(curr, curr):
                path.append(curr)
                curr = parent[curr]
            path.append(curr)
            path.reverse()
            # Add target edge cost like bidirectional does
            target_cost = get_edge_cost(con, target_edge)
            return d + target_cost, path, True
        if u not in fwd_adj:
            continue
        for to_edge, cost in fwd_adj[u]:
            nd = d + cost
            if to_edge not in dist or nd < dist[to_edge]:
                dist[to_edge] = nd
                parent[to_edge] = u
                heapq.heappush(pq, (nd, to_edge))
    
    return -1, [], False


def query_dijkstra_cached(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict[int, List[Tuple[int, float]]]
) -> Tuple[float, List[int], bool]:
    """General Dijkstra with pre-loaded adjacency (faster for batch testing)."""
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    dist = {source_edge: 0.0}
    parent = {source_edge: source_edge}
    pq = [(0.0, source_edge)]
    
    while pq:
        d, u = heapq.heappop(pq)
        if u in dist and d > dist[u]:
            continue
        if u == target_edge:
            path = []
            curr = u
            while curr != parent.get(curr, curr):
                path.append(curr)
                curr = parent[curr]
            path.append(curr)
            path.reverse()
            target_cost = get_edge_cost(con, target_edge)
            return d + target_cost, path, True
        if u not in fwd_adj:
            continue
        for to_edge, cost in fwd_adj[u]:
            nd = d + cost
            if to_edge not in dist or nd < dist[to_edge]:
                dist[to_edge] = nd
                parent[to_edge] = u
                heapq.heappush(pq, (nd, to_edge))
    
    return -1, [], False


def run_single_test(con: duckdb.DuckDBPyConnection, source_edge: int, target_edge: int):
    """Run single comparison."""
    print(f"=" * 60)
    print(f"Routing: {source_edge} -> {target_edge}")
    print(f"=" * 60)
    
    print("\n[1] General Dijkstra (ground truth):")
    dij_cost, dij_path, dij_success = query_dijkstra(con, source_edge, target_edge)
    if dij_success:
        print(f"    Cost: {dij_cost:.4f}")
        print(f"    Path: {len(dij_path)} edges")
        print(f"    Edges: {dij_path}")
    else:
        print(f"    FAILED: No path found")
    
    print("\n[2] Bidirectional Pruned Search:")
    bi_cost, bi_path, bi_success = query_bidirectional_pruned(con, source_edge, target_edge)
    if bi_success:
        print(f"    Cost: {bi_cost:.4f}")
        print(f"    Path: {len(bi_path)} edges")
        print(f"    Edges: {bi_path}")
    else:
        print(f"    FAILED: No path found")
    
    print("\n" + "=" * 60)
    print("COMPARISON:")
    if dij_success and bi_success:
        diff = abs(dij_cost - bi_cost)
        if diff < 0.0001:
            print(f"  ✓ MATCH! Cost: {dij_cost:.4f}")
        else:
            print(f"  ✗ MISMATCH!")
            print(f"    Dijkstra: {dij_cost:.4f}")
            print(f"    Bidirectional: {bi_cost:.4f}")
            print(f"    Difference: {diff:.4f}")
    elif dij_success:
        print(f"  ✗ Dijkstra found path, Bidirectional did NOT")
    elif bi_success:
        print(f"  ✗ Bidirectional found path, Dijkstra did NOT")
    else:
        print(f"  Both failed")
    print("=" * 60)


def run_batch_test(con: duckdb.DuckDBPyConnection, num_samples: int):
    """Batch test."""
    import random
    import time
    
    print(f"=" * 60)
    print(f"BATCH TEST: {num_samples} samples")
    print(f"=" * 60)
    
    edges = [e[0] for e in con.execute("SELECT DISTINCT id FROM edges").fetchall()]
    print(f"Found {len(edges)} edges")
    
    # Pre-load adjacency
    shortcuts_raw = con.execute("""
        SELECT from_edge, to_edge, cost, inside, cell FROM shortcuts
    """).fetchall()
    
    fwd_adj, bwd_adj, fwd_simple = {}, {}, {}
    for from_e, to_e, cost, inside, cell in shortcuts_raw:
        cell_res = h3.get_resolution(h3.int_to_str(cell)) if cell and cell != 0 else -1
        if from_e not in fwd_adj:
            fwd_adj[from_e] = []
            fwd_simple[from_e] = []
        fwd_adj[from_e].append((to_e, cost, inside, cell_res))
        fwd_simple[from_e].append((to_e, cost))
        if to_e not in bwd_adj:
            bwd_adj[to_e] = []
        bwd_adj[to_e].append((from_e, cost, inside, cell_res))
    
    matches, mismatches, dij_only, bi_only, both_fail = 0, 0, 0, 0, 0
    start = time.time()
    
    for i in range(num_samples):
        src, tgt = random.sample(edges, 2)
        
        # Dijkstra (call method - no inline modifications)
        dij_cost, _, dij_success = query_dijkstra_cached(con, src, tgt, fwd_simple)
        
        # Bidirectional
        bi_cost, _, bi_success = query_bidirectional_pruned(con, src, tgt, fwd_adj, bwd_adj)
        
        if dij_success and bi_success:
            if abs(dij_cost - bi_cost) < 0.0001:
                matches += 1
            else:
                mismatches += 1
                print(f"  MISMATCH: {src}->{tgt}: Dij={dij_cost:.4f}, Bi={bi_cost:.4f}")
        elif dij_success:
            dij_only += 1
        elif bi_success:
            bi_only += 1
        else:
            both_fail += 1
        
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{num_samples}: {matches} matches, {mismatches + dij_only} issues")
    
    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {elapsed:.2f}s ({elapsed/num_samples:.3f}s/sample)")
    print(f"  ✓ Matches: {matches}")
    print(f"  ✗ Mismatches: {mismatches}")
    print(f"  ✗ Dij only: {dij_only}")
    print(f"  ? Bi only: {bi_only}")
    print(f"  - Both fail: {both_fail}")
    print(f"  Success rate: {matches/num_samples*100:.1f}%")
    print(f"{'=' * 60}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single: python query_bidirectional_pruned.py <db_path> <source> <target>")
        print("  Batch:  python query_bidirectional_pruned.py <db_path> --batch [N]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    con = duckdb.connect(db_path, read_only=True)
    
    if len(sys.argv) >= 3 and sys.argv[2] == "--batch":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        run_batch_test(con, n)
    elif len(sys.argv) >= 4:
        run_single_test(con, int(sys.argv[2]), int(sys.argv[3]))
    else:
        print("Need source/target or --batch")
    
    con.close()


if __name__ == "__main__":
    main()
