# Building Detector

A production-ready tool for detecting buildings in satellite/aerial imagery using YOLOv8.

## 🏗️ Features

- **AI-Powered Detection**: YOLOv8-based building detection in satellite imagery
- **Tile-Based Processing**: Scalable processing for large geographic areas
- **Smart Merging**: Automatic merging of fragmented detections using Union-Find algorithm
- **Multiple Output Formats**: GeoJSON, JSON, and simple coordinate formats
- **Resume Capability**: Incremental processing with resume functionality
- **Visualization**: Built-in visualization and validation tools
- **Production Ready**: Clean, modular architecture with proper error handling

## 🚀 Quick Start

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd building-detector
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure the YOLOv8 model file (`best.pt`) is in the project root directory

### Basic Usage

**Command Line (Recommended):**
```bash
# Quick start with example
python main.py examples/sample_polygon.geojson

# Custom configuration
python main.py path/to/your/polygon.geojson --output results/ --zoom 18 --conf 0.3

# Start fresh (no resume)
python main.py examples/sample_polygon.geojson --no-resume

# Disable merging
python main.py examples/sample_polygon.geojson --no-merge --batch-size 10
```

**Python API:**
```python
from src.core.detection import load_model
from src.core.polygon_detection import detect_buildings_in_polygon

# Load model
model = load_model("best.pt")

# Run detection
results = detect_buildings_in_polygon(
    model, 
    "examples/sample_polygon.geojson",
    "output/",
    zoom=18,
    conf=0.25
)

print(f"Detected {results['total_buildings']} buildings")
```

## 📁 Project Structure

```
building-detector/
├── main.py                     # 🎯 Main entry point
├── best.pt                     # 🤖 YOLOv8 model
├── requirements.txt            # 📦 Dependencies
├── 📚 docs/                    # Documentation
│   ├── Coordinate_Transformation_Technical_Paper.md
│   ├── INCREMENTAL_SAVING_README.md
│   └── MERGE_TILES_README.md
├── 📋 examples/                # Example files
│   ├── README.md
│   └── sample_polygon.geojson
├── 🔧 src/                     # Source code
│   ├── core/                   # Core functionality
│   │   ├── detection.py        # YOLOv8 detection
│   │   ├── polygon_detection.py # Main orchestrator
│   │   └── tile_utils.py       # Tile operations
│   ├── utils/                  # Utility functions
│   │   ├── building_export.py  # Export functions
│   │   ├── geojson_utils.py    # GeoJSON processing
│   │   └── merge_tiles_utility.py # Advanced merging
│   ├── visualization/          # Visualization tools
│   │   └── visualization.py
│   └── validation/             # Validation tools
│       └── validate.py
├── 📤 output/                  # Production outputs
└── 🗃️ cache/                   # Temporary cache
```

## 🛠️ Advanced Usage

### Command Line Options

```bash
python main.py --help
```

**Key Parameters:**
- `--model, -m`: Path to YOLOv8 model (default: best.pt)
- `--output, -o`: Output directory (default: output)
- `--zoom, -z`: Zoom level for tiles (default: 18)
- `--conf, -c`: Confidence threshold (default: 0.25)
- `--batch-size, -b`: Tiles per batch (default: 5)
- `--no-merge`: Disable detection merging
- `--no-resume`: Start fresh (ignore cache)
- `--iou-threshold`: IoU threshold for merging (default: 0.1)

### Python API - Advanced

```python
from src.core.detection import load_model
from src.core.polygon_detection import detect_buildings_in_polygon

# Load model
model = load_model("best.pt")

# Advanced configuration
results = detect_buildings_in_polygon(
    model=model,
    geojson_path="path/to/polygon.geojson",
    output_dir="output",
    zoom=18,                           # Detail level
    conf=0.25,                         # Detection confidence
    batch_size=5,                      # Processing batch size
    enable_merging=True,               # Enable smart merging
    merge_iou_threshold=0.1,           # IoU threshold
    merge_touch_enabled=True,          # Enable touching detection
    merge_min_edge_distance_deg=0.000001,  # Proximity merging
    resume_from_saved=True             # Resume capability
)
```

### Module Imports

```python
# Core functionality
from src.core.detection import load_model, detect_buildings
from src.core.polygon_detection import detect_buildings_in_polygon

# Utilities
from src.utils.geojson_utils import load_geojson, create_example_geojson
from src.utils.building_export import save_buildings_to_json

# Visualization
from src.visualization.visualization import visualize_polygon_detections

# Validation
from src.validation.validate import validate_buildings
```

## 📊 Output Files

The system generates multiple output formats:

```
output/
├── detection_results.json      # 📋 Comprehensive results
├── buildings.json              # 🗺️ GeoJSON format
├── buildings_simple.json       # 📍 Simple coordinates (id, lon, lat)
├── polygon_visualization.png   # 🎨 Visualization map
└── cache/                      # 🗃️ Temporary processing files
```

### Output Format Examples

**Simple Format (`buildings_simple.json`):**
```json
[
  {"id": "1", "longitude": 106.8456, "latitude": -6.2088},
  {"id": "2", "longitude": 106.8460, "latitude": -6.2090}
]
```

**GeoJSON Format (`buildings.json`):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {"confidence": 0.95},
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
      }
    }
  ]
}
```

## 🔧 Development

### Adding New Features

1. **Core functionality**: Add to `src/core/`
2. **Utilities**: Add to `src/utils/`
3. **Visualization**: Add to `src/visualization/`
4. **Validation**: Add to `src/validation/`

### Testing

```bash
# Test with example data
python main.py examples/sample_polygon.geojson --output test_output/

# Test different configurations
python main.py examples/sample_polygon.geojson --no-merge --conf 0.1
```

## 🐛 Troubleshooting

### Common Issues

1. **Model not found**: Ensure `best.pt` is in the root directory
2. **Memory issues**: Reduce `--batch-size` parameter
3. **Slow processing**: Increase `--batch-size` or reduce `--zoom` level
4. **Cache issues**: Use `--no-resume` to start fresh

### Getting Help

- Check `docs/` folder for detailed documentation
- Review example usage in `examples/README.md`
- Use `python main.py --help` for command options

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]
