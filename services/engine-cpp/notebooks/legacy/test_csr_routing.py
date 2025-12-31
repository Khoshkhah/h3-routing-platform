#!/usr/bin/env python3
"""
Test script to compare CSR routing with classic Dijkstra algorithm.

This loads data from DuckDB (like the C++ engine does) and runs comparisons
using the pure Python algorithm implementations.

Usage:
    python test_csr_routing.py [db_path] [n_samples]
    
Example:
    python test_csr_routing.py /path/to/Somerset.db 50
"""

import sys
import random
from heapq import heappop, heappush
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple
import time

# Try to import h3
try:
    import h3
except ImportError:
    print("WARNING: h3 not installed, using mock implementation")
    class MockH3:
        def get_resolution(self, s): return 7
        def int_to_str(self, i): return f"0x{i:x}"
        def str_to_int(self, s): return int(s, 16) if s.startswith("0x") else 0
        def cell_to_parent(self, s, r): return s
    h3 = MockH3()


@dataclass
class Shortcut:
    from_edge: int
    to_edge: int
    cost: float
    via_edge: int
    cell: int
    inside: int
    cell_res: int


@dataclass
class AlgorithmData:
    shortcuts: List[Shortcut]
    fwd_adj: Dict[int, List[Shortcut]]
    bwd_adj: Dict[int, List[Shortcut]]
    edge_meta: Dict[int, dict]


def load_from_duckdb(db_path: str) -> AlgorithmData:
    """Load data from DuckDB database."""
    import duckdb
    
    print(f"Loading from DuckDB: {db_path}")
    conn = duckdb.connect(db_path, read_only=True)
    
    # Load shortcuts
    result = conn.execute("SELECT from_edge, to_edge, cost, via_edge, cell, inside FROM shortcuts").fetchall()
    
    shortcuts = []
    fwd_adj = defaultdict(list)
    bwd_adj = defaultdict(list)
    
    def get_res(cell):
        if cell == 0:
            return -1
        try:
            return h3.get_resolution(h3.int_to_str(cell))
        except:
            return -1
    
    for row in result:
        from_edge, to_edge, cost, via_edge, cell, inside = row
        sc = Shortcut(
            from_edge=from_edge,
            to_edge=to_edge,
            cost=cost,
            via_edge=via_edge,
            cell=cell,
            inside=inside,
            cell_res=get_res(cell)
        )
        shortcuts.append(sc)
        fwd_adj[from_edge].append(sc)
        bwd_adj[to_edge].append(sc)
    
    print(f"  Loaded {len(shortcuts)} shortcuts")
    
    # Load edges
    result = conn.execute("SELECT id, cost, lca_res, from_cell, to_cell FROM edges").fetchall()
    edge_meta = {}
    for row in result:
        edge_id, cost, lca_res, from_cell, to_cell = row
        edge_meta[edge_id] = {
            'cost': cost,
            'lca_res': lca_res,
            'from_cell': from_cell,
            'to_cell': to_cell
        }
    
    print(f"  Loaded {len(edge_meta)} edges")
    conn.close()
    
    return AlgorithmData(
        shortcuts=shortcuts,
        fwd_adj=dict(fwd_adj),
        bwd_adj=dict(bwd_adj),
        edge_meta=edge_meta
    )


def get_edge_cost(edge_id: int, data: AlgorithmData) -> float:
    if edge_id in data.edge_meta:
        return data.edge_meta[edge_id]['cost']
    return 0.0


def dijkstra_general(source: int, target: int, data: AlgorithmData) -> Tuple[float, List[int], bool]:
    """Standard Dijkstra using ALL shortcuts (baseline - no inside filtering)."""
    INF = float('inf')
    
    if source == target:
        return (get_edge_cost(source, data), [source], True)
    
    dist = {source: 0.0}
    parent = {source: None}
    pq = [(0.0, source)]
    
    while pq:
        d, u = heappop(pq)
        
        if u == target:
            break
        
        if d > dist.get(u, INF):
            continue
        
        for sc in data.fwd_adj.get(u, []):
            nd = d + sc.cost
            if sc.to_edge not in dist or nd < dist[sc.to_edge]:
                dist[sc.to_edge] = nd
                parent[sc.to_edge] = u
                heappush(pq, (nd, sc.to_edge))
    
    if target not in dist:
        return (-1, [], False)
    
    # Reconstruct path
    path = []
    curr = target
    while curr is not None:
        path.append(curr)
        curr = parent[curr]
    path.reverse()
    
    # Add target edge cost
    total_cost = dist[target] + get_edge_cost(target, data)
    return (total_cost, path, True)


