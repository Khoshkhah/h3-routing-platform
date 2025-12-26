"""
Test script for comparing optimized vs non-optimized multi-query performance.
"""

import time
from api.ch_query import CHQueryEngine

# Initialize engine
engine = CHQueryEngine(
    shortcuts_path="/home/kaveh/projects/spark-shortest-path/output/Somerset_shortcuts_final",
    edges_path="/home/kaveh/projects/spark-shortest-path/data/Somerset_driving_simplified_edges_with_h3.csv",
    binary_path="/home/kaveh/projects/dijkstra-on-Hierarchy/cpp/build/shortcut_router"
)

# Test cases with different N×M sizes
test_cases = [
    {
        "name": "2×2 (4 combinations)",
        "sources": [100, 200],
        "source_dists": [10.0, 20.0],
        "targets": [300, 400],
        "target_dists": [15.0, 25.0]
    },
    {
        "name": "3×3 (9 combinations)",
        "sources": [100, 200, 500],
        "source_dists": [10.0, 20.0, 30.0],
        "targets": [300, 400, 600],
        "target_dists": [15.0, 25.0, 35.0]
    },
    {
        "name": "5×5 (25 combinations)",
        "sources": [100, 200, 500, 700, 900],
        "source_dists": [10.0, 20.0, 30.0, 40.0, 50.0],
        "targets": [300, 400, 600, 800, 1000],
        "target_dists": [15.0, 25.0, 35.0, 45.0, 55.0]
    }
]

print("=" * 80)
print("Performance Comparison: Optimized vs Non-Optimized Multi-Query")
print("=" * 80)

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print("-" * 80)
    
    # Test non-optimized
    start = time.time()
    result_batch = engine.query_multi(
        source_edges=test["sources"],
        target_edges=test["targets"],
        source_distances=test["source_dists"],
        target_distances=test["target_dists"],
        optimized=False
    )
    time_batch = (time.time() - start) * 1000  # Convert to ms
    
    # Test optimized
    start = time.time()
    result_opt = engine.query_multi(
        source_edges=test["sources"],
        target_edges=test["targets"],
        source_distances=test["source_dists"],
        target_distances=test["target_dists"],
        optimized=True
    )
    time_opt = (time.time() - start) * 1000  # Convert to ms
    
    # Verify results match
    if result_batch.success and result_opt.success:
        distance_match = abs(result_batch.distance - result_opt.distance) < 0.001
        path_match = result_batch.path == result_opt.path
        
        print(f"  Distance (batch):    {result_batch.distance:.3f}m")
        print(f"  Distance (optimized): {result_opt.distance:.3f}m")
        print(f"  Paths match: {path_match}, Path length: {len(result_opt.path)} edges")
        print(f"\n  Non-optimized:")
        print(f"    Total time (Python): {time_batch:.3f} ms")
        print(f"    C++ runtime:         {result_batch.runtime_ms:.3f} ms")
        print(f"  Optimized:")
        print(f"    Total time (Python): {time_opt:.3f} ms")
        print(f"    C++ runtime:         {result_opt.runtime_ms:.3f} ms")
        if result_batch.runtime_ms and result_opt.runtime_ms:
            print(f"\n  C++ Speedup:         {result_batch.runtime_ms / result_opt.runtime_ms:.2f}x")
        
        if not distance_match:
            print(f"  ℹ️  Distance diff: {abs(result_batch.distance - result_opt.distance):.6f}m")
    else:
        print(f"  ❌ Query failed")
        print(f"     Batch: {result_batch.error}")
        print(f"     Optimized: {result_opt.error}")

print("\n" + "=" * 80)
