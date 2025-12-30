import argparse
import subprocess
import sys
import json
import logging
import os
from pathlib import Path
import h3_toolkit as h3t

import filter_pbf as pbf_filter

# Configure logging
Path('logs').mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler("logs/filter_cell.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("extract-cell")

def main():
    parser = argparse.ArgumentParser(description="Extract PBF for a buffered H3 cell using H3-Toolkit.")
    parser.add_argument("--input", required=True, help="Input PBF file")
    parser.add_argument("--cell", required=True, help="H3 Cell Index (Hex)")
    parser.add_argument("--output", help="Output PBF file (default: cell-{cell}.osm.pbf)")
    parser.add_argument("--boundary-res", type=int, default=10, help="Intermediate resolution for boundary tracing (default: 10)")
    parser.add_argument("--convex-hull", action="store_true", help="Use fast convex hull instead of precise union")
    # parser.add_argument("--keep-boundary", action="store_true", help="Keep the generated GeoJSON boundary file") # Always kept now

    args = parser.parse_args()

    if not Path(args.input).exists():
        logger.error(f"Input file {args.input} not found")
        sys.exit(1)

    logger.info(f"Generating buffered boundary for cell {args.cell} (Boundary Res: {args.boundary_res})...")

    try:
        # Generate boundary using H3-Toolkit (C++ accelerated)
        boundary = h3t.get_buffered_boundary_polygon_cpp(
            args.cell, 
            intermediate_res=args.boundary_res, 
            use_convex_hull=args.convex_hull
        )
    except Exception as e:
        logger.error(f"Error generating boundary: {e}")
        sys.exit(1)

    # Save to boundary file
    boundaries_dir = Path("data/boundaries")
    boundaries_dir.mkdir(parents=True, exist_ok=True)
    boundary_file = boundaries_dir / f"cell_{args.cell}.geojson"
    
    # Osmium expects a FeatureCollection usually, but Feature handles often work. 
    # Wrapping in FeatureCollection is safer.
    geojson_wrapper = {
        "type": "FeatureCollection",
        "features": [boundary]
    }

    with open(boundary_file, 'w') as f:
        json.dump(geojson_wrapper, f)
    
    logger.info(f"Saved boundary to {boundary_file}")

    # Determine output filename
    output_file = args.output
    if not output_file:
        maps_dir = Path("data/maps")
        maps_dir.mkdir(parents=True, exist_ok=True)
        output_file = maps_dir / f"cell_{args.cell}.osm.pbf"

    logger.info(f"Filtering PBF to {output_file}...")

    try:
        pbf_filter.filter_pbf(args.input, boundary_file, output_file)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)
    finally:
         logger.info(f"Boundary file persisted at {boundary_file}")

if __name__ == "__main__":
    main()
