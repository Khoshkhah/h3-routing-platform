"""
Data loader module for edge geometries and spatial indexing.

This module handles:
- Loading edge CSV files with WKT LineString geometries
- Building R-tree spatial indices for nearest-neighbor queries
- Finding nearest edges to lat/lon coordinates
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
from rtree import index
from shapely import wkt
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

logger = logging.getLogger(__name__)


@dataclass
class EdgeData:
    """Container for edge geometry and metadata."""
    edge_id: int
    geometry: LineString
    length: float
    highway: str


class SpatialIndex:
    """Spatial index for fast nearest-edge queries."""
    
    def __init__(self, edges_csv_path: str):
        """
        Initialize spatial index from edge CSV.
        
        Args:
            edges_csv_path: Path to CSV file with columns: id, geometry, length, highway
        """
        self.edges_csv_path = Path(edges_csv_path)
        self.edges: Dict[int, EdgeData] = {}
        self.idx = index.Index()
        self._load_edges()
    
    def _load_edges(self):
        """Load edges from CSV and build spatial index."""
        logger.info(f"Loading edges from {self.edges_csv_path}")
        
        if not self.edges_csv_path.exists():
            raise FileNotFoundError(f"Edge CSV not found: {self.edges_csv_path}")
        
        df = pd.read_csv(self.edges_csv_path)
        required_cols = ['id', 'geometry']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        logger.info(f"Parsing {len(df)} edges...")
        
        for idx_row, row in df.iterrows():
            try:
                edge_id = int(row['id'])
                geom = wkt.loads(row['geometry'])
                
                if not isinstance(geom, LineString):
                    logger.warning(f"Edge {edge_id} has non-LineString geometry: {type(geom)}")
                    continue
                
                # Extract optional metadata
                length = float(row.get('length', 0.0))
                highway = str(row.get('highway', 'unknown'))
                
                # Store edge data
                edge_data = EdgeData(
                    edge_id=edge_id,
                    geometry=geom,
                    length=length,
                    highway=highway
                )
                self.edges[edge_id] = edge_data
                
                # Add to spatial index (using bounding box)
                bounds = geom.bounds  # (minx, miny, maxx, maxy)
                self.idx.insert(edge_id, bounds)
                
            except Exception as e:
                logger.warning(f"Failed to parse edge at row {idx_row}: {e}")
                continue
        
        logger.info(f"Loaded {len(self.edges)} edges into spatial index")
    
    def find_nearest_edge(self, lat: float, lon: float, max_candidates: int = 10) -> Optional[Tuple[int, float]]:
        """
        Find the nearest edge to a given point.
        
        Args:
            lat: Latitude
            lon: Longitude
            max_candidates: Number of nearby edges to consider
        
        Returns:
            Tuple of (edge_id, distance) or None if no edges found
        """
        edges = self.find_nearest_edges(lat, lon, max_results=1, max_candidates=max_candidates)
        if not edges:
            return None
        return edges[0]
    
    def find_nearest_edges(self, lat: float, lon: float, max_results: int = 5, max_candidates: int = 20) -> list:
        """
        Find multiple nearest edges to a given point, sorted by distance.
        
        Args:
            lat: Latitude
            lon: Longitude
            max_results: Maximum number of results to return
            max_candidates: Number of nearby edges to consider from spatial index
        
        Returns:
            List of (edge_id, distance) tuples, sorted by distance (closest first)
        """
        point = Point(lon, lat)  # Shapely uses (x, y) = (lon, lat)
        
        # Query spatial index for nearby edges
        nearby_ids = list(self.idx.nearest(point.bounds, max_candidates))
        
        if not nearby_ids:
            logger.warning(f"No edges found near ({lat}, {lon})")
            return []
        
        # Compute actual distances for all nearby edges
        edge_distances = []
        
        for edge_id in nearby_ids:
            if edge_id not in self.edges:
                continue
            
            edge_geom = self.edges[edge_id].geometry
            dist = point.distance(edge_geom)
            edge_distances.append((edge_id, dist))
        
        # Sort by distance and return top N
        edge_distances.sort(key=lambda x: x[1])
        results = edge_distances[:max_results]
        
        logger.debug(f"Found {len(results)} nearest edges to ({lat}, {lon})")
        return results
    
    def find_edges_within_radius(self, lat: float, lon: float, radius_meters: float, max_results: int = 10) -> list:
        """
        Find all edges within a radius (in meters) of a given point.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_meters: Search radius in meters
            max_results: Maximum number of results to return
        
        Returns:
            List of (edge_id, distance) tuples, sorted by distance (closest first)
        """
        point = Point(lon, lat)
        
        # Convert radius from meters to approximate degrees
        # At equator: 1 degree ≈ 111,320 meters
        # This is approximate and works best for small radii
        radius_degrees = radius_meters / 111320.0
        
        # Create search box
        search_box = (
            lon - radius_degrees,
            lat - radius_degrees,
            lon + radius_degrees,
            lat + radius_degrees
        )
        
        # Query spatial index
        candidate_ids = list(self.idx.intersection(search_box))
        
        if not candidate_ids:
            logger.warning(f"No edges found within {radius_meters}m of ({lat}, {lon})")
            return []
        
        # Compute actual distances and filter by radius
        edge_distances = []
        
        for edge_id in candidate_ids:
            if edge_id not in self.edges:
                continue
            
            edge_geom = self.edges[edge_id].geometry
            # Distance in degrees (approximate)
            dist_degrees = point.distance(edge_geom)
            # Convert to meters (approximate)
            dist_meters = dist_degrees * 111320.0
            
            if dist_meters <= radius_meters:
                edge_distances.append((edge_id, dist_meters))
        
        # Sort by distance and return top N
        edge_distances.sort(key=lambda x: x[1])
        results = edge_distances[:max_results]
        
        logger.debug(f"Found {len(results)} edges within {radius_meters}m of ({lat}, {lon})")
        return results
    
    def get_edge(self, edge_id: int) -> Optional[EdgeData]:
        """Get edge data by ID."""
        return self.edges.get(edge_id)
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box of all edges.
        
        Returns:
            (min_lon, min_lat, max_lon, max_lat)
        """
        if not self.edges:
            return (-180, -90, 180, 90)
        
        all_bounds = [edge.geometry.bounds for edge in self.edges.values()]
        min_x = min(b[0] for b in all_bounds)
        min_y = min(b[1] for b in all_bounds)
        max_x = max(b[2] for b in all_bounds)
        max_y = max(b[3] for b in all_bounds)
        
        return (min_x, min_y, max_x, max_y)


