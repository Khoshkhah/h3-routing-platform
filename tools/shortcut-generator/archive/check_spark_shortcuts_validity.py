import duckdb
import h3
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CheckValidity")

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

def main():
    con = duckdb.connect(':memory:')
    
    # Register UDFs
    con.create_function("h3_lca", _find_lca_impl, ["BIGINT", "BIGINT"], "BIGINT")
    con.create_function("h3_resolution", _find_resolution_impl, ["BIGINT"], "INTEGER")
    
    district = "Burnaby"
    edges_path = f"/home/kaveh/projects/osm-to-road/data/output/{district}/{district}_driving_simplified_edges_with_h3.csv"
    spark_output = f"/home/kaveh/projects/road-to-shortcut/output/{district}_spark_hybrid/*.parquet"
    
    logger.info("Loading edges...")
    con.execute(f"CREATE TABLE edges AS SELECT edge_index as id, from_cell, to_cell, lca_res FROM read_csv_auto('{edges_path}')")
    
    logger.info("Loading Spark shortcuts...")
    con.execute(f"CREATE TABLE spark_shortcuts AS SELECT * FROM read_parquet('{spark_output}')")
    
    logger.info("Calculating metadata and checking validity...")
    
    query = """
    WITH metadata AS (
        SELECT 
            s.from_edge,
            s.to_edge,
            e1.lca_res as lca_in,
            e2.lca_res as lca_out,
            GREATEST(e1.lca_res, e2.lca_res) as lca_res,
            h3_resolution(h3_lca(e1.to_cell, e2.from_cell)) as inner_res,
            h3_resolution(h3_lca(e1.from_cell, e2.to_cell)) as outer_res
        FROM spark_shortcuts s
        JOIN edges e1 ON s.from_edge = e1.id
        JOIN edges e2 ON s.to_edge = e2.id
    )
    SELECT 
        count(*) as total_count,
        count(*) FILTER (WHERE lca_res <= inner_res OR lca_res <= outer_res) as valid_count,
        count(*) FILTER (WHERE NOT (lca_res <= inner_res OR lca_res <= outer_res)) as invalid_count
    FROM metadata
    """
    
    result = con.execute(query).fetchone()
    total, valid, invalid = result
    
    logger.info(f"Total Shortcuts: {total:,}")
    logger.info(f"Valid Shortcuts: {valid:,}")
    logger.info(f"Invalid Shortcuts: {invalid:,}")
    
    if invalid > 0:
        logger.warning(f"Found {invalid} shortcuts that violate the condition!")
        logger.info("Example invalid shortcuts:")
        examples = con.execute("""
            WITH metadata AS (
                SELECT 
                    s.from_edge, s.to_edge,
                    e1.lca_res as lca_in, e2.lca_res as lca_out,
                    GREATEST(e1.lca_res, e2.lca_res) as lca_res,
                    h3_resolution(h3_lca(e1.to_cell, e2.from_cell)) as inner_res,
                    h3_resolution(h3_lca(e1.from_cell, e2.to_cell)) as outer_res
                FROM spark_shortcuts s
                JOIN edges e1 ON s.from_edge = e1.id
                JOIN edges e2 ON s.to_edge = e2.id
            )
            SELECT * FROM metadata 
            WHERE NOT (lca_res <= inner_res OR lca_res <= outer_res)
            LIMIT 5
        """).df()
        print(examples)
    else:
        logger.info("All Spark shortcuts satisfy the condition.")

if __name__ == "__main__":
    main()
