"""
Unidirectional Pruned Search Algorithm (Python Prototype)

This implements a single-direction hierarchy search that transitions through
phases based on H3 resolution levels:

1. ASCENDING (u_res > high_res): Only use inside = 1 (upward)
2. PEAK (u_res == high_res): Use inside = 0 once, then inside = -1
3. DESCENDING (u_res < high_res): Use inside = -2 first, then inside = -1

Usage:
    python query_unidirectional.py <db_path> <source_edge> <target_edge>
"""

import heapq
import sys
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import duckdb
import h3


class Phase(Enum):
    """Current phase in the hierarchy traversal."""
    ASCENDING = auto()      # u_res > high_res
    PEAK_INTERNAL = auto()  # u_res == high_res, first crossing (inside=0)
    PEAK_DOWN = auto()      # u_res == high_res, after internal (inside=-1)
    DESCENDING_EXT = auto() # u_res < high_res, first external (inside=-2)
    DESCENDING = auto()     # u_res < high_res, downward only (inside=-1)


@dataclass
class PQEntry:
    """Priority queue entry with state."""
    dist: float
    edge: int
    res: int
    phase: Phase
    
    def __lt__(self, other):
        return self.dist < other.dist


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
    lca = h3.cell_to_parent(src_cell, 0)  # Start at res 0
    for res in range(15, -1, -1):
        p1 = h3.cell_to_parent(src_cell, res) if h3.get_resolution(src_cell) >= res else None
        p2 = h3.cell_to_parent(tgt_cell, res) if h3.get_resolution(tgt_cell) >= res else None
        if p1 and p2 and p1 == p2:
            lca = p1
            break
    
    return h3.str_to_int(lca), h3.get_resolution(lca)


def get_edge_cost(con: duckdb.DuckDBPyConnection, edge_id: int) -> float:
    """Get the cost of a single edge."""
    result = con.execute("SELECT cost FROM edges WHERE id = ?", [edge_id]).fetchone()
    return result[0] if result else 0.0


def get_edge_res(con: duckdb.DuckDBPyConnection, edge_id: int) -> int:
    """Get the lca_res of an edge."""
    result = con.execute("SELECT lca_res FROM edges WHERE id = ?", [edge_id]).fetchone()
    return result[0] if result else -1


