import duckdb
from typing import List, Tuple, Optional, Dict, Any
from .core import load_shortcut_data, expand_path, ShortestPathData
from .algorithms import (
    query_uni_dijkstra,
    query_bi_dijkstra,
    query_classic,
    query_uni_lca,
    query_bi_lca,
    query_bi_lca_res,
    query_m2m,
    query_alternative
)

class Router:
    def __init__(self, db_path: str):
        # Open in read-only mode to prevent locking issues
        try:
            self.con = duckdb.connect(db_path, read_only=True)
        except:
            self.con = duckdb.connect(db_path)
            
        self.data: ShortestPathData = load_shortcut_data(self.con)
        
    def find_nearest_edges(self, lat: float, lng: float, max_candidates: int = 5) -> List[int]:
        """Find the nearest edge IDs to a coordinate using DuckDB and H3."""
        try:
            import h3
            search_radii = [5, 20, 100, 500]
            center_cell = h3.latlng_to_cell(lat, lng, 15)
            
            found_edges = []
            for radius in search_radii:
                cells = h3.grid_disk(center_cell, radius)
                cell_ints = [str(int(h3.str_to_int(c))) for c in cells]
                
                if cell_ints:
                    nb_list = ",".join(cell_ints)
                    query = f"SELECT id FROM edges WHERE to_cell IN ({nb_list}) LIMIT {max_candidates}"
                    results = self.con.execute(query).fetchall()
                    for res in results:
                        if res[0] not in found_edges:
                            found_edges.append(res[0])
                        if len(found_edges) >= max_candidates:
                            return found_edges
            
            if found_edges:
                return found_edges

            # Fallback: Radial search
            try:
                results = self.con.execute(f"""
                    SELECT id 
                    FROM edges 
                    ORDER BY (to_lat - {lat})*(to_lat - {lat}) + (to_lng - {lng})*(to_lng - {lng}) 
                    LIMIT {max_candidates}
                """).fetchall()
                return [res[0] for res in results]
            except:
                pass

            return []
        except Exception as e:
            print(f"Nearest edges matching error: {e}")
            return []

    def find_nearest_edge(self, lat: float, lng: float) -> Optional[int]:
        """Convenience wrapper for a single nearest edge."""
        edges = self.find_nearest_edges(lat, lng, max_candidates=1)
        return edges[0] if edges else None

    def _format_result(self, cost: float, path: List[int], success: bool) -> Dict[str, Any]:
        if not success:
            return {"success": False, "error": "No path found"}
        expanded = expand_path(path, self.data.via_lookup)
        return {
            "success": True,
            "distance": cost,
            "path": expanded,
            "shortcut_path": path
        }

    def route(self, source: int, target: int, algorithm: str = "classic", include_alternative: bool = False, penalty_factor: float = 2.0) -> Dict[str, Any]:
        """
        Compute route between edge IDs.
        
        The 'algorithm' parameter controls the SHORTEST PATH calculation.
        If 'include_alternative' is True, the shortest path is used to find an alternative.
        
        Supported algorithms:
        - 'dijkstra': Unidirectional Dijkstra (baseline)
        - 'bidijkstra': Bidirectional Dijkstra (no pruning)
        - 'classic': Bidirectional Hierarchical (bi_classic_sp)
        - 'unidirectional': Unidirectional Pruned (uni_lca)
        - 'pruned': Bidirectional resolution-pruned (bi_lca_res)
        - 'm2m': Many-to-many classic bidirectional
        """
        # 1. SHORTEST PATH calculation
        if algorithm == "dijkstra":
            cost, path, success = query_uni_dijkstra(source, target, self.data)
        elif algorithm == "bidijkstra":
            cost, path, success = query_bi_dijkstra(source, target, self.data)
        elif algorithm in ["unidirectional", "uni_lca"]:
            cost, path, success = query_uni_lca(source, target, self.data)
        elif algorithm == "bi_lca":
            cost, path, success = query_bi_lca(source, target, self.data)
        elif algorithm == "pruned":
            cost, path, success = query_bi_lca_res(source, target, self.data)
        elif algorithm == "classic":
             cost, path, success = query_classic(source, target, self.data)
        elif algorithm == "m2m":
            cost, path, success = query_m2m([source], [target], self.data)
        else:
            # Default to classic
            cost, path, success = query_classic(source, target, self.data)
        
        result = self._format_result(cost, path, success)
        if not result["success"]:
            return result
            
        # 2. ALTERNATIVE PATH calculation (using expanded shortest path as penalty set)
        if include_alternative:
            # The 'result["path"]' is already expanded by _format_result
            alt_cost, alt_path, alt_success = query_alternative(
                source, target, self.data, 
                penalty_factor=penalty_factor, 
                shortest_path_expanded=result["path"]
            )
            
            if alt_success:
                alt_expanded = expand_path(alt_path, self.data.via_lookup)
                result["alternative_route"] = {
                    "distance": alt_cost,
                    "path": alt_expanded,
                    "shortcut_path": alt_path
                }
                
        return result

    def route_m2m(self, sources: List[int], targets: List[int], include_alternative: bool = False, penalty_factor: float = 2.0) -> Dict[str, Any]:
        """Many-to-Many route between lists of edge IDs."""
        cost, path, success = query_m2m(sources, targets, self.data)
        result = self._format_result(cost, path, success)
        
        if result["success"] and include_alternative:
            # For M2M, alternative is found between the BEST source and BEST target discovered in the first pass
            # The 'path' starts with the best source and ends with the best target
            if path:
                best_src = path[0]
                best_tgt = path[-1]
                alt_cost, alt_path, alt_success = query_alternative(
                    best_src, best_tgt, self.data,
                    penalty_factor=penalty_factor,
                    shortest_path_expanded=result["path"]
                )
                if alt_success:
                    alt_expanded = expand_path(alt_path, self.data.via_lookup)
                    result["alternative_route"] = {
                        "distance": alt_cost,
                        "path": alt_expanded,
                        "shortcut_path": alt_path
                    }
        return result

    def route_by_coordinates(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float, **kwargs) -> Dict[str, Any]:
        """Compute route between coordinates."""
        source = self.find_nearest_edge(start_lat, start_lng)
        target = self.find_nearest_edge(end_lat, end_lng)
        
        if source is None or target is None:
            return {"success": False, "error": f"Nearest edges not found for start({source}) or end({target})"}
            
        return self.route(source, target, **kwargs)

    def route_m2m_by_coordinates(self, start_lat: float, start_lng: float, end_lat: float, end_lng: float, max_candidates: int = 5, **kwargs) -> Dict[str, Any]:
        """Compute best route between multiple nearest edge candidates."""
        sources = self.find_nearest_edges(start_lat, start_lng, max_candidates=max_candidates)
        targets = self.find_nearest_edges(end_lat, end_lng, max_candidates=max_candidates)
        
        if not sources or not targets:
            return {"success": False, "error": "No candidate edges found for start or end"}
            
        return self.route_m2m(sources, targets, **kwargs)
