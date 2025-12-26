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
logger = logging.getLogger("Compare_15_14")

def run_duckdb_comparison():
    logger.info("Starting DuckDB Comparison for Res 15 and 14")
    
    db_path = ":memory:"
    deactivated_table = "deactivated_shortcuts"
    elementary_table = "elementary_table"
    partition_res = 7 # We only process down to 14
    
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
    
    # Tables to collect results across all partitions
    processor.con.execute("CREATE TABLE all_res_15 (from_edge BIGINT, to_edge BIGINT, cost DOUBLE, via_edge BIGINT)")
    processor.con.execute("CREATE TABLE all_res_14 (from_edge BIGINT, to_edge BIGINT, cost DOUBLE, via_edge BIGINT)")

    for i, chunk_id in enumerate(chunk_ids, 1):
        # A. Load initial shortcuts for this chunk
        processor.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts AS
            SELECT *
            FROM {elementary_table}
            WHERE h3_parent(inner_cell, {partition_res}) = {chunk_id}
               OR h3_parent(outer_cell, {partition_res}) = {chunk_id}
        """)
        
        # B. Resolution 15
        processor.assign_cell_to_shortcuts(15, phase=1, direction="forward", input_table="shortcuts", single_assignment=False)
        # We need to capture what was generated at Res 15.
        # process_cell_forward modifies 'shortcuts' table.
        active, news, decs = processor.process_cell_forward("shortcuts")
        
        # Save generated shortcuts for this partition at Res 15
        # Note: 'shortcuts' now contains the state after Res 15
        processor.con.execute("INSERT INTO all_res_15 SELECT from_edge, to_edge, cost, via_edge FROM shortcuts")
        
        # C. Resolution 14
        processor.assign_cell_to_shortcuts(14, phase=1, direction="forward", input_table="shortcuts", single_assignment=False)
        active, news, decs = processor.process_cell_forward("shortcuts")
        
        # Save generated shortcuts for this partition at Res 14
        processor.con.execute("INSERT INTO all_res_14 SELECT from_edge, to_edge, cost, via_edge FROM shortcuts")
        
        if i % 10 == 0 or i == len(chunk_ids):
            logger.info(f"Processed {i}/{len(chunk_ids)} chunks")

    # Deduplicate global results
    logger.info("Deduplicating global results...")
    
    # Get counts
    def get_dedup_count(table_name):
        return processor.con.sql(f"""
            SELECT COUNT(*) FROM (
                SELECT from_edge, to_edge, MIN(cost) 
                FROM {table_name} 
                GROUP BY from_edge, to_edge
            )
        """).fetchone()[0]

    count_15 = get_dedup_count("all_res_15")
    count_14 = get_dedup_count("all_res_14")
    
    # Save DuckDB Res 14 results
    duck_output_path = "/home/kaveh/projects/road-to-shortcut-duckdb/output/duckdb_res14_debug.csv"
    processor.con.execute(f"""
        COPY (
            SELECT from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge
            FROM all_res_14
            GROUP BY from_edge, to_edge
        ) TO '{duck_output_path}' (HEADER, DELIMITER ',')
    """)
    logger.info(f"Saved DuckDB Res 14 to: {duck_output_path}")

    # Spark Hybrid Baseline (Hardcoded from previous run or extracted)
    spark_results = {
        15: 284725,
        14: 285057
    }
    
    logger.info("="*60)
    logger.info(f"{'RESOLUTION':<15} | {'DUCKDB':<12} | {'SPARK':<12} | {'DIFF':<10}")
    logger.info("-"*60)
    
    for res in [15, 14]:
        duck_val = count_15 if res == 15 else count_14
        spark_val = spark_results[res]
        diff = duck_val - spark_val
        logger.info(f"Res {res:<13} | {duck_val:<12} | {spark_val:<12} | {diff:<10}")
    
    logger.info("="*60)
    
    if count_15 == spark_results[15] and count_14 == spark_results[14]:
        logger.info("MATCH SUCCESS: DuckDB results match Spark results!")
    else:
        logger.warning("MATCH DISCREPANCY: DuckDB results differ from Spark results.")
    
    processor.close()

if __name__ == "__main__":
    run_duckdb_comparison()
