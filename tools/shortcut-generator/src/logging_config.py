
import logging
import time
from pathlib import Path

# Global verbose flag (can be set by main.py)
VERBOSE = True

def setup_logging(name: str = None, level: str = "INFO", verbose: bool = True) -> logging.Logger:
    """
    Setup logging to file and console.
    Logs are saved in 'logs/' directory with timestamp.
    Configures the ROOT logger so all modules log to the file.
    
    Args:
        name: Log file name prefix
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        verbose: If False, suppresses per-item detail logs
    """
    global VERBOSE
    VERBOSE = verbose
    
    root_logger = logging.getLogger()
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times
    if root_logger.hasHandlers():
        return logging.getLogger(name)
    
    # Create logs directory relative to project root (parent of src/)
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Timestamped log file with script name
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    prefix = name if name else "duckdb_shortcuts"
    log_file = log_dir / f"{prefix}_{timestamp}.log"
    
    # Formatter
    formatter = logging.Formatter(
        '[%(levelname)-7s] %(asctime)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger(name)

def log_section(logger: logging.Logger, title: str, width: int = 60):
    """Log a section header with separators."""
    separator = "=" * width
    logger.info(separator)
    logger.info(title)
    logger.info(separator)

def log_dict(logger: logging.Logger, data: dict, title: str = None):
    """Log dictionary as formatted key-value pairs."""
    if title:
        logger.info(f"--- {title} ---")
    if not data:
        return
    max_key_len = max(len(str(k)) for k in data.keys())
    for key, value in data.items():
        logger.info(f"{str(key).ljust(max_key_len)} : {value}")

