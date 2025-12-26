import requests
import json
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class RouteResponse:
    success: bool
    distance: float = 0.0
    distance_meters: float = 0.0
    runtime_ms: float = 0.0
    path: List[int] = None
    geojson: Dict = None
    error: str = None

class RoutingClient:
    """
    Client for the Routing Platform C++ Engine.
    """
    def __init__(self, base_url: str = "http://localhost:8082"):
        self.base_url = base_url.rstrip("/")

    def health(self) -> Dict:
        """Check server health."""
        return requests.get(f"{self.base_url}/health").json()

    def route(
        self, 
        dataset: str,
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float,
        mode: str = "knn",
        num_candidates: int = 3,
        algorithm: str = "pruned"
    ) -> RouteResponse:
        """
        Calculate a route between two points.
        """
        payload = {
            "dataset": dataset,
            "start_lat": start_lat, "start_lng": start_lng,
            "end_lat": end_lat, "end_lng": end_lng,
            "mode": mode,
            "num_candidates": num_candidates,
            "algorithm": algorithm
        }
        
        try:
            resp = requests.post(f"{self.base_url}/route", json=payload, timeout=10)
            data = resp.json()
            
            if not data.get("success"):
                return RouteResponse(success=False, error=data.get("error"))
                
            r = data.get("route", {})
            return RouteResponse(
                success=True,
                distance=r.get("distance"),
                distance_meters=r.get("distance_meters"),
                runtime_ms=data.get("timing_breakdown", {}).get("total_ms", 0),
                path=r.get("path"),
                geojson=r.get("geojson")
            )
        except Exception as e:
            return RouteResponse(success=False, error=str(e))

    def load_dataset(self, name: str, shortcuts_path: str, edges_path: str) -> bool:
        """Load a dataset into the engine."""
        payload = {
            "dataset": name,
            "shortcuts_path": shortcuts_path,
            "edges_path": edges_path
        }
        resp = requests.post(f"{self.base_url}/load_dataset", json=payload)
        return resp.status_code == 200
