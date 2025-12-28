"""
FastAPI server for the Contraction Hierarchies routing application.

This server provides REST API endpoints for:
- Listing available datasets
- Finding nearest edges to coordinates
- Computing shortest paths and returning GeoJSON routes
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.data_loader import DatasetRegistry
from api.ch_query import CHQueryEngineFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Contraction Hierarchies Routing API",
    description="REST API for querying shortest paths on road networks using Contraction Hierarchies",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dataset registry
registry = DatasetRegistry()

# Global CH query engine factory
ch_factory = CHQueryEngineFactory()


class DatasetInfo(BaseModel):
    """Dataset metadata."""
    name: str
    db_path: Optional[str] = None  # DuckDB database path (preferred)
    shortcuts_path: Optional[str] = None  # Legacy: Parquet path
    edges_path: Optional[str] = None  # Legacy: CSV path
    binary_path: Optional[str] = None
    bounds: Optional[List[float]] = None
    center: Optional[List[float]] = None


class NearestEdgeResponse(BaseModel):
    """Response for nearest edge query."""
    edge_id: int
    distance: float
    lat: float
    lon: float


class RouteResponse(BaseModel):
    """Response for route query."""
    success: bool
    dataset: Optional[str] = None
    distance: Optional[float] = None
    distance_meters: Optional[float] = None
    runtime_ms: Optional[float] = None
    path: Optional[List[int]] = None
    geojson: Optional[Dict] = None
    timing_breakdown: Optional[Dict[str, float]] = None
    debug: Optional[Dict] = None
    error: Optional[str] = None


import requests
import time

def load_config(config_path: str = "config/datasets.yaml"):
    """Load dataset configuration from YAML file and initialize C++ server."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}")
        return
    
    logger.info(f"Loading configuration from {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    datasets = config.get('datasets', [])
    paths_config = config.get('paths', {})
    
    # Auto-detect project root: .../services/api-gateway/api/server.py -> 3 levels up -> project_root
    project_root = Path(__file__).resolve().parents[3]
    
    # Context for resolution
    resolution_context = {"project_root": str(project_root)}
    
    # 1. Resolve paths_config first (e.g. data_root using project_root)
    resolved_paths = {}
    if paths_config:
        for key, value in paths_config.items():
            if isinstance(value, str):
                resolved_paths[key] = value.format(**resolution_context)
        # Update context with resolved paths
        resolution_context.update(resolved_paths)

    # Wait for C++ server health
    server_url = "http://localhost:8082"
    max_retries = 60
    server_ready = False
    
    for i in range(max_retries):
        try:
            requests.get(f"{server_url}/health", timeout=1)
            server_ready = True
            break
        except requests.RequestException:
            logger.info(f"Waiting for C++ server... ({i+1}/{max_retries})")
            time.sleep(1)
            
    if not server_ready:
        logger.error("C++ server is not reachable. Skipping dataset loading.")
    
    for ds in datasets:
        name = ds['name']
        
        # Support both DuckDB (preferred) and legacy file paths
        db_path = ds.get('db_path', '')
        shortcuts_path = ds.get('shortcuts_path', '')
        edges_path = ds.get('edges_path', '')
        binary_path = ds.get('binary_path', '')
        boundary_path = ds.get('boundary_path', '')

        # Resolve variables using the full context (project_root + paths)
        if resolution_context:
            if db_path: db_path = db_path.format(**resolution_context)
            if shortcuts_path: shortcuts_path = shortcuts_path.format(**resolution_context)
            if edges_path: edges_path = edges_path.format(**resolution_context)
            if binary_path: binary_path = binary_path.format(**resolution_context)
            if boundary_path: boundary_path = boundary_path.format(**resolution_context)
            # Store resolved boundary path back in dataset info
            ds['boundary_path'] = boundary_path
        
        # Resolve relative paths (fallback to config dir relative)
        base_dir = config_file.parent.parent
        if db_path and not Path(db_path).is_absolute():
            db_path = str(base_dir / db_path)
        if shortcuts_path and not Path(shortcuts_path).is_absolute():
            shortcuts_path = str(base_dir / shortcuts_path)
        if edges_path and not Path(edges_path).is_absolute():
            edges_path = str(base_dir / edges_path)
        if binary_path and not Path(binary_path).is_absolute():
            binary_path = str(base_dir / binary_path)
        
        # Register dataset (prefer db_path)
        registry.register_dataset(name, db_path=db_path, shortcuts_path=shortcuts_path, edges_path=edges_path, binary_path=binary_path, boundary_path=boundary_path)
        logger.info(f"Registered dataset '{name}' (db_path={db_path if db_path else 'N/A'})")
        
        # Also register with CH query engine factory (legacy support)
        if shortcuts_path and edges_path:
            try:
                ch_factory.register_dataset(
                    name=name,
                    shortcuts_path=shortcuts_path,
                    edges_path=edges_path,
                    binary_path=binary_path,
                    timeout=30
                )
            except Exception as e:
                logger.warning(f"CH engine not available for {name}: {e}")


@app.on_event("startup")
async def startup_event():
    """Load configuration on startup."""
    logger.info("Starting Contraction Hierarchies API server...")
    load_config()
    logger.info("Server startup complete")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Contraction Hierarchies Routing API",
        "version": "1.0.0",
        "endpoints": {
            "/datasets": "List available datasets",
            "/nearest-edge": "Find nearest edge to coordinates",
            "/route": "Compute shortest path between two points"
        }
    }


