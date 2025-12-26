#!/usr/bin/env python3
"""
Performance Comparison: Subprocess vs HTTP API

This script compares the performance of the old subprocess-based approach
versus the new persistent C++ HTTP server.
"""

import time
import subprocess
import requests
import sys
from pathlib import Path

def time_subprocess_approach(binary_path: str, num_queries: int = 10) -> float:
    """Time the old subprocess approach."""
    if not Path(binary_path).exists():
        print(f"⚠️  Binary not found: {binary_path}")
        return float('inf')

    total_time = 0.0

    for i in range(num_queries):
        start_time = time.time()

        # Simulate a routing query (this would be the actual binary call)
        # For demo purposes, we'll just sleep to simulate processing time
        try:
            result = subprocess.run(
                [binary_path, "query", "burnaby", "49.123", "-123.456", "49.789", "-123.012"],
                capture_output=True,
                text=True,
                timeout=30
            )
            end_time = time.time()
            total_time += (end_time - start_time)
        except subprocess.TimeoutExpired:
            print(f"❌ Query {i+1} timed out")
            return float('inf')
        except Exception as e:
            print(f"❌ Query {i+1} failed: {e}")
            return float('inf')

    return total_time / num_queries

def time_http_approach(server_url: str, num_queries: int = 10) -> float:
    """Time the new HTTP approach."""
    client = requests.Session()
    total_time = 0.0

    payload = {
        "dataset": "burnaby",
        "start_lat": 49.123,
        "start_lng": -123.456,
        "end_lat": 49.789,
        "end_lng": -123.012,
        "search_radius": 1000.0,
        "max_candidates": 10
    }

    for i in range(num_queries):
        start_time = time.time()

        try:
            response = client.post(f"{server_url}/route", json=payload, timeout=10)
            response.raise_for_status()
            end_time = time.time()
            total_time += (end_time - start_time)
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTP query {i+1} failed: {e}")
            return float('inf')

    return total_time / num_queries

def run_comparison():
    """Run performance comparison between old and new approaches."""

    print("⚡ Routing Pipeline v2 - Performance Comparison")
    print("=" * 60)

    # Configuration
    binary_path = "../dijkstra-on-Hierarchy/build/ch_query"  # Adjust path as needed
    server_url = "http://localhost:8080"
    num_queries = 5

    print(f"Running {num_queries} queries for each approach...")
    print()

    # Test subprocess approach
    print("🐌 Testing subprocess approach...")
    subprocess_time = time_subprocess_approach(binary_path, num_queries)

    if subprocess_time == float('inf'):
        print("❌ Subprocess approach failed or binary not found")
        subprocess_time = None
    else:
        print(".2f")

    # Test HTTP approach
    print("\n🚀 Testing HTTP approach...")
    http_time = time_http_approach(server_url, num_queries)

    if http_time == float('inf'):
        print("❌ HTTP approach failed (server not running?)")
        http_time = None
    else:
        print(".2f")

    # Results
    print("\n📊 Results:")
    print("-" * 30)

    if subprocess_time and http_time:
        speedup = subprocess_time / http_time
        print(".2f")
        print(".2f")
        print(".0f")

        if speedup >= 20:
            print("🎉 Excellent! Achieved target 20x+ performance improvement!")
        elif speedup >= 10:
            print("👍 Good! Significant performance improvement achieved.")
        else:
            print("🤔 Modest improvement. Check server optimization opportunities.")
    else:
        print("❌ Cannot compare - one or both approaches failed")

    print("\n💡 Tips:")
    print("- Make sure the C++ server is running: cd routing-server-v2 && ./scripts/run.sh")
    print("- Ensure routing datasets are loaded before testing")
    print("- For accurate results, run multiple times and average")

if __name__ == "__main__":
    run_comparison()