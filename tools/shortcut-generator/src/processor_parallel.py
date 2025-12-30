"""
Parallel Shortcut Generation using DuckDB with multiprocessing.

This is an optimized version of processor.py that uses
parallel processing for Phase 1 and Phase 4 where chunks are independent.
"""
import logging
import time
import gc
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import duckdb
import h3
import pandas as pd
import os
import resource

def log_memory(logger_instance, stage: str):
    """Log current memory usage."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux returns maxrss in KB
    mb = usage / 1024
    logger_instance.info(f"[MEMORY] {stage}: {mb:.2f} MB")


import utilities as utils
from sp_methods.pure import compute_shortest_paths_pure_duckdb
from sp_methods.scipy import process_partition_scipy

import logging_config as log_conf
import config

logger = logging.getLogger(__name__)

PARTITION_RES = 7
SP_METHOD = "SCIPY"
MAX_WORKERS = min(4, cpu_count())  # Limit parallelism to avoid memory issues


def process_chunk_phase1(args):
    """
    Worker function for Phase 1 parallel processing.
    Reads data from Parquet files, processes in in-memory DuckDB.
    Writes results to Parquet files to avoid large DataFrame IPC.
    Returns: (chunk_id, active_path, deactivated_path, active_count, timing_info, duration)
    """
    chunk_id, shortcuts_parquet_path, edges_parquet_path, temp_dir, partition_res, sp_method, hybrid_res = args
    
    timing_info = []  # List of (res, method, time)
    start_time = time.time()
    active_path = f"{temp_dir}/phase1_active_{chunk_id}.parquet"
    deactivated_path = f"{temp_dir}/phase1_deactivated_{chunk_id}.parquet"
    
    try:
        # Worker uses in-memory DuckDB
        con = duckdb.connect(":memory:")
        
        # Register H3 UDFs
        con.create_function("h3_lca", utils._find_lca_impl, ["BIGINT", "BIGINT"], "BIGINT")
        con.create_function("h3_resolution", utils._find_resolution_impl, ["BIGINT"], "INTEGER")
        con.create_function("h3_parent", utils._get_parent_cell_impl, ["BIGINT", "INTEGER"], "BIGINT")
        
        # Load data from Parquet files
        con.execute(f"CREATE TABLE edges AS SELECT * FROM '{edges_parquet_path}'")
        con.execute(f"CREATE TABLE shortcuts AS SELECT * FROM '{shortcuts_parquet_path}'")
        
        initial_count = con.execute("SELECT count(*) FROM shortcuts").fetchone()[0]
        if initial_count == 0:
            con.close()
            return (chunk_id, None, None, 0, [], time.time() - start_time)
        
        # Create table to collect deactivated shortcuts
        con.execute("""
            CREATE TABLE deactivated (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, 
                inner_res TINYINT, outer_res TINYINT
            )
        """)
        
        for res in range(15, partition_res - 1, -1):
            res_start = time.time()
            
            _assign_cell_to_shortcuts_worker(con, res, "shortcuts")
            
            # Expand from current_cell_in/out to current_cell
            con.execute("""
                CREATE OR REPLACE TABLE shortcuts_expanded AS
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res, current_cell_in AS current_cell
                FROM shortcuts
                WHERE current_cell_in IS NOT NULL
                UNION
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res, current_cell_out AS current_cell
                FROM shortcuts
                WHERE current_cell_out IS NOT NULL 
                  AND (current_cell_in IS NULL OR current_cell_out != current_cell_in)
                UNION ALL
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res, NULL AS current_cell
                FROM shortcuts
                WHERE current_cell_in IS NULL AND current_cell_out IS NULL
            """)
            
            # Collect deactivated shortcuts
            con.execute("""
                INSERT INTO deactivated
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
                FROM shortcuts_expanded WHERE current_cell IS NULL
            """)
            
            # Keep only active shortcuts
            con.execute("CREATE OR REPLACE TABLE shortcuts AS SELECT * FROM shortcuts_expanded WHERE current_cell IS NOT NULL")
            con.execute("DROP TABLE IF EXISTS shortcuts_expanded")
            
            active_count = con.execute("SELECT count(*) FROM shortcuts").fetchone()[0]
            if active_count == 0:
                break
            
            # Determine method
            if sp_method == "HYBRID":
                method = "PURE" if res >= hybrid_res else "SCIPY"
            else:
                method = sp_method
            
            # Run SP
            _run_shortest_paths_worker(con, "shortcuts", method=method)
            
            res_time = time.time() - res_start
            timing_info.append((res, method, res_time))
        
        # Write results to Parquet files
        active_count = con.execute("SELECT count(*) FROM shortcuts").fetchone()[0]
        deactivated_count = con.execute("SELECT count(*) FROM deactivated").fetchone()[0]
        
        if active_count > 0:
            con.execute(f"COPY shortcuts TO '{active_path}' (FORMAT PARQUET)")
        else:
            active_path = None
            
        if deactivated_count > 0:
            con.execute(f"COPY deactivated TO '{deactivated_path}' (FORMAT PARQUET)")
        else:
            deactivated_path = None
        
        con.close()
        return (chunk_id, active_path, deactivated_path, active_count, timing_info, time.time() - start_time)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (chunk_id, None, None, 0, [], time.time() - start_time)




def process_chunk_phase4(args):
    """
    Worker function for Phase 4 parallel processing.
    Reads data from Parquet files, processes in in-memory DuckDB.
    Writes results to Parquet file to avoid large DataFrame IPC.
    Returns: (cell_id, result_path, count, timing_info, duration)
    """
    cell_id, cell_parquet_path, edges_parquet_path, temp_dir, partition_res, sp_method, hybrid_res = args
    
    timing_info = []  # List of (res, method, time)
    start_time = time.time()
    result_path = f"{temp_dir}/phase4_result_{cell_id}.parquet"
    
    try:
        # Worker uses disk-backed DuckDB (spills to disk, manages memory)
        worker_db_path = f"{temp_dir}/worker_{cell_id}.db"
        con = duckdb.connect(worker_db_path)
        
        # Register H3 UDFs
        con.create_function("h3_lca", utils._find_lca_impl, ["BIGINT", "BIGINT"], "BIGINT")
        con.create_function("h3_resolution", utils._find_resolution_impl, ["BIGINT"], "INTEGER")
        con.create_function("h3_parent", utils._get_parent_cell_impl, ["BIGINT", "INTEGER"], "BIGINT")
        
        # Use a VIEW for cell data to stream from Parquet instead of loading everything
        # This prevents the initial memory/disk spike of materializing the table
        con.execute(f"CREATE VIEW cell_data AS SELECT * FROM '{cell_parquet_path}'")
        
        # We still materialize edges (filtered) as they are accessed repeatedly in JOINs
        # and are relatively small (~50-100K)
        con.execute(f"""
            CREATE TABLE edges AS 
            SELECT * FROM '{edges_parquet_path}'
            WHERE id IN (
                SELECT DISTINCT from_edge FROM cell_data
                UNION
                SELECT DISTINCT to_edge FROM cell_data
            )
        """)
        
        initial_count = con.execute("SELECT count(*) FROM cell_data").fetchone()[0]
        if initial_count == 0:
            con.close()
            return (cell_id, None, 0, [], time.time() - start_time)
        
        # Create table to collect deactivated shortcuts
        con.execute("""
            CREATE TABLE deactivated (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, 
                inner_res TINYINT, outer_res TINYINT
            )
        """)
        
        # Iterative backward loop: partition_res -> 15
        for res in range(partition_res, 16):
            # First: Deactivate shortcuts where res > max(inner_res, outer_res)
            con.execute(f"""
                INSERT INTO deactivated
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res
                FROM cell_data
                WHERE {res} > GREATEST(inner_res, outer_res)
            """)
            
            # Keep only shortcuts that can still be refined
            # We use a temp table + rename because cell_data starts as a VIEW, 
            # and DuckDB's CREATE OR REPLACE TABLE doesn't replace VIEWs.
            con.execute(f"""
                CREATE TABLE cell_data_next AS
                SELECT * FROM cell_data
                WHERE {res} <= GREATEST(inner_res, outer_res)
            """)
            
            # Robust drop: Check type from information_schema to avoid Catalog Errors
            res_type = con.execute("SELECT table_type FROM information_schema.tables WHERE table_name = 'cell_data'").fetchone()
            if res_type:
                if res_type[0] == 'VIEW':
                    con.execute("DROP VIEW cell_data")
                else:
                    con.execute("DROP TABLE cell_data")
                    
            con.execute("ALTER TABLE cell_data_next RENAME TO cell_data")
            
            remaining = con.execute("SELECT count(*) FROM cell_data").fetchone()[0]
            if remaining == 0:
                break
            
            # Then: Assign cells and process
            _assign_cell_to_shortcuts_worker(con, res, "cell_data")
            
            # Determine method for this resolution
            if sp_method == "HYBRID":
                method = "PURE" if res >= hybrid_res else "SCIPY"
            else:
                method = sp_method
            
            # Run SP using _process_cell_backward_worker
            res_start = time.time()
            active_count, total_count = _process_cell_backward_worker(con, "cell_data", method=method)
            if active_count > 0:
                timing_info.append((res, method, time.time() - res_start))
        
        # Add any remaining shortcuts to deactivated (at res 15)
        con.execute("""
            INSERT INTO deactivated
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                   inner_res, outer_res
            FROM cell_data
        """)
        
        # Get final count and write to Parquet (avoids large DataFrame IPC)
        final_count = con.execute("SELECT count(*) FROM deactivated").fetchone()[0]
        
        if final_count > 0:
            con.execute(f"COPY deactivated TO '{result_path}' (FORMAT PARQUET)")
        else:
            result_path = None
        
        con.close()
        # Cleanup worker DB file
        Path(worker_db_path).unlink(missing_ok=True)
        return (cell_id, result_path, final_count, timing_info, time.time() - start_time)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Cleanup on error
        if 'worker_db_path' in locals():
            Path(worker_db_path).unlink(missing_ok=True)
        return (cell_id, None, 0, [], time.time() - start_time)


def _assign_cell_to_shortcuts_worker(con, res: int, input_table: str):
    """
    Worker version of assign_cell_to_shortcuts.
    Adds current_cell_in and current_cell_out columns instead of creating UNION.
    """
    con.execute(f"DROP TABLE IF EXISTS {input_table}_tmp")
    
    if res == -1:
        # Global level: all shortcuts belong to cell 0
        con.execute(f"""
            CREATE TABLE {input_table}_tmp AS
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                   inner_res, outer_res, 
                   0::BIGINT AS current_cell_in, 
                   0::BIGINT AS current_cell_out
            FROM {input_table}
        """)
    else:
        # Compute parent cells for inner and outer, store as separate columns
        con.execute(f"""
            CREATE TABLE {input_table}_tmp AS
            SELECT 
                from_edge, to_edge, cost, via_edge, lca_res, 
                inner_cell, outer_cell, inner_res, outer_res,
                CASE WHEN lca_res <= {res} AND inner_res >= {res} 
                     THEN h3_parent(inner_cell::BIGINT, {res}) 
                     ELSE NULL END AS current_cell_in,
                CASE WHEN lca_res <= {res} AND outer_res >= {res} 
                     THEN h3_parent(outer_cell::BIGINT, {res}) 
                     ELSE NULL END AS current_cell_out
            FROM {input_table}
        """)
    
    con.execute(f"DROP TABLE {input_table}")
    con.execute(f"ALTER TABLE {input_table}_tmp RENAME TO {input_table}")




def _process_cell_forward_worker(con, table_name: str, method: str = "SCIPY", num_workers: int = 1):
    """
    Worker version of process_cell_forward.
    Expands from current_cell_in/out to current_cell, 
    splits active (SP) and inactive (deactivated), 
    returns counts and ensures result is back in table_name.
    """
    # Step 1: Expand
    con.execute(f"DROP TABLE IF EXISTS {table_name}_expanded")
    con.execute(f"""
        CREATE TABLE {table_name}_expanded AS
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
               inner_res, outer_res, current_cell_in AS current_cell
        FROM {table_name}
        WHERE current_cell_in IS NOT NULL
        UNION
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
               inner_res, outer_res, current_cell_out AS current_cell
        FROM {table_name}
        WHERE current_cell_out IS NOT NULL 
          AND (current_cell_in IS NULL OR current_cell_out != current_cell_in)
        UNION ALL
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
               inner_res, outer_res, NULL AS current_cell
        FROM {table_name}
        WHERE current_cell_in IS NULL AND current_cell_out IS NULL
    """)
    
    # Step 2: Separate
    con.execute(f"DROP TABLE IF EXISTS shortcuts_to_process")
    con.execute(f"CREATE TEMPORARY TABLE shortcuts_to_process AS SELECT * FROM {table_name}_expanded WHERE current_cell IS NOT NULL")
    
    con.execute(f"DROP TABLE IF EXISTS deactivated")
    con.execute(f"""
        CREATE TABLE deactivated AS
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
        FROM {table_name}_expanded WHERE current_cell IS NULL
    """)
    
    active_count = con.execute("SELECT count(*) FROM shortcuts_to_process").fetchone()[0]
    deactivated_count = con.execute("SELECT count(*) FROM deactivated").fetchone()[0]
    
    new_count = 0
    if active_count > 0:
        _run_shortest_paths_worker(con, "shortcuts_to_process", method=method, num_workers=num_workers)
        con.execute(f"DROP TABLE {table_name}")
        con.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
            FROM shortcuts_to_process
        """)
        new_count = con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
    else:
        con.execute(f"DROP TABLE {table_name}")
        con.execute(f"""
            CREATE TABLE {table_name} (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, 
                inner_res TINYINT, outer_res TINYINT
            )
        """)
    
    con.execute("DROP TABLE IF EXISTS shortcuts_to_process")
    con.execute(f"DROP TABLE IF EXISTS {table_name}_expanded")
    
    return active_count, new_count, deactivated_count


