"""
Compare bi_classic algorithm against Dijkstra.

Usage:
    python compare_bi_classic.py <db_path> [--samples N]
"""

import sys
import time
import random
from routing_algorithms_sp import dijkstra_sp, bi_classic_sp, load_adjacency
import duckdb


def compare(db_path: str, n_samples: int = 100):
    """Compare bi_classic to dijkstra on random samples."""
    
    con = duckdb.connect(db_path, read_only=True)
    
    print("Loading shortcuts...")
    fwd_adj, bwd_adj = load_adjacency(con)
    edges = list(fwd_adj.keys())
    print(f"Loaded {len(edges)} edges, {sum(len(v) for v in fwd_adj.values())} shortcuts")
    
    random.seed(42)
    
    matches = 0
    mismatches = []
    dij_time = 0
    bi_time = 0
    
    print(f"\nComparing {n_samples} random pairs...")
    print("=" * 60)
    
    for i in range(n_samples):
        src = random.choice(edges)
        tgt = random.choice(edges)
        while src == tgt:
            tgt = random.choice(edges)
        
        # Dijkstra
        t0 = time.time()
        dij_cost, dij_path, dij_ok = dijkstra_sp(con, src, tgt, fwd_adj)
        dij_time += time.time() - t0
        
        # bi_classic
        t0 = time.time()
        bi_cost, bi_path, bi_ok = bi_classic_sp(con, src, tgt, fwd_adj, bwd_adj)
        bi_time += time.time() - t0
        
        if dij_ok and bi_ok:
            if abs(dij_cost - bi_cost) < 0.01:
                matches += 1
            else:
                mismatches.append({
                    'source': src,
                    'target': tgt,
                    'dijkstra_cost': dij_cost,
                    'bi_cost': bi_cost,
                    'diff': bi_cost - dij_cost,
                    'dijkstra_path_len': len(dij_path),
                    'bi_path_len': len(bi_path)
                })
        elif not dij_ok and not bi_ok:
            matches += 1  # Both failed = match
        else:
            mismatches.append({
                'source': src,
                'target': tgt,
                'dijkstra_cost': dij_cost if dij_ok else None,
                'bi_cost': bi_cost if bi_ok else None,
                'diff': None,
                'dijkstra_path_len': len(dij_path) if dij_ok else 0,
                'bi_path_len': len(bi_path) if bi_ok else 0
            })
        
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{n_samples}: {matches} matches, {len(mismatches)} mismatches")
    
    print("=" * 60)
    print(f"\nRESULTS:")
    print(f"  Total samples: {n_samples}")
    print(f"  Matches: {matches} ({100*matches/n_samples:.1f}%)")
    print(f"  Mismatches: {len(mismatches)} ({100*len(mismatches)/n_samples:.1f}%)")
    print()
    print(f"  Dijkstra avg time: {1000*dij_time/n_samples:.2f} ms")
    print(f"  bi_classic avg time: {1000*bi_time/n_samples:.2f} ms")
    print(f"  Speedup: {dij_time/bi_time:.1f}x")
    
    if mismatches:
        print("\n" + "=" * 60)
        print("MISMATCH DETAILS (first 10):")
        for m in mismatches[:10]:
            print(f"  {m['source']} -> {m['target']}")
            print(f"    Dijkstra: {m['dijkstra_cost']}, path={m['dijkstra_path_len']} edges")
            print(f"    bi_classic: {m['bi_cost']}, path={m['bi_path_len']} edges")
            if m['diff'] is not None:
                print(f"    Diff: {m['diff']:.4f}")
            print()
    
    con.close()
    return matches, len(mismatches)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_bi_classic.py <db_path> [--samples N]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    n_samples = 100
    
    if "--samples" in sys.argv:
        idx = sys.argv.index("--samples")
        n_samples = int(sys.argv[idx + 1])
    
    compare(db_path, n_samples)
