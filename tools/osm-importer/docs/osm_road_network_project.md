# OSM to Road Conversion Project

A comprehensive Python project for converting OpenStreetMap (OSM) data into optimized road network files with turn restrictions and H3 spatial indexing.

## Project Structure

```
osm-to-road/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── network_builder.py
│   ├── speed_processor.py
│   ├── restriction_handler.py
│   ├── h3_processor.py
│   └── utils.py
├── scripts/
│   └── filter_pbf.py
├── logs/
│   ├── pipeline.log
│   └── filter.log
├── tests/
├── notebooks/
└── data/
    ├── maps/
    └── output/
```

## Core Modules

### 1. `scripts/filter_pbf.py`
A high-performance utility to clip large OSM PBF files to a specific geographic boundary using `osmium-tool`.

```python
import argparse
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
Path('logs').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler("logs/filter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("filter-pbf")

def main():
    # CLI wrapper for 'osmium extract'
    # ... (implementation calls osmium-tool)
```

### 2. `src/speed_processor.py`
Processes and predicts speed limits.

```python
import re
import pandas as pd
import numpy as np

class SpeedProcessor:
    MPH_TO_KMPH = 1.60934
    
    SPEED_DEFAULTS = {
        "motorway": 110,
        "motorway_link": 110,
        "trunk": 90,
        "trunk_link": 90,
        "primary": 70,
        "primary_link": 70,
        "secondary": 60,
        "secondary_link": 60,
        "tertiary": 50,
        "tertiary_link": 50,
        "residential": 30,
        "living_street": 30,
        "service": 20,
        "unclassified": 40,
        "road": 40,
    }
    
    @staticmethod
    def predict_maxspeed(highway):
        """Predict speed based on highway type."""
        if isinstance(highway, list):
            highway = highway[0]
        highway = str(highway).lower() if highway else ""
        return SpeedProcessor.SPEED_DEFAULTS.get(highway, 50)
    
    @staticmethod
    def fix_speed_format(df):
        """Convert speed values to km/h format."""
        speed_parts = df['maxspeed'].astype(str).str.extract(
            r'(\d+\.?\d*)\s*(mph|km/h|kmh|kph)?',
            flags=re.IGNORECASE
        )
        
        df['speed_value'] = pd.to_numeric(speed_parts[0], errors='coerce')
        df['speed_unit'] = speed_parts[1].str.lower()
        df['maxspeed'] = df['speed_value'].copy()
        
        df.loc[df['speed_unit'] == 'mph', 'maxspeed'] = (
            df['speed_value'] * SpeedProcessor.MPH_TO_KMPH
        )
        
        return df.drop(columns=['speed_value', 'speed_unit'])
    
    @staticmethod
    def process_speeds(edges_df, highway_col='highway'):
        """Process and fill missing speeds."""
        edges_df = SpeedProcessor.fix_speed_format(edges_df)
        edges_df['maxspeed'] = edges_df.apply(
            lambda row: (
                SpeedProcessor.predict_maxspeed(row[highway_col])
                if pd.isna(row['maxspeed'])
                else row['maxspeed']
            ),
            axis=1
        )
        edges_df['maxspeed'] = edges_df['maxspeed'].astype(float)
        return edges_df
```

### 3. `src/restriction_handler.py`
Extracts and processes turn restrictions.

```python
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
```

### 4. `src/h3_processor.py`
Handles H3 spatial indexing with progress tracking.

```python
import h3
from tqdm import tqdm

class H3Processor:
    @staticmethod
    def latlng_to_cell(lat, lng, resolution=15):
        """Convert coordinates to H3 cell."""
        cell_str = h3.latlng_to_cell(lat, lng, resolution)
        return h3.str_to_int(cell_str)

    @staticmethod
    def find_lca(cell1, cell2):
        """Find Lowest Common Ancestor between two H3 cells."""
        # ... (logical implementation to find common parent)

    @staticmethod
    def add_h3_cells(edges_df, nodes_df, resolution=15):
        """Add H3 cells to edges dataframe."""
        tqdm.pandas(desc="Adding H3 cells to edges")
        
        edges_df['to_cell'] = edges_df['target'].progress_apply(
            lambda t: H3Processor.latlng_to_cell(
                nodes_df.loc[t]['geometry'].y,
                nodes_df.loc[t]['geometry'].x,
                resolution
            )
        )
        edges_df['from_cell'] = edges_df['source'].progress_apply(
            lambda s: H3Processor.latlng_to_cell(
                nodes_df.loc[s]['geometry'].y,
                nodes_df.loc[s]['geometry'].x,
                resolution
            )
        )
        
        # Enforce integer type
        edges_df['to_cell'] = edges_df['to_cell'].astype(int)
        edges_df['from_cell'] = edges_df['from_cell'].astype(int)
        
        edges_df['lca_res'] = edges_df.progress_apply(
            lambda row: H3Processor.get_lca_resolution(
                row['to_cell'],
                row['from_cell']
            ),
            axis=1
        )
        return edges_df
```

### 5. `src/network_builder.py`
Main network building orchestration with progress bars and flexible boundary handling.

