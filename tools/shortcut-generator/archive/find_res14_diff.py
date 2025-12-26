import duckdb
import pandas as pd

def find_differences():
    con = duckdb.connect(':memory:')
    
    duck_csv = "/home/kaveh/projects/road-to-shortcut-duckdb/output/duckdb_res14_debug.csv"
    spark_csv = "/home/kaveh/projects/road-to-shortcut/output/spark_res14_debug.csv"
    
    # Load both CSVs
    con.execute(f"CREATE TABLE duck_res AS SELECT * FROM read_csv_auto('{duck_csv}')")
    con.execute(f"CREATE TABLE spark_res AS SELECT * FROM read_csv_auto('{spark_csv}')")
    
    print(f"DuckDB table count: {con.execute('SELECT count(*) FROM duck_res').fetchone()[0]}")
    print(f"Spark table count: {con.execute('SELECT count(*) FROM spark_res').fetchone()[0]}")
    
    print(f"DuckDB unique pairs: {con.execute('SELECT count(*) FROM (SELECT DISTINCT from_edge, to_edge FROM duck_res)').fetchone()[0]}")
    print(f"Spark unique pairs: {con.execute('SELECT count(*) FROM (SELECT DISTINCT from_edge, to_edge FROM spark_res)').fetchone()[0]}")
    
    print("\nDetails of duplicates in Spark (same from_edge, to_edge but different cost/via):")
    spark_dupes = con.execute("""
        SELECT from_edge, to_edge, count(*) as cnt
        FROM spark_res
        GROUP BY from_edge, to_edge
        HAVING cnt > 1
    """).df()
    print(spark_dupes)
    
    if len(spark_dupes) > 0:
        print("\nFull info for those duplicates in Spark:")
        for _, row in spark_dupes.iterrows():
            f, t = row['from_edge'], row['to_edge']
            print(f"\nPair ({f}, {t}):")
            print(con.execute(f"SELECT * FROM spark_res WHERE from_edge={f} AND to_edge={t}").df())
            print(f"DuckDB value for this pair:")
            print(con.execute(f"SELECT * FROM duck_res WHERE from_edge={f} AND to_edge={t}").df())
    diff_spark = con.execute("""
        SELECT s.from_edge, s.to_edge, s.cost as spark_cost, s.via_edge as spark_via
        FROM spark_res s
        LEFT JOIN duck_res d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
        WHERE d.from_edge IS NULL
    """).df()
    print(f"Total missing in DuckDB: {len(diff_spark)}")
    print(diff_spark)

    print("\nFinding shortcuts present in DuckDB but missing in Spark...")
    diff_duck = con.execute("""
        SELECT d.from_edge, d.to_edge, d.cost as duck_cost, d.via_edge as duck_via
        FROM duck_res d
        LEFT JOIN spark_res s ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
        WHERE s.from_edge IS NULL
    """).df()
    print(f"Total missing in Spark: {len(diff_duck)}")
    print(diff_duck)
    
    print("\nChecking if costs are different for existing shortcuts...")
    cost_diff = con.execute("""
        SELECT s.from_edge, s.to_edge, s.cost as spark_cost, d.cost as duck_cost,
               abs(s.cost - d.cost) as diff
        FROM spark_res s
        JOIN duck_res d ON s.from_edge = d.from_edge AND s.to_edge = d.to_edge
        WHERE abs(s.cost - d.cost) > 1e-12
    """).df()
    
    if len(cost_diff) > 0:
        print(f"Total shortcuts with cost difference: {len(cost_diff)}")
        print(cost_diff.head())
    else:
        print("No cost differences found for existing shortcuts.")

if __name__ == "__main__":
    find_differences()
