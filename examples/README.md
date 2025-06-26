# Examples

This directory contains example GeoJSON files for testing the building detection system.

## Available Examples

### sample_polygon.geojson
A sample polygon area that can be used to test the building detection functionality.

## Usage

To run building detection on an example:

```python
from src.core.detection import load_model
from src.core.polygon_detection import detect_buildings_in_polygon

# Load the model
model = load_model("best.pt")

# Run detection on example
results = detect_buildings_in_polygon(
    model, 
    "examples/sample_polygon.geojson",
    "output/",
    zoom=18,
    conf=0.25
)
```

Or using command line:

```bash
python -m src.core.polygon_detection examples/sample_polygon.geojson
```

## Output

Results will be saved to the `output/` directory:
- `detection_results.json` - Detailed detection results
- `buildings.json` - GeoJSON format buildings
- `buildings_simple.json` - Simple format (id, longitude, latitude)
- `polygon_visualization.png` - Visualization of results 