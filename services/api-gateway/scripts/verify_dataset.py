
import pandas as pd
import pyarrow.parquet as pq
import sys
import os

def check_dataset(name, edges_path, shortcuts_path):
    print(f"Checking {name}...")
    
    # Check Edges
    if not os.path.exists(edges_path):
        print(f"  Edges file missing: {edges_path}")
        return
        
    try:
        # Just read the 'id' column to be fast
        df_edges = pd.read_csv(edges_path, usecols=['id'])
        edge_ids = df_edges['id']
        print(f"  Edges: count={len(edge_ids)}, min={edge_ids.min()}, max={edge_ids.max()}, unique={edge_ids.nunique()}")
        
        if len(edge_ids) != edge_ids.nunique():
            print("  WARNING: Duplicate edge IDs in CSV!")
            
    except Exception as e:
        print(f"  Error reading edges: {e}")

    # Check Shortcuts (Graph references)
    if not os.path.exists(shortcuts_path):
        print(f"  Shortcuts path missing: {shortcuts_path}")
        return

    try:
        # Parquet might be a directory
        dataset = pq.ParquetDataset(shortcuts_path)
        table = dataset.read()
        print(f"  Shortcuts columns: {table.column_names}")
        
        num_rows = table.num_rows
        print(f"  Shortcuts total rows: {num_rows}")
        
        if 'via_edge' in table.column_names:
            via = table['via_edge'].to_pandas()
            # Handle possible floats/nulls
            via = via.fillna(0)
            non_zero = via[via != 0].count()
            max_via = via.max()
            print(f"  via_edge stats: total={len(via)}, non_zero={non_zero} ({non_zero/len(via)*100:.1f}%), max={max_via}")

            # Check incoming/outgoing ranges
            inc = table['incoming_edge'].to_pandas()
            out = table['outgoing_edge'].to_pandas()
            print(f"  incoming range: min={inc.min()}, max={inc.max()}")
            print(f"  outgoing range: min={out.min()}, max={out.max()}")
        else:
            print("  via_edge column missing!")
            
    except Exception as e:
        print(f"  Error reading shortcuts: {e}")

    except Exception as e:
        print(f"  Error reading shortcuts: {e}")
    print("-" * 40)

if __name__ == "__main__":
    base_dir = "data"
    check_dataset("burnaby", f"{base_dir}/burnaby/edges.csv", f"{base_dir}/burnaby/shortcuts.parquet")
    check_dataset("somerset", f"{base_dir}/somerset/edges.csv", f"{base_dir}/somerset/shortcuts.parquet")
    check_dataset("all_vancouver", f"{base_dir}/all_vancouver/edges.csv", f"{base_dir}/all_vancouver/shortcuts.parquet")
