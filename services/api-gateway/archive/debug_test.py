"""Quick debug test."""
import logging
from api.ch_query import CHQueryEngine

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

engine = CHQueryEngine(
    shortcuts_path="/home/kaveh/projects/spark-shortest-path/output/Somerset_shortcuts_final",
    edges_path="/home/kaveh/projects/spark-shortest-path/data/Somerset_driving_simplified_edges_with_h3.csv",
    binary_path="/home/kaveh/projects/dijkstra-on-Hierarchy/cpp/build/shortcut_router"
)

# Test non-optimized
result = engine.query_multi(
    source_edges=[100, 200],
    target_edges=[300, 400],
    source_distances=[10.0, 20.0],
    target_distances=[15.0, 25.0],
    optimized=False
)

print(f"Non-optimized result:")
print(f"  Success: {result.success}")
print(f"  Distance: {result.distance}")
print(f"  Runtime: {result.runtime_ms} ms")
print(f"  Path: {result.path}")

# Test optimized
result_opt = engine.query_multi(
    source_edges=[100, 200],
    target_edges=[300, 400],
    source_distances=[10.0, 20.0],
    target_distances=[15.0, 25.0],
    optimized=True
)

print(f"\nOptimized result:")
print(f"  Success: {result_opt.success}")
print(f"  Distance: {result_opt.distance}")
print(f"  Runtime: {result_opt.runtime_ms} ms")
print(f"  Path: {result_opt.path}")