@app.get("/datasets", response_model=List[DatasetInfo])
async def list_datasets():
    """List all available datasets."""
    dataset_names = registry.list_datasets()
    
    result = []
    for name in dataset_names:
        info = registry.get_dataset_info(name)
        
        # Get spatial bounds (lazy load)
        # Skip spatial index loading to avoid performance hit
        # bounds = spatial_idx.get_bounds()
        bounds_list = None
        if info.get('center'):
             # Create dummy bounds around center if needed, or just leave None
             pass
        
        result.append(DatasetInfo(
            name=name,
            shortcuts_path=info['shortcuts_path'],
            edges_path=info['edges_path'],
            binary_path=info['binary_path'],
            bounds=bounds_list,
            center=center
        ))
    
    return result


@app.get("/nearest-edge", response_model=NearestEdgeResponse)
async def find_nearest_edge(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    dataset: str = Query(..., description="Dataset name")
):
    """Find the nearest edge to given coordinates."""
    if dataset not in registry.list_datasets():
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset}")
    
    try:
        spatial_idx = registry.get_spatial_index(dataset)
        result = spatial_idx.find_nearest_edge(lat, lon)
        
        if result is None:
            raise HTTPException(status_code=404, detail="No nearby edges found")
        
        edge_id, distance = result
        
        return NearestEdgeResponse(
            edge_id=edge_id,
            distance=distance,
            lat=lat,
            lon=lon
        )
    
    except Exception as e:
        logger.error(f"Error finding nearest edge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nearest-edges")
async def find_nearest_edges(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    dataset: str = Query(..., description="Dataset name"),
    k: int = Query(5, description="Number of nearest edges to return", ge=1, le=20)
):
    """Find k nearest edges to given coordinates using C++ server."""
    if dataset not in registry.list_datasets():
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset}")
    
    try:
        # Forward request to C++ server
        server_url = "http://localhost:8082"
        params = {
            "dataset": dataset,
            "lat": lat,
            "lon": lon,
            "k": k
        }
        
        response = requests.get(f"{server_url}/nearest_edges", params=params, timeout=10)
        data = response.json()
        
        return data
        
    except requests.RequestException as e:
        logger.error(f"Error calling C++ server: {e}")
        raise HTTPException(status_code=503, detail=f"C++ server error: {str(e)}")
    except Exception as e:
        logger.error(f"Error finding nearest edges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/route", response_model=RouteResponse)
