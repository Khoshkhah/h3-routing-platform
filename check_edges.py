import pandas as pd
from shapely import wkt

csv_path = "tools/osm-importer/data/output/Somerset/Somerset_driving_simplified_edges_with_h3.csv"
df = pd.read_csv(csv_path)

# Ensure ID column is handled
if 'id' not in df.columns and 'edge_index' in df.columns:
    df = df.rename(columns={'edge_index': 'id'})

edges_to_check = [1169, 2091, 1170, 2090]

for edge_id in edges_to_check:
    try:
        row = df[df['id'] == edge_id].iloc[0]
        print(f"--- EDGE {edge_id} ---")
        print(f"  Length: {row.get('length', 'N/A')}")
        print(f"  Cost: {row.get('cost', 'N/A')}")
        print(f"  to_cell: {row.get('to_cell', 'N/A')}")
        print(f"  from_cell: {row.get('from_cell', 'N/A')}")
        print(f"  lca_res: {row.get('lca_res', 'N/A')}")
        print(f"  Geometry: {row.get('geometry', 'N/A')}")
        print()
    except IndexError:
        print(f"--- EDGE {edge_id} ---")
        print(f"  NOT FOUND")
        print()
