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

    def unload_dataset(self, name: str) -> bool:
        """Unload a dataset from engine memory."""
        payload = {"dataset": name}
        resp = requests.post(f"{self.base_url}/unload_dataset", json=payload)
        return resp.status_code == 200

    def nearest_edges(
        self,
        dataset: str,
        lat: float,
        lon: float,
        k: int = 5,
        radius_meters: float = 100.0
    ) -> List[Dict]:
        """
        Find the nearest graph edges to a location.
        
        Args:
            dataset: Dataset name
            lat, lon: Query coordinates
            k: Number of nearest edges to return
            radius_meters: Maximum search radius
            
        Returns:
            List of dicts with edge_id, distance, length, cost
        """
        params = {
            "dataset": dataset,
            "lat": lat,
            "lon": lon,
            "k": k,
            "radius": radius_meters
        }
        try:
            resp = requests.get(f"{self.base_url}/nearest_edges", params=params, timeout=5)
            data = resp.json()
            return data.get("edges", [])
        except Exception:
            return []

    # ============================================================
    # DEBUG METHODS - For testing and development
    # ============================================================
    
    def route_by_edge(
        self,
        dataset: str,
        source_edge: int,
        target_edge: int
    ) -> Dict:
        """
        [DEBUG] Route between two edge IDs. Returns expanded path (base edges).
        Skips nearest-edge lookup.
        
        Returns:
            Dict with 'success', 'path' (expanded edge IDs), 'distance', 'geojson'
        """
        payload = {
            "dataset": dataset,
            "source_edge": source_edge,
            "target_edge": target_edge
        }
        try:
            resp = requests.post(f"{self.base_url}/route_by_edge", json=payload, timeout=30)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def route_by_edge_raw(
        self,
        dataset: str,
        source_edge: int,
        target_edge: int
    ) -> Dict:
        """
        [DEBUG] Route between two edge IDs. Returns shortcut-level path (not expanded).
        Useful for debugging the CH/shortcut structure.
        
        Returns:
            Dict with 'success', 'shortcut_path' (shortcut IDs before expansion)
        """
        payload = {
            "dataset": dataset,
            "source_edge": source_edge,
            "target_edge": target_edge,
            "expand": False  # Request shortcut-level path
        }
        try:
            resp = requests.post(f"{self.base_url}/route_by_edge", json=payload, timeout=30)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def route_raw(
        self,
        dataset: str,
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float,
        num_candidates: int = 3
    ) -> Dict:
        """
        [DEBUG] Route by coordinates. Returns shortcut-level path (not expanded).
        Useful for debugging the CH/shortcut structure.
        
        Returns:
            Dict with 'success', 'shortcut_path' (shortcut IDs before expansion)
        """
        payload = {
            "dataset": dataset,
            "start_lat": start_lat, "start_lng": start_lng,
            "end_lat": end_lat, "end_lng": end_lng,
            "num_candidates": num_candidates,
            "expand": False  # Request shortcut-level path
        }
        try:
            resp = requests.post(f"{self.base_url}/route", json=payload, timeout=30)
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
