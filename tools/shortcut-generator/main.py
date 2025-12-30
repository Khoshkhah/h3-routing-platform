#!/usr/bin/env python3
"""
Main entry point for Shortcut Generation.

Usage:
    python main.py burnaby          # Run with config/burnaby.yaml
    python main.py somerset         # Run with config/somerset.yaml
    python main.py --config custom  # Run with config/custom.yaml
    python main.py --list           # List available configs
"""

import sys
import os
import gc
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import load_config, CONFIG_DIR


def list_configs():
    """List available configuration profiles."""
    print("Available configuration profiles:")
    for f in CONFIG_DIR.glob("*.yaml"):
        name = f.stem
        print(f"  - {name}")


def run_algorithm(cfg):
    """Run the appropriate algorithm based on config."""
    algo_name = cfg.algorithm.name.lower()
    workers = cfg.parallel.workers
    
    print(f"Running algorithm: {algo_name}")
    print(f"  District: {cfg.input.district}")
    print(f"  Edges: {cfg.input.edges_file}")
    print(f"  Graph: {cfg.input.graph_file}")
    print(f"  Output: {cfg.output.directory}/{cfg.output.shortcuts_file}")
    print(f"  Workers: {workers} ({'parallel' if workers > 1 else 'single-threaded'})")
    print(f"  SP Method: {cfg.algorithm.sp_method}")
    print(f"  Partition Res: {cfg.algorithm.partition_res}")
    print()
    
    # Set environment variables for the algorithms to use
    os.environ["SP_METHOD"] = cfg.algorithm.sp_method
    os.environ["DUCKDB_MEMORY_LIMIT"] = cfg.duckdb.memory_limit
    os.environ["DUCKDB_PERSIST_DIR"] = str(cfg.output.persist_dir)
    
    # Import and run the appropriate algorithm
    if algo_name == "partitioned":
        # The parallel implementation now handles workers=1 correctly
        run_partitioned_parallel(cfg)
    
    elif algo_name in ["hybrid", "scipy", "pure"]:
        print(f"Note: '{algo_name}' is deprecated. Use 'partitioned' with sp_method setting.")
        print(f"  Example: sp_method: '{algo_name.upper()}'")
        sys.exit(1)
    
    else:
        print(f"Unknown algorithm: {algo_name}")
        print("Use 'partitioned' with workers setting:")
        print("  workers: 1    -> single-threaded")
        print("  workers: N    -> parallel with N workers")
        sys.exit(1)


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m{secs}s"




