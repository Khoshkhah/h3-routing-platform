import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DUCKOSM_CONFIG_DIR = PROJECT_ROOT / "tools/duckOSM/config"
SHORTCUT_CONFIG_DIR = PROJECT_ROOT / "tools/shortcut-generator/config"
SOURCES_FILE = DUCKOSM_CONFIG_DIR / "sources.yaml"
DATASETS_FILE = PROJECT_ROOT / "services/api-gateway/config/datasets.yaml"


def load_sources():
    with open(SOURCES_FILE) as f:
        return yaml.safe_load(f)["sources"]


def create_duckosm_config(city: str):
    output_file = DUCKOSM_CONFIG_DIR / f"{city}.yaml"
    if output_file.exists():
        print(f"  duckOSM config already exists: {output_file.relative_to(PROJECT_ROOT)}")
        return

    default_file = DUCKOSM_CONFIG_DIR / "default.yaml"
    with open(default_file) as f:
        config = yaml.safe_load(f)

    config["name"] = city
    config["pbf_path"] = f"data/maps/{city}.osm.pbf"
    config["output_path"] = "../../data"
    config["boundary_path"] = f"data/boundaries/{city}.geojson"

    with open(output_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"  Created: {output_file.relative_to(PROJECT_ROOT)}")


def create_shortcut_config(city: str):
    output_file = SHORTCUT_CONFIG_DIR / f"{city}_duckdb.yaml"
    if output_file.exists():
        print(f"  Shortcut config already exists: {output_file.relative_to(PROJECT_ROOT)}")
        return

    default_file = SHORTCUT_CONFIG_DIR / "default_duckdb.yaml"
    with open(default_file) as f:
        config = yaml.safe_load(f)

    config["input"]["name"] = city
    config["input"]["database_path"] = "../../data"

    with open(output_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"  Created: {output_file.relative_to(PROJECT_ROOT)}")


def register_dataset(city: str, place: str):
    with open(DATASETS_FILE) as f:
        datasets_config = yaml.safe_load(f)

    existing = [d["name"] for d in datasets_config["datasets"]]
    if city in existing:
        print(f"  datasets.yaml already contains: {city}")
        return

    short_name = place.split(",")[0].strip()
    datasets_config["datasets"].append({
        "name": city,
        "db_path": f"{{data_root}}/{city}.duckdb",
        "short_name": short_name,
        "description": place,
    })

    with open(DATASETS_FILE, "w") as f:
        yaml.dump(datasets_config, f, default_flow_style=False, sort_keys=False)

    print(f"  Added '{city}' to services/api-gateway/config/datasets.yaml")


def main():
    parser = argparse.ArgumentParser(description="Generate duckOSM and shortcut-generator configs for a city")
    parser.add_argument("--city", required=True, help="City name (must exist in sources.yaml)")
    args = parser.parse_args()

    city = args.city
    sources = load_sources()

    if city not in sources:
        print(f"Error: '{city}' not found in sources.yaml")
        print(f"Available: {', '.join(sources.keys())}")
        sys.exit(1)

    print(f"Generating configs for: {city}")
    create_duckosm_config(city)
    create_shortcut_config(city)
    register_dataset(city, sources[city]["place"])
    print("Done.")


if __name__ == "__main__":
    main()
