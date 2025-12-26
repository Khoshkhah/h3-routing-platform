import duckdb

def main():
    con = duckdb.connect(':memory:')
    con.execute("CREATE TABLE spark AS SELECT * FROM read_parquet('/home/kaveh/projects/road-to-shortcut/output/Burnaby_spark_hybrid/*.parquet')")
    
    def get_path(f, t, visited=None):
        if visited is None: visited = set()
        if (f, t) in visited: return ["LOOP"]
        visited.add((f, t))
        
        res = con.execute(f"SELECT via_edge, cost FROM spark WHERE from_edge={f} AND to_edge={t}").fetchone()
        if not res: return [f"({f}->{t} MISSING)"]
        v, c = res
        if v == t: return [f"{f}->{t}"]
        return get_path(f, v, visited) + get_path(v, t, visited)

    print("Path for 31283 -> 31282:")
    path = get_path(31283, 31282)
    print(" -> ".join(path))

if __name__ == "__main__":
    main()
