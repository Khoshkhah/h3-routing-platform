import requests
import json
import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class RouteResponse:
    success: bool
    distance: float = 0.0  # Total path cost (sum of weights)
    distance_meters: float = 0.0  # Physical distance in meters
    runtime_ms: float = 0.0
    path: List[int] = None
    geojson: Dict = None
    error: str = None
    alternative_route: Dict = None  # Alternative route if requested

    @property
    def cost(self) -> float:
        """Alias for distance, representing the total path cost."""
        return self.distance

class RoutingClient:
    """
    Client for the Routing Platform C++ Engine.
    """
    def __init__(self, base_url: str = "http://localhost:8082", config_path: str = None):
        self.base_url = base_url.rstrip("/")
        self.is_gateway = self._check_is_gateway()
        self.config_path = config_path
        self.dataset_registry = {}
        
        # If not connected to gateway, try to load local config to support by-name loading
        if not self.is_gateway:
            self._try_load_local_config()

    def _try_load_local_config(self):
        """Try to locate and load datasets.yaml for local path resolution."""
        candidates = []
        if self.config_path:
            candidates.append(Path(self.config_path))
        
        # Common locations relative to this SDK file or project root
        sdk_dir = Path(__file__).parent.absolute()
        
        # Heuristic: Walk up parents to find 'h3-routing-platform'
        project_root = sdk_dir
        for parent in sdk_dir.parents:
            if parent.name == 'h3-routing-platform':
                project_root = parent
                break
        else:
             # Fallback if not found in parents (e.g. symlinked/editable install weirdness)
             # Try assuming standard layout: sdk/python/client.py -> ../.. -> project_root
             project_root = sdk_dir.parents[1]

        candidates.extend([
            project_root / "services/api-gateway/config/datasets.yaml",
            Path("config/datasets.yaml"),
            Path("../config/datasets.yaml"),
            Path("../services/api-gateway/config/datasets.yaml"),
             # Hardcoded absolute fallback for reliability
            Path("../services/api-gateway/config/datasets.yaml")
        ])
        
        for p in candidates:
            if p.exists():
                try:
                    with open(p, 'r') as f:
                        config = yaml.safe_load(f)
                        
                    # Pre-resolve paths
                    # If we found it at the hardcoded path, Force project root to be that path's grandparent
                    if str(p) == "../services/api-gateway/config/datasets.yaml":
                         project_root = Path("../")

                    data_root = config.get('paths', {}).get('data_root', '{project_root}/data')
                    data_root = data_root.replace('{project_root}', str(project_root))
                    
                    datasets = config.get('datasets', [])
                    
                    for ds in datasets:
                        name = ds['name']
                        self.dataset_registry[name] = ds
                        
                        # automatic deduction of db_path if missing
                        if 'db_path' not in ds:
                             # Try {name}.db and {Name}.db
                             candidates_db = [
                                 f"{name}.db",
                                 f"{name.capitalize()}.db", 
                                 f"{name.title()}.db"
                             ]
                             
                             for db_name in candidates_db:
                                 path_candidate = Path(data_root) / db_name
                                 if path_candidate.exists():
                                     ds['db_path'] = str(path_candidate)
                                     print(f"DEBUG: Auto-deduced db_path for '{name}': {ds['db_path']}")
                                     break
                        
                        # Resolve {data_root} in db_path if it exists
                        if 'db_path' in ds:
                            ds['db_path'] = ds['db_path'].replace('{data_root}', data_root)
                            # Handle relative paths
                            if not Path(ds['db_path']).is_absolute():
                                ds['db_path'] = str(project_root / ds['db_path'])
                                
                    print(f"Loaded local config from {p} with {len(self.dataset_registry)} datasets")
                    break
                except Exception as e:
                    print(f"Warning: Failed to load config from {p}: {e}")

    def _check_is_gateway(self) -> bool:
        """Check if connected to API Gateway (vs C++ Engine directly)."""
        try:
            # Gateway has /server-status, Engine has /health
            resp = requests.get(f"{self.base_url}/server-status", timeout=1)
            return resp.status_code == 200
        except:
            return False

    def health(self) -> Dict:
        """Check server health."""
        if self.is_gateway:
            return requests.get(f"{self.base_url}/server-status").json()
        return requests.get(f"{self.base_url}/health").json()

    def route(
        self, 
        dataset: str,
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float,
        mode: str = "knn",
        num_candidates: int = 3,
        algorithm: str = "pruned",
        include_alternative: bool = False,
        penalty_factor: float = 2.0
    ) -> RouteResponse:
        """
        Calculate a route between two points.

        Args:
            dataset: Name of the dataset to use
            start_lat, start_lng: Source coordinates
            end_lat, end_lng: Target coordinates
            mode: Search mode ("knn", "one_to_one", or "one_to_one_v2")
            num_candidates: Number of nearest edges to consider per point
            algorithm: Routing algorithm (e.g., "bi_classic_sp", "bi_dijkstra_sp", "bi_lca_res_sp", 
                       "bi_lca_sp", "uni_lca_sp", "m2m_classic_sp", "dijkstra_sp")
            include_alternative: If True, also return an alternative route
            penalty_factor: Penalty multiplier for alternative route (default 2.0)

        Returns:
            RouteResponse object containing:
                - cost / distance: Total path cost (optimization objective)
                - distance_meters: Physical length in meters
                - path: List of edge IDs
                - geojson: Route geometry
                - alternative_route: Dict with alternative route info (if requested)
        """
        # API Gateway (Project OSRM style)
        if self.is_gateway:
            params = {
                "dataset": dataset,
                "source_lat": start_lat, "source_lon": start_lng,
                "target_lat": end_lat, "target_lon": end_lng,
                "search_mode": mode,
                "num_candidates": num_candidates,
                "search_radius": 2000.0 
            }
            try:
                resp = requests.get(f"{self.base_url}/route", params=params, timeout=10)
                data = resp.json()
                
                if not data.get("success"):
                     return RouteResponse(success=False, error=data.get("error"))
                
                return RouteResponse(
                    success=True,
                    distance=data.get("distance"),
                    distance_meters=data.get("distance_meters"),
                    runtime_ms=data.get("runtime_ms"),
                    path=data.get("path"),
                    geojson=data.get("geojson"),
                    error=data.get("error")
                )
            except Exception as e:
                return RouteResponse(success=False, error=str(e))
                
        # C++ Engine (Direct POST)
        else:
            payload = {
                "dataset": dataset,
                "start_lat": start_lat, "start_lng": start_lng,
                "end_lat": end_lat, "end_lng": end_lng,
                "mode": mode,
                "num_candidates": num_candidates,
                "algorithm": algorithm,
                "include_alternative": include_alternative,
                "penalty_factor": penalty_factor
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
                    geojson=r.get("geojson"),
                    alternative_route=data.get("alternative_route")
                )
            except Exception as e:
                return RouteResponse(success=False, error=str(e))

    def route_unidirectional(
        self,
        dataset: str,
        start_lat: float, start_lng: float,
        end_lat: float, end_lng: float,
        num_candidates: int = 3
    ) -> RouteResponse:
        """
        Convenience method for unidirectional pruned routing.
        Uses the 'unidirectional' algorithm type.
        """
        return self.route(
            dataset=dataset,
            start_lat=start_lat, start_lng=start_lng,
            end_lat=end_lat, end_lng=end_lng,
            num_candidates=num_candidates,
            algorithm="unidirectional"
        )

    def load_dataset(
        self, 
        name: str, 
        shortcuts_path: str = None, 
        edges_path: str = None,
        db_path: str = None
    ) -> bool:
        """
        Load a dataset into the engine.
        
        Args:
            name: Dataset name identifier
            shortcuts_path: Path to shortcuts file (Legacy)
            edges_path: Path to edges CSV/Parquet (Legacy)
            db_path: Path to DuckDB database (Preferred for CSR engine)
        """
        payload = {"dataset": name}
        
        # If no paths provided and not using gateway, try to resolve from local config
        if not self.is_gateway and not (db_path or (shortcuts_path and edges_path)):
            # Try exact match
            info = self.dataset_registry.get(name)
            
            # Try lowercase match
            if not info:
                info = self.dataset_registry.get(name.lower())
                
            # Try matching by short_name (case-insensitive)
            if not info:
                for ds in self.dataset_registry.values():
                    if ds.get('short_name', '').lower() == name.lower():
                        info = ds
                        break
            
            if info:
                # Use the resolved name (e.g. "somerset" instead of "Somerset")
                # This ensures the server receives the canonical ID
                payload["dataset"] = info['name']
                
                if 'db_path' in info:
                    db_path = info['db_path']
                    print(f"Resolved dataset '{name}' -> '{info['name']}' (db_path: {db_path})")
                elif 'shortcuts_path' in info and 'edges_path' in info:
                    shortcuts_path = info['shortcuts_path']
                    edges_path = info['edges_path']
            else:
                print(f"Warning: Could not resolve paths for dataset '{name}' in local config.")
                print(f"Available datasets: {list(self.dataset_registry.keys())}")
        
        if db_path: payload["db_path"] = db_path
        if shortcuts_path: payload["shortcuts_path"] = shortcuts_path
        if edges_path: payload["edges_path"] = edges_path
            
        endpoint = "/load-dataset" if self.is_gateway else "/load_dataset"
        try:
            resp = requests.post(f"{self.base_url}{endpoint}", json=payload)
            return resp.status_code == 200
        except:
            return False

    def unload_dataset(self, name: str) -> bool:
        """Unload a dataset from engine memory."""
        payload = {"dataset": name}
        endpoint = "/unload-dataset" if self.is_gateway else "/unload_dataset"
        try:
            resp = requests.post(f"{self.base_url}{endpoint}", json=payload)
            return resp.status_code == 200
        except:
            return False

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
