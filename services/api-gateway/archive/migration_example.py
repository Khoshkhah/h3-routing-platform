#!/usr/bin/env python3
"""
Migration Example: From Subprocess to HTTP API

This script demonstrates how to migrate from the old subprocess-based
routing approach to the new persistent C++ HTTP server.
"""

import requests
import json
import time
from typing import Dict, Any

class RoutingClientV2:
    """Client for the new persistent routing server."""

    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check server health and loaded datasets."""
        response = self.session.get(f"{self.server_url}/health")
        return response.json()

    def load_dataset(self, dataset: str) -> Dict[str, Any]:
        """Load a routing dataset into memory."""
        payload = {"dataset": dataset}
        response = self.session.post(f"{self.server_url}/load_dataset", json=payload)
        return response.json()

    def compute_route(self, dataset: str, start_lat: float, start_lng: float,
                     end_lat: float, end_lng: float,
                     search_radius: float = 1000.0,
                     max_candidates: int = 10) -> Dict[str, Any]:
        """Compute shortest path between two points."""
        payload = {
            "dataset": dataset,
            "start_lat": start_lat,
            "start_lng": start_lng,
            "end_lat": end_lat,
            "end_lng": end_lng,
            "search_radius": search_radius,
            "max_candidates": max_candidates
        }
        response = self.session.post(f"{self.server_url}/route", json=payload)
        return response.json()

def demo_migration():
    """Demonstrate the migration from subprocess to HTTP API."""

    print("🔄 Routing Pipeline v2 - Migration Demo")
    print("=" * 50)

    # Initialize client
    client = RoutingClientV2()

    try:
        # Check server health
        print("🏥 Checking server health...")
        health = client.health_check()
        print(f"✅ Server status: {health.get('status', 'unknown')}")
        print(f"📊 Loaded datasets: {health.get('datasets_loaded', [])}")

        # Load a dataset
        print("\n📦 Loading dataset 'burnaby'...")
        result = client.load_dataset("burnaby")
        if result.get("success"):
            print("✅ Dataset loaded successfully")
        else:
            print(f"⚠️  Dataset loading failed: {result.get('error', 'unknown error')}")

        # Compute a route
        print("\n🛣️  Computing route...")
        start_time = time.time()

        route = client.compute_route(
            dataset="burnaby",
            start_lat=49.123,
            start_lng=-123.456,
            end_lat=49.789,
            end_lng=-123.012,
            search_radius=1000.0,
            max_candidates=10
        )

        end_time = time.time()

        if route.get("success"):
            print("✅ Route computed successfully!")
            print(".2f")
            if "route" in route:
                r = route["route"]
                print(f"   📏 Distance: {r.get('distance', 'N/A')} meters")
                print(f"   ⚡ Runtime: {r.get('runtime_ms', 'N/A')} ms")
                print(f"   🛤️  Path length: {len(r.get('path', []))} edges")
        else:
            print(f"❌ Route computation failed: {route.get('error', 'unknown error')}")

        print(".2f")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to routing server")
        print("   Make sure the server is running: cd routing-server-v2 && ./scripts/run.sh")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    demo_migration()