class DatasetRegistry:
    """Registry for managing multiple datasets."""
    
    def __init__(self):
        self.datasets: Dict[str, Dict[str, str]] = {}
        self.spatial_indices: Dict[str, SpatialIndex] = {}
    
    def register_dataset(self, name: str, shortcuts_path: str, edges_path: str, binary_path: str):
        """Register a new dataset."""
        self.datasets[name] = {
            'shortcuts_path': shortcuts_path,
            'edges_path': edges_path,
            'binary_path': binary_path
        }
        logger.info(f"Registered dataset: {name}")
    
    def load_dataset(self, name: str):
        """Load spatial index for a dataset."""
        if name not in self.datasets:
            raise ValueError(f"Unknown dataset: {name}")
        
        if name in self.spatial_indices:
            logger.debug(f"Dataset {name} already loaded")
            return
        
        edges_path = self.datasets[name]['edges_path']
        logger.info(f"Loading spatial index for {name}...")
        self.spatial_indices[name] = SpatialIndex(edges_path)
        logger.info(f"Dataset {name} loaded successfully")
    
    def get_spatial_index(self, name: str) -> SpatialIndex:
        """Get spatial index for a dataset, loading it if necessary."""
        if name not in self.spatial_indices:
            self.load_dataset(name)
        return self.spatial_indices[name]
    
    def get_dataset_info(self, name: str) -> Dict[str, str]:
        """Get dataset configuration."""
        if name not in self.datasets:
            raise ValueError(f"Unknown dataset: {name}")
        return self.datasets[name]
    
    def list_datasets(self) -> list:
        """List all registered datasets."""
        return list(self.datasets.keys())
