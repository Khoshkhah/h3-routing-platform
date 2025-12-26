#!/usr/bin/env python3
"""
Test script for CH Query SDK.

Demonstrates both single query and multi-query capabilities.
"""

from api.ch_query import CHQueryEngine
import time


def main():
    print("=== Contraction Hierarchy Query SDK Test ===\n")
    
    # Initialize engine
    engine = CHQueryEngine(
        shortcuts_path="/home/kaveh/projects/spark-shortest-path/output/Burnaby_shortcuts_final",
        edges_path="/home/kaveh/projects/osm-to-road-network/data/output/Burnaby_driving_simplified_edges_with_h3.csv",
        binary_path="/home/kaveh/projects/dijkstra-on-Hierarchy/cpp/build/shortcut_router"
    )
    
    print("1. Testing single query...")
    print("-" * 50)
    
    start = time.time()
    result = engine.query(source=9219, target=24723)
    elapsed = time.time() - start
    
    if result.success:
        print(f"✓ Success!")
        print(f"  Distance: {result.distance:.2f}m")
        print(f"  Runtime: {result.runtime_ms:.2f}ms")
        print(f"  Path length: {len(result.path)} edges")
        print(f"  Path: {' → '.join(map(str, result.path[:5]))} ... {' → '.join(map(str, result.path[-3:]))}")
        print(f"  Total time (including Python overhead): {elapsed*1000:.2f}ms")
    else:
        print(f"✗ Failed: {result.error}")
    
    print("\n2. Testing multi-source multi-target query...")
    print("-" * 50)
    
    # Simulate finding nearest edges to start/end points
    source_edges = [23133, 30928, 8540]
    source_dists = [10.5, 15.2, 20.8]  # Distance from origin to each edge
    
    target_edges = [8543, 8544, 8545]
    target_dists = [12.3, 18.7, 25.1]  # Distance from each edge to destination
    
    print(f"Source candidates: {source_edges} (distances: {source_dists})")
    print(f"Target candidates: {target_edges} (distances: {target_dists})")
    print(f"Total combinations: {len(source_edges)} × {len(target_edges)} = {len(source_edges) * len(target_edges)}\n")
    
    start = time.time()
    result = engine.query_multi(
        source_edges=source_edges,
        target_edges=target_edges,
        source_distances=source_dists,
        target_distances=target_dists
    )
    elapsed = time.time() - start
    
    if result.success:
        print(f"✓ Success!")
        print(f"  Total distance (origin → edge → path → edge → dest): {result.distance:.2f}m")
        print(f"  Runtime: {result.runtime_ms:.2f}ms")
        print(f"  Path length: {len(result.path)} edges")
        print(f"  Path: {' → '.join(map(str, result.path))}")
        print(f"  Total time (including Python overhead): {elapsed*1000:.2f}ms")
        print(f"\n  Note: This tested {len(source_edges) * len(target_edges)} combinations in ONE query!")
    else:
        print(f"✗ Failed: {result.error}")
    
    print("\n3. Comparing efficiency...")
    print("-" * 50)
    print(f"Multi-query tested {len(source_edges) * len(target_edges)} paths in {elapsed*1000:.2f}ms")
    print(f"That's approximately {elapsed*1000 / (len(source_edges) * len(target_edges)):.2f}ms per path")
    print(f"vs ~{elapsed*1000:.2f}ms for a single query using separate processes")
    print(f"\nSpeedup: ~{(len(source_edges) * len(target_edges)) * elapsed / elapsed:.1f}x faster!")


if __name__ == "__main__":
    main()
