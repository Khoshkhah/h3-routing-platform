"""
Pure DuckDB Shortest Path Algorithm
====================================
Uses iterative SQL (Bellman-Ford-style) to compute shortest paths.
"""

import logging
import duckdb

logger = logging.getLogger(__name__)


def compute_shortest_paths_pure_duckdb(con: duckdb.DuckDBPyConnection, max_iterations: int = 100, 
                                       quiet: bool = False, input_table: str = "shortcuts_active"):
    """
    Compute shortest paths using iterative SQL (Bellman-Ford-ish / Delta Stepping).
    Input: input table (subset of shortcuts valid for current cell).
    Output: Modifies input_table in-place with all-pairs shortest paths.
    """
    if not quiet:
        logger.info(f"Starting pure DuckDB shortest path computation using {input_table}")
    
    # 1. Initialize 'paths' with base shortcuts
    con.execute("DROP TABLE IF EXISTS paths")
    con.execute(f"""
        CREATE TABLE paths AS 
        SELECT from_edge, to_edge, cost, via_edge, current_cell 
        FROM {input_table}
    """)
    
    stats = con.sql("SELECT COUNT(*), SUM(cost) FROM paths").fetchone()
    if not quiet:
        logger.info(f"Initial: {stats[0]} paths, CostSum: {stats[1] if stats[1] else 0.0:.4f}")
    
    # 2. Iterative expansion
    i = 0
    while i < max_iterations:
        stats_before = con.sql("SELECT COUNT(*), SUM(cost) FROM paths").fetchone()
        row_count_before = stats_before[0]
        cost_sum_before = stats_before[1] if stats_before[1] is not None else 0.0
        
        # Geometric expansion: paths JOIN paths
        con.execute("""
            CREATE OR REPLACE TABLE new_paths AS
            SELECT 
                L.from_edge,
                R.to_edge,
                L.cost + R.cost AS cost,
                L.to_edge AS via_edge,
                L.current_cell
            FROM paths L
            JOIN paths R ON L.to_edge = R.from_edge AND L.current_cell = R.current_cell
            WHERE L.from_edge != R.to_edge
        """)
        
        # Merge new paths into existing paths, keeping MIN cost
        con.execute("""
            CREATE OR REPLACE TABLE combined_paths AS
            SELECT * FROM paths
            UNION ALL
            SELECT * FROM new_paths
        """)
        
        con.execute("""
            CREATE OR REPLACE TABLE paths_reduced AS
            SELECT 
                from_edge, 
                to_edge, 
                min(cost) as cost,
                arg_min(via_edge, cost) as via_edge,
                current_cell
            FROM combined_paths
            GROUP BY from_edge, to_edge, current_cell
        """)
        
        con.execute("DROP TABLE paths")
        con.execute("ALTER TABLE paths_reduced RENAME TO paths")
        
        # Convergence check
        stats = con.sql("SELECT COUNT(*), SUM(cost) FROM paths").fetchone()
        row_count_after = stats[0]
        cost_sum_after = stats[1] if stats[1] is not None else 0.0
        
        cost_diff = cost_sum_before - cost_sum_after
        if not quiet:
            logger.info(f"Iteration {i}: Rows {row_count_before} -> {row_count_after}, CostSum {cost_sum_before:.4f} -> {cost_sum_after:.4f} (diff: {cost_diff:.4f})")
        
        # Stop if STABLE (no new rows AND no cost improvement)
        if row_count_after == row_count_before and abs(cost_sum_after - cost_sum_before) < 1e-6:
            if not quiet:
                logger.info("Converged.")
            break
            
        i += 1
    
    # Replace input table with result  
    con.execute(f"DROP TABLE IF EXISTS {input_table}")
    con.execute(f"ALTER TABLE paths RENAME TO {input_table}")
    
    # Cleanup
    con.execute("DROP TABLE IF EXISTS new_paths")
    con.execute("DROP TABLE IF EXISTS combined_paths")
