import pandas as pd
from shapely import wkt
from shapely.geometry import Point
import sys
import os

def validate_somerset_geometry():
    print("Loading Somerset dataset...")
    
    # Paths to processed data
    # Adjust paths if necessary based on your exact file structure
    base_dir = "tools/osm-importer/data/output/Somerset"
    edges_path = os.path.join(base_dir, "Somerset_driving_simplified_edges_with_h3.csv")
    nodes_path = os.path.join(base_dir, "Somerset_driving_simplified_nodes.csv")
    
    if not os.path.exists(edges_path) or not os.path.exists(nodes_path):
        print(f"Error: Data files not found in {base_dir}")
        return

    # Load DataFrames
    edges_df = pd.read_csv(edges_path)
    nodes_df = pd.read_csv(nodes_path)
    
    # Load ID mapping to get source/target
    id_map_path = os.path.join(base_dir, "Somerset_driving_edge_id.csv")
    if not os.path.exists(id_map_path):
        print(f"Error: ID mapping file not found at {id_map_path}")
        return
        
    print("Loading edge ID mapping...")
    id_map_df = pd.read_csv(id_map_path)
    
    # id_map_df has columns: 'id' (string tuple), 'index' (int)
    # Parse the string tuple "(u, v)" -> source, target
    import ast
    
    print("Parsing edge definitions...")
    # Create a dictionary for fast lookup: index -> (u, v)
    edge_connectivity = {}
    for _, row in id_map_df.iterrows():
        # strict=True ensures it's a valid literal
        u, v = ast.literal_eval(row['id']) 
        edge_connectivity[row['index']] = (u, v)
        
    # Map back to edges_df
    # edges_df has 'edge_index' which corresponds to 'index' in id_map
    if 'edge_index' not in edges_df.columns:
        # Fallback if column name is different
        if 'id' in edges_df.columns:
            edges_df['edge_index'] = edges_df['id']
        else:
            print("Error: edges_df missing 'edge_index' column")
            return

    # Assign source/target columns
    edges_df['source'] = edges_df['edge_index'].apply(lambda x: edge_connectivity.get(x, (None, None))[0])
    edges_df['target'] = edges_df['edge_index'].apply(lambda x: edge_connectivity.get(x, (None, None))[1])
    
    source_col = 'source'
    target_col = 'target'
    
    # Filter out any edges where mapping failed (shouldn't happen)
    valid_mask = edges_df['source'].notna()
    if (~valid_mask).any():
        print(f"Warning: {len(edges_df) - valid_mask.sum()} edges could not be mapped to source/target nodes.")
        edges_df = edges_df[valid_mask]


    print("Parsing geometries...")
    # Parse WKT geometries
    edges_df['geometry'] = edges_df['geometry'].apply(wkt.loads)
    nodes_df['geometry'] = nodes_df['geometry'].apply(wkt.loads)
    
    # Index nodes by ID for fast lookup
    nodes_df.set_index('id', inplace=True)
    
    print("--- VALIDATION STARTED ---")
    
    # 1. No Self-Loops
    self_loops = edges_df[edges_df[source_col] == edges_df[target_col]]
    if len(self_loops) > 0:
        print(f"FAIL: Found {len(self_loops)} self-loop edges.")
        # print(self_loops.head())
    else:
        print("PASS: No self-loop edges found.")
        
    # 2. Unique Node Geometries
    node_geoms = nodes_df['geometry'].apply(lambda p: (p.x, p.y))
    duplicates = node_geoms[node_geoms.duplicated()]
    if len(duplicates) > 0:
        print(f"FAIL: Found {len(duplicates)} duplicate node geometries.")
        # print(duplicates.head())
    else:
        print("PASS: All nodes have distinct coordinates.")
        
    # 3. Geometry Consistency (Edge endpoints match Nodes)
    mismatches = 0
    checked_count = 0
    
    for idx, row in edges_df.iterrows():
        u = row[source_col]
        v = row[target_col]
        
        if u not in nodes_df.index or v not in nodes_df.index:
            # This might happen if nodes were pruned but edges kept (shouldn't happen in valid output)
            continue
            
        u_pt = nodes_df.loc[u, 'geometry']
        v_pt = nodes_df.loc[v, 'geometry']
        edge_geom = row['geometry']
        
        start_match = (edge_geom.coords[0] == (u_pt.x, u_pt.y))
        end_match = (edge_geom.coords[-1] == (v_pt.x, v_pt.y))
        
        if not start_match or not end_match:
            mismatches += 1
            if mismatches < 5: # Print first few errors
                print(f"Mismatch at edge {idx} ({u}->{v}):")
                if not start_match: print(f"  Start: Edge {edge_geom.coords[0]} != Node {u_pt}")
                if not end_match:   print(f"  End:   Edge {edge_geom.coords[-1]} != Node {v_pt}")
        
        checked_count += 1
        
    if mismatches > 0:
        print(f"FAIL: Found {mismatches} edges with mismatched geometry endpoints (out of {checked_count}).")
    else:
        print(f"PASS: All {checked_count} checked edges match their node endpoints.")

    print("--- VALIDATION COMPLETED ---")

if __name__ == "__main__":
    validate_somerset_geometry()
