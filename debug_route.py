import requests
import json

URL = "http://localhost:8082/route_by_edge"
HEADERS = {"Content-Type": "application/json"}

def test_route(algo):
    payload = {
        "dataset": "somerset",
        "source_edge": 1169,
        "target_edge": 390,
        "algorithm": algo
    }
    resp = requests.post(URL, json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(f"--- {algo.upper()} ---")
        if data['success']:
            route = data['route']
            print(f"Distance: {route['distance']}")
            print(f"Meters: {route['distance_meters']}")
            print(f"Runtime: {route['runtime_ms']} ms")
            print(f"Path Len: {len(route['path'])}")
            print(f"Shortcuts: {len(route['shortcut_path'])}")
        else:
            print(f"Error: {data.get('error')}")
    else:
        print(f"HTTP {resp.status_code}: {resp.text}")

test_route("classic")
test_route("pruned")
