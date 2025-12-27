"""
Configuration Loader for Shortcut Generation

Loads YAML configuration files from the config/ folder, merging with defaults.
Usage:
    from config_loader import load_config
    cfg = load_config("burnaby")  # Loads config/burnaby.yaml merged with default.yaml
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Project root
# traversing up from src/config_loader.py: src -> shortcut-generator -> tools -> h3-routing-platform
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


@dataclass
class InputConfig:
    edges_file: str = ""
    graph_file: str = ""
    district: str = "Burnaby"


@dataclass
class OutputConfig:
    directory: str = "output"
    shortcuts_file: str = "{district}_shortcuts"
    persist_dir: str = "persist"


@dataclass
class AlgorithmConfig:
    name: str = "partitioned"  # partitioned only (uses sp_method setting)
    sp_method: str = "SCIPY"   # SCIPY, PURE, HYBRID
    hybrid_res: int = 10       # Resolution threshold for HYBRID mode
    partition_res: int = 7
    min_res: int = 0
    max_res: int = 15


@dataclass
class DuckDBConfig:
    memory_limit: str = "12GB"
    threads: Optional[int] = None
    fresh_start: bool = False  # If true, delete existing DB before running


@dataclass
class PathsConfig:
    project_root: str = str(PROJECT_ROOT)
    # Default paths relative to project root
    osm_importer: str = "{project_root}/tools/osm-importer"
    data_output: str = "{project_root}/data"
    boundaries: str = "{osm_importer}/data/boundaries"
    input_data: str = "{osm_importer}/data/output"


@dataclass
class InputConfig:
    edges_file: str = ""
    graph_file: str = ""
    boundary_file: Optional[str] = None
    district: str = "Burnaby"


@dataclass
class OutputConfig:
    directory: str = "output"
    shortcuts_file: str = "{district}_shortcuts"
    persist_dir: str = "persist"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    verbose: bool = True


@dataclass
class ParallelConfig:
    workers: int = 1           # Default for all phases if phase-specific not set
    workers_phase1: Optional[int] = None  # Override for Phase 1
    workers_phase2: Optional[int] = None  # Override for Phase 2 (currently unused)
    workers_phase3: Optional[int] = None  # Override for Phase 3 (currently unused)
    workers_phase4: Optional[int] = None  # Override for Phase 4
    chunk_size: int = 1000


@dataclass
class Config:
    paths: PathsConfig = field(default_factory=PathsConfig)
    input: InputConfig = field(default_factory=InputConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)
    duckdb: DuckDBConfig = field(default_factory=DuckDBConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)

    def resolve_paths(self):
        """Resolve template variables like {district} and {project_root} in paths."""
        # 1. Resolve paths config variables first (e.g. project_root)
        # Allow env var override for project_root
        if os.environ.get("H3_ROUTING_ROOT"):
            self.paths.project_root = os.environ["H3_ROUTING_ROOT"]
            
        # Helper to resolve a path string with variables
        def resolve(path_str, context):
            if not path_str:
                return path_str
            # Simple iterative resolution to handle nested variables
            for _ in range(3):  # Limit depth
                try:
                    new_path = path_str.format(**context)
                    if new_path == path_str:
                        break
                    path_str = new_path
                except KeyError:
                    break # Stop if key missing (might be intended)
                except ValueError:
                    break # Malformed format
            return path_str

        # Resolve paths section itself (order matters)
        path_context = {"project_root": self.paths.project_root}
        self.paths.osm_importer = resolve(self.paths.osm_importer, path_context)
        
        path_context["osm_importer"] = self.paths.osm_importer
        self.paths.data_output = resolve(self.paths.data_output, path_context)
        self.paths.boundaries = resolve(self.paths.boundaries, path_context)
        self.paths.input_data = resolve(self.paths.input_data, path_context)
        
        # 2. Update context with all resolved paths and district
        full_context = {
            "district": self.input.district,
            **self.paths.__dict__
        }
        
        # 3. Resolve Input paths
        self.input.edges_file = resolve(self.input.edges_file, full_context)
        self.input.graph_file = resolve(self.input.graph_file, full_context)
        if self.input.boundary_file:
            self.input.boundary_file = resolve(self.input.boundary_file, full_context)
        
        # 4. Resolve Output paths
        self.output.shortcuts_file = resolve(self.output.shortcuts_file, full_context)
        self.output.directory = resolve(self.output.directory, full_context)
        self.output.persist_dir = resolve(self.output.persist_dir, full_context)
        
        # Ensure outputs are absolute
        if not os.path.isabs(self.output.directory):
             self.output.directory = str(PROJECT_ROOT / self.output.directory)
        if not os.path.isabs(self.output.persist_dir):
             self.output.persist_dir = str(PROJECT_ROOT / self.output.persist_dir)


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml(path: Path) -> dict:
    """Load a YAML file."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


def dict_to_config(data: dict) -> Config:
    """Convert a dictionary to a Config dataclass."""
    cfg = Config()
    
    if 'paths' in data:
        for k, v in data['paths'].items():
            if hasattr(cfg.paths, k):
                setattr(cfg.paths, k, v)

    if 'input' in data:
        for k, v in data['input'].items():
            if hasattr(cfg.input, k):
                setattr(cfg.input, k, v)
    
    if 'output' in data:
        for k, v in data['output'].items():
            if hasattr(cfg.output, k):
                setattr(cfg.output, k, v)
    
    if 'algorithm' in data:
        for k, v in data['algorithm'].items():
            if hasattr(cfg.algorithm, k):
                setattr(cfg.algorithm, k, v)
    
    if 'duckdb' in data:
        for k, v in data['duckdb'].items():
            if hasattr(cfg.duckdb, k):
                setattr(cfg.duckdb, k, v)
    
    if 'logging' in data:
        for k, v in data['logging'].items():
            if hasattr(cfg.logging, k):
                setattr(cfg.logging, k, v)
    
    if 'parallel' in data:
        for k, v in data['parallel'].items():
            if hasattr(cfg.parallel, k):
                setattr(cfg.parallel, k, v)
    
    return cfg


def load_config(profile: str = "default") -> Config:
    """
    Load configuration from a profile.
    
    Args:
        profile: Name of the config file (without .yaml extension)
                 e.g., "burnaby" loads config/burnaby.yaml
    
    Returns:
        Config object with all settings merged from default.yaml + profile.yaml
    """
    # Load default config
    default_data = load_yaml(CONFIG_DIR / "default.yaml")
    
    # Load profile config and merge
    if profile != "default":
        profile_data = load_yaml(CONFIG_DIR / f"{profile}.yaml")
        merged_data = deep_merge(default_data, profile_data)
    else:
        merged_data = default_data
    
    # Convert to Config object
    cfg = dict_to_config(merged_data)
    cfg.resolve_paths()
    
    return cfg


if __name__ == "__main__":
    # Test loading configs
    print("Loading default config:")
    cfg = load_config("default")
    print(f"  District: {cfg.input.district}")
    print(f"  Algorithm: {cfg.algorithm.name}")
    print(f"  SP Method: {cfg.algorithm.sp_method}")
    
    print("\nLoading burnaby config:")
    cfg = load_config("burnaby")
    print(f"  District: {cfg.input.district}")
    print(f"  Edges file: {cfg.input.edges_file}")
    print(f"  Output dir: {cfg.output.directory}")
