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
    parser = argparse.ArgumentParser(description="Filter PBF file by GeoJSON boundary using osmium-tool")
    parser.add_argument("--input", required=True, help="Input PBF file")
    parser.add_argument("--boundary", required=True, help="GeoJSON boundary file")
    parser.add_argument("--output", required=True, help="Output PBF file")
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        logger.error(f"Input file {args.input} not found")
        sys.exit(1)
    if not Path(args.boundary).exists():
        logger.error(f"Boundary file {args.boundary} not found")
        sys.exit(1)
        
    logger.info(f"Filtering PBF using osmium-tool...")
    logger.info(f"Input: {args.input}")
    logger.info(f"Boundary: {args.boundary}")
    logger.info(f"Output: {args.output}")
    
    try:
        # Generate the osmium extract command
        # -p: boundary polygon
        # -s: strategy (simple or complete_ways)
        # We use complete_ways to ensure we don't break way geometries
        cmd = [
            "osmium", "extract",
            "-p", args.boundary,
            args.input,
            "-o", args.output,
            "--overwrite"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("Filtering completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during osmium execution: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'osmium' command not found. Please install osmium-tool.")
        sys.exit(1)

if __name__ == "__main__":
    main()
