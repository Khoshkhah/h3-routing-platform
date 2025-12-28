import duckdb
import pandas as pd
import os
import sys

def export_edges():
    if len(sys.argv) < 3:
        print("Usage: python export_edges.py <db_path> <output_csv>")
        sys.exit(1)

    DB_PATH = sys.argv[1]
    OUTPUT_CSV = sys.argv[2]

    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    print(f"Connecting to {DB_PATH}...")
    con = duckdb.connect(DB_PATH)
    
    # Check if edges table exists
    tables = con.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    
    if 'edges' not in table_names:
        print("Error: 'edges' table not found in database.")
        print(f"Tables found: {table_names}")
        return

    print(f"Exporting 'edges' table to {OUTPUT_CSV}...")
    
    # Export
    con.execute(f"COPY edges TO '{OUTPUT_CSV}' (HEADER, DELIMITER ',')")
    
    print(f"Successfully exported to {OUTPUT_CSV}")
    con.close()

if __name__ == "__main__":
    export_edges()
