import argparse
import json
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def compute_zoom(area_deg2: float) -> int:
    """Estimate a reasonable default zoom level from boundary area in degrees^2."""
    if area_deg2 > 5:
        return 9
    elif area_deg2 > 1:
        return 10
    elif area_deg2 > 0.1:
        return 11
    elif area_deg2 > 0.01:
        return 12
    return 13


def add_metadata(city: str):
    boundary_file = PROJECT_ROOT / f"tools/duckOSM/data/boundaries/{city}.geojson"
    db_file = PROJECT_ROOT / f"data/{city}.duckdb"

    if not boundary_file.exists():
        print(f"Error: boundary file not found: {boundary_file}")
        sys.exit(1)

    if not db_file.exists():
        print(f"Error: DuckDB file not found: {db_file}")
        sys.exit(1)

    with open(boundary_file) as f:
        geojson = json.load(f)

    # Compute centroid and bounding box from the boundary geometry
    coords = []

    def collect_coords(geometry):
        gtype = geometry.get("type")
        if gtype == "Point":
            coords.append(geometry["coordinates"])
        elif gtype in ("LineString", "MultiPoint"):
            coords.extend(geometry["coordinates"])
        elif gtype in ("Polygon", "MultiLineString"):
            for ring in geometry["coordinates"]:
                coords.extend(ring)
        elif gtype == "MultiPolygon":
            for polygon in geometry["coordinates"]:
                for ring in polygon:
                    coords.extend(ring)

    features = geojson.get("features", [geojson] if geojson.get("type") != "FeatureCollection" else [])
    for feature in features:
        collect_coords(feature.get("geometry", feature))

    if not coords:
        print("Error: could not extract coordinates from boundary GeoJSON")
        sys.exit(1)

    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]

    center_lon = (min(lons) + max(lons)) / 2
    center_lat = (min(lats) + max(lats)) / 2
    area = (max(lons) - min(lons)) * (max(lats) - min(lats))
    zoom = compute_zoom(area)

    # Get the first feature's geometry as the boundary
    if features and features[0].get("geometry"):
        boundary_geojson = json.dumps(features[0]["geometry"])
    else:
        boundary_geojson = json.dumps(geojson)

    con = duckdb.connect(str(db_file))
    con.execute("""
        CREATE TABLE IF NOT EXISTS visualization_metadata (
            boundary_geojson JSON,
            center_lat DOUBLE,
            center_lon DOUBLE,
            initial_zoom INTEGER
        )
    """)
    con.execute("DELETE FROM visualization_metadata")
    con.execute(
        "INSERT INTO visualization_metadata VALUES (?, ?, ?, ?)",
        [boundary_geojson, center_lat, center_lon, zoom]
    )
    con.close()

    print(f"  Added visualization metadata for '{city}': center=[{center_lat:.4f}, {center_lon:.4f}], zoom={zoom}")


def main():
    parser = argparse.ArgumentParser(description="Add visualization metadata to a city DuckDB")
    parser.add_argument("--city", required=True, help="City name")
    args = parser.parse_args()
    add_metadata(args.city)


if __name__ == "__main__":
    main()
