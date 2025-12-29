import argparse
import subprocess
import sys
import json
import logging
import os
from pathlib import Path
import h3_toolkit as h3t

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
    parser.add_argument("--keep-boundary", action="store_true", help="Keep the generated GeoJSON boundary file")

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

    # Save to temporary GeoJSON file
    boundary_file = f"boundary_{args.cell}.geojson"
    
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
        output_file = f"cell-{args.cell}.osm.pbf"

    logger.info(f"Filtering PBF to {output_file}...")

    try:
        cmd = [
            "osmium", "extract",
            "-p", boundary_file,
            args.input,
            "-o", output_file,
            "--overwrite"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # osmium usually prints to stderr
        if result.stderr:
            logger.info(f"Osmium Output:\n{result.stderr.strip()}")
        
        logger.info("Filtering completed successfully!")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during osmium execution: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("Error: 'osmium' command not found. Please install osmium-tool (sudo apt install osmium-tool).")
        sys.exit(1)
    finally:
        if not args.keep_boundary and Path(boundary_file).exists():
            Path(boundary_file).unlink()
            logger.info(f"Removed temporary boundary file {boundary_file}")
        elif args.keep_boundary:
             logger.info(f"Kept boundary file {boundary_file}")

if __name__ == "__main__":
    main()
