import duckdb
import time
from pathlib import Path

def run_prototype():
    con = duckdb.connect()
    
    print("--- DuckPGQ Prototype ---")
    
    # 1. Install and Load DuckPGQ
    try:
        con.execute("INSTALL duckpgq FROM community; LOAD duckpgq;")
        print("✓ DuckPGQ Loaded")
    except Exception as e:
        print(f"✗ Failed to load DuckPGQ: {e}")
        return

    # 2. Setup Data (Small subset for Burnaby)
    DISTRICT = "Burnaby"
    edges_file = f"/home/kaveh/projects/osm-to-road/data/output/{DISTRICT}/{DISTRICT}_driving_simplified_edges_with_h3.csv"
    graph_file = f"/home/kaveh/projects/osm-to-road/data/output/{DISTRICT}/{DISTRICT}_driving_edge_graph.csv"

    print(f"Loading subset of {DISTRICT} data...")
    # Use 2000 edges and their connections
    con.execute(f"CREATE TABLE edges_raw AS SELECT * FROM read_csv_auto('{edges_file}') LIMIT 2000")
    con.execute(f"CREATE TABLE graph_raw AS SELECT * FROM read_csv_auto('{graph_file}')")

    # vertices for property graph
    con.execute("CREATE TABLE nodes (n_id BIGINT PRIMARY KEY)")
    con.execute("INSERT INTO nodes SELECT DISTINCT edge_index FROM edges_raw")

    # filter graph to only include available nodes
    con.execute("""
        CREATE TABLE graph_filtered AS
        SELECT g.from_edge, g.to_edge, e.cost as weight
        FROM graph_raw g
        JOIN nodes n1 ON g.from_edge = n1.n_id
        JOIN nodes n2 ON g.to_edge = n2.n_id
        JOIN edges_raw e ON g.from_edge = e.edge_index
    """)

    # 3. Create Property Graph with Syntax 1 (Verified)
    print("Defining Property Graph...")
    con.execute("""
        CREATE PROPERTY GRAPH road_graph
        VERTEX TABLES (nodes)
        EDGE TABLES (graph_filtered 
            SOURCE KEY (from_edge) REFERENCES nodes(n_id)
            DESTINATION KEY (to_edge) REFERENCES nodes(n_id)
            LABEL linked
        )
    """)

    # 4. Run All-Pairs Shortest Path (Weighted)
    print("Computing Weighted Shortest Paths via DuckPGQ...")
    start = time.time()
    
    try:
        # Match pattern for weighted shortest paths
        con.execute("""
            CREATE TABLE shortcuts_pgq AS
            FROM GRAPH_TABLE (road_graph
                MATCH ANY SHORTEST (a)-[e:linked* COST weight]->(b)
                COLUMNS (a.n_id AS from_edge, b.n_id AS to_edge, COST AS total_cost)
            )
        """)
        elapsed = time.time() - start
        count = con.sql("SELECT COUNT(*) FROM shortcuts_pgq").fetchone()[0]
        print(f"✓ DuckPGQ found {count} shortcuts in {elapsed:.4f}s")
    except Exception as e:
        print(f"✗ DuckPGQ Error: {e}")

    # 5. Iterative SQL Comparison
    print("\nComputing All-Pairs Shortest Paths via Iterative SQL...")
    con.execute("CREATE TABLE shortcuts_sql AS SELECT from_edge, to_edge, weight as cost FROM graph_filtered")
    
    start_sql = time.time()
    for i in range(5):
        print(f"  Iteration {i+1}...")
        con.execute(f"""
            CREATE TABLE shortcuts_sql_next AS
            SELECT from_edge, to_edge, MIN(cost) as cost
            FROM (
                SELECT from_edge, to_edge, cost FROM shortcuts_sql
                UNION ALL
                SELECT L.from_edge, R.to_edge, L.cost + R.cost
                FROM shortcuts_sql L
                JOIN shortcuts_sql R ON L.to_edge = R.from_edge
                WHERE L.from_edge != R.to_edge
            )
            GROUP BY 1, 2
        """)
        con.execute("DROP TABLE shortcuts_sql")
        con.execute("ALTER TABLE shortcuts_sql_next RENAME TO shortcuts_sql")
    
    elapsed_sql = time.time() - start_sql
    count_sql = con.sql("SELECT COUNT(*) FROM shortcuts_sql").fetchone()[0]
    print(f"✓ Iterative SQL found {count_sql} shortcuts in {elapsed_sql:.4f}s")

    con.close()

if __name__ == "__main__":
    run_prototype()
