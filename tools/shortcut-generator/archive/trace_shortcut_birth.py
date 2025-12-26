import duckdb
import h3
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TraceShortcut")

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
    spark_output = f"/home/kaveh/projects/road-to-shortcut/output/{district}_spark_hybrid/*.parquet"
    duckdb_output = f"/home/kaveh/projects/road-to-shortcut-duckdb/output/{district}_shortcuts"
    
    persist_dir = Path("/home/kaveh/projects/road-to-shortcut-duckdb/persist")
    persist_dir.mkdir(exist_ok=True)
    trace_output = persist_dir / "spark_birth_trace.parquet"
    
    logger.info("Loading Spark data...")
    con.execute(f"CREATE TABLE edges AS SELECT edge_index as id, from_cell, to_cell, lca_res FROM read_csv_auto('{edges_path}')")
    con.execute(f"CREATE TABLE spark_shortcuts AS SELECT * FROM read_parquet('{spark_output}')")
    
    logger.info("Reconstructing birth metadata...")
    
    con.execute("""
    CREATE TABLE traced AS
    WITH base AS (
        SELECT 
            s.from_edge, s.to_edge, s.cost, s.via_edge,
            e1.lca_res as lca_in,
            e2.lca_res as lca_out,
            GREATEST(e1.lca_res, e2.lca_res) as lca_res,
            h3_lca(e1.to_cell, e2.from_cell) as inner_cell,
            h3_lca(e1.from_cell, e2.to_cell) as outer_cell,
            h3_resolution(h3_lca(e1.to_cell, e2.from_cell)) as inner_res,
            h3_resolution(h3_lca(e1.from_cell, e2.to_cell)) as outer_res
        FROM spark_shortcuts s
        JOIN edges e1 ON s.from_edge = e1.id
        JOIN edges e2 ON s.to_edge = e2.id
    ),
    birth_logic AS (
        SELECT 
            *,
            GREATEST(inner_res, outer_res) as birth_res,
            CASE 
                WHEN inner_res >= outer_res THEN inner_cell
                ELSE outer_cell
            END as birth_cell_id
        FROM base
    )
    SELECT 
        from_edge, to_edge, cost, via_edge,
        birth_res,
        birth_cell_id,
        CASE 
            WHEN birth_res >= 0 THEN 'Forward'
            ELSE 'Backward/Global'
        END as phase,
        lca_res, inner_res, outer_res
    FROM birth_logic
    """)
    
    logger.info(f"Saving trace to {trace_output}...")
    con.execute(f"COPY traced TO '{trace_output}' (FORMAT PARQUET)")
    
    logger.info("Loading DuckDB Partitioned data for comparison...")
    con.execute(f"CREATE TABLE duck_shortcuts AS SELECT * FROM read_parquet('{duckdb_output}')")
    
    logger.info("Finding missing shortcuts in DuckDB with max resolution...")
    
    # We want: 
    # 1. In Spark but NOT in DuckDB
    # 2. Phase = 'Forward'
    # 3. Max birth_res
    
    query = """
    WITH missing AS (
        SELECT s.*
        FROM traced s
        LEFT JOIN duck_shortcuts d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
        WHERE d.from_edge IS NULL AND s.phase = 'Forward'
    )
    SELECT * 
    FROM missing 
    ORDER BY birth_res DESC, cost ASC
    LIMIT 1
    """
    
    result = con.execute(query).df()
    
    if not result.empty:
        print("\n--- FOUND MISSING SHORTCUT ---")
        print(result.to_string())
        
        # Explain why it might be missing
        missing_row = result.iloc[0]
        print(f"\nAnalysis:")
        print(f"This shortcut (from={missing_row['from_edge']}, to={missing_row['to_edge']})")
        print(f"was born at resolution {missing_row['birth_res']} in the Forward phase.")
        print(f"Its lca_res is {missing_row['lca_res']}, while its junction (inner_res) is {missing_row['inner_res']}.")
    else:
        print("No missing shortcuts found in the Forward phase!")

if __name__ == "__main__":
    main()
