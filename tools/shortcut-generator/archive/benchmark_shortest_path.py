import duckdb
import time
from pathlib import Path

def benchmark():
    con = duckdb.connect()
    print("--- Shortest Path Benchmark: Iterative vs USING KEY ---")
    
    # 1. Setup Data (Small subset for Burnaby)
    DISTRICT = "Burnaby"
    edges_file = f"/home/kaveh/projects/osm-to-road/data/output/{DISTRICT}/{DISTRICT}_driving_simplified_edges_with_h3.csv"
    graph_file = f"/home/kaveh/projects/osm-to-road/data/output/{DISTRICT}/{DISTRICT}_driving_edge_graph.csv"

    print(f"Loading data for {DISTRICT} (Subset)...")
    con.execute(f"CREATE TABLE edges_raw AS SELECT * FROM read_csv_auto('{edges_file}') LIMIT 2000")
    con.execute(f"CREATE TABLE graph_raw AS SELECT * FROM read_csv_auto('{graph_file}')")

    # Filter graph to only include available edges
    con.execute("""
        CREATE TABLE base_edges AS
        SELECT g.from_edge as src, g.to_edge as dst, e.cost
        FROM graph_raw g
        JOIN edges_raw e1 ON g.from_edge = e1.edge_index
        JOIN edges_raw e2 ON g.to_edge = e2.edge_index
        JOIN edges_raw e ON g.from_edge = e.edge_index
    """)

    # 2. Iterative SQL Approach (Current "Pure" logic)
    print("\n[1] Running Iterative SQL (Current Pure logic)...")
    con.execute("CREATE TABLE paths_iter AS SELECT src, dst, cost FROM base_edges")
    
    start = time.time()
    for i in range(20): # Enough iterations to likely converge on this small subset
        con.execute(f"""
            CREATE OR REPLACE TABLE paths_iter_next AS
            SELECT src, dst, MIN(cost) as cost
            FROM (
                SELECT src, dst, cost FROM paths_iter
                UNION ALL
                SELECT L.src, R.dst, L.cost + R.cost
                FROM paths_iter L
                JOIN base_edges R ON L.dst = R.src
                WHERE L.src != R.dst
            )
            GROUP BY 1, 2
        """)
        
        # Check convergence
        diff = con.sql("""
            SELECT COUNT(*) FROM paths_iter_next 
            EXCEPT 
            SELECT COUNT(*) FROM paths_iter
        """).fetchone()[0] # This is a simplified check
        
        con.execute("DROP TABLE paths_iter")
        con.execute("ALTER TABLE paths_iter_next RENAME TO paths_iter")
        
        if i > 0 and i % 5 == 0:
            print(f"  Iteration {i} complete...")
            
    iter_time = time.time() - start
    iter_count = con.sql("SELECT COUNT(*) FROM paths_iter").fetchone()[0]
    print(f"✓ Iterative SQL: {iter_count} paths in {iter_time:.4f}s")

    # 3. Recursive CTE with USING KEY
    print("\n[2] Running Recursive CTE with USING KEY...")
    # This syntax uses the v1.3+ dictionary-style recursion.
    # It keeps only the best path (src, dst) and allows us to prune inside the recursion.
    
    start = time.time()
    try:
        con.execute("""
            CREATE TABLE paths_using_key AS
            WITH RECURSIVE search(src, dst, cost) USING KEY (src, dst) AS (
                SELECT src, dst, cost
                FROM base_edges
                UNION
                SELECT s.src, e.dst, s.cost + e.cost
                FROM search s 
                JOIN base_edges e ON s.dst = e.src
                WHERE s.src != e.dst
            )
            SELECT * FROM search
        """)
        key_time = time.time() - start
        key_count = con.sql("SELECT COUNT(*) FROM paths_using_key").fetchone()[0]
        print(f"✓ Recursive CTE (USING KEY): {key_count} paths in {key_time:.4f}s")
    except Exception as e:
        print(f"✗ Recursive CTE (USING KEY) failed: {e}")
        key_count = 0
        key_time = 0

    # 4. Compare Results
    print("\n--- Comparison ---")
    if key_count > 0:
        match = iter_count == key_count
        print(f"Count Match: {match}")
        if match:
            # Check if costs match (for the shortest paths)
            diff_costs = con.sql("""
                SELECT COUNT(*) 
                FROM paths_iter i
                JOIN paths_using_key k ON i.src = k.src AND i.dst = k.dst
                WHERE ABS(i.cost - k.cost) > 1e-6
            """).fetchone()[0]
            print(f"Cost Discrepancies: {diff_costs}")
            if diff_costs == 0:
                print("✓ Output is IDENTICAL and OPTIMAL.")
            else:
                print("⚠ USING KEY found potentially sub-optimal paths (expected for weighted graphs without specific ordering).")
        
        speedup = iter_time / key_time if key_time > 0 else 0
        print(f"Speedup Factor: {speedup:.2f}x")

    con.close()

if __name__ == "__main__":
    benchmark()
