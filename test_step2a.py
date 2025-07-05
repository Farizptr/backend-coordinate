#!/usr/bin/env python3
"""
Test Step 2A: Enhanced Percentage Comparison
"""

from create_enhanced_evaluation import EnhancedEvaluationVisualizer, PercentageComparisonAnalyzer
from pathlib import Path
import json

def test_percentage_comparison():
    print('📊 Testing Step 2A: Enhanced Percentage Comparison')
    print('=' * 55)
    
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
    
    # Perform evaluation
    visualizer = EnhancedEvaluationVisualizer(distance_threshold=5.0)
    building_matches, detection_matches = visualizer.matcher.perform_spatial_matching(
        model_detections, osm_buildings
    )
    metrics = visualizer.calculate_metrics(building_matches, detection_matches)
    
    # Test percentage comparison analyzer
    analyzer = PercentageComparisonAnalyzer()
    detailed_summary = analyzer.generate_simple_summary(metrics)
    
    # Display the enhanced summary
    print(detailed_summary)
    
    # Test simple export
    summary_file = base_dir / 'output' / 'evaluation_summary.txt'
    try:
        # Simple export
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        export_summary = f"""Building Detection Evaluation Summary
Generated: {timestamp}
Threshold: 5.0 meters

{detailed_summary}

📁 FILES GENERATED:
- Interactive Map: improved_colors_evaluation_map.html
- This Summary: evaluation_summary.txt

🔗 For detailed analysis, open the interactive map to see:
- 🔵 Blue circles: Model detections
- 🟢 Green polygons: Successfully detected buildings
- 🔴 Red polygons: Missed buildings
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(export_summary)
        print(f"\n📄 Summary exported to: {summary_file}")
        
    except Exception as e:
        print(f"❌ Error exporting summary: {e}")
    
    print(f"\n✅ Step 2A: Enhanced Percentage Comparison - COMPLETED!")

if __name__ == "__main__":
    test_percentage_comparison()
