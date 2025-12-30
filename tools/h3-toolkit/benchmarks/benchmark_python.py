#!/usr/bin/env python3
"""
Benchmark: children_on_boundary_faces from res 0 to res 15
"""
import time
import h3
from h3_toolkit.utils import children_on_boundary_faces

def benchmark():
    # Get a resolution 0 cell (base cell)
    # There are 122 base cells, pick one
    cell_res0 = h3.get_res0_cells()[0]
    print(f"Base cell: {cell_res0}")
    print(f"Resolution: {h3.get_resolution(cell_res0)}")
    print()
    
    target_res = 15
    
    print(f"Computing boundary children from res 0 to res {target_res}...")
    print("This may take a while...")
    print()
    
    start_time = time.perf_counter()
    
    boundary_children = children_on_boundary_faces(cell_res0, target_res)
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    print(f"Results:")
    print(f"  Number of boundary children: {len(boundary_children):,}")
    print(f"  Time elapsed: {elapsed:.3f} seconds")
    print(f"  Rate: {len(boundary_children) / elapsed:,.0f} cells/second")

if __name__ == "__main__":
    benchmark()
