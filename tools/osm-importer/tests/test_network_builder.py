import pytest
import pandas as pd
import networkx as nx
from shapely.geometry import LineString, Point
import sys
import os

# Add src to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.network_builder import NetworkBuilder

class TestNetworkBuilder:
    
    @pytest.fixture
    def builder(self):
        # Initialize with dummy arguments since we are mocking the graph
        # build_graph normally uses pbf_file, but we are skipping that.
        dummy_pbf = "dummy.osm.pbf"
        dummy_name = "test_output"
        return NetworkBuilder(dummy_pbf, dummy_name)

    def test_geometry_reversal_logic(self, builder):
        """
        Regression Test: Verifies that edges in the reverse direction 
        have their LINESTRING geometry reversed to match the flow 
        from 'source' to 'target'.
        """
        # 1. Setup Nodes
        # Node 1 at (0,0), Node 2 at (10,10)
        # nodes_df expects 'geometry' column with Point objects, indexed by node ID
        nodes_data = {
            'id': [1, 2],
            'geometry': [Point(0,0), Point(10,10)]
        }
        builder.nodes_df = pd.DataFrame(nodes_data).set_index('id')
        
        # 2. Setup Edges
        geom_a_to_b = LineString([(0,0), (5,5), (10,10)])
        
        # Case 1: Forward edge (1->2). Node 1=(0,0). Geom starts at (0,0). 
        # Should remain unchanged.
        
        # Case 2: Reverse edge (2->1). Node 2=(10,10). Geom starts at (0,0).
        # This MISMATCH means the geometry is backwards relative to the edge direction.
        # The fix should reverse this geometry.
        
        edges_data = {
            'source': [1, 2],
            'target': [2, 1],
            'geometry': [geom_a_to_b, geom_a_to_b], 
            'length': [100.0, 100.0],
            'maxspeed': [50, 50],
            'highway': ['residential', 'residential']
        }
        builder.edges_df = pd.DataFrame(edges_data)
        
        # 3. Action: Run the fix method directly
        # It operates in-place on builder.edges_df
        builder._fix_geometry_directions()
        
        # 4. Verification
        fixed_df = builder.edges_df
        
        # Check Forward Edge (1 -> 2)
        # Should strictly start at Node 1 (0,0) and end at Node 2 (10,10)
        fwd_edge = fixed_df[(fixed_df['source'] == 1) & (fixed_df['target'] == 2)].iloc[0]
        assert fwd_edge['geometry'].coords[0] == (0.0, 0.0), "Forward edge start point incorrect"
        assert fwd_edge['geometry'].coords[-1] == (10.0, 10.0), "Forward edge end point incorrect"
        
        # Check Reverse Edge (2 -> 1)
        # Should strictly start at Node 2 (10,10) and end at Node 1 (0,0)
        rev_edge = fixed_df[(fixed_df['source'] == 2) & (fixed_df['target'] == 1)].iloc[0]
        
        # CRITICAL ASSERTION: The geometry must be reversed compared to input
        print(f"Reverse Edge Geom: {rev_edge['geometry']}")
        assert rev_edge['geometry'].coords[0] == (10.0, 10.0), "Reverse edge should start at Node 2"
    def test_geometry_consistency(self, builder):
        """
        Comprehensive Geometry Test:
        1. Access the produced edges after _fix_geometry_directions.
        2. Verify no self-loop edges (source != target).
        3. Verify Edge Geometry matches Node Geometry at endpoints.
        4. Verify Connectivity: If Edge A->B and Edge B->C exist, 
           the end of A->B match the start of B->C.
        """
        # 1. Setup a chain of nodes: 1 -> 2 -> 3
        # Node 1 at (0,0), Node 2 at (10,10), Node 3 at (20,0)
        nodes_data = {
            'id': [1, 2, 3],
            'geometry': [Point(0,0), Point(10,10), Point(20,0)]
        }
        builder.nodes_df = pd.DataFrame(nodes_data).set_index('id')
        
        # Geometries
        # Edge 1->2 (Forward) matches flow
        geom_1_2 = LineString([(0,0), (5,5), (10,10)])
        
        # Edge 2->3 (Forward) matches flow
        geom_2_3 = LineString([(10,10), (15,5), (20,0)])
        
        # Edge 3->2 (Reverse) - INITIALLY BACKWARDS (starts at 2, ends at 3)
        # This simulates the problematic case we want to ensure is NOT in the final output
        # If we passed this as-is without fixing, it would be wrong.
        # But here we pass the WRONG geometry to see if fix logic handles it,
        # OR we just test that a valid graph maintains consistency.
        # Let's test checking logic: We assume _fix_geometry_directions has run.
        # So we pass "Correct" geometries to simulate a processed graph 
        # (or pass incorrect ones and run the fix first).
        
        # Let's run the fix first to be safe, simulating full pipeline
        geom_3_2_raw = LineString([(10,10), (15,5), (20,0)]) # Backwards geometry for 3->2
        
        valid_edges_data = {
            'source': [1, 2, 3],
            'target': [2, 3, 2],
            # 1->2 (good), 2->3 (good), 3->2 (needs flip)
            'geometry': [geom_1_2, geom_2_3, geom_3_2_raw], 
            'length': [100.0, 100.0, 100.0],
            'maxspeed': [50, 50, 50],
            'highway': ['residential', 'residential', 'residential']
        }
        builder.edges_df = pd.DataFrame(valid_edges_data)
        
        # Run cleanup
        builder._fix_geometry_directions()
        edges = builder.edges_df
        
        # --- VERIFICATION ---
        
        # 1. No Parallel/Self-loop edges (Start != End)
        # Verify EVERY edge has different source and target
        for idx, row in edges.iterrows():
            assert row['source'] != row['target'], \
                f"Edge {idx} is a self-loop! Source {row['source']} == Target {row['target']}"
        
        print("Self-loop check passed: All edges connect distinct nodes.")
        
        # 2. Nodes have unique geometry (No overlapping nodes)
        node_geoms = builder.nodes_df['geometry'].apply(lambda p: (p.x, p.y))
        duplicates = node_geoms[node_geoms.duplicated()]
        assert len(duplicates) == 0, f"Found duplicate node geometries: {duplicates}"
        print("Node Uniqueness check passed: All nodes have distinct coordinates.")

        # 3. Edge Geometry Matches Node Geometry
        # Iterate over all edges
        for idx, row in edges.iterrows():
            u, v = row['source'], row['target']
            geom = row['geometry']
            
            # Lookup Node Geometries
            u_pt = builder.nodes_df.loc[u, 'geometry']
            v_pt = builder.nodes_df.loc[v, 'geometry']
            
            # Assert Start Matches Source Node
            assert geom.coords[0] == (u_pt.x, u_pt.y), \
                f"Edge {u}->{v} start {geom.coords[0]} != Node {u} {u_pt}"
                
            # Assert End Matches Target Node
            assert geom.coords[-1] == (v_pt.x, v_pt.y), \
                f"Edge {u}->{v} end {geom.coords[-1]} != Node {v} {v_pt}"

        # 3. Connectivity Matches (A->B End == B->C Start)
        # Check connection at Node 2:  (1->2) and (2->3)
        edge_1_2 = edges[(edges['source'] == 1) & (edges['target'] == 2)].iloc[0]
        edge_2_3 = edges[(edges['source'] == 2) & (edges['target'] == 3)].iloc[0]
        
        # The End of 1->2 must match Start of 2->3
        end_1_2 = edge_1_2['geometry'].coords[-1]
        start_2_3 = edge_2_3['geometry'].coords[0]
        
        assert end_1_2 == start_2_3, \
            f"Gap at Node 2! Edge 1->2 ends at {end_1_2}, Edge 2->3 starts at {start_2_3}"
            
        print("Geometry Consistency Verified: Nodes match endpoints, connectivity is continuous.")
