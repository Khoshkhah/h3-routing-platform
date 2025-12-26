import requests
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result from a shortest path query."""
    success: bool
    distance: Optional[float] = None
    distance_meters: Optional[float] = None
    runtime_ms: Optional[float] = None
    path: Optional[List[int]] = None
    geojson: Optional[dict] = None  # Add GeoJSON support
    timing_breakdown: Optional[dict] = None
    debug: Optional[dict] = None
    error: Optional[str] = None


class CHQueryEngine:
    # ... (init and loaded check remain same)

    def __init__(
        self,
        dataset_name: str,
        server_url: str = "http://localhost:8082",
        timeout: int = 30
    ):
        """
        Initialize the query engine client.
        
        Args:
            dataset_name: Name of the dataset to query (e.g. "Burnaby")
            server_url: Base URL of the routing server
            timeout: Request timeout in seconds
        """
        self.dataset_name = dataset_name.lower()
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        
        # REMOVED: Do not auto-load. Let user control it via /load_dataset endpoint.
        # self._ensure_dataset_loaded()
    
    def _ensure_dataset_loaded(self):
        try:
            payload = {"dataset": self.dataset_name}
            # Just try to load - idempotent
            requests.post(
                f"{self.server_url}/load_dataset",
                json=payload,
                timeout=self.timeout
            )
        except Exception as e:
            logger.error(f"Failed to communicate with routing server: {e}")

    def query(self, source: int, target: int) -> QueryResult:
        return QueryResult(False, error="Raw edge query not supported by HTTP client yet. Use compute_route_latlon.")
    
    def query_multi(self, *args, **kwargs) -> QueryResult:
        return QueryResult(False, error="Raw edge query not supported by HTTP client yet. Use compute_route_latlon.")

    def compute_route_latlon(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        search_mode: str = "knn",
        num_candidates: int = 3,
        search_radius: float = 100.0
    ) -> QueryResult:
        """
        Compute route using the routing server's full stack (NN + CH).
        """
        # For one-to-one, we strictly want the best match (1 candidate)
        # to ensure deterministic behavior matching the C++ engine's direct query
        if search_mode == "one_to_one":
            num_candidates = 1
            
        try:
            payload = {
                "dataset": self.dataset_name,
                "start_lat": start_lat,
                "start_lng": start_lng,
                "end_lat": end_lat,
                "end_lng": end_lng,
                "mode": search_mode,
                "num_candidates": num_candidates,
                "search_radius": search_radius
            }
            
            t0 = time.time()
            response = requests.post(
                f"{self.server_url}/route",
                json=payload,
                timeout=self.timeout
            )
            t1 = time.time()
            client_side_ms = (t1 - t0) * 1000.0

            if response.status_code != 200:
                logger.error(f"Routing server returned {response.status_code}")
                return QueryResult(success=False, error=f"Server returned {response.status_code}")

            data = response.json()
            
            # Check for explicit errors from server
            if not data.get("success", False):
                return QueryResult(success=False, error=data.get("error", "Unknown server error"))
            
            # The server structure: {success:true, route: {dataset:..., debug:{...}, route:{distance:..., geojson:...}}}
            # It seems the response is wrapped inside a "route" object by the server framework
            route_container = data.get("route", {})
            route_details = route_container.get("route", {})
            
            # Additional safety: maybe wrapping is inconsistent?
            if not route_details and "distance" in route_container:
                route_details = route_container

            dist_val = route_details.get("distance")
            
            return QueryResult(
                success=True,
                distance=dist_val,
                distance_meters=route_details.get("distance_meters"),
                path=route_details.get("path"),
                geojson=route_details.get("geojson"),
                runtime_ms=route_details.get("runtime_ms") or client_side_ms,
                timing_breakdown=data.get("timing_breakdown") or route_container.get("timing_breakdown"),
                debug=data.get("debug")  # debug is at top level of response
            )
        except Exception as e:
            logger.error(f"Routing request failed: {e}")
            return QueryResult(success=False, error=str(e))

    def find_nearest_edges(self, lat: float, lon: float, radius: float = 1000.0, max_candidates: int = 5) -> dict:
        """
        Find multiple nearest edges to the given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters
            max_candidates: Maximum number of edges to return
            
        Returns:
            Dict with keys: success, edges (list of {id, distance}), error
        """
        try:
            payload = {
                "dataset": self.dataset_name,
                "lat": lat,
                "lon": lon,
                "radius": radius,
                "max_candidates": max_candidates
            }
            response = requests.post(
                f"{self.server_url}/nearest_edges",
                json=payload,
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            logger.error(f"Nearest edges request failed: {e}")
            return {"success": False, "error": str(e)}

    def find_nearest_edge(self, lat: float, lon: float) -> dict:
        """
        Find the nearest edge to the given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with keys: success, edge_id, distance_meters, runtime_ms, error
        """
        try:
            payload = {
                "dataset": self.dataset_name,
                "lat": lat,
                "lon": lon
            }
            response = requests.post(
                f"{self.server_url}/nearest_edge",
                json=payload,
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            logger.error(f"Nearest edge request failed: {e}")
            return {"success": False, "error": str(e)}


class CHQueryEngineFactory:
    """
    Factory that now produces HTTP clients.
    """
    
    def __init__(self, server_url: str = "http://localhost:8082"):
        self.server_url = server_url
        self._configs = {}
        self._engines = {}  # Cache for instantiated engines
    
    def register_dataset(self, name: str, **kwargs):
        """
        Register dataset.
        
        Args:
           name: Dataset name (e.g. "Burnaby")
           **kwargs: Ignored for HTTP client (paths are handled by server)
        """
        self._configs[name] = kwargs
        # Invalidate cache if re-registering? 
        # For now, simplistic overwrite.
        if name in self._engines:
            del self._engines[name]
    
    def get_engine(self, name: str) -> CHQueryEngine:
        # Check cache first
        if name not in self._engines:
            self._engines[name] = CHQueryEngine(name, self.server_url)
        return self._engines[name]
    
    def check_health(self) -> dict:
        """
        Check if the routing server is healthy and get loaded datasets.
        
        Returns:
            Dict with keys: status, datasets_loaded
        """
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def list_datasets(self) -> List[str]:
        return list(self._configs.keys())
