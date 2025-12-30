#!/usr/bin/env python3
"""
Benchmark: C++ bindings (pybind11)
"""
import time
import h3
from h3_toolkit._h3_toolkit_cpp import children_on_boundary_faces

TARGET_RES = 15

def main():
    print("=" * 50)
    print("C++ BINDINGS (pybind11) Benchmark")
    print("=" * 50)
    
    cell_res0 = h3.get_res0_cells()[0]
    print(f"Base cell: {cell_res0}")
    print(f"Target resolution: {TARGET_RES}")
    print()
    print("Computing...")
    
    start = time.perf_counter()
    result = children_on_boundary_faces(cell_res0, TARGET_RES)
    elapsed = time.perf_counter() - start
    
    print(f"Count: {len(result):,}")
    print(f"Time:  {elapsed:.3f} seconds")
    print(f"Rate:  {len(result)/elapsed:,.0f} cells/sec")

if __name__ == "__main__":
    main()
