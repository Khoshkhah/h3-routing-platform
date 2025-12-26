
import requests
import json
import time

URL = "http://localhost:8080/route"
DATASET = "burnaby"  # or somerset

payload = {
    "dataset": DATASET,
    "start_lat": 49.25,
    "start_lng": -123.00,
    "end_lat": 49.26,
    "end_lng": -123.02,
    "search_radius": 1000,
    "max_candidates": 10
}

def run_query(i):
    t0 = time.time()
    try:
        resp = requests.post(URL, json=payload)
        t1 = time.time()
        print(f"Run {i}: HTTP={((t1-t0)*1000):.2f}ms", end=" | ")
        if resp.status_code == 200:
            data = resp.json()
            if data['success']:
                rt = data['route'].get('runtime_ms', -1)
                print(f"Server Routing Time={rt}ms")
            else:
                 print(f"Error: {data}")
        else:
            print(f"HTTP Error: {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

print(f"Testing {DATASET} route query warm-up...")
for i in range(1, 6):
    run_query(i)
    time.sleep(0.5)