def process_chunk_phase2(args):
    """
    Worker function for Phase 2 parallel processing.
    """
    parent_id, edges_df, shortcuts_df, target_res, sp_method, hybrid_res = args
    
    con = duckdb.connect(":memory:")
    con.create_function("h3_lca", utils._find_lca_impl, ["BIGINT", "BIGINT"], "BIGINT")
    con.create_function("h3_resolution", utils._find_resolution_impl, ["BIGINT"], "INTEGER")
    con.create_function("h3_parent", utils._get_parent_cell_impl, ["BIGINT", "INTEGER"], "BIGINT")
    
    start_time = time.time()
    
    try:
        con.execute("CREATE TABLE edges AS SELECT * FROM edges_df")
        con.execute("CREATE TABLE shortcuts AS SELECT * FROM shortcuts_df")
        
        # Merge and Deduplicate
        con.execute("""
            CREATE OR REPLACE TABLE shortcuts_merged AS
            SELECT 
                from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge,
                FIRST(lca_res) as lca_res, FIRST(inner_cell) as inner_cell, FIRST(outer_cell) as outer_cell,
                FIRST(inner_res) as inner_res, FIRST(outer_res) as outer_res
            FROM shortcuts
            GROUP BY from_edge, to_edge
        """)
        
        merged_count = con.execute("SELECT count(*) FROM shortcuts_merged").fetchone()[0]
        
        # Assign cells
        _assign_cell_to_shortcuts_worker(con, target_res, "shortcuts_merged")
        
        # Process cell (Forward)
        active, news, decs = _process_cell_forward_worker(con, "shortcuts_merged", method=sp_method)
        
        result_df = con.execute("SELECT * FROM shortcuts_merged").df()
        deactivated_df = con.execute("SELECT * FROM deactivated").df()
        
        return (parent_id, result_df, deactivated_df, merged_count, active, news, decs, time.time() - start_time)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (parent_id, None, None, 0, 0, 0, 0, time.time() - start_time)
    finally:
        con.close()


def _process_cell_backward_worker(con, table_name: str, method: str = "SCIPY", num_workers: int = 1):
    """
    Worker version of process_cell_backward.
    Expands current_cell_in/out to single current_cell, then splits active/inactive, 
    runs SP only on active, merges back.
    """
    # Step 1: Expand from current_cell_in/out to current_cell
    con.execute(f"DROP TABLE IF EXISTS {table_name}_expanded")
    con.execute(f"""
        CREATE TABLE {table_name}_expanded AS
        -- Inner cell (always include if not null)
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
               inner_res, outer_res, current_cell_in AS current_cell
        FROM {table_name}
        WHERE current_cell_in IS NOT NULL
        UNION
        -- Outer cell (only if different from inner)
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
               inner_res, outer_res, current_cell_out AS current_cell
        FROM {table_name}
        WHERE current_cell_out IS NOT NULL 
          AND (current_cell_in IS NULL OR current_cell_out != current_cell_in)
        UNION ALL
        -- Inactive (both NULL)
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
               inner_res, outer_res, NULL AS current_cell
        FROM {table_name}
        WHERE current_cell_in IS NULL AND current_cell_out IS NULL
    """)
    
    # Step 2: Split active vs inactive
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts_active AS
        SELECT * FROM {table_name}_expanded WHERE current_cell IS NOT NULL
    """)
    con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts_inactive AS
        SELECT * FROM {table_name}_expanded WHERE current_cell IS NULL
    """)
    
    active_count = con.execute("SELECT count(*) FROM shortcuts_active").fetchone()[0]
    
    if active_count > 0:
        _run_shortest_paths_worker(con, "shortcuts_active", method=method, num_workers=num_workers)
    
    # Merge active + inactive back into original table (without current_cell)
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    con.execute(f"DROP TABLE IF EXISTS {table_name}_expanded")
    con.execute(f"""
        CREATE TABLE {table_name} AS
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
        FROM shortcuts_active
        UNION ALL
        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
        FROM shortcuts_inactive
    """)
    
    total_count = con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
    
    # Cleanup
    con.execute("DROP TABLE IF EXISTS shortcuts_active")
    con.execute("DROP TABLE IF EXISTS shortcuts_inactive")
    
    return active_count, total_count


