from pyrosm import OSM
import pandas as pd

pbf_file = "data/maps/Vancouver.osm.pbf"
osm = OSM(pbf_file)

print(f"Loading boundaries from {pbf_file}...")
boundaries = osm.get_boundaries()

import os

# Create boundary directory
os.makedirs("data/boundaries", exist_ok=True)

if boundaries is not None:
    # Set of districts to extract
    targets = ["Burnaby", "Vancouver", "Metro Vancouver Regional District"]
    
    for target in targets:
        print(f"Extracting boundary for {target}...")
        try:
            target_gdf = boundaries[boundaries["name"] == target]
            print(f"Found {len(target_gdf)} rows for {target}")
            if not target_gdf.empty:
                # Dissolve if multiple rows
                target_gdf = target_gdf.dissolve(by="name")
                print(f"Geometry type after dissolve: {target_gdf.geometry.iloc[0].geom_type}")
                
                filename = target.lower().replace(" ", "_") + ".geojson"
                filepath = os.path.join("data/boundaries", filename)
                target_gdf.to_file(filepath, driver='GeoJSON')
                print(f"Saved to {filepath}")
            else:
                print(f"Warning: {target} not found in boundaries.")
        except Exception as e:
            print(f"Error extracting {target}: {e}")
else:
    print("No boundaries found in PBF.")