async def compute_route(
    # Preferred/current parameter names
    source_lat: Optional[float] = Query(None, description="Source latitude (preferred)"),
    source_lon: Optional[float] = Query(None, description="Source longitude (preferred)"),
    target_lat: Optional[float] = Query(None, description="Target latitude (preferred)"),
    target_lon: Optional[float] = Query(None, description="Target longitude (preferred)"),
    # Legacy parameter names (kept for backward compatibility)
    start_lat: Optional[float] = Query(None, description="Legacy: start latitude"),
    start_lng: Optional[float] = Query(None, description="Legacy: start longitude"),
    end_lat: Optional[float] = Query(None, description="Legacy: end latitude"),
    end_lng: Optional[float] = Query(None, description="Legacy: end longitude"),
    dataset: str = Query(..., description="Dataset name"),
    search_mode: str = Query("knn", description="Search mode: 'knn', 'one_to_one', or 'one_to_one_v2'"),
    num_candidates: int = Query(3, description="Number of candidates for KNN", ge=1, le=10),
    search_radius: float = Query(2000.0, description="Search radius in meters", ge=10.0, le=10000.0),
    algorithm: str = Query("pruned", description="Routing algorithm: 'pruned', 'classic', 'unidirectional', 'dijkstra'")
):
    """
    Compute a route between Source and Target.
    Delegates to the C++ routing engine.
    """
    if dataset not in registry.list_datasets():
        return RouteResponse(success=False, error=f"Dataset not found: {dataset}")
    
    if search_mode not in ['knn', 'one_to_one', 'one_to_one_v2', 'dijkstra']:
        return RouteResponse(success=False, error="search_mode must be 'knn', 'one_to_one', 'one_to_one_v2', or 'dijkstra'")
    
    try:
        # Resolve coordinate parameters: prefer current names, fall back to legacy names
        def pick(primary: Optional[float], legacy: Optional[float]) -> Optional[float]:
            return primary if primary is not None else legacy

        src_lat = pick(source_lat, start_lat)
        src_lon = pick(source_lon, start_lng)
        tgt_lat = pick(target_lat, end_lat)
        tgt_lon = pick(target_lon, end_lng)

        # Validate presence of coordinates
        missing = []
        if src_lat is None:
            missing.append('source_lat/start_lat')
        if src_lon is None:
            missing.append('source_lon/start_lng')
        if tgt_lat is None:
            missing.append('target_lat/end_lat')
        if tgt_lon is None:
            missing.append('target_lon/end_lng')
        if missing:
            return RouteResponse(success=False, error=f"Missing required coordinate parameters: {', '.join(missing)}")
        # Get CH query engine
        try:
            ch_engine = ch_factory.get_engine(dataset)
        except KeyError:
            return RouteResponse(success=False, error=f"Query engine not available for dataset: {dataset}")
        
        # Delegate full routing to the high-performance routing server
        # The server handles nearest neighbor search and pathfinding internally
        result = ch_engine.compute_route_latlon(
            start_lat=src_lat,
            start_lng=src_lon,
            end_lat=tgt_lat,
            end_lng=tgt_lon,
            search_mode=search_mode,
            num_candidates=num_candidates,
            search_radius=search_radius,
            algorithm=algorithm
        )
        
        if not result.success:
            return RouteResponse(success=False, error=result.error or "Routing failed")
            
        # The GeoJSON is now propagated from the server via the SDK
        feature = result.geojson
        
        # Fallback if server didn't return geojson (should not happen with new server)
        if not feature:
            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": []},
                "properties": {"distance": result.distance, "warning": "No geometry returned"}
            }
        
        return RouteResponse(
            success=True,
            dataset=dataset,
            distance=result.distance,
            distance_meters=result.distance_meters,
            runtime_ms=result.runtime_ms,
            path=result.path,
            geojson=feature,
            timing_breakdown=result.timing_breakdown,
            debug=result.debug
        )
    
    except Exception as e:
        logger.error(f"Error computing route: {e}", exc_info=True)
        return RouteResponse(success=False, error=f"Internal server error: {str(e)}")


class LoadDatasetRequest(BaseModel):
    dataset: str