def _run_shortest_paths_worker(con, input_table: str, method: str = "SCIPY", num_workers: int = 1):
    """Worker version of run_shortest_paths. Supports SCIPY and PURE methods."""
    con.execute("DROP TABLE IF EXISTS sp_input")
    con.execute(f"""
        CREATE TEMPORARY TABLE sp_input AS 
        SELECT from_edge, to_edge, cost, via_edge, current_cell::BIGINT as current_cell 
        FROM {input_table}
    """)
    
    if method == "PURE":
        # Use pure DuckDB approach
        from sp_methods.pure import compute_shortest_paths_pure_duckdb
        compute_shortest_paths_pure_duckdb(con, quiet=True, input_table="sp_input")
        con.execute("CREATE OR REPLACE TABLE shortcuts_next AS SELECT * FROM sp_input")
        con.execute("ALTER TABLE shortcuts_next DROP COLUMN current_cell")
    else:
        # BATCHED SCIPY: Process cells one at a time to avoid loading all data into RAM
        cells = [r[0] for r in con.execute("SELECT DISTINCT current_cell FROM sp_input WHERE current_cell IS NOT NULL").fetchall()]
        
        # Create empty result table
        con.execute("""
            CREATE OR REPLACE TABLE shortcuts_next (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER
            )
        """)
        
        # Process each cell separately
        for cell in cells:
            cell_df = con.execute(f"SELECT * FROM sp_input WHERE current_cell = {cell}").df()
            
            if len(cell_df) > 0:
                processed = process_partition_scipy(cell_df)
                if not processed.empty:
                    con.execute("INSERT INTO shortcuts_next SELECT from_edge, to_edge, cost, via_edge FROM processed")
            
            del cell_df
        
        # Final deduplication across all cells
        con.execute("""
            CREATE OR REPLACE TABLE shortcuts_next AS
            SELECT from_edge, to_edge, MIN(cost) as cost, 
                   arg_min(via_edge, cost) as via_edge
            FROM shortcuts_next
            GROUP BY from_edge, to_edge
        """)
    
    # Re-enrich
    table_exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'shortcuts_next'").fetchone()[0] > 0
    if table_exists:
        con.execute("""
            CREATE OR REPLACE TABLE shortcuts_next_enriched AS
            SELECT 
                s.from_edge, s.to_edge, s.cost, s.via_edge,
                GREATEST(e1.lca_res, e2.lca_res) as lca_res,
                h3_lca(e1.to_cell, e2.from_cell)::BIGINT as inner_cell,
                h3_lca(e1.from_cell, e2.to_cell)::BIGINT as outer_cell,
                h3_resolution(h3_lca(e1.to_cell, e2.from_cell))::TINYINT as inner_res,
                h3_resolution(h3_lca(e1.from_cell, e2.to_cell))::TINYINT as outer_res
            FROM shortcuts_next s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        """)
        con.execute("DROP TABLE shortcuts_next")
        con.execute("ALTER TABLE shortcuts_next_enriched RENAME TO shortcuts_next")
    else:
        # Fallback empty table
        con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts_next AS 
            SELECT from_edge, to_edge, cost, via_edge, 
                   0 as lca_res, 0::BIGINT as inner_cell, 0::BIGINT as outer_cell, 
                   0::TINYINT as inner_res, 0::TINYINT as outer_res
            FROM {input_table} WHERE 1=0
        """)
    
    con.execute(f"DROP TABLE IF EXISTS {input_table}")
    con.execute(f"ALTER TABLE shortcuts_next RENAME TO {input_table}")
    con.execute("DROP TABLE IF EXISTS sp_input")


class ParallelShortcutProcessor:
    """Parallel version of ShortcutProcessor with multiprocessing for Phase 1 and 4."""
    
    def __init__(self, db_path: str, forward_deactivated_table: str, backward_deactivated_table: str, 
                 partition_res: int = 7, elementary_table: str = "elementary_table",
                 sp_method: str = "HYBRID", hybrid_res: int = 10, worker_config: dict = None):
        self.db_path = db_path
        self.con = utils.initialize_duckdb(db_path)
        self.forward_deactivated_table = forward_deactivated_table
        self.backward_deactivated_table = backward_deactivated_table
        self.partition_res = partition_res
        self.elementary_table = elementary_table
        self.sp_method = sp_method
        self.hybrid_res = hybrid_res
        self.current_cells = []
        
        # Setup worker configuration
        if worker_config:
            self.workers = worker_config
        else:
            # Fallback to current global settings
            self.workers = {
                'phase1': MAX_WORKERS,
                'phase4': MAX_WORKERS
            }
        
        # Ensure tables exist
        self.con.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.forward_deactivated_table} (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, 
                inner_res TINYINT, outer_res TINYINT
            )
        """)
        self.con.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.backward_deactivated_table} (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, 
                inner_res TINYINT, outer_res TINYINT
            )
        """)

    def load_shared_data(self, edges_file: str, graph_file: str):
        """Loads edges and initial shortcuts into the database."""
        if self.con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'edges'").fetchone()[0] > 0:
            logger.info("Shared data already loaded, skipping.")
            return
            
        logger.info("Loading shared data...")
        utils.read_edges(self.con, edges_file)
        utils.create_edges_cost_table(self.con, edges_file)
        utils.initial_shortcuts_table(self.con, graph_file)
        
        # Log initial statistics
        edge_count = self.con.execute("SELECT count(*) FROM edges").fetchone()[0]
        node_count = self.con.execute("""
            SELECT count(DISTINCT id) FROM (
                SELECT from_cell as id FROM edges
                UNION
                SELECT to_cell as id FROM edges
            )
        """).fetchone()[0]
        elementary_count = self.con.execute("SELECT count(*) FROM shortcuts").fetchone()[0]
        
        logger.info(f"Statistics:")
        logger.info(f"  Nodes: {node_count:,}")
        logger.info(f"  Edges: {edge_count:,}")
        logger.info(f"  Initial Shortcuts: {elementary_count:,}")
        
        logger.info("Pre-calculating H3 metadata...")
        self.con.execute(f"""
            CREATE TABLE {self.elementary_table} AS
            SELECT 
                s.from_edge, s.to_edge, s.cost, s.via_edge,
                GREATEST(e1.lca_res, e2.lca_res) AS lca_res,
                h3_lca(e1.to_cell::BIGINT, e2.from_cell::BIGINT)::BIGINT AS inner_cell,
                h3_lca(e1.from_cell::BIGINT, e2.to_cell::BIGINT)::BIGINT AS outer_cell,
                h3_resolution(h3_lca(e1.to_cell::BIGINT, e2.from_cell::BIGINT))::TINYINT AS inner_res,
                h3_resolution(h3_lca(e1.from_cell::BIGINT, e2.to_cell::BIGINT))::TINYINT AS outer_res,
                CAST(NULL AS BIGINT) AS current_cell
            FROM shortcuts s
            LEFT JOIN edges e1 ON s.from_edge = e1.id
            LEFT JOIN edges e2 ON s.to_edge = e2.id
        """)
        self.con.execute("DROP TABLE shortcuts")

    def process_forward_phase1_parallel(self):
        """
        PARALLEL Phase 1: Process chunks concurrently using multiprocessing.
        Workers read from Parquet files, write results to Parquet.
        No DataFrame IPC - all data exchange via disk files.
        """
        log_conf.log_section(logger, f"PHASE 1: PARALLEL FORWARD (15 -> {self.partition_res})")
        
        # Create temp directory for Parquet files
        temp_dir = Path(self.db_path).parent / "phase1_temp"
        temp_dir.mkdir(exist_ok=True)
        
        log_memory(logger, "Phase 1: Starting")
        
        # Export edges to Parquet (shared by all workers)
        edges_parquet_path = str(temp_dir / "edges.parquet")
        self.con.execute(f"COPY edges TO '{edges_parquet_path}' (FORMAT PARQUET)")
        log_memory(logger, "Phase 1: Edges exported to Parquet")
        
        # Identify chunks via SQL
        self.con.execute(f"""
            CREATE OR REPLACE TABLE chunks AS
            SELECT DISTINCT h3_parent(c, {self.partition_res}) as cell_id
            FROM (
                SELECT inner_cell as c FROM {self.elementary_table} WHERE inner_cell IS NOT NULL AND h3_resolution(inner_cell) >= {self.partition_res}
                UNION ALL
                SELECT outer_cell as c FROM {self.elementary_table} WHERE outer_cell IS NOT NULL AND h3_resolution(outer_cell) >= {self.partition_res}
            )
            WHERE c != 0
        """)
        chunk_ids = [r[0] for r in self.con.execute("SELECT cell_id FROM chunks").fetchall()]
        log_memory(logger, f"Phase 1: {len(chunk_ids)} chunks identified")
        
        # Add parent columns to elementary_table for efficient SQL grouping
        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts_with_parents AS
            SELECT *, 
                   h3_parent(inner_cell, {self.partition_res}) as inner_parent,
                   h3_parent(outer_cell, {self.partition_res}) as outer_parent
            FROM {self.elementary_table}
        """)
        
        # Export per-chunk Parquet files via SQL (no pandas!)
        chunk_parquet_files = {}  # chunk_id -> parquet_path
        t_export = time.time()
        
        for chunk_id in chunk_ids:
            chunk_path = str(temp_dir / f"chunk_{chunk_id}.parquet")
            # Get shortcuts where inner_parent OR outer_parent matches chunk_id
            self.con.execute(f"""
                COPY (
                    SELECT from_edge, to_edge, cost, via_edge, lca_res, 
                           inner_cell, outer_cell, inner_res, outer_res, current_cell
                    FROM shortcuts_with_parents
                    WHERE inner_parent = {chunk_id} OR outer_parent = {chunk_id}
                ) TO '{chunk_path}' (FORMAT PARQUET)
            """)
            chunk_parquet_files[chunk_id] = chunk_path
        
        # Drop temp table
        self.con.execute("DROP TABLE IF EXISTS shortcuts_with_parents")
        
        log_memory(logger, f"Phase 1: Exported {len(chunk_ids)} chunk Parquet files in {time.time() - t_export:.1f}s")
        
        res_partition_cells = []
        total_deactivated = 0
        all_timing_info = []
        
        num_workers = self.workers.get('phase1', MAX_WORKERS)
        
        if num_workers > 1:
            logger.info(f"  Processing {len(chunk_ids)} chunks in parallel (max {num_workers} workers)...")
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                # Submit futures with Parquet paths
                futures = {}
                for chunk_id in chunk_ids:
                    if chunk_id in chunk_parquet_files:
                        future = executor.submit(process_chunk_phase1, 
                            (chunk_id, chunk_parquet_files[chunk_id], edges_parquet_path, 
                             str(temp_dir), self.partition_res, self.sp_method, self.hybrid_res))
                        futures[future] = chunk_id
                
                for i, future in enumerate(as_completed(futures), 1):
                    chunk_id, active_path, deactivated_path, count, timing_info, duration = future.result()
                    all_timing_info.extend(timing_info)
                    
                    # Insert results from Parquet files
                    if active_path and Path(active_path).exists():
                        self.con.execute(f"CREATE OR REPLACE TABLE cell_{chunk_id} AS SELECT * FROM '{active_path}'")
                        res_partition_cells.append(chunk_id)
                        Path(active_path).unlink()
                    
                    if deactivated_path and Path(deactivated_path).exists():
                        deact_count = self.con.execute(f"SELECT count(*) FROM '{deactivated_path}'").fetchone()[0]
                        self.con.execute(f"""
                            INSERT INTO {self.forward_deactivated_table}
                            SELECT * FROM '{deactivated_path}'
                        """)
                        total_deactivated += deact_count
                        Path(deactivated_path).unlink()
                    
                    # Delete input chunk Parquet file
                    if chunk_id in chunk_parquet_files and Path(chunk_parquet_files[chunk_id]).exists():
                        Path(chunk_parquet_files[chunk_id]).unlink()
                    
                    # Batch checkpoint and memory cleanup
                    if i % 10 == 0:
                        self.checkpoint()
                        gc.collect()
                    
                    logger.info(f"  [{i}/{len(chunk_ids)}] Chunk {chunk_id} complete in {duration:.2f}s. {count} active")
        else:
            logger.info(f"  Processing {len(chunk_ids)} chunks sequentially...")
            for i, chunk_id in enumerate(chunk_ids, 1):
                if chunk_id not in chunk_parquet_files:
                    continue
                    
                args = (chunk_id, chunk_parquet_files[chunk_id], edges_parquet_path, 
                        str(temp_dir), self.partition_res, self.sp_method, self.hybrid_res)
                chunk_id, active_path, deactivated_path, count, timing_info, duration = process_chunk_phase1(args)
                all_timing_info.extend(timing_info)
                
                if active_path and Path(active_path).exists():
                    self.con.execute(f"CREATE OR REPLACE TABLE cell_{chunk_id} AS SELECT * FROM '{active_path}'")
                    res_partition_cells.append(chunk_id)
                    Path(active_path).unlink()
                
                if deactivated_path and Path(deactivated_path).exists():
                    deact_count = self.con.execute(f"SELECT count(*) FROM '{deactivated_path}'").fetchone()[0]
                    self.con.execute(f"""
                        INSERT INTO {self.forward_deactivated_table}
                        SELECT * FROM '{deactivated_path}'
                    """)
                    total_deactivated += deact_count
                    Path(deactivated_path).unlink()
                
                # Delete input chunk Parquet file
                if Path(chunk_parquet_files[chunk_id]).exists():
                    Path(chunk_parquet_files[chunk_id]).unlink()
                
                # Batch checkpoint and memory cleanup
                if i % 10 == 0:
                    self.checkpoint()
                    gc.collect()
                
                logger.info(f"  [{i}/{len(chunk_ids)}] Chunk {chunk_id} complete in {duration:.2f}s. {count} active")
        
        # Final checkpoint before cleanup
        self.checkpoint()
        gc.collect()
        
        # Cleanup temp directory
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Log timing summary
        if all_timing_info:
            pure_times = [t for res, method, t in all_timing_info if method == "PURE"]
            scipy_times = [t for res, method, t in all_timing_info if method == "SCIPY"]
            if pure_times:
                logger.info(f"  PURE timing: {len(pure_times)} calls, total {sum(pure_times):.1f}s, avg {sum(pure_times)/len(pure_times):.2f}s")
            if scipy_times:
                logger.info(f"  SCIPY timing: {len(scipy_times)} calls, total {sum(scipy_times):.1f}s, avg {sum(scipy_times)/len(scipy_times):.2f}s")
        
        logger.info(f"  Total deactivated from Phase 1: {total_deactivated}")
        
        self.current_cells = res_partition_cells
        gc.collect()
        return res_partition_cells

    def process_forward_phase2_consolidation(self):
        """
        Phase 2: Hierarchical Consolidation (Forward Pass)
        Merges cells upward level by level from partition_res-1 to 0.
        """
        log_conf.log_section(logger, f"PHASE 2: HIERARCHICAL CONSOLIDATION ({self.partition_res-1} -> 0)")
        logger.info(f"  Starting Phase 2 with {len(self.current_cells)} cell tables.")

        for target_res in range(self.partition_res - 1, -2, -1):
            res_start = time.time()
            
            # 1. Group cells by their parent at target_res
            parent_to_children = {}
            for cell_id in self.current_cells:
                parent_id = self.con.execute(f"SELECT h3_parent({cell_id}, {target_res})").fetchone()[0] if target_res >= 0 else 0
                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                parent_to_children[parent_id].append(cell_id)
            
            logger.info(f"  Resolution {target_res}: {len(self.current_cells)} cells -> {len(parent_to_children)} parent cells.")
            
            new_cells = []
            # 2. Process each parent cell
            for parent_id, children in parent_to_children.items():
                cell_start = time.time()
                
                # Filter children to only those that actually exist
                valid_children = []
                for child in children:
                    if self.con.sql(f"SELECT count(*) FROM information_schema.tables WHERE table_name = 'cell_{child}'").fetchone()[0] > 0:
                        valid_children.append(child)
                
                if not valid_children:
                    continue

                # 1. Merge children shortcuts and deduplicate
                merge_sql = " UNION ALL ".join([f"SELECT * FROM cell_{child}" for child in valid_children])
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE cell_{parent_id}_tmp AS
                    SELECT 
                        from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge,
                        FIRST(lca_res) as lca_res, FIRST(inner_cell) as inner_cell, FIRST(outer_cell) as outer_cell,
                        FIRST(inner_res) as inner_res, FIRST(outer_res) as outer_res
                    FROM ({merge_sql})
                    GROUP BY from_edge, to_edge
                """)
                
                # Drop old child cell tables BEFORE renaming the parent
                for child in valid_children:
                    if child != parent_id:
                        self.con.execute(f"DROP TABLE IF EXISTS cell_{child}")
                
                self.con.execute(f"DROP TABLE IF EXISTS cell_{parent_id}")
                self.con.execute(f"ALTER TABLE cell_{parent_id}_tmp RENAME TO cell_{parent_id}")
                
                merged_count = self.con.sql(f"SELECT count(*) FROM cell_{parent_id}").fetchone()[0]
                
                # 2. Assign and process parent cell
                self.assign_cell_to_shortcuts(target_res, input_table=f"cell_{parent_id}")
                
                # Step 3: Process cell
                active, news, decs = self.process_cell_forward(f"cell_{parent_id}")
                
                # Add to new cells list
                new_cells.append(parent_id)
                
                logger.info(f"    Parent {parent_id}: {len(valid_children)} children, {merged_count} merged -> {active} active -> {news} pool, {decs} deactivated ({format_time(time.time() - cell_start)})")
            
            self.con.execute("DROP TABLE IF EXISTS shortcuts_active")
            self.con.execute("DROP TABLE IF EXISTS shortcuts_next")
            self.checkpoint()
            gc.collect()  # Memory cleanup after each resolution
            
            self.current_cells = list(set(new_cells))
            logger.info(f"  Res {target_res} complete in {format_time(time.time() - res_start)}. Active cells: {len(self.current_cells)}, Deactivated: {self.con.sql(f'SELECT count(*) FROM {self.forward_deactivated_table}').fetchone()[0]}")

        # Move remaining active cells to deactivated for final processing
        remaining_active = 0
        for cell_id in self.current_cells:
            count = self.con.sql(f"SELECT count(*) FROM cell_{cell_id}").fetchone()[0]
            remaining_active += count
            self.con.execute(f"INSERT INTO {self.forward_deactivated_table} SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res FROM cell_{cell_id}")
            self.con.execute(f"DROP TABLE cell_{cell_id}")
        
        total_forward = self.con.sql(f"SELECT count(*) FROM {self.forward_deactivated_table}").fetchone()[0]
        
        # Stream dedup directly to Parquet (no temp table in memory)
        # Use district name from db_path for unique checkpoint file
        district_name = Path(self.db_path).stem  # e.g., "burnaby" from "burnaby.db"
        parquet_path = str(Path(self.db_path).parent / f"{district_name}_forward_deactivated.parquet")
        self.con.execute(f"""
            COPY (
                SELECT 
                    from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge,
                    FIRST(lca_res) as lca_res, FIRST(inner_cell) as inner_cell, FIRST(outer_cell) as outer_cell, 
                    FIRST(inner_res) as inner_res, FIRST(outer_res) as outer_res
                FROM {self.forward_deactivated_table}
                GROUP BY from_edge, to_edge
            ) TO '{parquet_path}' (FORMAT PARQUET)
        """)
        
        # Get dedup count from parquet metadata
        dedup_count = self.con.execute(f"SELECT count(*) FROM '{parquet_path}'").fetchone()[0]
        
        logger.info("--------------------------------------------------")
        logger.info(f"  Remaining active at Res -1: {remaining_active}")
        logger.info(f"  Total deactivated (before dedup): {total_forward}")  
        logger.info(f"  Deduplicated forward results: {dedup_count}")
        logger.info(f"  Saved to: {parquet_path}")
        
        return dedup_count

    def process_backward_phase4_parallel(self):
        """
        PARALLEL Phase 4: Process cells concurrently using multiprocessing.
        Workers read from persistent DB (read-only) and write results to Parquet.
        Main process inserts from Parquet files - eliminates large DataFrame IPC.
        """
        log_conf.log_section(logger, f"PHASE 4: PARALLEL BACKWARD ({self.partition_res} -> 15)")
        
        # Create temp directory for Parquet results
        temp_dir = Path(self.db_path).parent / "phase4_temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Use cell Parquet files from Phase 3
        cell_ids = self.current_cells
        total_shortcuts = sum(
            self.con.execute(f"SELECT count(*) FROM '{path}'").fetchone()[0]
            for path in self.cell_parquet_files.values()
        ) if hasattr(self, 'cell_parquet_files') else 0
        
        total_deactivated = self.con.execute(f"SELECT count(*) FROM {self.backward_deactivated_table}").fetchone()[0]
        all_timing_info = []  # Collect timing from all workers
        
        num_workers = self.workers.get('phase4', MAX_WORKERS)
        checkpoint_interval = 10  # Checkpoint every N cells instead of every cell
        
        if num_workers > 1:
            logger.info(f"  Starting with {len(cell_ids)} cells ({total_shortcuts} shortcuts), max {num_workers} workers...")
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                # Submit futures - pass Parquet file paths
                futures = {}
                for cell_id in cell_ids:
                    if cell_id in self.cell_parquet_files:
                        cell_parquet = self.cell_parquet_files[cell_id]
                        future = executor.submit(process_chunk_phase4, 
                            (cell_id, cell_parquet, self.edges_parquet_path, str(temp_dir), 
                             self.partition_res, self.sp_method, self.hybrid_res))
                        futures[future] = cell_id
                
                for i, future in enumerate(as_completed(futures), 1):
                    cell_id, result_path, count, timing_info, duration = future.result()
                    all_timing_info.extend(timing_info)
                    
                    # Insert from Parquet file (already on disk, no IPC overhead)
                    if result_path and count > 0 and Path(result_path).exists():
                        self.con.execute(f"""
                            INSERT INTO {self.backward_deactivated_table}
                            SELECT * FROM '{result_path}'
                        """)
                        total_deactivated += count
                        Path(result_path).unlink()  # Delete temp result Parquet file
                    
                    # Delete the cell input Parquet file (no longer needed)
                    if cell_id in self.cell_parquet_files:
                        cell_parquet = Path(self.cell_parquet_files[cell_id])
                        if cell_parquet.exists():
                            cell_parquet.unlink()
                    
                    # Batch checkpoint - only every N cells
                    if i % checkpoint_interval == 0:
                        self.checkpoint()
                        gc.collect()
                    
                    logger.info(f"  [{i}/{len(futures)}] Cell {cell_id} complete in {duration:.2f}s: {count} shortcuts, total: {total_deactivated}")
        else:
            logger.info(f"  Starting with {len(cell_ids)} cells ({total_shortcuts} shortcuts) sequentially...")
            for i, cell_id in enumerate(cell_ids, 1):
                if cell_id not in self.cell_parquet_files:
                    continue
                
                cell_parquet = self.cell_parquet_files[cell_id]
                args = (cell_id, cell_parquet, self.edges_parquet_path, str(temp_dir), 
                        self.partition_res, self.sp_method, self.hybrid_res)
                cell_id, result_path, count, timing_info, duration = process_chunk_phase4(args)
                all_timing_info.extend(timing_info)
                
                # Insert from Parquet file
                if result_path and count > 0 and Path(result_path).exists():
                    self.con.execute(f"""
                        INSERT INTO {self.backward_deactivated_table}
                        SELECT * FROM '{result_path}'
                    """)
                    total_deactivated += count
                    Path(result_path).unlink()  # Delete temp result Parquet file
                
                # Delete the cell input Parquet file
                cell_parquet_path = Path(cell_parquet)
                if cell_parquet_path.exists():
                    cell_parquet_path.unlink()
                
                # Batch checkpoint
                if i % checkpoint_interval == 0:
                    self.checkpoint()
                    gc.collect()
                
                logger.info(f"  [{i}/{len(cell_ids)}] Cell {cell_id} complete in {duration:.2f}s: {count} shortcuts, total: {total_deactivated}")
        
        # Final checkpoint and cleanup
        self.checkpoint()
        gc.collect()
        
        # Cleanup temp directories and files (robust - handle any remaining files)
        import shutil
        
        # Clean phase4_temp (results directory)
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Clean phase4_cells (cell data directory)
        cell_data_dir = Path(self.db_path).parent / "phase4_cells"
        if cell_data_dir.exists():
            shutil.rmtree(cell_data_dir, ignore_errors=True)
        
        logger.info(f"  Cleaned up temporary Parquet files")
        
        # Log PURE vs SCIPY timing summary
        if all_timing_info:
            pure_times = [t for res, method, t in all_timing_info if method == "PURE"]
            scipy_times = [t for res, method, t in all_timing_info if method == "SCIPY"]
            if pure_times:
                logger.info(f"  PURE timing: {len(pure_times)} calls, total {sum(pure_times):.1f}s, avg {sum(pure_times)/len(pure_times):.2f}s")
            if scipy_times:
                logger.info(f"  SCIPY timing: {len(scipy_times)} calls, total {sum(scipy_times):.1f}s, avg {sum(scipy_times)/len(scipy_times):.2f}s")
        
        return total_deactivated

    def checkpoint(self):
        self.con.execute("CHECKPOINT")

    def vacuum(self):
        self.con.execute("VACUUM")

    def close(self):
        self.con.close()

    def get_sp_method_for_resolution(self, res: int, is_forward: bool) -> str:
        """
        Determine which SP method to use based on resolution and phase direction.
        
        For HYBRID mode:
          - res >= hybrid_res: PURE
          - res < hybrid_res: SCIPY
            
        For PURE or SCIPY modes, always return that method.
        """
        if self.sp_method == "HYBRID":
            if res >= self.hybrid_res:
                return "PURE"
            else:
                return "SCIPY"
        else:
            return self.sp_method

    def clear_backward_deactivated_shortcuts(self):
        self.con.execute(f"DELETE FROM {self.backward_deactivated_table}")
        self.con.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.backward_deactivated_table} (
                from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER,
                lca_res INTEGER, inner_cell BIGINT, outer_cell BIGINT, inner_res TINYINT, outer_res TINYINT, current_cell BIGINT
            )
        """)

    def assign_cell_to_shortcuts(self, res: int, phase: int = 1, direction: str = "forward", input_table: str = "shortcuts", single_assignment: bool = False):
        """
        Assigns each shortcut to H3 cell(s) at resolution res.
        Instead of creating UNION (row duplication), adds current_cell_in and current_cell_out columns.
        Row expansion is deferred to process_cell_forward/backward.
        """
        self.con.execute(f"DROP TABLE IF EXISTS {input_table}_tmp")
        
        if res == -1:
            # Global level: all shortcuts belong to cell 0
            self.con.execute(f"""
                CREATE TABLE {input_table}_tmp AS
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell,
                       inner_res, outer_res, 
                       0::BIGINT AS current_cell_in, 
                       0::BIGINT AS current_cell_out
                FROM {input_table}
            """)
        else:
            # Compute parent cells for inner and outer, store as separate columns
            self.con.execute(f"""
                CREATE TABLE {input_table}_tmp AS
                SELECT 
                    from_edge, to_edge, cost, via_edge, lca_res, 
                    inner_cell, outer_cell, inner_res, outer_res,
                    CASE WHEN lca_res <= {res} AND inner_res >= {res} 
                         THEN h3_parent(inner_cell::BIGINT, {res}) 
                         ELSE NULL END AS current_cell_in,
                    CASE WHEN lca_res <= {res} AND outer_res >= {res} 
                         THEN h3_parent(outer_cell::BIGINT, {res}) 
                         ELSE NULL END AS current_cell_out
                FROM {input_table}
            """)
        
        self.con.execute(f"DROP TABLE {input_table}")
        self.con.execute(f"ALTER TABLE {input_table}_tmp RENAME TO {input_table}")

    def h3_get_children(self, cell_id: int, res: int) -> list[int]:
        """Helper to get children, handling the global parent 0."""
        if cell_id == 0:
            return [int(h, 16) for h in h3.get_res0_cells()]
        return [int(h, 16) for h in h3.cell_to_children(h3.int_to_str(cell_id), res)]

    def partition_to_children(self, child_res: int, child_list: list[int], input_table: str = "shortcuts"):
        """Partition shortcuts to child cells using hash join."""
        self.con.execute(f"ALTER TABLE {input_table} DROP COLUMN IF EXISTS current_cell")    
        
        if not child_list:
            self.con.execute(f"ALTER TABLE {input_table} ADD COLUMN IF NOT EXISTS current_cell BIGINT DEFAULT NULL")
            return

        self.con.execute("DROP TABLE IF EXISTS _child_cells")
        self.con.execute("CREATE TEMP TABLE _child_cells (cell_id BIGINT PRIMARY KEY)")
        self.con.execute("INSERT INTO _child_cells VALUES " + ",".join(f"({c})" for c in child_list))

        self.con.execute(f"DROP TABLE IF EXISTS {input_table}_tmp")
        self.con.execute(f"""
            CREATE TABLE {input_table}_tmp AS
            WITH with_parents AS (
                SELECT from_edge, to_edge, cost, via_edge, lca_res, 
                    inner_cell, outer_cell, inner_res, outer_res,
                    h3_parent(inner_cell::BIGINT, {child_res}) AS inner_parent,
                    h3_parent(outer_cell::BIGINT, {child_res}) AS outer_parent
                FROM {input_table}
            ),
            inner_matches AS (
                SELECT p.*, p.inner_parent AS current_cell
                FROM with_parents p
                INNER JOIN _child_cells c ON p.inner_parent = c.cell_id
            ),
            outer_matches AS (
                SELECT p.*, p.outer_parent AS current_cell
                FROM with_parents p
                INNER JOIN _child_cells c ON p.outer_parent = c.cell_id
                WHERE p.inner_parent IS DISTINCT FROM p.outer_parent
            ),
            no_matches AS (
                SELECT p.*, NULL::BIGINT AS current_cell
                FROM with_parents p
                LEFT JOIN _child_cells c1 ON p.inner_parent = c1.cell_id
                LEFT JOIN _child_cells c2 ON p.outer_parent = c2.cell_id
                WHERE c1.cell_id IS NULL AND c2.cell_id IS NULL
            )
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell FROM inner_matches
            UNION ALL
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell FROM outer_matches
            UNION ALL
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell FROM no_matches
        """)

        self.con.execute(f"DROP TABLE {input_table}")
        self.con.execute(f"ALTER TABLE {input_table}_tmp RENAME TO {input_table}")
        self.con.execute("DROP TABLE IF EXISTS _child_cells")

    def process_cell_forward(self, table_name: str, method: str = SP_METHOD, num_workers: int = 1):
        """
        Processes shortcuts for forward pass with deactivation.
        Expands current_cell_in/out to single current_cell column first.
        """
        active, news, decs = _process_cell_forward_worker(self.con, table_name, method=method, num_workers=num_workers)
        
        # Insert deactivated shortcuts into forward_deactivated_table
        # The worker creates a 'deactivated' table with the inactive shortcuts
        if decs > 0:
            self.con.execute(f"""
                INSERT INTO {self.forward_deactivated_table}
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
                FROM deactivated
            """)
        self.con.execute("DROP TABLE IF EXISTS deactivated")
        
        return active, news, decs

    def process_cell_backward(self, table_name: str, method: str = SP_METHOD):
        """
        Processes shortcuts for backward pass:
        1. Expand from current_cell_in/out to current_cell
        2. Split into active (current_cell IS NOT NULL) and inactive (current_cell IS NULL)
        3. Run SP only on active shortcuts
        4. Merge back with inactive shortcuts
        """
        # Step 1: Expand from current_cell_in/out to current_cell
        self.con.execute(f"DROP TABLE IF EXISTS {table_name}_expanded")
        self.con.execute(f"""
            CREATE TABLE {table_name}_expanded AS
            -- Inner cell (always include if not null)
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                   inner_res, outer_res, current_cell_in AS current_cell
            FROM {table_name}
            WHERE current_cell_in IS NOT NULL
            UNION
            -- Outer cell (only if different from inner)
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                   inner_res, outer_res, current_cell_out AS current_cell
            FROM {table_name}
            WHERE current_cell_out IS NOT NULL 
              AND (current_cell_in IS NULL OR current_cell_out != current_cell_in)
            UNION ALL
            -- Inactive (both NULL)
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                   inner_res, outer_res, NULL AS current_cell
            FROM {table_name}
            WHERE current_cell_in IS NULL AND current_cell_out IS NULL
        """)
        
        # Step 2: Split active vs inactive
        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts_active AS
            SELECT * FROM {table_name}_expanded WHERE current_cell IS NOT NULL
        """)
        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts_inactive AS
            SELECT * FROM {table_name}_expanded WHERE current_cell IS NULL
        """)
        
        active_count = self.con.sql("SELECT count(*) FROM shortcuts_active").fetchone()[0]
        
        new_count = 0
        if active_count > 0:
            # Run SP only on active shortcuts
            self.run_shortest_paths(method=method, quiet=True, input_table="shortcuts_active")
            new_count = self.con.sql("SELECT count(*) FROM shortcuts_active").fetchone()[0]
        
        # Merge active + inactive back into original table (WITHOUT current_cell)
        self.con.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.con.execute(f"DROP TABLE IF EXISTS {table_name}_expanded")
        self.con.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
            FROM shortcuts_active
            UNION ALL
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
            FROM shortcuts_inactive
        """)
        
        total_count = self.con.sql(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        
        # Cleanup
        self.con.execute("DROP TABLE IF EXISTS shortcuts_active")
        self.con.execute("DROP TABLE IF EXISTS shortcuts_inactive")
            
        return active_count, total_count, 0


    def run_shortest_paths(self, method: str = None, quiet: bool = True, input_table: str = "shortcuts"):
        """Run shortest paths on input table with slim and enrich optimization."""
        if method is None:
            method = SP_METHOD
        
        self.con.execute("DROP TABLE IF EXISTS sp_input")
        self.con.execute(f"CREATE TEMPORARY TABLE sp_input AS SELECT from_edge, to_edge, cost, via_edge, current_cell::BIGINT as current_cell FROM {input_table}")
        
        if method == "PURE":
            compute_shortest_paths_pure_duckdb(self.con, quiet=quiet, input_table="sp_input")
            self.con.execute("CREATE OR REPLACE TABLE shortcuts_next AS SELECT * FROM sp_input")
        elif method == "SCIPY":
            # BATCHED SCIPY: Process cells one at a time to avoid loading all data into RAM
            # Get list of distinct cells
            cells = [r[0] for r in self.con.execute("SELECT DISTINCT current_cell FROM sp_input WHERE current_cell IS NOT NULL").fetchall()]
            
            # Create empty result table
            self.con.execute("""
                CREATE OR REPLACE TABLE shortcuts_next (
                    from_edge INTEGER, to_edge INTEGER, cost FLOAT, via_edge INTEGER
                )
            """)
            
            # Process each cell separately
            for cell in cells:
                # Load only this cell's shortcuts into pandas
                cell_df = self.con.execute(f"SELECT * FROM sp_input WHERE current_cell = {cell}").df()
                
                if len(cell_df) > 0:
                    processed = process_partition_scipy(cell_df)
                    if not processed.empty:
                        # Insert results back to DuckDB
                        self.con.execute("INSERT INTO shortcuts_next SELECT from_edge, to_edge, cost, via_edge FROM processed")
                
                # Clear memory after each cell
                del cell_df
                gc.collect()
            
            # Final deduplication across all cells
            self.con.execute("""
                CREATE OR REPLACE TABLE shortcuts_next AS
                SELECT from_edge, to_edge, MIN(cost) as cost, 
                       arg_min(via_edge, cost) as via_edge
                FROM shortcuts_next
                GROUP BY from_edge, to_edge
            """)

        table_exists = self.con.sql("SELECT count(*) FROM information_schema.tables WHERE table_name = 'shortcuts_next'").fetchone()[0] > 0
        if table_exists:
            self.con.execute("""
                CREATE OR REPLACE TABLE shortcuts_next_enriched AS
                SELECT 
                    s.from_edge, s.to_edge, s.cost, s.via_edge,
                    GREATEST(e1.lca_res, e2.lca_res) as lca_res,
                    h3_lca(e1.to_cell, e2.from_cell)::BIGINT as inner_cell,
                    h3_lca(e1.from_cell, e2.to_cell)::BIGINT as outer_cell,
                    h3_resolution(h3_lca(e1.to_cell, e2.from_cell))::TINYINT as inner_res,
                    h3_resolution(h3_lca(e1.from_cell, e2.to_cell))::TINYINT as outer_res
                FROM shortcuts_next s
                LEFT JOIN edges e1 ON s.from_edge = e1.id
                LEFT JOIN edges e2 ON s.to_edge = e2.id
            """)
            self.con.execute("DROP TABLE shortcuts_next")
            self.con.execute("ALTER TABLE shortcuts_next_enriched RENAME TO shortcuts_next")
        else:
            self.con.execute(f"""
                CREATE OR REPLACE TABLE shortcuts_next AS 
                SELECT from_edge, to_edge, cost, via_edge, 
                       0 as lca_res, 0::BIGINT as inner_cell, 0::BIGINT as outer_cell, 
                       0::TINYINT as inner_res, 0::TINYINT as outer_res
                FROM {input_table} WHERE 1=0
            """)

        self.con.execute(f"DROP TABLE IF EXISTS {input_table}")
        self.con.execute(f"ALTER TABLE shortcuts_next RENAME TO {input_table}")
        self.con.execute("DROP TABLE IF EXISTS sp_input")


    def process_backward_phase3_consolidation(self):
        """Phase 3: Backward Consolidation (0 -> partition_res-1)"""
        log_conf.log_section(logger, f"PHASE 3: BACKWARD CONSOLIDATION (0 -> {self.partition_res-1})")
        
        # Check if forward_deactivated has data (works for both fresh run and resume)
        forward_count = self.con.sql(f"SELECT count(*) FROM {self.forward_deactivated_table}").fetchone()[0]
        if forward_count == 0:
            logger.warning("No shortcuts in forward_deactivated to process in Phase 3.")
            return

        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts AS
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
            FROM {self.forward_deactivated_table}
        """)
        logger.info(f"Starting backward consolidation with {forward_count} shortcuts from forward pass.")

        self.con.execute("DROP TABLE IF EXISTS cell_0")
        self.con.execute("ALTER TABLE shortcuts RENAME TO cell_0")
        self.current_cells = [0]
        logger.info(f"  Starting with {forward_count} shortcuts in global cell_0.")

        # Track cumulative timing
        total_partition_time = 0.0
        total_assign_time = 0.0
        total_sp_time = 0.0

        for target_res in range(-1, self.partition_res):
            res_start = time.time()
            total_deactivated = 0
            child_res = target_res + 1
            list_children_cells = []
            
            for parent_cell in self.current_cells:
                if self.con.sql(f"SELECT count(*) FROM information_schema.tables WHERE table_name = 'cell_{parent_cell}'").fetchone()[0] == 0:
                    continue

                active_children = set()
                children_for_parent = self.h3_get_children(parent_cell, child_res)
                t_partition = time.time()
                self.partition_to_children(child_res, children_for_parent, input_table=f"cell_{parent_cell}")
                t_partition = time.time() - t_partition
                total_partition_time += t_partition
                
                null_count = self.con.execute(f"SELECT COUNT(*) FROM cell_{parent_cell} WHERE current_cell IS NULL").fetchone()[0]
                if null_count > 0:
                    self.con.execute(f"""
                        INSERT INTO {self.backward_deactivated_table}
                        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
                        FROM cell_{parent_cell} WHERE current_cell IS NULL
                    """)
                    total_deactivated += null_count
                
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE current_splits AS
                    SELECT DISTINCT current_cell FROM cell_{parent_cell} WHERE current_cell IS NOT NULL
                """)
                child_ids = [r[0] for r in self.con.execute("SELECT current_cell FROM current_splits").fetchall()]
                
                for child_id in child_ids:
                    self.con.execute(f"""
                        CREATE OR REPLACE TABLE cell_{child_id} AS
                        SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res, current_cell
                        FROM cell_{parent_cell} WHERE current_cell = {child_id}
                    """)
                    active_children.add(child_id)
                
                self.con.execute(f"DROP TABLE IF EXISTS cell_{parent_cell}")
                if child_res == self.partition_res:
                    self.con.execute(f"DROP TABLE IF EXISTS cell_{parent_cell}")
                    list_children_cells += list(active_children)
                    continue

                for child_id in active_children:
                    child_start = time.time()
                    child_count = self.con.sql(f"SELECT count(*) FROM cell_{child_id}").fetchone()[0]
                    if child_count == 0:
                        self.con.execute(f"DROP TABLE IF EXISTS cell_{child_id}")
                        continue
                    
                    t_assign = time.time()
                    self.assign_cell_to_shortcuts(child_res, input_table=f"cell_{child_id}")
                    t_assign = time.time() - t_assign
                    total_assign_time += t_assign
                    
                    # Use process_cell_backward to split active/inactive, run SP, merge back
                    t_sp = time.time()
                    method = self.get_sp_method_for_resolution(child_res, is_forward=False)
                    active_count, news, _ = self.process_cell_backward(f"cell_{child_id}", method=method)
                    t_sp = time.time() - t_sp
                    total_sp_time += t_sp
                    
                    logger.info(f"      Cell {child_id}: {child_count} -> {news} [assign={t_assign:.2f}s, partition={t_partition:.2f}s, SP={t_sp:.2f}s]")
                    
                self.con.execute("DROP TABLE IF EXISTS current_splits")
                self.con.execute("DROP TABLE IF EXISTS shortcuts")
                self.con.execute("DROP TABLE IF EXISTS shortcuts_next")
                self.con.execute("DROP TABLE IF EXISTS shortcuts_active")
                self.con.execute("DROP TABLE IF EXISTS children_list")
                self.checkpoint()
                
                list_children_cells += list(active_children)
            self.current_cells = list_children_cells
            
            if child_res < self.partition_res:
                logger.info(f"  Res {target_res} -> {child_res} complete in {format_time(time.time() - res_start)}. Active cells: {len(list_children_cells)}, Deactivated so far: {self.con.sql(f'SELECT count(*) FROM {self.backward_deactivated_table}').fetchone()[0]}")
          
        remaining_active = sum(
            self.con.sql(f"SELECT count(*) FROM cell_{cell_id}").fetchone()[0]
            for cell_id in self.current_cells
        )
        total_backward = self.con.sql(f"SELECT count(*) FROM {self.backward_deactivated_table}").fetchone()[0]
        logger.info("--------------------------------------------------")
        logger.info(f"  Timing breakdown: partition={total_partition_time:.2f}s, assign={total_assign_time:.2f}s, SP={total_sp_time:.2f}s")
        logger.info(f"  Summary: {len(self.current_cells)} cells ({remaining_active} shortcuts) remain for Phase 4. Deactivated: {total_backward}")
        
        return total_backward

    def process_backward_phase3_efficient(self):
        """
        Phase 3 Efficient: Backward Consolidation (0 -> partition_res)
        Simplified version that processes all shortcuts in a single table (cell_0).
        Similar structure to Phase 1 but in reverse direction.
        """
        log_conf.log_section(logger, f"PHASE 3 EFFICIENT: BACKWARD CONSOLIDATION (0 -> {self.partition_res - 1})")
        
        phase3_start = time.time()
        
        # Create cell_0 from forward_deactivated
        # Optimization: If it's a table (fresh start), RENAME it (zero cost).
        # If it's a view (resume), load it (necessary cost).
        t_load = time.time()
        forward_count = self.con.sql(f"SELECT count(*) FROM {self.forward_deactivated_table}").fetchone()[0]
        
        # Check if it's a view or a table
        res = self.con.execute(f"""
            SELECT table_type 
            FROM information_schema.tables 
            WHERE table_name = '{self.forward_deactivated_table}'
        """).fetchone()
        
        table_type = res[0] if res else 'VIEW' # Default to VIEW if missing (maybe dropped but parquet exists)
        
        self.con.execute("DROP TABLE IF EXISTS cell_0")
        
        if table_type == 'VIEW':
            logger.info(f"  {self.forward_deactivated_table} is a VIEW. Loading to cell_0 (materializing from Parquet)...")
            # If the view doesn't exist, this will error later, which is fine as it's a fatal error anyway.
            self.con.execute(f"CREATE TABLE cell_0 AS SELECT * FROM {self.forward_deactivated_table}")
            # Drop the view since we have the data in cell_0
            self.con.execute(f"DROP VIEW IF EXISTS {self.forward_deactivated_table}")
        else:
            logger.info(f"  {self.forward_deactivated_table} is a TABLE. Renaming to cell_0 (instant)...")
            self.con.execute(f"ALTER TABLE {self.forward_deactivated_table} RENAME TO cell_0")
            
        t_load = time.time() - t_load
        
        self.current_cells = [0]
        logger.info(f"  Initialized cell_0 from {self.forward_deactivated_table} ({forward_count:,} shortcuts). [{t_load:.2f}s]")
        
        if forward_count == 0:
            logger.warning("  No shortcuts to process in Phase 3.")
            self.current_cells = []
            return 0
        
        # Track cumulative timing
        total_deactivate_time = 0.0
        total_assign_time = 0.0
        total_sp_time = 0.0
        
        # Iterative backward loop: 0 -> partition_res
        for res in range(0, self.partition_res):
            res_start = time.time()
            
            # First: Deactivate shortcuts where res > max(inner_res, outer_res)
            t_deact = time.time()
            deactivated_count = self.con.execute(f"""
                SELECT count(*) FROM cell_0 WHERE {res} > GREATEST(inner_res, outer_res)
            """).fetchone()[0]
            
            if deactivated_count > 0:
                self.con.execute(f"""
                    INSERT INTO {self.backward_deactivated_table}
                    SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                           inner_res, outer_res
                    FROM cell_0
                    WHERE {res} > GREATEST(inner_res, outer_res)
                """)
                
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE cell_0 AS
                    SELECT * FROM cell_0
                    WHERE {res} <= GREATEST(inner_res, outer_res)
                """)
            t_deact = time.time() - t_deact
            total_deactivate_time += t_deact
            
            remaining = self.con.execute("SELECT count(*) FROM cell_0").fetchone()[0]
            if remaining == 0:
                logger.info(f"  Res {res}: All shortcuts deactivated. Stopping.")
                break
            
            # Assign cells
            t_assign = time.time()
            self.assign_cell_to_shortcuts(res, input_table="cell_0")
            t_assign = time.time() - t_assign
            total_assign_time += t_assign
            
            # Determine method and run SP (SCIPY is now batched, memory-safe)
            method = self.get_sp_method_for_resolution(res, is_forward=False)
            t_sp = time.time()
            active_count, new_count, _ = self.process_cell_backward("cell_0", method=method)
            t_sp = time.time() - t_sp
            total_sp_time += t_sp
            
            after_count = self.con.execute("SELECT count(*) FROM cell_0").fetchone()[0]
            total_deactivated = self.con.sql(f"SELECT count(*) FROM {self.backward_deactivated_table}").fetchone()[0]
            
            logger.info(f"  Res {res}: {remaining} -> {active_count} active -> {after_count} pool [deact={t_deact:.2f}s, assign={t_assign:.2f}s, SP={t_sp:.2f}s]")
            
            # Memory cleanup after each resolution
            self.checkpoint()
            gc.collect()
        
        # Final deactivation at partition_res boundary
        t_final_deact = time.time()
        deactivated_count = self.con.execute(f"""
                SELECT count(*) FROM cell_0 WHERE {self.partition_res} > GREATEST(inner_res, outer_res)
            """).fetchone()[0]

        if deactivated_count > 0:
                self.con.execute(f"""
                    INSERT INTO {self.backward_deactivated_table}
                    SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                           inner_res, outer_res
                    FROM cell_0
                    WHERE {self.partition_res} > GREATEST(inner_res, outer_res)
                """)
                
                self.con.execute(f"""
                    CREATE OR REPLACE TABLE cell_0 AS
                    SELECT * FROM cell_0
                    WHERE {self.partition_res} <= GREATEST(inner_res, outer_res)
                """)
        t_final_deact = time.time() - t_final_deact
        total_deactivate_time += t_final_deact

        # Split shortcuts for Phase 4
        t_split = time.time()
        self.con.execute(f"""
            CREATE OR REPLACE TABLE cell_0 AS
            SELECT 
                from_edge, to_edge, cost, via_edge, lca_res, 
                inner_cell, outer_cell, inner_res, outer_res,
                CASE WHEN inner_res >= {self.partition_res} 
                     THEN h3_parent(inner_cell::BIGINT, {self.partition_res}) 
                     ELSE NULL END AS current_cell_in,
                CASE WHEN outer_res >= {self.partition_res} 
                     THEN h3_parent(outer_cell::BIGINT, {self.partition_res}) 
                     ELSE NULL END AS current_cell_out
            FROM cell_0
        """)

        # Get distinct cells and create cell tables
        self.con.execute("""
            CREATE OR REPLACE TABLE current_splits AS
            SELECT DISTINCT current_cell_in AS current_cell FROM cell_0 WHERE current_cell_in IS NOT NULL
            UNION
            SELECT DISTINCT current_cell_out AS current_cell FROM cell_0 WHERE current_cell_out IS NOT NULL
        """)

        cell_ids = [r[0] for r in self.con.execute("SELECT current_cell FROM current_splits").fetchall()]
        
        for cell_id in cell_ids:
            self.con.execute(f"""
                CREATE OR REPLACE TABLE cell_{cell_id} AS
                SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, 
                       inner_res, outer_res, current_cell_in, current_cell_out
                FROM cell_0
                WHERE current_cell_in = {cell_id} OR current_cell_out = {cell_id}
            """)
        
        self.current_cells = cell_ids
        
        # Insert inactive shortcuts (no assigned cell) directly into backward_deactivated
        self.con.execute(f"""
            INSERT INTO {self.backward_deactivated_table}
            SELECT from_edge, to_edge, cost, via_edge, lca_res, inner_cell, outer_cell, inner_res, outer_res
            FROM cell_0
            WHERE current_cell_in IS NULL AND current_cell_out IS NULL
        """)
        
        self.con.execute("DROP TABLE IF EXISTS cell_0")
        self.con.execute("DROP TABLE IF EXISTS current_splits")
        t_split = time.time() - t_split
        
        # Export cell tables to Parquet files for Phase 4 workers (solves concurrent DB access issue)
        t_export = time.time()
        cell_data_dir = Path(self.db_path).parent / "phase4_cells"
        cell_data_dir.mkdir(exist_ok=True)
        
        self.cell_parquet_files = {}  # cell_id -> parquet_path
        for cell_id in cell_ids:
            cell_count = self.con.execute(f"SELECT count(*) FROM cell_{cell_id}").fetchone()[0]
            if cell_count > 0:
                parquet_path = str(cell_data_dir / f"cell_{cell_id}.parquet")
                self.con.execute(f"COPY cell_{cell_id} TO '{parquet_path}' (FORMAT PARQUET)")
                self.cell_parquet_files[cell_id] = parquet_path
            # Drop table after export - data is now in Parquet
            self.con.execute(f"DROP TABLE IF EXISTS cell_{cell_id}")
        
        t_export = time.time() - t_export
        
        remaining_active = sum(
            self.con.execute(f"SELECT count(*) FROM '{path}'").fetchone()[0]
            for path in self.cell_parquet_files.values()
        ) if self.cell_parquet_files else 0
        total_backward = self.con.sql(f"SELECT count(*) FROM {self.backward_deactivated_table}").fetchone()[0]
        
        logger.info("--------------------------------------------------")
        logger.info(f"  Timing breakdown: deactivate={total_deactivate_time:.2f}s, assign={total_assign_time:.2f}s, SP={total_sp_time:.2f}s, split={t_split:.2f}s, export={t_export:.2f}s")
        logger.info(f"  Summary: {len(self.cell_parquet_files)} cells ({remaining_active} shortcuts) exported for Phase 4. Deactivated: {total_backward}")
        
        # Also export edges table for workers
        edges_path = str(cell_data_dir / "edges.parquet")
        self.con.execute(f"COPY edges TO '{edges_path}' (FORMAT PARQUET)")
        self.edges_parquet_path = edges_path
        
        self.current_cells = list(self.cell_parquet_files.keys())
        self.checkpoint()
        gc.collect()
        return total_backward

    def finalize_and_save(self, output_path: str):
        """Deduplicates backward pass results and saves output."""
        log_conf.log_section(logger, "FINALIZING")
        
        self.con.execute(f"""
            CREATE OR REPLACE TABLE shortcuts_final AS
            SELECT from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge
            FROM {self.backward_deactivated_table}
            GROUP BY from_edge, to_edge
        """)
        
        final_count = self.con.sql("SELECT COUNT(*) FROM shortcuts_final").fetchone()[0]
        logger.info(f"Final Count (after dedup): {final_count}")
        
        self.con.execute("DROP TABLE IF EXISTS shortcuts")
        self.con.execute("ALTER TABLE shortcuts_final RENAME TO shortcuts")

        utils.add_final_info(self.con)
        utils.save_output(self.con, output_path)
        self.close()
        return final_count



