#!/usr/bin/env python3
"""
Compare DuckDB and Spark hybrid shortcut results.
"""

import duckdb

# Paths
SPARK_PARQUET = "/home/kaveh/projects/road-to-shortcut/output/Burnaby_spark_hybrid/*.parquet"
DUCKDB_PARQUET = "/home/kaveh/projects/road-to-shortcut-duckdb/output/Burnaby_shortcuts"

con = duckdb.connect(":memory:")

print("Loading Spark hybrid results...")
con.execute(f"""
    CREATE TABLE spark AS 
    SELECT from_edge, to_edge, cost, via_edge 
    FROM read_parquet('{SPARK_PARQUET}')
""")
spark_count = con.execute("SELECT count(*) FROM spark").fetchone()[0]
print(f"  Spark count: {spark_count:,}")

print("\nLoading DuckDB results...")
con.execute(f"""
    CREATE TABLE duckdb AS 
    SELECT from_edge, to_edge, cost, via_edge 
    FROM read_parquet('{DUCKDB_PARQUET}')
""")
duckdb_count = con.execute("SELECT count(*) FROM duckdb").fetchone()[0]
print(f"  DuckDB count: {duckdb_count:,}")

print("\n" + "="*60)
print("COMPARISON RESULTS")
print("="*60)

# Deduplicate both to ensure fair comparison
print("\nDeduplicating both tables (MIN cost per from_edge, to_edge)...")
con.execute("""
    CREATE TABLE spark_dedup AS
    SELECT from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge
    FROM spark
    GROUP BY from_edge, to_edge
""")
con.execute("""
    CREATE TABLE duckdb_dedup AS
    SELECT from_edge, to_edge, MIN(cost) as cost, arg_min(via_edge, cost) as via_edge
    FROM duckdb
    GROUP BY from_edge, to_edge
""")

spark_dedup_count = con.execute("SELECT count(*) FROM spark_dedup").fetchone()[0]
duckdb_dedup_count = con.execute("SELECT count(*) FROM duckdb_dedup").fetchone()[0]
print(f"  Spark dedup count: {spark_dedup_count:,}")
print(f"  DuckDB dedup count: {duckdb_dedup_count:,}")

# Find exact matches
print("\n--- Exact Matches (same from_edge, to_edge, cost) ---")
con.execute("""
    CREATE TABLE exact_matches AS
    SELECT s.from_edge, s.to_edge, s.cost as spark_cost, d.cost as duckdb_cost
    FROM spark_dedup s
    INNER JOIN duckdb_dedup d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
    WHERE ABS(s.cost - d.cost) < 0.0001
""")
exact_match_count = con.execute("SELECT count(*) FROM exact_matches").fetchone()[0]
print(f"  Exact matches: {exact_match_count:,}")

# Find cost mismatches
print("\n--- Cost Mismatches (same from_edge, to_edge, different cost) ---")
con.execute("""
    CREATE TABLE cost_mismatches AS
    SELECT s.from_edge, s.to_edge, s.cost as spark_cost, d.cost as duckdb_cost,
           (d.cost - s.cost) as cost_diff,
           CASE WHEN d.cost < s.cost THEN 'DuckDB better' ELSE 'Spark better' END as better
    FROM spark_dedup s
    INNER JOIN duckdb_dedup d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
    WHERE ABS(s.cost - d.cost) >= 0.0001
""")
mismatch_count = con.execute("SELECT count(*) FROM cost_mismatches").fetchone()[0]
print(f"  Cost mismatches: {mismatch_count:,}")

if mismatch_count > 0:
    spark_better = con.execute("SELECT count(*) FROM cost_mismatches WHERE better = 'Spark better'").fetchone()[0]
    duckdb_better = con.execute("SELECT count(*) FROM cost_mismatches WHERE better = 'DuckDB better'").fetchone()[0]
    print(f"    Spark has better cost: {spark_better:,}")
    print(f"    DuckDB has better cost: {duckdb_better:,}")
    
    print("\n  Sample cost mismatches (first 10):")
    samples = con.execute("""
        SELECT from_edge, to_edge, spark_cost, duckdb_cost, cost_diff, better
        FROM cost_mismatches
        ORDER BY ABS(cost_diff) DESC
        LIMIT 10
    """).fetchall()
    for row in samples:
        print(f"    {row[0]} -> {row[1]}: Spark={row[2]:.4f}, DuckDB={row[3]:.4f}, diff={row[4]:.4f} ({row[5]})")

# Find shortcuts only in Spark
print("\n--- Shortcuts only in Spark ---")
con.execute("""
    CREATE TABLE only_spark AS
    SELECT s.from_edge, s.to_edge, s.cost
    FROM spark_dedup s
    LEFT JOIN duckdb_dedup d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
    WHERE d.from_edge IS NULL
""")
only_spark_count = con.execute("SELECT count(*) FROM only_spark").fetchone()[0]
print(f"  Only in Spark: {only_spark_count:,}")

# Find shortcuts only in DuckDB
print("\n--- Shortcuts only in DuckDB ---")
con.execute("""
    CREATE TABLE only_duckdb AS
    SELECT d.from_edge, d.to_edge, d.cost
    FROM duckdb_dedup d
    LEFT JOIN spark_dedup s ON d.from_edge = s.from_edge AND d.to_edge = s.to_edge
    WHERE s.from_edge IS NULL
""")
only_duckdb_count = con.execute("SELECT count(*) FROM only_duckdb").fetchone()[0]
print(f"  Only in DuckDB: {only_duckdb_count:,}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"  Spark total (dedup): {spark_dedup_count:,}")
print(f"  DuckDB total (dedup): {duckdb_dedup_count:,}")
print(f"  Exact matches: {exact_match_count:,}")
print(f"  Cost mismatches: {mismatch_count:,}")
print(f"  Only in Spark: {only_spark_count:,}")
print(f"  Only in DuckDB: {only_duckdb_count:,}")
print(f"\n  Match rate: {exact_match_count / spark_dedup_count * 100:.2f}%")

con.close()
