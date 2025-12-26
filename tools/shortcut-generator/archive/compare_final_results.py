import duckdb
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CompareFinal")

def main():
    con = duckdb.connect(':memory:')
    
    duckdb_output = "/home/kaveh/projects/road-to-shortcut-duckdb/output/Burnaby_shortcuts"
    spark_output = "/home/kaveh/projects/road-to-shortcut/output/Burnaby_spark_hybrid"
    
    logger.info("Loading DuckDB output...")
    con.execute(f"CREATE TABLE duck_final AS SELECT * FROM read_parquet('{duckdb_output}')")
    
    logger.info("Loading Spark output...")
    # Spark output is a directory of parquets
    con.execute(f"CREATE TABLE spark_final AS SELECT * FROM read_parquet('{spark_output}/*.parquet')")
    
    # Raw Counts
    duck_raw = con.execute("SELECT count(*) FROM duck_final").fetchone()[0]
    spark_raw = con.execute("SELECT count(*) FROM spark_final").fetchone()[0]
    
    logger.info(f"Raw Counts -> DuckDB: {duck_raw:,} | Spark: {spark_raw:,}")

    # Deduplicated Counts (MIN cost per pair)
    logger.info("Deduplicating...")
    # For DuckDB and Spark, we need to handle ties for via_edge if any
    con.execute("""
        CREATE TABLE duck_dedup AS 
        SELECT from_edge, to_edge, cost, via_edge
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY from_edge, to_edge ORDER BY cost ASC) as rn
            FROM duck_final
        ) WHERE rn = 1
    """)
    con.execute("""
        CREATE TABLE spark_dedup AS 
        SELECT from_edge, to_edge, cost, via_edge
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY from_edge, to_edge ORDER BY cost ASC) as rn
            FROM spark_final
        ) WHERE rn = 1
    """)
    
    duck_dedup_count = con.execute("SELECT count(*) FROM duck_dedup").fetchone()[0]
    spark_dedup_count = con.execute("SELECT count(*) FROM spark_dedup").fetchone()[0]
    
    logger.info("="*60)
    logger.info(f"{'METRIC':<20} | {'DUCKDB':<15} | {'SPARK':<15} | {'DIFF':<10}")
    logger.info("-"*60)
    logger.info(f"{'Deduplicated Count':<20} | {duck_dedup_count:<15,} | {spark_dedup_count:<15,} | {duck_dedup_count - spark_dedup_count:<10,}")
    logger.info("="*60)

    # Intersection analysis
    logger.info("Analyzing differences...")
    
    # Missing in DuckDB
    missing_in_duck = con.execute("""
        SELECT count(*) FROM spark_dedup s
        LEFT JOIN duck_dedup d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
        WHERE d.from_edge IS NULL
    """).fetchone()[0]
    
    # Missing in Spark
    missing_in_spark = con.execute("""
        SELECT count(*) FROM duck_dedup d
        LEFT JOIN spark_dedup s ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
        WHERE s.from_edge IS NULL
    """).fetchone()[0]
    
    logger.info(f"Pairs missing in DuckDB: {missing_in_duck:,}")
    logger.info(f"Pairs missing in Spark: {missing_in_spark:,}")
    
    # Cost discrepancies for common pairs
    diff_stats = con.execute("""
        SELECT 
            count(*) filter (where s.cost < d.cost - 1e-9) as spark_lower,
            count(*) filter (where d.cost < s.cost - 1e-9) as duck_lower,
            avg(abs(s.cost - d.cost)) as avg_abs_diff,
            max(abs(s.cost - d.cost)) as max_abs_diff
        FROM spark_dedup s
        JOIN duck_dedup d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
        WHERE abs(s.cost - d.cost) > 1e-9
    """).fetchone()
    
    logger.info(f"Common pairs with Spark lower cost: {diff_stats[0]:,}")
    logger.info(f"Common pairs with DuckDB lower cost: {diff_stats[1]:,}")
    logger.info(f"Average cost difference: {diff_stats[2]:.6f}")
    logger.info(f"Maximum cost difference: {diff_stats[3]:.6f}")

    if diff_stats[0] > 0:
        logger.info("\nTop 5 Shortcuts where DuckDB is sub-optimal:")
        examples = con.execute("""
            SELECT s.from_edge, s.to_edge, s.cost as spark_cost, s.via_edge as spark_via,
                   d.cost as duck_cost, d.via_edge as duck_via,
                   (d.cost - s.cost) as extra_cost
            FROM spark_dedup s
            JOIN duck_dedup d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
            WHERE d.cost > s.cost + 1e-9
            ORDER BY extra_cost DESC
            LIMIT 5
        """).df()
        print(examples)

if __name__ == "__main__":
    main()
