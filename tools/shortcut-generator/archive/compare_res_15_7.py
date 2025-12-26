import logging
import time
from pathlib import Path
import duckdb
import pandas as pd
import os

# Add src to path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

import config
import utilities as utils
from generate_shortcuts_partitioned import ShortcutProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] %(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("Compare_15_7")

def run_duckdb_comparison():
    logger.info("Starting DuckDB Comparison for Res 15 down to 7 (Total Pool Comparison)")
    
    db_path = ":memory:"
    deactivated_table = "deactivated_shortcuts"
    elementary_table = "elementary_table"
    partition_res = 7
    
    processor = ShortcutProcessor(db_path, deactivated_table, partition_res, elementary_table)
    
    edges_file = str(config.EDGES_FILE)
    graph_file = str(config.GRAPH_FILE)
    
    processor.load_shared_data(edges_file, graph_file)
    
    # 1. Identify chunks at partition_res
    processor.con.execute(f"""
        CREATE OR REPLACE TABLE chunks AS
        SELECT DISTINCT h3_parent(c, {partition_res}) as cell_id
        FROM (
            SELECT inner_cell as c FROM {elementary_table} WHERE inner_cell IS NOT NULL AND h3_resolution(inner_cell) >= {partition_res}
            UNION ALL
            SELECT outer_cell as c FROM {elementary_table} WHERE outer_cell IS NOT NULL AND h3_resolution(outer_cell) >= {partition_res}
        )
        WHERE c != 0
    """)
    chunk_ids = [r[0] for r in processor.con.execute("SELECT cell_id FROM chunks").fetchall()]
    logger.info(f"Processing {len(chunk_ids)} chunks at resolution {partition_res}...")
    
    # Tables to collect ALL shortcuts (active + deactivated) for each resolution
    for res in range(15, 6, -1):
        processor.con.execute(f"CREATE TABLE all_res_{res} (from_edge BIGINT, to_edge BIGINT, cost DOUBLE)")

    for i, chunk_id in enumerate(chunk_ids, 1):
        # A. Load initial shortcuts for this chunk
        processor.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts AS
            SELECT *
            FROM {elementary_table}
            WHERE h3_parent(inner_cell, {partition_res}) = {chunk_id}
               OR h3_parent(outer_cell, {partition_res}) = {chunk_id}
        """)
        
        # B. Iterative Pass 15 -> 7
        for res in range(15, 6, -1):
            processor.assign_cell_to_shortcuts(res, phase=1, direction="forward", input_table="shortcuts", single_assignment=False)
            
            # BEFORE running SP and deactivating, we need to know what's in the pool.
            # But wait, Spark builds NEW shortcuts. 
            # Spark flow: assign -> filter active -> compute SP (new) -> merge (old + new).
            # So the pool at resolution R is: (shortcuts from R+1) UNION (new shortcuts generated at R).
            
            # To match Spark exactly:
            # 1. Run SP on active ones
            processor.process_cell_forward("shortcuts")
            
            # 2. Now 'shortcuts' contains active ones, and 'deactivated_shortcuts' contains deactivated ones.
            # Combined, they represent the total pool for this chunk at this resolution.
            processor.con.execute(f"""
                INSERT INTO all_res_{res} 
                SELECT from_edge, to_edge, cost FROM shortcuts
                UNION ALL
                SELECT from_edge, to_edge, cost FROM {deactivated_table}
            """)
        
        # Clear deactivated table for next chunk to avoid double counting
        processor.con.execute(f"DELETE FROM {deactivated_table}")
        
        if i % 5 == 0 or i == len(chunk_ids):
            logger.info(f"Processed {i}/{len(chunk_ids)} chunks")

    # Deduplicate global results
    logger.info("Deduplicating global results...")
    
    duckdb_results = {}
    for res in range(15, 6, -1):
        count = processor.con.sql(f"""
            SELECT COUNT(*) FROM (
                SELECT from_edge, to_edge
                FROM all_res_{res}
                GROUP BY from_edge, to_edge
            )
        """).fetchone()[0]
        duckdb_results[res] = count
    
    # Spark results (Cumulative Pool)
    spark_results = {
        15: 284725,
        14: 285057,
        13: 287032,
        12: 301043,
        11: 370007,
        10: 629203,
        9: 1203111,
        8: 2141836,
        7: 3112640
    }
    
    logger.info("="*60)
    logger.info(f"{'RESOLUTION':<15} | {'DUCKDB':<12} | {'SPARK':<12} | {'DIFF':<10}")
    logger.info("-"*60)
    
    for res in range(15, 6, -1):
        duck_val = duckdb_results[res]
        spark_val = spark_results.get(res, 0)
        diff = duck_val - spark_val
        logger.info(f"Res {res:<13} | {duck_val:<12} | {spark_val:<12} | {diff:<10}")
    
    logger.info("="*60)
    
    processor.close()

if __name__ == "__main__":
    run_duckdb_comparison()
