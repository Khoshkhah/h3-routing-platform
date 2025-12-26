"""
Compare Pure DuckDB vs Partitioned DuckDB for a single resolution step.
This script demonstrates the cell resolution mismatch bug.
"""
import sys
sys.path.insert(0, '/home/kaveh/projects/road-to-shortcut/src')
import duckdb
import pandas as pd
import config
import utilities as utils
from generate_shortcuts_pure import compute_shortest_paths_pure_duckdb
from generate_shortcuts_partitioned import partition_by_cell, process_partition_forward

edges_file = str(config.EDGES_FILE)
graph_file = str(config.GRAPH_FILE)

# Configuration: Change this to test different resolution ranges
TARGET_RES = 10  # Test Res 15→10

print("="*60)
print(f"TEST: Res 15 → {TARGET_RES}")
print("="*60)

# =====================
# APPROACH 1: Pure DuckDB (No Partitioning)
# =====================
print("\n=== PURE DUCKDB (No Partitioning) ===")
con1 = utils.initialize_duckdb(":memory:")
utils.read_edges(con1, edges_file)
utils.create_edges_cost_table(con1, edges_file)
utils.initial_shortcuts_table(con1, graph_file)

initial_count = con1.sql("SELECT COUNT(*) FROM shortcuts").fetchone()[0]
print(f"Initial shortcuts: {initial_count}")

# Process resolutions 15 down to TARGET_RES
for res in range(15, TARGET_RES - 1, -1):
    utils.assign_cell_forward(con1, res)
    
    # Create shortcuts_active table (all shortcuts for non-partitioned)
    con1.execute("DROP TABLE IF EXISTS shortcuts_active")
    con1.execute("CREATE TABLE shortcuts_active AS SELECT * FROM shortcuts_next")
    
    active_count = con1.sql("SELECT COUNT(*) FROM shortcuts_active").fetchone()[0]
    
    # Run shortest paths
    compute_shortest_paths_pure_duckdb(con1, quiet=True)
    utils.merge_shortcuts(con1)
    
    after_count = con1.sql("SELECT COUNT(*) FROM shortcuts").fetchone()[0]
    print(f"Res {res}: {active_count} active → {after_count} total shortcuts")

pure_df = con1.sql("SELECT DISTINCT from_edge, to_edge, cost FROM shortcuts").df()
print(f"PURE Final unique shortcuts: {len(pure_df)}")
con1.close()

# =====================
# APPROACH 2: Partitioned (Like Phase 1)
# =====================
print(f"\n=== PARTITIONED (Res 15 → {TARGET_RES}) ===")

con2 = utils.initialize_duckdb(":memory:")
utils.read_edges(con2, edges_file)
utils.create_edges_cost_table(con2, edges_file)
utils.initial_shortcuts_table(con2, graph_file)

# Get initial shortcuts with cell columns
shortcuts_df = con2.sql("""
    SELECT s.from_edge, s.to_edge, s.cost, s.via_edge,
           e1.from_cell as cell1, e1.to_cell as cell2, e2.to_cell as cell3
    FROM shortcuts s
    JOIN edges e1 ON s.from_edge = e1.id
    JOIN edges e2 ON s.to_edge = e2.id
""").df()
con2.close()

print(f"Initial shortcuts: {len(shortcuts_df)}")

# Partition at Res-7 (like Phase 1) but only run Res 15→TARGET_RES
PARTITION_RES = 7
partitions = partition_by_cell(shortcuts_df, PARTITION_RES)
print(f"Partitioned into {len(partitions)} cells at Res-{PARTITION_RES}")

# Process each partition for Res 15→TARGET_RES only
partition_results = {}
for i, (cell_id, cell_df) in enumerate(partitions.items()):
    # We can use the same function, it will open its own :memory: DB by default.
    # To be safer, we could pass a db_path, but let's just make sure it stays alive.
    try:
        result = process_partition_forward(cell_id, cell_df, edges_file, 15, TARGET_RES)
        partition_results[cell_id] = result
        if (i+1) % 5 == 0:
            print(f"  Processed {i+1}/{len(partitions)} partitions... (current total: {sum(len(df) for df in partition_results.values())})", flush=True)
    except Exception as e:
        print(f"Error in partition {cell_id}: {e}")

# Combine results
partitioned_combined = pd.concat(list(partition_results.values()), ignore_index=True)
partitioned_combined = partitioned_combined.sort_values('cost').drop_duplicates(subset=['from_edge', 'to_edge'], keep='first')
print(f"PARTITIONED Final unique shortcuts: {len(partitioned_combined)}")

# =====================
# COMPARE
# =====================
print("\n=== COMPARISON ===")
pure_df['key'] = pure_df['from_edge'].astype(str) + '_' + pure_df['to_edge'].astype(str)
partitioned_combined['key'] = partitioned_combined['from_edge'].astype(str) + '_' + partitioned_combined['to_edge'].astype(str)

pure_keys = set(pure_df['key'])
part_keys = set(partitioned_combined['key'])

print(f"Pure keys: {len(pure_keys)}")
print(f"Partitioned keys: {len(part_keys)}")
print(f"In both: {len(pure_keys & part_keys)}")
print(f"Only in Pure: {len(pure_keys - part_keys)}")
print(f"Only in Partitioned: {len(part_keys - pure_keys)}")

# =====================
# DEBUG: Show the cell resolution mismatch
# =====================
print("\n=== DEBUG: Cell Resolution Mismatch ===")
cell_id, cell_df = list(partitions.items())[0]
print(f"Partition cell_id (Res-7): {cell_id}")
print(f"Partition has {len(cell_df)} shortcuts")

con3 = utils.initialize_duckdb(":memory:")
utils.read_edges(con3, edges_file)
utils.create_edges_cost_table(con3, edges_file)
con3.register("shortcuts_df", cell_df)
con3.execute("CREATE TABLE shortcuts AS SELECT from_edge, to_edge, cost, via_edge FROM shortcuts_df")

utils.assign_cell_forward(con3, 15)

sample_cells = con3.sql("SELECT DISTINCT current_cell FROM shortcuts_next LIMIT 5").df()
print(f"\nAfter assign_cell_forward(15), sample current_cell values:")
for cell in sample_cells['current_cell'].tolist():
    print(f"  current_cell (Res-15): {cell}")

matching = con3.sql(f"SELECT COUNT(*) FROM shortcuts_next WHERE current_cell = {cell_id}").fetchone()[0]
print(f"\nMatching current_cell = {cell_id}: {matching}")
print("\n*** THE BUG: cell_id is Res-7, but current_cell is Res-15 - they NEVER match! ***")
con3.close()
