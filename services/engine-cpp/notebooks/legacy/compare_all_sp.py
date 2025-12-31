"""
Compare all shortest path algorithms against Dijkstra.

Usage:
    python compare_all_sp.py <db_path> [--samples N]
"""

import sys
import time
import random
from routing_algorithms_sp import (
    dijkstra_sp, bi_classic_sp, uni_lca_sp, bi_lca_sp, bi_lca_res_sp, 
    load_adjacency
)
import duckdb


def compare_all(db_path: str, n_samples: int = 100):
    """Compare all algorithms to dijkstra on random samples."""
    
    con = duckdb.connect(db_path, read_only=True)
    
    print("Loading shortcuts...")
    fwd_adj, bwd_adj = load_adjacency(con)
    edges = list(fwd_adj.keys())
    print(f"Loaded {len(edges)} edges, {sum(len(v) for v in fwd_adj.values())} shortcuts")
    
    random.seed(42)
    
    algorithms = {
        'bi_classic_sp': bi_classic_sp,
        'uni_lca_sp': uni_lca_sp,
        'bi_lca_sp': bi_lca_sp,
        'bi_lca_res_sp': bi_lca_res_sp
    }
    
    matches = {name: 0 for name in algorithms}
    times = {name: 0.0 for name in algorithms}
    times['dijkstra_sp'] = 0.0
    
    print(f"\nComparing {n_samples} random pairs...")
    print("=" * 70)
    
    for i in range(n_samples):
        src = random.choice(edges)
        tgt = random.choice(edges)
        while src == tgt:
            tgt = random.choice(edges)
        
        t0 = time.time()
        dij_cost, _, dij_ok = dijkstra_sp(con, src, tgt, fwd_adj)
        times['dijkstra_sp'] += time.time() - t0
        
        for name, func in algorithms.items():
            t0 = time.time()
            if 'bi_' in name:
                cost, _, ok = func(con, src, tgt, fwd_adj, bwd_adj)
            else:
                cost, _, ok = func(con, src, tgt, fwd_adj)
            times[name] += time.time() - t0
            
            if ok and dij_ok and abs(cost - dij_cost) < 0.01:
                matches[name] += 1
        
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{n_samples} completed")
    
    print("=" * 70)
    print()
    print("RESULTS (vs Dijkstra):")
    print("-" * 70)
    print(f"{'Algorithm':<20} {'Match Rate':>12} {'Avg Time':>12} {'Speedup':>10}")
    print("-" * 70)
    
    dij_avg = times['dijkstra_sp'] / n_samples * 1000
    print(f"{'dijkstra_sp':<20} {'(baseline)':<12} {dij_avg:>10.2f} ms {'-':>10}")
    
    for name in algorithms:
        avg_time = times[name] / n_samples * 1000
        rate = f"{matches[name]}/{n_samples}"
        pct = f"({100*matches[name]/n_samples:.0f}%)"
        speedup = times['dijkstra_sp'] / times[name] if times[name] > 0 else 0
        print(f"{name:<20} {rate:>6} {pct:<5} {avg_time:>10.2f} ms {speedup:>9.1f}x")
    
    print("-" * 70)
    con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_all_sp.py <db_path> [--samples N]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    n_samples = 100
    
    if "--samples" in sys.argv:
        idx = sys.argv.index("--samples")
        n_samples = int(sys.argv[idx + 1])
    
    compare_all(db_path, n_samples)
