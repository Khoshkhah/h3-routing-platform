#!/usr/bin/env python3
"""
Standalone route visualization script
Generates an HTML file with the map - no Jupyter needed!
"""

import subprocess
import pandas as pd
import folium
from shapely import wkt
import yaml
from pathlib import Path
import h3
import sys

# Configuration
DATASET_INDEX = 0  # 0 for Somerset, 1 for Burnaby
SOURCE_EDGE = 2311
TARGET_EDGE = 447

print("="*60)
print("ROUTING VISUALIZATION")
print("="*60)

# Load config
config_path = Path(__file__).parent.parent / 'config/datasets.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

dataset = config['datasets'][DATASET_INDEX].copy()

# Adjust paths
for key in ['shortcuts_path', 'edges_path', 'binary_path']:
    if key in dataset and not Path(dataset[key]).is_absolute():
        dataset[key] = str(Path(__file__).parent.parent / dataset[key])

print(f"\nDataset: {dataset['name']}")

# Load edges
print(f"Loading edges...")
edges_df = pd.read_csv(dataset['edges_path'])
edge_lookup = edges_df.set_index('id').to_dict('index')
print(f"Loaded {len(edges_df)} edges")

# Query path
print(f"\nQuerying path: {SOURCE_EDGE} → {TARGET_EDGE}")
cmd = [
    dataset['binary_path'],
    '--shortcuts', dataset['shortcuts_path'],
    '--edges', dataset['edges_path'],
    '--source', str(SOURCE_EDGE),
    '--target', str(TARGET_EDGE)
]

result = subprocess.run(cmd, capture_output=True, text=True, check=True)
output = result.stdout

# Parse paths
shortcut_path = []
expanded_path = []

for line in output.strip().split('\n'):
    if 'Shortcut path:' in line or ('Path:' in line and 'Expanded' not in line):
        path_str = line.split(':', 1)[1].strip()
        if '->' in path_str:
            shortcut_path = [int(x.strip()) for x in path_str.split('->')]
        else:
            path_str = path_str.strip('[]')
            if path_str:
                shortcut_path = [int(x.strip()) for x in path_str.split(',')]
                
    elif 'Expanded path:' in line or 'Expanded base edge path:' in line:
        path_str = line.split(':', 1)[1].strip()
        if '->' in path_str:
            expanded_path = [int(x.strip()) for x in path_str.split('->')]
        else:
            path_str = path_str.strip('[]')
            if path_str:
                expanded_path = [int(x.strip()) for x in path_str.split(',')]

print(f"Shortcut path ({len(shortcut_path)} edges): {' → '.join(map(str, shortcut_path))}")
print(f"Expanded path ({len(expanded_path)} edges): {' → '.join(map(str, expanded_path))}")

# Create visualization
print(f"\nCreating map...")

# Get path coordinates
all_coords = []
for edge_id in expanded_path:
    if edge_id in edge_lookup:
        geom = wkt.loads(edge_lookup[edge_id]['geometry'])
        all_coords.extend(list(geom.coords))

center_lat = sum(c[1] for c in all_coords) / len(all_coords)
center_lon = sum(c[0] for c in all_coords) / len(all_coords)

# Create map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=13,
    tiles='OpenStreetMap'
)

# Add H3 base cells (resolution 0) for source edge
try:
    source_edge_data = edge_lookup[expanded_path[0]]
    
    # Add incoming cell base
    source_incoming_cell = source_edge_data['incoming_cell']
    if source_incoming_cell != 0:
        source_base_cell = h3.cell_to_parent(h3.int_to_str(source_incoming_cell), 0)
        base_boundary = h3.cell_to_boundary(source_base_cell)
        base_coords = [(lat, lon) for lat, lon in base_boundary]
        
        folium.Polygon(
            base_coords,
            color='blue',
            weight=2,
            fill=True,
            fillColor='blue',
            fillOpacity=0.05,
            popup=f"Base H3 Cell (res 0) - Incoming Cell"
        ).add_to(m)
        print(f"Added H3 base cell for incoming_cell (resolution 0)")
    
    # Add outgoing cell base
    source_outgoing_cell = source_edge_data['outgoing_cell']
    if source_outgoing_cell != 0:
        outgoing_base_cell = h3.cell_to_parent(h3.int_to_str(source_outgoing_cell), 0)
        outgoing_boundary = h3.cell_to_boundary(outgoing_base_cell)
        outgoing_coords = [(lat, lon) for lat, lon in outgoing_boundary]
        
        folium.Polygon(
            outgoing_coords,
            color='purple',
            weight=2,
            fill=True,
            fillColor='purple',
            fillOpacity=0.05,
            popup=f"Base H3 Cell (res 0) - Outgoing Cell"
        ).add_to(m)
        print(f"Added H3 base cell for outgoing_cell (resolution 0)")
except Exception as e:
    print(f"Could not add H3 cells: {e}")

# Add expanded path (red)
for edge_id in expanded_path:
    if edge_id in edge_lookup:
        edge_data = edge_lookup[edge_id]
        geom = wkt.loads(edge_data['geometry'])
        coords = [(lat, lon) for lon, lat in geom.coords]
        
        is_source = (edge_id == expanded_path[0])
        is_dest = (edge_id == expanded_path[-1])
        
        edge_color = 'green' if is_source else ('red' if is_dest else 'orange')
        edge_weight = 6 if (is_source or is_dest) else 3
        
        folium.PolyLine(
            coords,
            color=edge_color,
            weight=edge_weight,
            opacity=0.8,
            popup=f"Edge {edge_id}"
        ).add_to(m)

# Add shortcut path (blue, on top)
for edge_id in shortcut_path:
    if edge_id in edge_lookup:
        edge_data = edge_lookup[edge_id]
        geom = wkt.loads(edge_data['geometry'])
        coords = [(lat, lon) for lon, lat in geom.coords]
        
        folium.PolyLine(
            coords,
            color='blue',
            weight=5,
            opacity=0.9,
            popup=f"Shortcut Edge {edge_id}"
        ).add_to(m)

# Add markers
start_geom = wkt.loads(edge_lookup[expanded_path[0]]['geometry'])
start_coords = list(start_geom.coords)[0]
folium.Marker(
    [start_coords[1], start_coords[0]],
    popup=f"Start (Edge {expanded_path[0]})",
    icon=folium.Icon(color='green', icon='play')
).add_to(m)

end_geom = wkt.loads(edge_lookup[expanded_path[-1]]['geometry'])
end_coords = list(end_geom.coords)[-1]
folium.Marker(
    [end_coords[1], end_coords[0]],
    popup=f"End (Edge {expanded_path[-1]})",
    icon=folium.Icon(color='red', icon='stop')
).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 280px; height: 140px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:14px; padding: 10px">
<b>Legend</b><br>
<i style="background: blue; width: 30px; height: 3px; display: inline-block;"></i> Shortcut Path<br>
<i style="background: orange; width: 30px; height: 3px; display: inline-block;"></i> Expanded Path<br>
<i style="background: blue; width: 30px; height: 15px; display: inline-block; opacity: 0.2;"></i> H3 Incoming (res 0)<br>
<i style="background: purple; width: 30px; height: 15px; display: inline-block; opacity: 0.2;"></i> H3 Outgoing (res 0)
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
output_file = Path(__file__).parent / f'route_{SOURCE_EDGE}_to_{TARGET_EDGE}.html'
m.save(str(output_file))

print(f"\n✓ Map saved to: {output_file}")
print(f"\nOpen this file in your browser to view the route!")
print("="*60)
