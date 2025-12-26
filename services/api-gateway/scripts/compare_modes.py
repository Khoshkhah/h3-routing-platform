
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/route"
DATASET = "burnaby" # User mentioned Metro Vancouver, 'burnaby' is usually the dataset key we use or maybe 'vancouver' if available. 
# Looking at previous logs, user uses 'burnaby' or similar. 
# I will check available datasets first.


def check_datasets():
    try:
        resp = requests.get("http://localhost:8000/datasets")
        if resp.status_code == 200:
            datasets = [d['name'] for d in resp.json()]
            return datasets
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        return []

def run_query(mode, start_lat, start_lon, end_lat, end_lon, dataset):
    params = {
        "dataset": dataset,
        "source_lat": start_lat,
        "source_lon": start_lon,
        "target_lat": end_lat,
        "target_lon": end_lon,
        "search_mode": mode,
        "search_mode": mode,
        "num_candidates": 1,
        "search_radius": 5000 # Increase to 5km to be safe
    }
    
    try:
        response = requests.get(API_URL, params=params)
        data = response.json()
        if data.get("success"):
            print(json.dumps(data)) # DEBUG
            dist = data['distance']
            metric = "m" if mode == "one_to_one" else "s (cost)" 
            return dist, data['distance_meters'], data['runtime_ms']
        else:
            logger.error(f"Query failed for {mode}: {data}")
            return None, None, None
    except Exception as e:
        logger.error(f"Request error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def main():
    datasets = check_datasets()
    print(f"Available datasets: {datasets}")
    
    # Prefer all_vancouver
    target_dataset = "all_vancouver" if "all_vancouver" in datasets else None
    
    if not target_dataset:
        for d in datasets:
             if "burnaby" in d.lower() or "vancouver" in d.lower():
                target_dataset = d
                break
            
    if not target_dataset:
        if datasets:
            target_dataset = datasets[0]
            print(f"Defaulting to first dataset: {target_dataset}")
        else:
            print("No datasets found.")
            return

    # Somerset Test Case (User Requested)
    # Source: 37.08805, -84.61481
    # Target: 37.09849, -84.62121
    start_lat, start_lon = 37.08805, -84.61481
    end_lat,   end_lon   = 37.09849, -84.62121
    
    DATASET_NAME = "somerset"
    
    # Ensure dataset is loaded
    requests.post("http://localhost:8000/load-dataset", json={"dataset": DATASET_NAME})
    
    # Update target_dataset for the query to use DATASET_NAME
    target_dataset = DATASET_NAME

    print(f"\nComparing modes for {target_dataset} ({start_lat},{start_lon} -> {end_lat},{end_lon})...")
    
    modes = ["knn", "one_to_one", "one_to_one_v2"]
    
    results = {}
    
    for mode in modes:
        cost, meters, time_ms = run_query(mode, start_lat, start_lon, end_lat, end_lon, target_dataset)
        results[mode] = {"cost": cost, "meters": meters, "time": time_ms}
        print(f"Mode: {mode:15} | Cost: {cost} | Dist: {meters} m | Time: {time_ms} ms")

    # Analysis
    v1 = results["one_to_one"]
    v2 = results["one_to_one_v2"]
    knn = results["knn"]
    
    if v1['cost'] != v2['cost']:
        print("\n[!] Discrepancy detected between V1 and V2!")
        diff = abs(v1['cost'] - v2['cost'])
        print(f"Difference: {diff}")
    else:
        print("\nV1 and V2 match.")

    if v1['cost'] != knn['cost']:
         print(f"V1 differs from KNN by {abs(v1['cost'] - knn['cost'])}")

if __name__ == "__main__":
    main()