def query_unidirectional_pruned(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int,
    fwd_adj: Dict[int, List[Tuple[int, float, int, int]]] = None
) -> Tuple[float, List[int], bool]:
    """
    Unidirectional pruned search algorithm.
    
    Filtering rules based on current edge resolution (u_res) vs LCA resolution (high_res):
    
    1. u_res > high_res  : Allow ALL inside values (1, 0, -1, -2)
    2. u_res == high_res : Allow ALL inside values (1, 0, -1, -2)  
    3. u_res < high_res  : Allow inside=-2 (once), -1, 0. NO inside=1
    
    Args:
        con: DuckDB connection
        source_edge: Starting edge ID
        target_edge: Destination edge ID
        fwd_adj: Optional pre-loaded adjacency list
        
    Returns:
        (cost, path, success)
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Step 1: Compute LCA (high cell) resolution
    high_cell, high_res = compute_high_cell(con, source_edge, target_edge)
    
    # Step 2: Load shortcuts if not provided
    if fwd_adj is None:
        shortcuts_raw = con.execute("""
            SELECT from_edge, to_edge, cost, inside, cell
            FROM shortcuts
        """).fetchall()
        
        fwd_adj = {}
        for from_e, to_e, cost, inside, cell in shortcuts_raw:
            cell_res = h3.get_resolution(h3.int_to_str(cell)) if cell and cell != 0 else -1
            if from_e not in fwd_adj:
                fwd_adj[from_e] = []
            fwd_adj[from_e].append((to_e, cost, inside, cell_res))
    
    # Step 3: Initialize Dijkstra with state tracking
    # State: (edge_id, counter, used_minus1)
    # - counter: number of times inside=0 or -2 was used
    # - used_minus1: True if inside=-1 was used (after that, only -1 allowed)
    src_res = get_edge_res(con, source_edge)
    
    # dist[(edge, counter, used_minus1)] -> distance
    dist: Dict[Tuple[int, int, bool], float] = {}
    parent: Dict[Tuple[int, int, bool], Tuple[int, int, bool]] = {}
    
    start_key = (source_edge, 0, False)
    dist[start_key] = 0.0
    parent[start_key] = start_key
    
    # Priority queue: (distance, edge, u_res, counter, used_minus1)
    pq = [(0.0, source_edge, src_res, 0, False)]
    
    MAX_USES = 2  # Maximum times inside=0 or -2 can be used
    
    # Step 4: Dijkstra with inside filtering
    while pq:
        d, u, u_res, counter, used_minus1 = heapq.heappop(pq)
        state_key = (u, counter, used_minus1)
        
        # Skip if we already found better path
        if state_key in dist and d > dist[state_key]:
            continue
        
        # Found target
        if u == target_edge:
            path = []
            curr_key = state_key
            while curr_key != parent.get(curr_key, curr_key):
                path.append(curr_key[0])
                curr_key = parent[curr_key]
            path.append(curr_key[0])
            path.reverse()
            return d, path, True
        
        # Explore neighbors
        if u not in fwd_adj:
            continue
        
        for to_edge, cost, inside, cell_res in fwd_adj[u]:
            allowed = False
            next_counter = counter
            next_used_minus1 = used_minus1
            
            # ========== FILTERING LOGIC ==========
            if u_res > high_res:
                # ABOVE PEAK: only inside=1 allowed
                if inside == 1 and not used_minus1:
                    allowed = True
                elif inside == -1 and used_minus1:
                    allowed = True
            elif inside in {0, -2} and counter < MAX_USES:
                allowed = True
                next_counter = counter + 1
                next_used_minus1 = True
            elif inside == -1:
                allowed = True
                next_used_minus1 = True
            # =====================================
            
            if not allowed:
                continue
            
            nd = d + cost
            next_key = (to_edge, next_counter, next_used_minus1)
            
            if next_key not in dist or nd < dist[next_key]:
                dist[next_key] = nd
                parent[next_key] = state_key
                heapq.heappush(pq, (nd, to_edge, cell_res, next_counter, next_used_minus1))
    
    return -1, [], False



def query_dijkstra(
    con: duckdb.DuckDBPyConnection,
    source_edge: int,
    target_edge: int
) -> Tuple[float, List[int], bool]:
    """
    General Dijkstra search on the shortcut graph (no inside filtering).
    This serves as ground truth for comparison.
    
    Returns:
        (cost, path, success)
    """
    INF = float('inf')
    
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    # Load all shortcuts into memory
    shortcuts = con.execute("""
        SELECT from_edge, to_edge, cost FROM shortcuts
    """).fetchall()
    
    # Build forward adjacency (no inside filtering)
    fwd_adj: Dict[int, List[Tuple[int, float]]] = {}
    for from_e, to_e, cost in shortcuts:
        if from_e not in fwd_adj:
            fwd_adj[from_e] = []
        fwd_adj[from_e].append((to_e, cost))
    
    # Standard Dijkstra
    dist: Dict[int, float] = {source_edge: 0.0}
    parent: Dict[int, int] = {source_edge: source_edge}
    pq: List[Tuple[float, int]] = [(0.0, source_edge)]
    
    while pq:
        d, u = heapq.heappop(pq)
        
        if u in dist and d > dist[u]:
            continue
        
        if u == target_edge:
            # Reconstruct path
            path = []
            curr = u
            while curr != parent.get(curr, curr):
                path.append(curr)
                curr = parent[curr]
            path.append(curr)
            path.reverse()
            return d, path, True
        
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
    """
    General Dijkstra with pre-loaded adjacency (faster for batch testing).
    """
    if source_edge == target_edge:
        return get_edge_cost(con, source_edge), [source_edge], True
    
    dist: Dict[int, float] = {source_edge: 0.0}
    parent: Dict[int, int] = {source_edge: source_edge}
    pq: List[Tuple[float, int]] = [(0.0, source_edge)]
    
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
            return d, path, True
        
        if u not in fwd_adj:
            continue
        
        for to_edge, cost in fwd_adj[u]:
            nd = d + cost
            if to_edge not in dist or nd < dist[to_edge]:
                dist[to_edge] = nd
                parent[to_edge] = u
                heapq.heappush(pq, (nd, to_edge))
    
    return -1, [], False


def main():
    import random
    import time
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single: python query_unidirectional.py <db_path> <source_edge> <target_edge>")
        print("  Batch:  python query_unidirectional.py <db_path> --batch [num_samples]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    con = duckdb.connect(db_path, read_only=True)
    
    # Check for batch mode
    if len(sys.argv) >= 3 and sys.argv[2] == "--batch":
        num_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        run_batch_test(con, num_samples)
    elif len(sys.argv) >= 4:
        source_edge = int(sys.argv[2])
        target_edge = int(sys.argv[3])
        run_single_test(con, source_edge, target_edge)
    else:
        print("Error: Need source and target edges, or --batch flag")
        sys.exit(1)
    
    con.close()


def run_single_test(con: duckdb.DuckDBPyConnection, source_edge: int, target_edge: int):
    """Run single comparison between Dijkstra and Unidirectional."""
    print(f"=" * 60)
    print(f"Routing: {source_edge} -> {target_edge}")
    print(f"=" * 60)
    
    # Run Dijkstra (ground truth)
    print("\n[1] General Dijkstra (ground truth):")
    dij_cost, dij_path, dij_success = query_dijkstra(con, source_edge, target_edge)
    if dij_success:
        print(f"    Cost: {dij_cost:.4f}")
        print(f"    Path: {len(dij_path)} edges")
    else:
        print(f"    FAILED: No path found")
    
    # Run Unidirectional Pruned
    print("\n[2] Unidirectional Pruned Search:")
    uni_cost, uni_path, uni_success = query_unidirectional_pruned(con, source_edge, target_edge)
    if uni_success:
        print(f"    Cost: {uni_cost:.4f}")
        print(f"    Path: {len(uni_path)} edges")
    else:
        print(f"    FAILED: No path found")
    
    # Compare
    print("\n" + "=" * 60)
    print("COMPARISON:")
    compare_results(dij_cost, dij_success, uni_cost, uni_success)
    print("=" * 60)


def run_batch_test(con: duckdb.DuckDBPyConnection, num_samples: int):
    """Run batch comparison with random source/target pairs."""
    import random
    import time
    
    print(f"=" * 60)
    print(f"BATCH TEST: {num_samples} random samples")
    print(f"=" * 60)
    
    # Get all edge IDs
    edges = con.execute("SELECT DISTINCT id FROM edges").fetchall()
    edge_ids = [e[0] for e in edges]
    print(f"Found {len(edge_ids)} edges in database")
    
    if len(edge_ids) < 2:
        print("Error: Need at least 2 edges for testing")
        return
    
    # Pre-load shortcuts for efficiency
    print("Loading shortcuts...")
    shortcuts_raw = con.execute("""
        SELECT from_edge, to_edge, cost, inside, cell
        FROM shortcuts
    """).fetchall()
    
    fwd_adj = {}
    fwd_adj_simple = {}  # For Dijkstra
    for from_e, to_e, cost, inside, cell in shortcuts_raw:
        cell_res = h3.get_resolution(h3.int_to_str(cell)) if cell and cell != 0 else -1
        if from_e not in fwd_adj:
            fwd_adj[from_e] = []
            fwd_adj_simple[from_e] = []
        fwd_adj[from_e].append((to_e, cost, inside, cell_res))
        fwd_adj_simple[from_e].append((to_e, cost))
    
    print(f"Loaded {len(shortcuts_raw)} shortcuts")
    
    # Stats
    matches = 0
    mismatches = 0
    dij_only = 0
    uni_only = 0
    both_fail = 0
    mismatch_details = []
    
    start_time = time.time()
    stop_on_mismatch = True  # Stop at first mismatch for debugging
    
    for i in range(num_samples):
        # Random source and target
        source, target = random.sample(edge_ids, 2)
        
        # Run both (with cached adjacency)
        dij_cost, _, dij_success = query_dijkstra_cached(con, source, target, fwd_adj_simple)
        uni_cost, _, uni_success = query_unidirectional_pruned(con, source, target, fwd_adj)
        
        # Compare
        if dij_success and uni_success:
            if abs(dij_cost - uni_cost) < 0.0001:
                matches += 1
            else:
                mismatches += 1
                mismatch_details.append((source, target, dij_cost, uni_cost))
                if stop_on_mismatch:
                    print(f"\n  MISMATCH at sample {i+1}: {source} -> {target}")
                    print(f"    Dijkstra: {dij_cost:.4f}, Unidirectional: {uni_cost:.4f}")
                    break
        elif dij_success and not uni_success:
            dij_only += 1
            mismatch_details.append((source, target, dij_cost, None))
            if stop_on_mismatch:
                print(f"\n  MISMATCH at sample {i+1}: {source} -> {target}")
                print(f"    Dijkstra found path (cost={dij_cost:.4f}), Unidirectional FAILED")
                break
        elif not dij_success and uni_success:
            uni_only += 1
        else:
            both_fail += 1
        
        # Progress
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{num_samples} ({matches} matches, {mismatches + dij_only} mismatches)")
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("BATCH TEST RESULTS:")
    print(f"  Total samples: {num_samples}")
    print(f"  Time: {elapsed:.2f}s ({elapsed/num_samples:.3f}s per sample)")
    print(f"  ✓ Matches: {matches}")
    print(f"  ✗ Mismatches (both found, different cost): {mismatches}")
    print(f"  ✗ Dijkstra only (uni failed): {dij_only}")
    print(f"  ? Uni only (dij failed): {uni_only}")
    print(f"  - Both failed: {both_fail}")
    
    success_rate = matches / num_samples * 100 if num_samples > 0 else 0
    print(f"\n  SUCCESS RATE: {success_rate:.1f}%")
    
    if mismatch_details:
        print("\n  MISMATCH DETAILS (first 10):")
        for src, tgt, d_cost, u_cost in mismatch_details[:10]:
            if u_cost is None:
                print(f"    {src} -> {tgt}: Dijkstra={d_cost:.4f}, Uni=FAILED")
            else:
                print(f"    {src} -> {tgt}: Dijkstra={d_cost:.4f}, Uni={u_cost:.4f}")
    
    print("=" * 60)


def compare_results(dij_cost, dij_success, uni_cost, uni_success):
    """Compare results from both algorithms."""
    if dij_success and uni_success:
        diff = abs(dij_cost - uni_cost)
        if diff < 0.0001:
            print(f"  ✓ MATCH! Both algorithms found cost: {dij_cost:.4f}")
        else:
            print(f"  ✗ MISMATCH!")
            print(f"    Dijkstra: {dij_cost:.4f}")
            print(f"    Unidirectional: {uni_cost:.4f}")
            print(f"    Difference: {diff:.4f}")
    elif dij_success and not uni_success:
        print(f"  ✗ Dijkstra found path (cost={dij_cost:.4f}), Unidirectional did NOT")
    elif not dij_success and uni_success:
        print(f"  ✗ Unidirectional found path, Dijkstra did NOT (unexpected!)")
    else:
        print(f"  Both algorithms: No path found")


if __name__ == "__main__":
    main()
