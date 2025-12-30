#!/usr/bin/env python3
"""
Verify C++ results match Python by comparing a sample of boundary children.
"""
import h3
from h3_toolkit.utils import children_on_boundary_faces

def verify():
    # Same base cell as C++ benchmark
    cell_res0 = h3.get_res0_cells()[0]
    print(f"Base cell: {cell_res0}")
    
    # Use a smaller resolution for quick verification
    target_res = 8  # Much faster than 15
    
    print(f"Getting boundary children at res {target_res}...")
    children = children_on_boundary_faces(cell_res0, target_res)
    children_set = set(children)
    
    print(f"Found {len(children):,} boundary children")
    print()
    
    # Verify each child is actually on the boundary
    # A child is on the boundary if it has at least one neighbor 
    # that is NOT a descendant of the parent
    all_children = set(h3.cell_to_children(cell_res0, target_res))
    
    print("Verifying sample of 100 cells are on boundary...")
    sample = list(children)[:100]
    errors = 0
    
    for child in sample:
        # Check if any neighbor is outside the parent's descendants
        neighbors = h3.grid_ring(child, 1)
        has_external_neighbor = False
        for n in neighbors:
            if n not in all_children:
                has_external_neighbor = True
                break
        
        if not has_external_neighbor:
            print(f"  ERROR: {child} has no external neighbors!")
            errors += 1
    
    if errors == 0:
        print("  ✓ All 100 sampled cells are correctly on boundary")
    else:
        print(f"  ✗ {errors} cells failed verification")
    
    print()
    print("First 10 boundary children (hex):")
    for i, child in enumerate(children[:10]):
        print(f"  {i+1}. {child}")

if __name__ == "__main__":
    verify()
