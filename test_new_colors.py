#!/usr/bin/env python3
"""
Test script for new color scheme
"""

from create_enhanced_evaluation import EnhancedEvaluationVisualizer
from pathlib import Path
import json

def test_new_colors():
    print('🎨 Testing New Color Scheme')
    print('=' * 40)
    
    # Load data
    base_dir = Path('/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector')
    
    # Load model detections
    with open(base_dir / 'output' / 'buildings_simple.json', 'r') as f:
        model_detections_raw = json.load(f)
        model_detections = [
            {
                'id': d['id'], 
                'lat': d['latitude'], 
                'lon': d['longitude']
            } 
            for d in model_detections_raw
        ]
    
    # Load OSM buildings
    with open(base_dir / 'output' / 'osm_buildings_ground_truth.json', 'r') as f:
        osm_data = json.load(f)
        osm_buildings = []
        for i, feature in enumerate(osm_data['features']):
            building = {
                'id': feature['properties'].get('id', i), 
                'geometry': feature['geometry']
            }
            if feature['geometry']['type'] == 'Polygon':
                coords = feature['geometry']['coordinates'][0]
                avg_lat = sum(coord[1] for coord in coords) / len(coords)
                avg_lon = sum(coord[0] for coord in coords) / len(coords)
                building['centroid'] = {'lat': avg_lat, 'lon': avg_lon}
            osm_buildings.append(building)
    
    # Load study area
    with open(base_dir / 'examples' / 'sample_polygon.geojson', 'r') as f:
        study_area = json.load(f)
        study_area_coords = study_area['features'][0]['geometry']['coordinates'][0]
    
    print(f'✅ Data loaded:')
    print(f'   - Model detections: {len(model_detections)}')
    print(f'   - OSM buildings: {len(osm_buildings)}')
    
    # Create visualization with new color scheme
    visualizer = EnhancedEvaluationVisualizer(distance_threshold=5.0)
    output_file = base_dir / 'output' / 'improved_colors_evaluation_map.html'
    
    try:
        results = visualizer.create_enhanced_map(
            model_detections=model_detections,
            osm_buildings=osm_buildings,
            study_area_coords=study_area_coords,
            output_path=str(output_file)
        )
        
        print('\n🎨 NEW COLOR SCHEME APPLIED:')
        print(f'🔵 Model Detections: Blue circles ({len(model_detections)} total)')
        print(f'🟢 OSM Detected: Green polygons ({results["metrics"]["true_positives"]} buildings)')
        print(f'🔴 OSM Missed: Red polygons ({results["metrics"]["false_negatives"]} buildings)')
        
        print(f'\n✅ Map created successfully!')
        print(f'🌐 View at: file://{output_file}')
        
        return str(output_file)
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_new_colors()