@app.post("/load-dataset")
async def load_dataset_endpoint(request: LoadDatasetRequest):
    """Load a dataset into the C++ server."""
    dataset = request.dataset
    if dataset not in registry.list_datasets():
        raise HTTPException(status_code=404, detail=f"Dataset not found in registry: {dataset}")
    
    info = registry.get_dataset_info(dataset)
    
    # Proxy to C++ server - prefer db_path for DuckDB loading
    try:
        if info.get('db_path'):
            # DuckDB loading (preferred for legacy engine)
            payload = {
                "dataset": dataset,
                "db_path": info['db_path']
            }
        elif info.get('shortcuts_path') and info.get('edges_path'):
            # File loading (fallback)
            payload = {
                "dataset": dataset,
                "shortcuts_path": info['shortcuts_path'],
                "edges_path": info['edges_path']
            }
        else:
            raise HTTPException(status_code=500, detail="Invalid dataset config: missing paths")
        
        logger.info(f"Sending load payload: {json.dumps(payload)}")
        resp = requests.post("http://localhost:8082/load_dataset", json=payload, timeout=180)
        
        if resp.status_code == 200:
            return {"success": True, "message": f"Dataset {dataset} loaded"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to load dataset: {resp.text}")
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"C++ server error: {str(e)}")


@app.post("/unload-dataset")
async def unload_dataset_endpoint(request: LoadDatasetRequest):
    """Unload a dataset from the C++ server."""
    dataset = request.dataset
    
    # Proxy to C++ server
    try:
        payload = {"dataset": dataset}
        resp = requests.post("http://localhost:8082/unload_dataset", json=payload, timeout=10)
        
        if resp.status_code == 200:
            return {"success": True, "message": f"Dataset {dataset} unloaded"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to unload dataset: {resp.text}")
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"C++ server error: {str(e)}")

@app.get("/server-status")
async def server_status():
    """Get C++ server status and loaded datasets."""
    try:
        resp = requests.get("http://localhost:8082/health", timeout=2)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"status": "error", "error": f"C++ server returned {resp.status_code}"}
    except Exception as e:
        return {"status": "down", "error": str(e)}


def parse_cpp_output(output: str) -> tuple:
    """
    Parse C++ binary output.
    
    Expected format:
        Query 1593 -> 4835
          Distance (including destination edge): 433.75
          Destination edge cost: 267.604
          Shortcut path length: 5 edges
          Shortcut path: 1593 -> 34486 -> 24508 -> 8504 -> 4835
          Expanded base edge path length: 6 edges
          Expanded base edge path: 1593 -> ... -> 4835
          Runtime: 0.42 ms
    
    Returns:
        (path, distance, runtime_ms) or (None, None, None) if parsing fails
    """
    try:
        lines = output.strip().split('\n')
        
        distance = None
        runtime_ms = None
        path = None
        
        for line in lines:
            line = line.strip()
            
            if "No path found" in line:
                return None, None, None
            
            # Handle both single query and multi-query output formats
            if "Distance" in line and ("including destination edge" in line or "total including" in line):
                distance = float(line.split(':')[1].strip())
            
            elif "Runtime:" in line:
                runtime_str = line.split(':')[1].strip().replace('ms', '').strip()
                runtime_ms = float(runtime_str)
            
            elif "Expanded path:" in line or "Expanded base edge path:" in line:
                # Extract path: "1593 -> 34486 -> 24508 -> 4835"
                path_str = line.split(':')[1].strip()
                # Handle both full paths and truncated paths with "..."
                path_str = path_str.replace('...', '')
                path_parts = [p.strip() for p in path_str.split('->')]
                path = [int(p) for p in path_parts if p and p.isdigit()]
        
        if path is None:
            logger.warning("Failed to parse path from C++ output")
            return None, None, None
        
        return path, distance, runtime_ms
    
    except Exception as e:
        logger.error(f"Error parsing C++ output: {e}")
        return None, None, None


def build_geojson(path: List[int], spatial_idx) -> Dict:
    """
    Build GeoJSON LineString from edge path.
    
    Args:
        path: List of edge IDs
        spatial_idx: SpatialIndex instance
    
    Returns:
        GeoJSON FeatureCollection
    """
    features = []
    
    for edge_id in path:
        edge_data = spatial_idx.get_edge(edge_id)
        
        if edge_data is None:
            logger.warning(f"Edge {edge_id} not found in spatial index")
            continue
        
        coords = list(edge_data.geometry.coords)
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            },
            "properties": {
                "edge_id": edge_id,
                "length": edge_data.length,
                "highway": edge_data.highway
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