def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"


def main():
    log_conf.setup_logging("parallel_shortcuts")
    log_conf.log_section(logger, f"PARALLEL SHORTCUTS GENERATION (WORKERS={MAX_WORKERS})")
    
    total_start = time.time()
    edges_file = str(config.EDGES_FILE)
    graph_file = str(config.GRAPH_FILE)
    
    db_path = ":memory:"
    if config.DUCKDB_PERSIST_DIR:
        db_path = str(Path(config.DUCKDB_PERSIST_DIR) / "parallel_db.db")
    
    # Use parallel processor for all phases
    processor = ParallelShortcutProcessor(
        db_path, "forward_deactivated_shortcuts", "backward_deactivated_shortcuts", 
        partition_res=PARTITION_RES
    )
    
    # Load data
    processor.load_shared_data(edges_file, graph_file)
    
    # PHASE 1: Parallel
    log_conf.log_section(logger, f"PHASE 1: PARALLEL FORWARD 15 -> {processor.partition_res}")
    phase1_start = time.time()
    res_partition_cells = processor.process_forward_phase1_parallel()
    logger.info(f"Phase 1 complete ({format_time(time.time() - phase1_start)}). Created {len(res_partition_cells)} cell tables.")
    processor.checkpoint()
    processor.vacuum()

    # PHASE 2: Sequential (using ParallelShortcutProcessor methods)
    log_conf.log_section(logger, f"PHASE 2: HIERARCHICAL CONSOLIDATION")
    phase2_start = time.time()
    processor.process_forward_phase2_consolidation()
    logger.info(f"Phase 2 complete ({format_time(time.time() - phase2_start)}).")
    processor.checkpoint()
    processor.vacuum()
    # PHASE 3: Sequential (using ParallelShortcutProcessor methods)
    log_conf.log_section(logger, "PHASE 3: BACKWARD CONSOLIDATION")
    phase3_start = time.time()
    processor.process_backward_phase3_consolidation()
    logger.info(f"Phase 3 complete ({format_time(time.time() - phase3_start)}).")
    processor.checkpoint()
    processor.vacuum()

    # PHASE 4: Parallel
    log_conf.log_section(logger, "PHASE 4: PARALLEL BACKWARD CHUNKED")
    phase4_start = time.time()
    processor.process_backward_phase4_parallel()
    logger.info(f"Phase 4 complete ({format_time(time.time() - phase4_start)}).")
    processor.checkpoint()
    processor.vacuum()
    
    # Finalize
    processor.con.execute(f"""
        CREATE OR REPLACE TABLE shortcuts AS
        SELECT from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge
        FROM {processor.backward_deactivated_table}
        GROUP BY from_edge, to_edge
    """)
    final_count = processor.con.execute("SELECT count(*) FROM shortcuts").fetchone()[0]
    logger.info(f"Final Count (after dedup): {final_count}")
    logger.info(f"Total time: {format_time(time.time() - total_start)}")
    
    processor.close()


if __name__ == "__main__":
    main()
