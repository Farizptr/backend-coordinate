"""
Configuration file for Building Detector

This file contains default configuration parameters that can be used
across the application for consistent behavior.
"""

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"
EXAMPLES_DIR = PROJECT_ROOT / "examples"
OUTPUT_DIR = PROJECT_ROOT / "output"
CACHE_DIR = PROJECT_ROOT / "cache"

# Model configuration
DEFAULT_MODEL_PATH = PROJECT_ROOT / "best.pt"
MODEL_CONFIDENCE_THRESHOLD = 0.25

# Detection parameters
DEFAULT_ZOOM_LEVEL = 18
DEFAULT_BATCH_SIZE = 5
DEFAULT_OUTPUT_DIR = str(OUTPUT_DIR)

# Merging parameters
DEFAULT_MERGING_ENABLED = True
DEFAULT_IOU_THRESHOLD = 0.1
DEFAULT_TOUCH_ENABLED = True
DEFAULT_MIN_EDGE_DISTANCE_DEG = 0.000001

# Processing parameters
DEFAULT_RESUME_FROM_SAVED = True
MAX_WORKERS = 2  # Optimal based on benchmarks

# Tile parameters
TILE_SIZE = 256  # Standard OSM tile size
OSM_TILE_URL_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "BuildingDetectionBot/1.0"

# Output file names
OUTPUT_FILES = {
    "detection_results": "detection_results.json",
    "buildings_geojson": "buildings.json",
    "buildings_simple": "buildings_simple.json",
    "visualization": "polygon_visualization.png",
    "buildings_export": "buildings_export.json",
    "incremental_simple": "buildings_incremental_simple.json"
}

# Cache settings
CACHE_ENABLED = True
CLEANUP_TILES_AFTER_COMPLETION = True

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Performance settings
MEMORY_LIMIT_MB = 2048
MAX_TILE_CACHE_SIZE = 100

# Validation settings
ENABLE_REVERSE_GEOCODING = False  # Disabled by default for performance
GEOCODING_PROVIDER = "nominatim"

# Visualization settings
VISUALIZATION_DPI = 300
VISUALIZATION_FIGSIZE = (12, 8)
CONFIDENCE_COLORMAP = "viridis"

def get_config():
    """
    Get the current configuration as a dictionary.
    
    Returns:
        dict: Configuration parameters
    """
    return {
        "model_path": str(DEFAULT_MODEL_PATH),
        "confidence_threshold": MODEL_CONFIDENCE_THRESHOLD,
        "zoom_level": DEFAULT_ZOOM_LEVEL,
        "batch_size": DEFAULT_BATCH_SIZE,
        "output_dir": DEFAULT_OUTPUT_DIR,
        "merging_enabled": DEFAULT_MERGING_ENABLED,
        "iou_threshold": DEFAULT_IOU_THRESHOLD,
        "touch_enabled": DEFAULT_TOUCH_ENABLED,
        "min_edge_distance_deg": DEFAULT_MIN_EDGE_DISTANCE_DEG,
        "resume_from_saved": DEFAULT_RESUME_FROM_SAVED,
        "max_workers": MAX_WORKERS,
        "cache_enabled": CACHE_ENABLED,
        "cleanup_tiles": CLEANUP_TILES_AFTER_COMPLETION,
    }

def validate_config():
    """
    Validate the current configuration.
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Check if model file exists
    if not DEFAULT_MODEL_PATH.exists():
        errors.append(f"Model file not found: {DEFAULT_MODEL_PATH}")
    
    # Check if directories exist, create if needed
    for directory in [OUTPUT_DIR, CACHE_DIR]:
        directory.mkdir(exist_ok=True)
    
    # Validate parameters
    if not (0.0 <= MODEL_CONFIDENCE_THRESHOLD <= 1.0):
        errors.append(f"Invalid confidence threshold: {MODEL_CONFIDENCE_THRESHOLD}")
    
    if not (1 <= DEFAULT_ZOOM_LEVEL <= 20):
        errors.append(f"Invalid zoom level: {DEFAULT_ZOOM_LEVEL}")
    
    if DEFAULT_BATCH_SIZE < 1:
        errors.append(f"Invalid batch size: {DEFAULT_BATCH_SIZE}")
    
    return len(errors) == 0, errors

# Environment-based overrides
def load_env_config():
    """
    Load configuration from environment variables if available.
    """
    global DEFAULT_MODEL_PATH, MODEL_CONFIDENCE_THRESHOLD, DEFAULT_ZOOM_LEVEL
    global DEFAULT_BATCH_SIZE, DEFAULT_OUTPUT_DIR
    
    # Override with environment variables if present
    if "BUILDING_DETECTOR_MODEL_PATH" in os.environ:
        DEFAULT_MODEL_PATH = Path(os.environ["BUILDING_DETECTOR_MODEL_PATH"])
    
    if "BUILDING_DETECTOR_CONFIDENCE" in os.environ:
        MODEL_CONFIDENCE_THRESHOLD = float(os.environ["BUILDING_DETECTOR_CONFIDENCE"])
    
    if "BUILDING_DETECTOR_ZOOM" in os.environ:
        DEFAULT_ZOOM_LEVEL = int(os.environ["BUILDING_DETECTOR_ZOOM"])
    
    if "BUILDING_DETECTOR_BATCH_SIZE" in os.environ:
        DEFAULT_BATCH_SIZE = int(os.environ["BUILDING_DETECTOR_BATCH_SIZE"])
    
    if "BUILDING_DETECTOR_OUTPUT_DIR" in os.environ:
        DEFAULT_OUTPUT_DIR = os.environ["BUILDING_DETECTOR_OUTPUT_DIR"]

# Load environment config on import
load_env_config() 