"""
Debug script to compare bidirectional vs Dijkstra paths step-by-step.
"""
import heapq
import duckdb
import h3

def get_edge_cost(con, edge_id):
    result = con.execute("SELECT cost FROM edges WHERE id = ?", [edge_id]).fetchone()
    return result[0] if result else 0.0

def get_edge_res(con, edge_id):
    result = con.execute("SELECT lca_res FROM edges WHERE id = ?", [edge_id]).fetchone()
    return result[0] if result else -1

def compute_high_cell(con, source_edge, target_edge):
    result = con.execute("""
        SELECT 
            e1.lca_res AS src_res, e1.to_cell AS src_cell,
            e2.lca_res AS tgt_res, e2.to_cell AS tgt_cell
        FROM edges e1, edges e2
        WHERE e1.id = ? AND e2.id = ?
    """, [source_edge, target_edge]).fetchone()
    
    if not result:
        return 0, -1
    
    src_res, src_cell, tgt_res, tgt_cell = result
    
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
    
    for res in range(15, -1, -1):
        p1 = h3.cell_to_parent(src_cell, res) if h3.get_resolution(src_cell) >= res else None
        p2 = h3.cell_to_parent(tgt_cell, res) if h3.get_resolution(tgt_cell) >= res else None
        if p1 and p2 and p1 == p2:
            return h3.str_to_int(p1), res
    return 0, -1

def debug_compare(con, source_edge, target_edge):
    """Compare Dijkstra and Bidirectional paths."""
    print(f"\n{'='*60}")
    print(f"DEBUG: {source_edge} -> {target_edge}")
    print(f"{'='*60}")
    
    # Get metadata
    high_cell, high_res = compute_high_cell(con, source_edge, target_edge)
    src_res = get_edge_res(con, source_edge)
    tgt_res = get_edge_res(con, target_edge)
    target_cost = get_edge_cost(con, target_edge)
    
    print(f"high_res = {high_res}, src_res = {src_res}, tgt_res = {tgt_res}")
    print(f"target_cost = {target_cost:.4f}")
    
    # Load shortcuts
    shortcuts_raw = con.execute("SELECT from_edge, to_edge, cost, inside, cell FROM shortcuts").fetchall()
    
    fwd_adj = {}
    fwd_simple = {}
    for from_e, to_e, cost, inside, cell in shortcuts_raw:
        cell_res = h3.get_resolution(h3.int_to_str(cell)) if cell and cell != 0 else -1
        if from_e not in fwd_adj:
            fwd_adj[from_e] = []
        fwd_adj[from_e].append((to_e, cost, inside, cell_res))
        if from_e not in fwd_simple:
            fwd_simple[from_e] = []
        fwd_simple[from_e].append((to_e, cost))
    
    # Run Dijkstra
    dist_dij = {source_edge: 0.0}
    parent_dij = {source_edge: source_edge}
    pq = [(0.0, source_edge)]
    dij_cost = -1
    
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist_dij.get(u, float('inf')):
            continue
        if u == target_edge:
            dij_cost = d + target_cost
            break
        for to_e, c in fwd_simple.get(u, []):
            nd = d + c
            if to_e not in dist_dij or nd < dist_dij[to_e]:
                dist_dij[to_e] = nd
                parent_dij[to_e] = u
                heapq.heappush(pq, (nd, to_e))
    
    # Reconstruct Dijkstra path
    dij_path = []
    curr = target_edge
    while curr != parent_dij.get(curr, curr):
        dij_path.append(curr)
        curr = parent_dij[curr]
    dij_path.append(curr)
    dij_path.reverse()
    
    print(f"\nDijkstra cost: {dij_cost:.4f}")
    print(f"Dijkstra path ({len(dij_path)} edges): {dij_path}")
    
    # Check each edge in Dijkstra path
    print("\nDijkstra path edge details:")
    for i, edge in enumerate(dij_path):
        e_res = get_edge_res(con, edge)
        e_cost = get_edge_cost(con, edge)
        # Find inside value from shortcuts leading TO this edge
        inside_val = None
        if i > 0:
            prev_edge = dij_path[i-1]
            for to_e, c, ins, _ in fwd_adj.get(prev_edge, []):
                if to_e == edge:
                    inside_val = ins
                    break
        print(f"  [{i}] Edge {edge}: res={e_res}, cost={e_cost:.4f}, inside={inside_val}")
        # Check if this edge would be allowed by filtering
        if i > 0 and inside_val is not None:
            prev_res = get_edge_res(con, dij_path[i-1])
            if prev_res > high_res:
                if inside_val == 1:
                    allowed = "✓ (above peak, inside=1)"
                elif inside_val == -1:
                    allowed = "? (above peak, inside=-1, needs used_flag)"
                else:
                    allowed = f"✗ (above peak, inside={inside_val} not allowed)"
            else:
                if inside_val in (0, -2):
                    allowed = "✓ (at/below peak, inside={0,-2})"
                elif inside_val == -1:
                    allowed = "✓ (at/below peak, inside=-1)"
                else:
                    allowed = f"? (at/below peak, inside={inside_val})"
            print(f"       Filter: {allowed}")

if __name__ == "__main__":
    con = duckdb.connect("/home/kaveh/projects/h3-routing-platform/data/Somerset.db", read_only=True)
    
    # Use a failing case from the batch test
    # MISMATCH: 1024->884: Dij=69.1813, Bi=71.2853
    debug_compare(con, 1024, 884)
    
    con.close()