```python
import pandas as pd
import networkx as nx
from tqdm import tqdm
from pyrosm import OSM

class NetworkBuilder:
    def __init__(self, pbf_file, output_name):
        self.pbf_file = pbf_file
        self.output_name = output_name
        self.graph = None
        self.edges_df = None
        self.nodes_df = None
    
    def build_graph(self, network_type='driving'):
        """Build network graph from the initialized PBF file."""
        osm_district = OSM(self.pbf_file)
        # The PBF is assumed to be already clipped to the area of interest
        nodes_gdf, edges_gdf = osm_district.get_network(network_type=network_type, nodes=True)
        self.graph = osm_district.to_graph(nodes_gdf, edges_gdf, osmnx_compatible=True)
        return self.graph

    def build_edge_graph(self, forbidden_turns=None):
        """Build edge graph with progress tracking."""
        edge_graph = []
        nodes = list(self.graph.nodes)
        for node in tqdm(nodes, desc="Building edge graph"):
            incoming = self.graph.in_edges(node, data=False)
            outgoing = self.graph.out_edges(node, data=False)
            for u, v in incoming:
                for x, y in outgoing:
                    edge_graph.append(((u, v), (x, y)))
        
        new_edge_graph = list(set(edge_graph) - set(forbidden_turns))
        return pd.DataFrame(new_edge_graph, columns=['from_edge', 'to_edge'])

    def create_shortcut_table(self, edge_graph_df):
        """Create shortcut table for hierarchical routing."""
        shortcut_table = edge_graph_df.copy()
        shortcut_table['cost'] = shortcut_table['from_edge'].apply(
            lambda x: self.edges_df.loc[x]['cost']
        )
        shortcut_table['via_cell'] = shortcut_table['from_edge'].apply(
            lambda x: self.edges_df.loc[x]['to_cell']
        )
        
        shortcut_table['lca_res_from_edge'] = shortcut_table['from_edge'].apply(
            lambda x: self.edges_df.loc[x]['lca_res']
        )
        shortcut_table['lca_res_to_edge'] = shortcut_table['to_edge'].apply(
            lambda x: self.edges_df.loc[x]['lca_res']
        )
        shortcut_table['lca_res'] = shortcut_table.apply(
            lambda row: max(row['lca_res_from_edge'], row['lca_res_to_edge']),
            axis=1
        )
        return shortcut_table

    def save_outputs(self, output_dir):
        """Save files with sequential edge indexing."""
        # ... (logic to map tuples to sequential integers)
        self.edges_df["edge_index"] = self.edges_df.index.map(lambda x: self.edge_id_df.loc[[x]]['index'].values[0])
        self.edges_df.to_csv(f"{prefix}_simplified_edges_with_h3.csv", index=False)
```
```

### 6. `main.py`
The primary entry point that coordinates the entire pipeline using a configuration-first approach.

```python
import argparse
import sys
import yaml
import logging
from src.network_builder import NetworkBuilder

# Configure logging with both console and file handlers
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("osm-to-road")

def main(config_path):
    # Load config, filter PBF if needed, then run builder...
```

## Requirements

The project requires Python 3.8+ and the `osmium-tool` system utility.

```
# requirements.txt
pyrosm>=0.6.1
osmnx>=1.9.1
networkx>=3.0
geopandas>=0.14.0
pandas>=2.0.0
h3>=3.7.0
tqdm>=4.66.0
osmium>=3.6.0
pyyaml>=6.0
mapclassify>=2.6.1
```

## Installation & Usage

### 1. System Setup
Install the `osmium-tool` CLI for fast PBF clipping:
```bash
sudo apt-get update && sudo apt-get install -y osmium-tool
```

### 2. Python Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Basic Usage (Config-based)
1. Create a `config/config.yaml`:
```yaml
name: "Somerset"
pbf_path: "data/maps/Somerset.osm.pbf"
# boundary_path: "data/boundaries/somerset.geojson" # Optional
```

2. Run the pipeline:
```bash
python main.py --config config/config.yaml
```

### In Python
```python
from src.network_builder import NetworkBuilder

# Initialize builder with a pre-filtered PBF
builder = NetworkBuilder("data/maps/Somerset.osm.pbf", "Somerset")

# Simple pipeline execution
builder.build_graph()
builder.simplify_graph()
builder.extract_edges_and_nodes()
builder.process_speeds()
builder.add_h3_indexing()
builder.calculate_costs()
builder.save_outputs("data/output")
```

## Output Files

Located in the specified `output_dir` (default: `data/output/`):

- **`{name}_driving_simplified_nodes.csv`**: Network nodes.
- **`{name}_driving_edge_id.csv`**: Mapping between edge tuples and sequential IDs.
- **`{name}_driving_simplified_edges_with_h3.csv`**: Edges with `edge_index`, costs, and H3 indexing.
- **`{name}_driving_edge_graph.csv`**: Dual graph for turn restrictions.
- **`{name}_driving_shortcut_table.csv`**: Optimized routing shortcuts.

## Key Features

- **PBF Clipping**: Integrated `osmium-tool` for fast geographic filtering.
- **Config-First**: Centralized YAML configuration for all pipeline parameters.
- **Progress Tracking**: Real-time feedback via `tqdm` progress bars.
- **Persistent Logging**: Structured logs saved to the `logs/` directory.
- **Sequential Indexing**: Every edge is assigned a unique, stable `edge_index`.
- **H3 Hierarchy**: Full support for hierarchical spatial indexing and LCA resolution.

## Testing

```bash
pytest tests/ -v
```

## License

MIT License