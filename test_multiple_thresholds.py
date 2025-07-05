#!/usr/bin/env python3
"""
Building Detection Evaluation with Multiple Distance Thresholds

This script tests different distance thresholds to find more realistic evaluation results.
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from create_enhanced_evaluation import EnhancedEvaluationVisualizer
from pathlib import Path

def test_multiple_thresholds():
    """Test evaluation with different distance thresholds"""
    
    print("🔍 Testing Multiple Distance Thresholds")
    print("=" * 50)
    
    # File paths
    base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
    model_detections_file = base_dir / "output" / "buildings_simple.json"
    osm_buildings_file = base_dir / "output" / "osm_buildings_corrected.json"
    study_area_file = base_dir / "examples" / "sample_polygon.geojson"
    
    # Load data
    print("📂 Loading data files...")
    
    try:
        with open(model_detections_file, 'r') as f:
            model_detections_raw = json.load(f)
            formatted_detections = []
            for detection in model_detections_raw:
                formatted_detections.append({
                    'id': detection['id'],
                    'lat': detection['latitude'],
                    'lon': detection['longitude']
                })
            model_detections = formatted_detections
        
        with open(osm_buildings_file, 'r') as f:
            osm_data = json.load(f)
            if 'features' in osm_data:
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
        
        with open(study_area_file, 'r') as f:
            study_area = json.load(f)
            study_area_coords = study_area['features'][0]['geometry']['coordinates'][0]
        
        print(f"✅ Loaded {len(model_detections)} model detections")
        print(f"✅ Loaded {len(osm_buildings)} OSM buildings")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Test different thresholds
    thresholds = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    
    print("\n📏 Testing Different Distance Thresholds:")
    print("=" * 60)
    
    results_summary = []
    
    for threshold in thresholds:
        print(f"\n🎯 Distance Threshold: {threshold}m")
        print("-" * 30)
        
        # Create visualizer
        visualizer = EnhancedEvaluationVisualizer(distance_threshold=threshold)
        
        # Perform matching and get metrics
        building_matches, detection_matches = visualizer.matcher.perform_spatial_matching(
            model_detections, osm_buildings
        )
        metrics = visualizer.calculate_metrics(building_matches, detection_matches)
        
        print(f"🟢 True Positives (TP): {metrics['true_positives']}")
        print(f"🟡 False Negatives (FN): {metrics['false_negatives']}")
        print(f"🔴 False Positives (FP): {metrics['false_positives']}")
        print(f"📈 Precision: {metrics['precision']:.3f}")
        print(f"📈 Recall: {metrics['recall']:.3f}")
        print(f"📈 F1-Score: {metrics['f1_score']:.3f}")
        
        results_summary.append({
            'threshold': threshold,
            'metrics': metrics
        })
        
        # Create map for interesting thresholds
        if threshold in [10.0, 15.0]:
            output_file = base_dir / "output" / f"enhanced_evaluation_map_{threshold}m.html"
            
            try:
                visualizer.create_enhanced_map(
                    model_detections=model_detections,
                    osm_buildings=osm_buildings,
                    study_area_coords=study_area_coords,
                    output_path=str(output_file)
                )
                print(f"💾 Map saved: {output_file}")
            except Exception as e:
                print(f"❌ Error creating map for {threshold}m: {e}")
    
    # Find the best threshold (highest F1-score with some missed buildings)
    print("\n🏆 THRESHOLD COMPARISON SUMMARY")
    print("=" * 60)
    print(f"{'Threshold':<10} {'TP':<5} {'FN':<5} {'FP':<5} {'Precision':<10} {'Recall':<8} {'F1-Score':<8}")
    print("-" * 60)
    
    best_threshold = None
    best_score = 0
    
    for result in results_summary:
        threshold = result['threshold']
        m = result['metrics']
        
        print(f"{threshold:<10.1f} {m['true_positives']:<5} {m['false_negatives']:<5} {m['false_positives']:<5} "
              f"{m['precision']:<10.3f} {m['recall']:<8.3f} {m['f1_score']:<8.3f}")
        
        # Find best threshold (prefer one with some FN to show real performance)
        if m['false_negatives'] > 0 and m['f1_score'] > best_score:
            best_score = m['f1_score']
            best_threshold = threshold
    
    if best_threshold:
        print(f"\n🎯 Recommended threshold: {best_threshold}m (F1-Score: {best_score:.3f})")
        print(f"📍 This threshold shows realistic performance with some missed buildings.")
    else:
        print(f"\n⚠️  All thresholds show perfect performance. Consider:")
        print("   - Using stricter thresholds (< 5m)")
        print("   - Checking data quality and alignment")
        print("   - Verifying coordinate systems match")

if __name__ == "__main__":
    test_multiple_thresholds()
