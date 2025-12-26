import requests
import json
import time

API_BASE = "http://localhost:8000"

SOURCE_LAT = 37.10612
SOURCE_LON = -84.60932
TARGET_LAT = 37.06846
TARGET_LON = -84.62357
DATASET = "somerset"

def check_status():
    try:
        resp = requests.get(f"{API_BASE}/server-status")
        print("Server Status:", resp.json())
        status = resp.json()
        if DATASET not in status.get('datasets_loaded', []):
            print(f"Loading dataset {DATASET}...")
            requests.post(f"{API_BASE}/load-dataset", json={"dataset": DATASET})
            time.sleep(2)
    except Exception as e:
        print(f"Failed to check status: {e}")

def test_route(mode, num_candidates=1):
    print(f"\n--- Testing Mode: {mode} (Candidates: {num_candidates}) ---")
    params = {
        "dataset": DATASET,
        "source_lat": SOURCE_LAT,
        "source_lon": SOURCE_LON,
        "target_lat": TARGET_LAT,
        "target_lon": TARGET_LON,
        "search_mode": mode,
        "num_candidates": num_candidates,
        "search_radius": 500
    }
    
    start_time = time.time()
    try:
        resp = requests.get(f"{API_BASE}/route", params=params)
        end_time = time.time()
        
        if resp.status_code != 200:
            print(f"Error {resp.status_code}: {resp.text}")
            return

        data = resp.json()
        print(f"Success: {data['success']}")
        print("Full Response:", json.dumps(data, indent=2))
        if data['success']:
            # Safe access
            print(f"Distance: {data.get('distance')}s (cost)")
            print(f"Distance (m): {data.get('distance_meters')}m")
            print(f"Runtime (Server): {data.get('runtime_ms')} ms")
            print(f"Total Request Time: {(end_time - start_time)*1000:.2f} ms")
            
            if 'timing_breakdown' in data:
                print("Timing Breakdown:", json.dumps(data['timing_breakdown'], indent=2))
                
            if 'debug' in data and 'cells' in data['debug']:
                cells = data['debug']['cells']
                print("Cells Debug:")
                if 'source' in cells: print(f"  Source: {cells['source'].get('id')} (Res {cells['source'].get('res')})")
                if 'target' in cells: print(f"  Target: {cells['target'].get('id')} (Res {cells['target'].get('res')})")
                if 'high' in cells: print(f"  High:   {cells['high'].get('id')} (Res {cells['high'].get('res')})")
        else:
            print(f"Error Message: {data.get('error')}")

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    check_status()
    test_route("knn", num_candidates=1)
    test_route("one_to_one")
