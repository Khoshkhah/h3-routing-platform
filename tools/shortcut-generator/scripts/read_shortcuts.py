"""
Read Shortcut Data

This script demonstrates how to read shortcut data from:
1. Output Parquet file - Final deduplicated shortcuts
2. DuckDB database - Full database with all tables

Usage:
    python scripts/read_shortcuts.py
    
    # Or convert to notebook:
    jupyter nbconvert --to notebook scripts/read_shortcuts.py
"""

import duckdb
import pandas as pd
from pathlib import Path

# Configuration - change these as needed
DISTRICT = "Burnaby"  # or "All_Vancouver"

OUTPUT_DIR = Path("output")
PERSIST_DIR = Path("persist")

PARQUET_FILE = OUTPUT_DIR / f"{DISTRICT}_shortcuts"
DB_FILE = PERSIST_DIR / f"{DISTRICT}.db"


def read_from_parquet():
    """Read shortcuts from parquet output file."""
    print("\n" + "="*60)
    print("1. READING FROM PARQUET OUTPUT")
    print("="*60)
    
    if not PARQUET_FILE.exists():
        print(f"Parquet file not found: {PARQUET_FILE}")
        return None
    
    # Read parquet with DuckDB (fastest)
    shortcuts_df = duckdb.read_parquet(str(PARQUET_FILE)).df()
    print(f"Loaded {len(shortcuts_df):,} shortcuts from parquet")
    
    # Basic stats
    print(f"\nShape: {shortcuts_df.shape}")
    print(f"Columns: {list(shortcuts_df.columns)}")
    print(f"\nCost range: {shortcuts_df['cost'].min():.2f} to {shortcuts_df['cost'].max():.2f}")
    print(f"Unique from_edge: {shortcuts_df['from_edge'].nunique():,}")
    print(f"Unique to_edge: {shortcuts_df['to_edge'].nunique():,}")
    
    print("\nSample rows:")
    print(shortcuts_df.head())
    
    return shortcuts_df


def read_from_database():
    """Read from DuckDB database."""
    print("\n" + "="*60)
    print("2. READING FROM DUCKDB DATABASE")
    print("="*60)
    
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return None
    
    # Connect to persistent database (read-only)
    con = duckdb.connect(str(DB_FILE), read_only=True)
    
    # List all tables
    tables = con.execute("SHOW TABLES").fetchall()
    print("\nAvailable tables:")
    for t in tables:
        count = con.execute(f"SELECT count(*) FROM {t[0]}").fetchone()[0]
        print(f"  - {t[0]}: {count:,} rows")
    
    # Edges table
    print("\n--- Edges Table ---")
    edges_df = con.execute("SELECT * FROM edges LIMIT 5").df()
    print(f"Columns: {list(edges_df.columns)}")
    print(edges_df)
    
    # Shortcuts table
    print("\n--- Shortcuts Table (Final) ---")
    shortcuts_df = con.execute("SELECT * FROM shortcuts LIMIT 5").df()
    print(shortcuts_df)
    
    # Elementary shortcuts
    elementary_count = con.execute("SELECT count(*) FROM elementary_shortcuts").fetchone()[0]
    print(f"\nElementary shortcuts: {elementary_count:,}")
    
    # Forward deactivated
    fwd_count = con.execute("SELECT count(*) FROM forward_deactivated").fetchone()[0]
    print(f"Forward deactivated: {fwd_count:,}")
    
    con.close()
    return shortcuts_df


def query_examples():
    """Example queries on the database."""
    print("\n" + "="*60)
    print("3. QUERY EXAMPLES")
    print("="*60)
    
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return
    
    con = duckdb.connect(str(DB_FILE), read_only=True)
    
    # Cost distribution
    print("\n--- Cost Statistics ---")
    cost_stats = con.execute("""
        SELECT 
            MIN(cost) as min_cost,
            AVG(cost) as avg_cost,
            MEDIAN(cost) as median_cost,
            MAX(cost) as max_cost,
            STDDEV(cost) as stddev_cost
        FROM shortcuts
    """).df()
    print(cost_stats)
    
    # Top connected edges
    print("\n--- Top 10 Most Connected Source Edges ---")
    top_connected = con.execute("""
        SELECT from_edge, COUNT(*) as num_destinations
        FROM shortcuts
        GROUP BY from_edge
        ORDER BY num_destinations DESC
        LIMIT 10
    """).df()
    print(top_connected)
    
    # Shortcut length distribution (by via_edge chain)
    print("\n--- Shortcuts by Via Edge ---")
    via_stats = con.execute("""
        SELECT 
            CASE WHEN via_edge IS NULL THEN 'Direct (1 hop)' ELSE 'Multi-hop' END as path_type,
            COUNT(*) as count
        FROM shortcuts
        GROUP BY path_type
    """).df()
    print(via_stats)
    
    con.close()


def find_path(from_edge: int, to_edge: int):
    """Find the shortest path between two edges."""
    if not DB_FILE.exists():
        print(f"Database file not found: {DB_FILE}")
        return None
    
    con = duckdb.connect(str(DB_FILE), read_only=True)
    
    result = con.execute(f"""
        SELECT from_edge, to_edge, cost, via_edge
        FROM shortcuts
        WHERE from_edge = {from_edge} AND to_edge = {to_edge}
    """).df()
    
    con.close()
    
    if len(result) == 0:
        print(f"No path found from {from_edge} to {to_edge}")
        return None
    
    print(f"Path from {from_edge} to {to_edge}:")
    print(result)
    return result


if __name__ == "__main__":
    # Run all examples
    read_from_parquet()
    read_from_database()
    query_examples()
    
    # Example: Find specific path (uncomment and set edge IDs)
    # find_path(from_edge=12345, to_edge=67890)
