"""
Compare bi_dijkstra_sp with standard dijkstra_sp.
"""
import sys
import time
import random
from routing_algorithms_sp import dijkstra_sp, bi_dijkstra_sp, load_adjacency
import duckdb

def compare_bi_dijkstra(db_path, n_samples=20):
    con = duckdb.connect(db_path, read_only=True)
    fwd_adj, bwd_adj = load_adjacency(con)
    edges = list(fwd_adj.keys())
    
    random.seed(42)
    matches = 0
    dij_time = 0.0
    bi_time = 0.0
    
    print(f"Comparing {n_samples} pairs...")
    
    for i in range(n_samples):
        src = random.choice(edges)
        tgt = random.choice(edges)
        while src == tgt:
            tgt = random.choice(edges)
            
        t0 = time.time()
        c1, _, ok1 = dijkstra_sp(con, src, tgt, fwd_adj)
        dij_time += time.time() - t0
        
        t0 = time.time()
        c2, _, ok2 = bi_dijkstra_sp(con, src, tgt, fwd_adj, bwd_adj)
        bi_time += time.time() - t0
        
        if ok1 and ok2 and abs(c1 - c2) < 0.01:
            matches += 1
        elif not ok1 and not ok2:
            matches += 1
            
        if (i+1) % 5 == 0:
            print(f"{i+1}/{n_samples} checked")
            
    print(f"\nResults:")
    print(f"Match Rate: {matches}/{n_samples} ({100*matches/n_samples}%)")
    print(f"Avg Dijkstra Time: {dij_time/n_samples*1000:.2f} ms")
    print(f"Avg Bi-Dijkstra Time: {bi_time/n_samples*1000:.2f} ms")
    print(f"Speedup: {dij_time/bi_time:.2f}x")
    
    con.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/Somerset.db"
    compare_bi_dijkstra(db_path)