def query_classic(source: int, target: int, data: AlgorithmData) -> Tuple[float, List[int], bool]:
    """Bidirectional Dijkstra with inside filtering (same as C++)."""
    INF = float('inf')
    
    if source == target:
        return (get_edge_cost(source, data), [source], True)
    
    dist_fwd = {}
    dist_bwd = {}
    parent_fwd = {}
    parent_bwd = {}
    pq_fwd = []
    pq_bwd = []
    
    dist_fwd[source] = 0.0
    parent_fwd[source] = source
    heappush(pq_fwd, (0.0, source))
    
    target_cost = get_edge_cost(target, data)
    dist_bwd[target] = target_cost
    parent_bwd[target] = target
    heappush(pq_bwd, (target_cost, target))
    
    best = INF
    meeting = None
    found = False
    
    while pq_fwd or pq_bwd:
        # Forward step
        if pq_fwd:
            d, u = heappop(pq_fwd)
            
            if u in dist_fwd and d > dist_fwd[u]:
                pass  # stale
            elif d >= best:
                pass  # pruned
            else:
                for sc in data.fwd_adj.get(u, []):
                    if sc.inside != 1:
                        continue
                    
                    nd = d + sc.cost
                    if sc.to_edge not in dist_fwd or nd < dist_fwd[sc.to_edge]:
                        dist_fwd[sc.to_edge] = nd
                        parent_fwd[sc.to_edge] = u
                        heappush(pq_fwd, (nd, sc.to_edge))
                        
                        if sc.to_edge in dist_bwd:
                            total = nd + dist_bwd[sc.to_edge]
                            if total < best:
                                best = total
                                meeting = sc.to_edge
                                found = True
        
        # Backward step  
        if pq_bwd:
            d, u = heappop(pq_bwd)
            
            if u in dist_bwd and d > dist_bwd[u]:
                pass
            elif d >= best:
                pass
            else:
                for sc in data.bwd_adj.get(u, []):
                    if sc.inside != -1 and sc.inside != 0:
                        continue
                    
                    nd = d + sc.cost
                    if sc.from_edge not in dist_bwd or nd < dist_bwd[sc.from_edge]:
                        dist_bwd[sc.from_edge] = nd
                        parent_bwd[sc.from_edge] = u
                        heappush(pq_bwd, (nd, sc.from_edge))
                        
                        if sc.from_edge in dist_fwd:
                            total = dist_fwd[sc.from_edge] + nd
                            if total < best:
                                best = total
                                meeting = sc.from_edge
                                found = True
        
        # Early termination
        if pq_fwd and pq_bwd:
            if pq_fwd[0][0] >= best and pq_bwd[0][0] >= best:
                break
        elif not pq_fwd and not pq_bwd:
            break
    
    if not found:
        return (-1, [], False)
    
    # Reconstruct path
    path = []
    curr = meeting
    while True:
        path.append(curr)
        if curr not in parent_fwd or parent_fwd[curr] == curr:
            break
        curr = parent_fwd[curr]
    path.reverse()
    
    curr = meeting
    while True:
        if curr not in parent_bwd or parent_bwd[curr] == curr:
            break
        curr = parent_bwd[curr]
        path.append(curr)
    
    return (best, path, True)


def test_algorithms(data: AlgorithmData, n_samples: int = 50, seed: int = 42):
    """Compare Dijkstra baseline with query_classic."""
    random.seed(seed)
    
    all_edges = list(data.fwd_adj.keys())
    if not all_edges:
        print("ERROR: No edges with shortcuts")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing {n_samples} random route queries")
    print(f"{'='*60}")
    
    matches = 0
    failures = []
    dijkstra_times = []
    classic_times = []
    
    for i in range(n_samples):
        source = random.choice(all_edges)
        target = random.choice(all_edges)
        if source == target:
            continue
        
        # Run Dijkstra (baseline)
        t0 = time.perf_counter()
        dij_cost, dij_path, dij_ok = dijkstra_general(source, target, data)
        dijkstra_times.append(time.perf_counter() - t0)
        
        # Run Classic (bidirectional with inside filtering)
        t0 = time.perf_counter()
        cls_cost, cls_path, cls_ok = query_classic(source, target, data)
        classic_times.append(time.perf_counter() - t0)
        
        # Compare
        if cls_ok and dij_ok:
            if abs(dij_cost - cls_cost) < 0.01:
                matches += 1
            else:
                failures.append({
                    'source': source,
                    'target': target,
                    'dijkstra_cost': dij_cost,
                    'classic_cost': cls_cost,
                    'diff': cls_cost - dij_cost
                })
        elif cls_ok == dij_ok:
            matches += 1  # Both unreachable
        else:
            failures.append({
                'source': source,
                'target': target,
                'dijkstra_ok': dij_ok,
                'classic_ok': cls_ok
            })
        
        # Progress
        if (i + 1) % 10 == 0:
            print(f"  Tested {i+1}/{n_samples}...")
    
    total = len(dijkstra_times)
    avg_dij = sum(dijkstra_times) / total * 1000 if total else 0
    avg_cls = sum(classic_times) / total * 1000 if total else 0
    
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total tests:     {total}")
    print(f"Matches:         {matches} ({100*matches/total:.1f}%)")
    print(f"Failures:        {len(failures)}")
    print(f"Dijkstra avg:    {avg_dij:.3f} ms")
    print(f"Classic avg:     {avg_cls:.3f} ms")
    print(f"Speedup:         {avg_dij/avg_cls:.1f}x" if avg_cls > 0 else "N/A")
    
    if failures:
        print(f"\n{'='*60}")
        print(f"FAILURE EXAMPLES (first 5)")
        print(f"{'='*60}")
        for f in failures[:5]:
            print(f"  {f}")
    
    return matches == total


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/home/kaveh/projects/h3-routing-platform/data/Somerset.db"
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    data = load_from_duckdb(db_path)
    success = test_algorithms(data, n_samples)
    
    print(f"\n{'='*60}")
    if success:
        print("✅ ALL TESTS PASSED - query_classic matches Dijkstra!")
    else:
        print("❌ TESTS FAILED - query_classic has discrepancies!")
    print(f"{'='*60}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
