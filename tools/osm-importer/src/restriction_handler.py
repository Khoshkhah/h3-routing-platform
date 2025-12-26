import osmium
import pandas as pd

class RestrictionHandler(osmium.SimpleHandler):
    """Extract turn restrictions from OSM relations."""
    
    def __init__(self):
        super().__init__()
        self.restrictions = []
    
    def relation(self, r):
        if 'restriction' not in r.tags:
            return
        
        rel = {
            "id": r.id,
            "restriction": r.tags["restriction"],
            "from": None,
            "via": None,
            "to": None
        }
        
        for m in r.members:
            if m.role == "from" and m.type == "w":
                rel["from"] = str(m.ref)
            elif m.role == "via" and m.type == "n":
                rel["via"] = str(m.ref)
            elif m.role == "to" and m.type == "w":
                rel["to"] = str(m.ref)
        
        self.restrictions.append(rel)

class TurnRestrictionProcessor:
    @staticmethod
    def extract_restrictions(pbf_file):
        """Extract turn restrictions from PBF file."""
        handler = RestrictionHandler()
        handler.apply_file(pbf_file, locations=False)
        return pd.DataFrame(handler.restrictions)
    
    @staticmethod
    def apply_restrictions(G, restriction_df):
        """Apply turn restrictions to graph."""
        forbidden = []
        
        for _, row in restriction_df.iterrows():
            via_node = row['via']
            from_way = row['from']
            to_way = row['to']
            
            if via_node not in G.nodes:
                continue
            
            from_edges = G.in_edges(via_node, data=True)
            to_edges = G.out_edges(via_node, data=True)
            
            from_edge = TurnRestrictionProcessor._find_edge(
                from_edges, from_way
            )
            to_edge = TurnRestrictionProcessor._find_edge(
                to_edges, to_way
            )
            
            if from_edge and to_edge:
                forbidden.append((from_edge, to_edge))
        
        return forbidden
    
    @staticmethod
    def _find_edge(edges, way_id):
        """Find edge matching a way ID."""
        for u, v, data in edges:
            osmid = data.get('osmid')
            if osmid == way_id or (isinstance(osmid, list) and way_id in osmid):
                return (u, v)
        return None
