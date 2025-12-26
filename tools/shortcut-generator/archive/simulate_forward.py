import duckdb
import h3
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimulateForward")

def _find_lca_impl(cell1: int, cell2: int):
    if cell1 == 0 or cell2 == 0:
        return 0
    try:
        cell1_str = h3.int_to_str(cell1)
        cell2_str = h3.int_to_str(cell2)
        min_res = min(h3.get_resolution(cell1_str), h3.get_resolution(cell2_str))
        for res in range(min_res, -1, -1):
            p1 = h3.cell_to_parent(cell1_str, res)
            p2 = h3.cell_to_parent(cell2_str, res)
            if p1 == p2:
                return h3.str_to_int(p1)
    except:
        pass
    return 0

def _find_resolution_impl(cell: int):
    if cell == 0:
        return -1
    try:
        return h3.get_resolution(h3.int_to_str(cell))
    except:
        return -1

def _get_parent_impl(cell: int, res: int):
    if cell == 0 or res < 0:
        return 0
    try:
        return h3.str_to_int(h3.cell_to_parent(h3.int_to_str(cell), res))
    except:
        return 0

def main():
    con = duckdb.connect(':memory:')
    
    # Register UDFs
    con.create_function("h3_lca", _find_lca_impl, ["BIGINT", "BIGINT"], "BIGINT")
    con.create_function("h3_resolution", _find_resolution_impl, ["BIGINT"], "INTEGER")
    con.create_function("h3_parent", _get_parent_impl, ["BIGINT", "INTEGER"], "BIGINT")
    
    district = "Burnaby"
    edges_path = f"/home/kaveh/projects/osm-to-road/data/output/{district}/{district}_driving_simplified_edges_with_h3.csv"
    graph_path = f"/home/kaveh/projects/osm-to-road/data/output/{district}/{district}_driving_edge_graph.csv"
    spark_output = f"/home/kaveh/projects/road-to-shortcut/output/{district}_spark_hybrid/*.parquet"
    
    logger.info("Loading Data...")
    con.execute(f"CREATE TABLE edges AS SELECT edge_index as id, from_cell, to_cell, lca_res FROM read_csv_auto('{edges_path}')")
    con.execute(f"CREATE TABLE spark_target AS SELECT from_edge, to_edge, cost FROM read_parquet('{spark_output}')")
    
    # Pre-calculate metadata for edges to speed up cell assignment
    con.execute("CREATE TABLE edge_meta AS SELECT id, from_cell, to_cell, lca_res FROM edges")
    
    # Current shortcuts table: from_edge, to_edge, cost, birth_res
    # Initialize with elementary shortcuts
    logger.info("Initializing elementary shortcuts...")
    con.execute(f"""
        CREATE TABLE known_shortcuts AS
        SELECT 
            g.from_edge, 
            g.to_edge, 
            e.cost,
            15 as birth_res
        FROM read_csv_auto('{graph_path}') g
        JOIN (SELECT edge_index, length/maxspeed as cost FROM read_csv_auto('{edges_path}') WHERE maxspeed > 0) e 
          ON g.from_edge = e.edge_index
    """)
    
    # Track birth for all spark shortcuts
    con.execute("CREATE TABLE shortcut_birth (from_edge INT, to_edge INT, birth_res INT, cost DOUBLE)")
    
    # Insert initially known elementary ones that match Spark
    con.execute("""
        INSERT INTO shortcut_birth
        SELECT k.from_edge, k.to_edge, k.birth_res, k.cost
        FROM known_shortcuts k
        JOIN spark_target s ON k.from_edge = s.from_edge AND k.to_edge = s.to_edge
    """)
    
    # Forward Pass Simulation: 15 down to 1 (limiting for speed, focusing on finer grains)
    for res in range(15, 6, -1):
        logger.info(f"--- Processing Forward Resolution {res} ---")
        
        # 1. Assign cells to current known shortcuts
        # We simulate assign_cell_forward logic
        con.execute(f"""
            CREATE OR REPLACE TABLE active_shortcuts AS
            WITH meta AS (
                SELECT 
                    s.*,
                    e1.lca_res as lca_in,
                    e2.lca_res as lca_out,
                    GREATEST(e1.lca_res, e2.lca_res) as lca_res,
                    h3_resolution(h3_lca(e1.to_cell, e2.from_cell)) as inner_res,
                    h3_resolution(h3_lca(e1.from_cell, e2.to_cell)) as outer_res,
                    h3_lca(e1.to_cell, e2.from_cell) as inner_cell,
                    h3_lca(e1.from_cell, e2.to_cell) as outer_cell
                FROM known_shortcuts s
                JOIN edge_meta e1 ON s.from_edge = e1.id
                JOIN edge_meta e2 ON s.to_edge = e2.id
            ),
            assigned AS (
                SELECT from_edge, to_edge, cost, h3_parent(inner_cell, {res}) as cell
                FROM meta WHERE lca_res <= {res} AND inner_res >= {res}
                UNION ALL
                SELECT from_edge, to_edge, cost, h3_parent(outer_cell, {res}) as cell
                FROM meta WHERE lca_res <= {res} AND outer_res >= {res}
            )
            SELECT DISTINCT * FROM assigned
        """)
        
        # 2. Join to find new paths (Iterative Join - simulating many-to-many SP)
        # We do 3 iterations per resolution level to catch multi-hop paths
        for iteration in range(2):
            con.execute(f"""
                CREATE OR REPLACE TABLE new_paths AS
                SELECT 
                    L.from_edge, 
                    R.to_edge, 
                    L.cost + R.cost as cost,
                    L.cell
                FROM active_shortcuts L
                JOIN active_shortcuts R ON L.to_edge = R.from_edge AND L.cell = R.cell
                WHERE L.from_edge != R.to_edge
            """)
            
            # Update known_shortcuts and active_shortcuts with min cost
            con.execute("""
                CREATE OR REPLACE TABLE active_shortcuts AS
                SELECT from_edge, to_edge, MIN(cost) as cost, cell
                FROM (SELECT * FROM active_shortcuts UNION ALL SELECT * FROM new_paths)
                GROUP BY from_edge, to_edge, cell
            """)
            
            # Record births for shortcuts found in Spark results
            con.execute(f"""
                INSERT INTO shortcut_birth
                SELECT DISTINCT n.from_edge, n.to_edge, {res}, n.cost
                FROM new_paths n
                JOIN spark_target s ON n.from_edge = s.from_edge AND n.to_edge = s.to_edge
                LEFT JOIN shortcut_birth b ON n.from_edge = b.from_edge AND n.to_edge = b.to_edge
                WHERE b.from_edge IS NULL
            """)
            
            # Update main known_shortcuts
            con.execute("""
                CREATE OR REPLACE TABLE known_shortcuts AS
                SELECT from_edge, to_edge, MIN(cost) as cost
                FROM (SELECT from_edge, to_edge, cost FROM known_shortcuts UNION ALL SELECT from_edge, to_edge, cost FROM new_paths)
                GROUP BY from_edge, to_edge
            """)
            
            new_count = con.execute("SELECT count(*) FROM new_paths").fetchone()[0]
            logger.info(f"  Iteration {iteration}: found {new_count} paths")
            if new_count == 0: break

    logger.info("Forward simulation finished.")
    
    # Save the births
    birth_file = "/home/kaveh/projects/road-to-shortcut-duckdb/persist/spark_forward_births.parquet"
    con.execute(f"COPY shortcut_birth TO '{birth_file}' (FORMAT PARQUET)")
    
    # Final check on the missing shortcut
    logger.info("Checking birth for missing shortcut 23037 -> 23030...")
    res = con.execute("SELECT * FROM shortcut_birth WHERE from_edge = 23037 AND to_edge = 23030").df()
    if not res.empty:
        print("\n--- ACTUAL BIRTH INFO (SIMULATED FORWARD) ---")
        print(res.to_string())
    else:
        print("\nShortcut 23037 -> 23030 was not born in the Res 15-7 Forward simulation range.")

if __name__ == "__main__":
    main()
