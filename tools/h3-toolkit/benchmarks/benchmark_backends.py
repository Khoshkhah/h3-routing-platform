#!/usr/bin/env python3
"""
Benchmark comparing Python vs C++ backends for children_on_boundary_faces
"""
import time
import h3

# Configuration
TARGET_RES = 15  # Change this to test different resolutions

def benchmark_python(cell_res0, target_res):
    """Run with pure Python backend"""
    from h3_toolkit.utils import children_on_boundary_faces as py_children
    
    start = time.perf_counter()
    result = py_children(cell_res0, target_res)
    elapsed = time.perf_counter() - start
    
    return result, elapsed

def benchmark_cpp(cell_res0, target_res):
    """Run with C++ backend"""
    try:
        from h3_toolkit._h3_toolkit_cpp import children_on_boundary_faces as cpp_children
    except ImportError as e:
        return None, None, str(e)
    
    start = time.perf_counter()
    result = cpp_children(cell_res0, target_res)
    elapsed = time.perf_counter() - start
    
    return result, elapsed, None

def main():
    print("=" * 60)
    print("H3-Toolkit Backend Benchmark")
    print("=" * 60)
    print()
    
    cell_res0 = h3.get_res0_cells()[0]
    print(f"Base cell: {cell_res0}")
    print(f"Target resolution: {TARGET_RES}")
    print()
    
    # Python benchmark
    print("Running Python backend...")
    py_result, py_time = benchmark_python(cell_res0, TARGET_RES)
    py_count = len(py_result)
    print(f"  Count: {py_count:,}")
    print(f"  Time:  {py_time:.3f}s")
    if py_time > 0:
        print(f"  Rate:  {py_count/py_time:,.0f} cells/sec")
    print()
    
    # C++ benchmark
    print("Running C++ backend...")
    cpp_result, cpp_time, error = benchmark_cpp(cell_res0, TARGET_RES)
    
    if error:
        print(f"  ERROR: {error}")
        print()
        print("To build C++ bindings:")
        print("  cd ~/projects/h3-toolkit")
        print("  rm -rf build && mkdir build && cd build")
        print("  cmake .. && make _h3_toolkit_cpp")
        print("  cp _h3_toolkit_cpp*.so ../src/python/h3_toolkit/")
    else:
        cpp_count = len(cpp_result)
        print(f"  Count: {cpp_count:,}")
        print(f"  Time:  {cpp_time:.3f}s")
        if cpp_time > 0:
            print(f"  Rate:  {cpp_count/cpp_time:,.0f} cells/sec")
        print()
        
        # Comparison
        print("-" * 60)
        if cpp_time > 0 and py_time > 0:
            speedup = py_time / cpp_time
            print(f"C++ is {speedup:.1f}x faster than Python")
        
        results_match = py_count == cpp_count
        print(f"Results match: {results_match}")
        
        if not results_match:
            print()
            print("DEBUG: Checking first 5 results...")
            py_sorted = sorted(py_result)[:5]
            cpp_sorted = sorted(cpp_result)[:5]
            print(f"  Python: {py_sorted}")
            print(f"  C++:    {cpp_sorted}")

if __name__ == "__main__":
    main()
