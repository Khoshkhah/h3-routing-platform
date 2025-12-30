#!/usr/bin/env python3
"""
Generate a table showing boundary children count and polygon complexity
for cells at each resolution with children at a target resolution.
"""
import h3
import time
from h3_toolkit import children_on_boundary_faces, get_backend
from h3_toolkit.geom import cell_boundary_from_children
from shapely.geometry import shape

# Configuration - use 10 for reasonable speed, 15 for complete data
TARGET_RES = 10

def main():
    print(f"Using backend: {get_backend()}")
    print(f"Target resolution: {TARGET_RES}")
    print()
    
    # Get a sample cell at each resolution
    base_cell = h3.get_res0_cells()[0]
    
    print("| Parent Res | Boundary Children | Polygon Vertices | Time (s) |")
    print("|------------|-------------------|------------------|----------|")
    
    results = []
    
    for parent_res in range(0, TARGET_RES):
        # Get cell at this resolution
        if parent_res == 0:
            cell = base_cell
        else:
            cell = h3.cell_to_children(base_cell, parent_res).pop()
        
        start = time.perf_counter()
        
        # Get boundary children
        children = children_on_boundary_faces(cell, TARGET_RES)
        num_children = len(children)
        
        # Get polygon and count vertices
        geojson = cell_boundary_from_children(cell, TARGET_RES)
        polygon = shape(geojson['geometry'])
        
        if polygon.geom_type == 'Polygon':
            num_vertices = len(polygon.exterior.coords) - 1
        else:
            num_vertices = sum(len(p.exterior.coords) - 1 for p in polygon.geoms)
        
        elapsed = time.perf_counter() - start
        
        print(f"| {parent_res:10} | {num_children:17,} | {num_vertices:16,} | {elapsed:8.2f} |")
        results.append((parent_res, num_children, num_vertices, elapsed))
    
    print()
    print("Summary:")
    print(f"  Resolution 0 cell has {results[0][1]:,} boundary children at res {TARGET_RES}")
    print(f"  Resolution {TARGET_RES-1} cell has {results[-1][1]:,} boundary children at res {TARGET_RES}")

if __name__ == "__main__":
    main()

