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
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


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
class LoggingConfig:
    level: str = "INFO"
    verbose: bool = True


@dataclass
class ParallelConfig:
    workers: int = 1           # 1 = single-threaded, >1 = parallel
    chunk_size: int = 1000


@dataclass
class Config:
    input: InputConfig = field(default_factory=InputConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)
    duckdb: DuckDBConfig = field(default_factory=DuckDBConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)

    def resolve_paths(self):
        """Resolve template variables like {district} in paths."""
        district = self.input.district
        
        # Resolve input paths
        self.input.edges_file = self.input.edges_file.format(district=district)
        self.input.graph_file = self.input.graph_file.format(district=district)
        
        # Resolve output paths
        self.output.shortcuts_file = self.output.shortcuts_file.format(district=district)
        
        # Convert relative paths to absolute
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