def run_partitioned_parallel(cfg):
    """Run partitioned algorithm in parallel mode."""
    import time
    import logging
    import logging_config as log_conf
    from processor_parallel import ParallelShortcutProcessor, MAX_WORKERS
    
    logger = logging.getLogger(__name__)
    log_conf.setup_logging(f"{cfg.input.district}", level=cfg.logging.level, verbose=cfg.logging.verbose)
    
    # Log config info at start
    log_conf.log_section(logger, "CONFIGURATION")
    logger.info(f"District: {cfg.input.district}")
    logger.info(f"Edges: {cfg.input.edges_file}")
    logger.info(f"Graph: {cfg.input.graph_file}")
    logger.info(f"Output: {cfg.output.directory}/{cfg.output.shortcuts_file}")
    logger.info(f"SP Method: {cfg.algorithm.sp_method}")
    if cfg.algorithm.sp_method == "HYBRID":
        logger.info(f"Hybrid Res: {cfg.algorithm.hybrid_res} (PURE for res >= {cfg.algorithm.hybrid_res}, SCIPY for res < {cfg.algorithm.hybrid_res})")
    logger.info(f"Partition Res: {cfg.algorithm.partition_res}")
    logger.info(f"Workers: {cfg.parallel.workers}")
    logger.info(f"DuckDB Memory: {cfg.duckdb.memory_limit}")
    
    # Setup paths
    persist_dir = Path(cfg.output.persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    db_path = str(persist_dir / f"{cfg.input.district}.db")
    
    # Delete existing DB and checkpoint files if fresh_start is enabled
    if cfg.duckdb.fresh_start:
        import glob
        for f in glob.glob(f"{db_path}*"):
            Path(f).unlink()
            logger.info(f"Deleted: {f}")
        # Also delete parquet checkpoint
        parquet_checkpoint = persist_dir / "forward_deactivated.parquet"
        if parquet_checkpoint.exists():
            parquet_checkpoint.unlink()
            logger.info(f"Deleted: {parquet_checkpoint}")
    
    output_dir = Path(cfg.output.directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Database: {db_path}")
    print(f"Workers: {cfg.parallel.workers}")
    
    # Override MAX_WORKERS from config
    import processor_parallel as parallel_module
    parallel_module.MAX_WORKERS = cfg.parallel.workers
    
    total_start = time.time()
    
    # Prepare worker configuration (use phase-specific if set, else default)
    worker_config = {
        'phase1': cfg.parallel.workers_phase1 or cfg.parallel.workers,
        'phase2': cfg.parallel.workers_phase2 or cfg.parallel.workers,
        'phase3': cfg.parallel.workers_phase3 or cfg.parallel.workers,
        'phase4': cfg.parallel.workers_phase4 or cfg.parallel.workers,
    }
    logger.info(f"Worker config: Phase1={worker_config['phase1']}, Phase4={worker_config['phase4']}")
    
    # Create parallel processor
    processor = ParallelShortcutProcessor(
        db_path=db_path,
        forward_deactivated_table="forward_deactivated",
        backward_deactivated_table="backward_deactivated",
        partition_res=cfg.algorithm.partition_res,
        elementary_table="elementary_shortcuts",
        sp_method=cfg.algorithm.sp_method,
        hybrid_res=cfg.algorithm.hybrid_res,
        worker_config=worker_config
    )
    
    # Load shared data
    processor.load_shared_data(cfg.input.edges_file, cfg.input.graph_file)
    
    # Check if we can resume from Phase 3
    # Check parquet file first, then table
    parquet_path = persist_dir / "forward_deactivated.parquet"
    try:
        forward_count = processor.con.execute("SELECT count(*) FROM forward_deactivated").fetchone()[0]
    except:
        forward_count = 0
    
    can_resume = forward_count > 0 or parquet_path.exists()
    
    if can_resume:
        if forward_count > 0:
            logger.info(f"Resuming: forward_deactivated table has {forward_count:,} rows. Skipping Phase 1 & 2.")
        elif parquet_path.exists():
            logger.info(f"Resuming: Found {parquet_path}. Loading and skipping Phase 1 & 2.")
            # Drop existing empty table if it exists, then create from parquet
            processor.con.execute("DROP TABLE IF EXISTS forward_deactivated")
            processor.con.execute(f"CREATE TABLE forward_deactivated AS SELECT * FROM '{parquet_path}'")
        # Clear backward_deactivated for fresh Phase 3
        processor.con.execute("DELETE FROM backward_deactivated")
        res_partition_cells = []  # Not needed for Phase 3
    else:
        # Phase 1: Parallel (processor logs its own header)
        phase1_start = time.time()
        res_partition_cells = processor.process_forward_phase1_parallel()
        logger.info(f"Phase 1 complete ({format_time(time.time() - phase1_start)}). Created {len(res_partition_cells)} cell tables.")
        processor.checkpoint()
        gc.collect()  # Memory cleanup after Phase 1
        
        # Phase 2: Hierarchical Consolidation (forward pass)
        phase2_start = time.time()
        processor.process_forward_phase2_consolidation()
        logger.info(f"Phase 2 complete ({format_time(time.time() - phase2_start)}).")
        
        # =============================================
        # MEMORY CLEANUP between Phase 2 and Phase 3
        # This prevents OOM crashes in Phase 4
        # =============================================
        logger.info("Cleaning up memory after Phase 2...")
        processor.checkpoint()  # Force DuckDB to flush to disk
        
        # Drop temp tables that are no longer needed
        try:
            processor.con.execute("DROP TABLE IF EXISTS elementary_shortcuts")
            processor.con.execute("DROP TABLE IF EXISTS shortcuts")
        except:
            pass
        
        # Force Python garbage collection
        gc.collect()
        logger.info("Memory cleanup complete.")
    
    # Phase 3: Sequential (OLD consolidation version)
    phase3_start = time.time()
    #processor.process_backward_phase3_consolidation()
    processor.process_backward_phase3_efficient()
    logger.info(f"Phase 3 complete ({format_time(time.time() - phase3_start)}).")
    processor.checkpoint()
    gc.collect()  # Memory cleanup after Phase 3
    
    # Phase 4: Parallel (processor logs its own header)
    phase4_start = time.time()
    processor.process_backward_phase4_parallel()
    logger.info(f"Phase 4 complete ({format_time(time.time() - phase4_start)}).")
    processor.checkpoint()
    gc.collect()  # Memory cleanup after Phase 4
    
    # Finalize: compute cell and inside columns for routing engine
    # MUST join to edges to get lca_in/lca_out for correct inside calculation
    log_conf.log_section(logger, "FINALIZING")
    processor.con.execute("""
        CREATE OR REPLACE TABLE shortcuts AS
        WITH deduped AS (
            SELECT from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge,
                   FIRST(inner_cell) as inner_cell, FIRST(outer_cell) as outer_cell,
                   FIRST(inner_res) as inner_res, FIRST(outer_res) as outer_res,
                   FIRST(lca_res) as lca_res
            FROM backward_deactivated
            GROUP BY from_edge, to_edge
        ),
        with_edge_info AS (
            SELECT d.*, e1.lca_res AS lca_in, e2.lca_res AS lca_out
            FROM deduped d
            LEFT JOIN edges e1 ON d.from_edge = e1.id
            LEFT JOIN edges e2 ON d.to_edge = e2.id
        ),
        with_inside AS (
            SELECT 
                from_edge, to_edge, cost, via_edge,
                inner_cell, outer_cell, inner_res, outer_res, lca_res, lca_in, lca_out,
                CASE 
                    WHEN lca_res > inner_res THEN -2  -- outer-only (base edge)
                    WHEN lca_in = lca_out THEN 0      -- lateral
                    WHEN lca_in < lca_out THEN -1     -- downward
                    ELSE 1                             -- upward
                END AS inside
            FROM with_edge_info
            WHERE lca_res <= inner_res OR lca_res <= outer_res
        )
        SELECT 
            CAST(from_edge AS INT) AS from_edge,
            CAST(to_edge AS INT) AS to_edge,
            cost,
            CAST(via_edge AS INT) AS via_edge,
            CAST(inside AS TINYINT) AS inside,
            h3_parent(outer_cell, LEAST(lca_in, lca_out)::INTEGER) AS cell
        FROM with_inside
    """)
    
    final_count = processor.con.execute("SELECT count(*) FROM shortcuts").fetchone()[0]
    logger.info(f"Final Count: {final_count}")
    logger.info(f"Total time: {format_time(time.time() - total_start)}")
    
    # ============================================================
    # CONSOLIDATE DATABASE: Add full edge data and boundary
    # ============================================================
    log_conf.log_section(logger, "CONSOLIDATING DATABASE")
    
    # 1. Enhance edges table with geometry, length, cost from CSV
    edges_csv_path = cfg.input.edges_file
    logger.info(f"Loading full edge data from: {edges_csv_path}")
    
    processor.con.execute(f"""
        CREATE OR REPLACE TABLE edges_full AS
        SELECT 
            edge_index AS id,
            from_cell,
            to_cell,
            lca_res,
            length,
            cost,
            geometry
        FROM read_csv_auto('{edges_csv_path}')
    """)
    
    # Replace edges table with full version
    processor.con.execute("DROP TABLE IF EXISTS edges")
    processor.con.execute("ALTER TABLE edges_full RENAME TO edges")
    
    edge_count = processor.con.execute("SELECT count(*) FROM edges").fetchone()[0]
    logger.info(f"Enhanced edges table: {edge_count} edges with geometry")
    
    # 2. Create dataset_info table with metadata
    processor.con.execute("""
        CREATE TABLE IF NOT EXISTS dataset_info (
            key VARCHAR PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Insert dataset name
    district_name = cfg.input.district
    processor.con.execute(f"INSERT OR REPLACE INTO dataset_info VALUES ('name', '{district_name}')")
    processor.con.execute(f"INSERT OR REPLACE INTO dataset_info VALUES ('created_at', CURRENT_TIMESTAMP::VARCHAR)")
    processor.con.execute(f"INSERT OR REPLACE INTO dataset_info VALUES ('edge_count', '{edge_count}')")
    processor.con.execute(f"INSERT OR REPLACE INTO dataset_info VALUES ('shortcut_count', '{final_count}')")
    
    # 3. Load boundary GeoJSON if provided
    boundary_path = getattr(cfg.input, 'boundary_file', None)
    if boundary_path and Path(boundary_path).exists():
        logger.info(f"Loading boundary from: {boundary_path}")
        with open(boundary_path, 'r') as f:
            boundary_geojson = f.read().replace("'", "''")  # Escape single quotes for SQL
        processor.con.execute(f"INSERT OR REPLACE INTO dataset_info VALUES ('boundary_geojson', '{boundary_geojson}')")
        logger.info("Stored boundary GeoJSON in database")
    else:
        logger.info("No boundary file provided, skipping boundary storage")
    
    # Save output (Parquet for backwards compatibility)
    output_file = str(output_dir / cfg.output.shortcuts_file)
    processor.con.execute(f"""
        COPY shortcuts TO '{output_file}' (FORMAT PARQUET)
    """)
    print(f"Saved shortcuts to: {output_file}")
    
    # Cleanup: Drop temporary tables, keep only essential ones
    # Essential: edges, shortcuts, dataset_info, elementary_shortcuts (for debugging)
    tables_to_keep = {'edges', 'shortcuts', 'dataset_info', 'elementary_shortcuts'}
    all_tables = [r[0] for r in processor.con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()]
    
    for table in all_tables:
        if table not in tables_to_keep:
            processor.con.execute(f"DROP TABLE IF EXISTS \"{table}\"")
    
    # Vacuum to reclaim space
    processor.con.execute("VACUUM")
    logger.info(f"Database consolidated. Final tables: {', '.join(tables_to_keep)}")
    
    db_size_mb = Path(db_path).stat().st_size / 1024 / 1024
    logger.info(f"Database size: {db_size_mb:.1f} MB")
    
    processor.close()


def normalize_profile(profile: str) -> str:
    """Normalize profile input to just the profile name."""
    # Handle full paths like "config/somerset.yaml"
    if "/" in profile or "\\" in profile:
        profile = Path(profile).stem
    # Remove .yaml extension if present
    if profile.endswith(".yaml") or profile.endswith(".yml"):
        profile = Path(profile).stem
    return profile


def main():
    parser = argparse.ArgumentParser(
        description="Shortcut Generation with Config-based Settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default="default",
        help="Config profile name (e.g., 'burnaby', 'somerset')"
    )
    parser.add_argument(
        "--config", "-c",
        help="Alternative way to specify config profile"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available config profiles"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_configs()
        return
    
    # Determine which config to use
    profile = args.config if args.config else args.profile
    profile = normalize_profile(profile)
    
    print(f"Loading config: {profile}")
    try:
        cfg = load_config(profile)
    except Exception as e:
        print(f"Error loading config '{profile}': {e}")
        print("\nAvailable configs:")
        list_configs()
        sys.exit(1)
    
    # Run the algorithm
    run_algorithm(cfg)


if __name__ == "__main__":
    main()
