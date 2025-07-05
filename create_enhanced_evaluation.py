#!/usr/bin/env python3
"""
Enhanced Building Detection Evaluation with Spatial Matching

This script performs spatial matching between model detections and OSM ground truth,
then creates a color-coded visualization showing:
- True Positives (green): OSM buildings successfully detected
- False Negatives (yellow/orange): OSM buildings missed by the model  
- False Positives (red): Model detections with no nearby OSM building

Author: Building Detection Evaluation System
"""

import json
import folium
import math
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from pathlib import Path

# Simple comparison functionality
class PercentageComparisonAnalyzer:
    """Simple analyzer for percentage-based comparison"""
    
    def generate_simple_summary(self, metrics: Dict[str, any]) -> str:
        """Generate a simple, clear percentage summary"""
        
        total_ground_truth = metrics['total_osm_buildings']
        total_detections = metrics['total_detections']
        successfully_matched = metrics['true_positives']
        missed_buildings = metrics['false_negatives']
        false_detections = metrics['false_positives']
        
        # Calculate percentages
        detection_rate = (successfully_matched / total_ground_truth * 100) if total_ground_truth > 0 else 0
        miss_rate = (missed_buildings / total_ground_truth * 100) if total_ground_truth > 0 else 0
        precision_pct = (successfully_matched / total_detections * 100) if total_detections > 0 else 0
        
        summary = f"""
🏠 GROUND TRUTH vs MODEL COMPARISON
{'='*50}
📊 Ground Truth (OSM Buildings): {total_ground_truth} buildings
🎯 Model Detections: {total_detections} detections
✅ Successfully Matched: {successfully_matched} buildings

📈 ACCURACY METRICS:
{'='*30}
✅ Detection Rate: {detection_rate:.1f}% ({successfully_matched}/{total_ground_truth})
❌ Miss Rate: {miss_rate:.1f}% ({missed_buildings}/{total_ground_truth})
🎯 Precision: {precision_pct:.1f}% ({successfully_matched}/{total_detections})
📊 Overall Accuracy: {detection_rate:.1f}%

📋 DETAILED BREAKDOWN:
{'='*25}
🟢 Buildings Successfully Detected: {successfully_matched}
🔴 Buildings Missed by Model: {missed_buildings}
🔵 False Detections: {false_detections}

💡 INTERPRETATION:
{'='*20}"""
        
        if detection_rate >= 95:
            summary += f"\n🌟 EXCELLENT: Model achieves {detection_rate:.1f}% detection rate!"
        elif detection_rate >= 90:
            summary += f"\n👍 GOOD: Model achieves {detection_rate:.1f}% detection rate."
        elif detection_rate >= 80:
            summary += f"\n⚠️  FAIR: Model achieves {detection_rate:.1f}% detection rate. Consider improvement."
        else:
            summary += f"\n❌ POOR: Model only achieves {detection_rate:.1f}% detection rate. Needs significant improvement."
        
        if missed_buildings > 0:
            summary += f"\n🔍 {missed_buildings} buildings were missed - check red polygons on map for analysis."
        else:
            summary += "\n🎯 Perfect detection - no buildings missed!"
            
        if false_detections > 0:
            summary += f"\n⚠️  {false_detections} false detections found - model may be over-detecting."
        else:
            summary += "\n✅ No false detections - excellent precision!"
        
        return summary

@dataclass
class BuildingMatch:
    """Represents the matching status of a building"""
    osm_id: int
    osm_centroid: Tuple[float, float]
    matched_detection_id: Optional[int] = None
    distance_to_match: Optional[float] = None
    is_matched: bool = False

@dataclass
class DetectionMatch:
    """Represents the matching status of a model detection"""
    detection_id: int
    detection_point: Tuple[float, float]
    matched_osm_id: Optional[int] = None
    distance_to_match: Optional[float] = None
    is_matched: bool = False

class SpatialMatcher:
    """Handles spatial matching between model detections and OSM buildings"""
    
    def __init__(self, distance_threshold_meters: float = 25.0):
        self.distance_threshold = distance_threshold_meters
    
    def haversine_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """
        Calculate the great circle distance between two points on Earth in meters
        
        Args:
            point1: (latitude, longitude) of first point
            point2: (latitude, longitude) of second point
            
        Returns:
            Distance in meters
        """
        lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
        lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in meters
        earth_radius = 6371000
        
        return earth_radius * c
    
    def find_closest_detection(self, osm_centroid: Tuple[float, float], 
                              detections: List[Dict]) -> Tuple[int, float]:
        """
        Find the closest model detection to an OSM building centroid
        
        Args:
            osm_centroid: (lat, lon) of OSM building centroid
            detections: List of model detection dictionaries
            
        Returns:
            Tuple of (detection_id, distance) or (None, float('inf')) if none found
        """
        min_distance = float('inf')
        closest_detection_id = None
        
        for detection in detections:
            detection_point = (detection['lat'], detection['lon'])
            distance = self.haversine_distance(osm_centroid, detection_point)
            
            if distance < min_distance:
                min_distance = distance
                closest_detection_id = detection['id']
        
        return closest_detection_id, min_distance
    
    def find_closest_osm_building(self, detection_point: Tuple[float, float], 
                                 osm_buildings: List[Dict]) -> Tuple[int, float]:
        """
        Find the closest OSM building to a model detection
        
        Args:
            detection_point: (lat, lon) of model detection
            osm_buildings: List of OSM building dictionaries
            
        Returns:
            Tuple of (osm_id, distance) or (None, float('inf')) if none found
        """
        min_distance = float('inf')
        closest_osm_id = None
        
        for building in osm_buildings:
            if 'centroid' in building:
                osm_centroid = (building['centroid']['lat'], building['centroid']['lon'])
                distance = self.haversine_distance(detection_point, osm_centroid)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_osm_id = building['id']
        
        return closest_osm_id, min_distance
    
    def perform_spatial_matching(self, model_detections: List[Dict], 
                               osm_buildings: List[Dict]) -> Tuple[List[BuildingMatch], List[DetectionMatch]]:
        """
        Perform spatial matching between model detections and OSM buildings
        
        Args:
            model_detections: List of model detection dictionaries
            osm_buildings: List of OSM building dictionaries
            
        Returns:
            Tuple of (building_matches, detection_matches)
        """
        building_matches = []
        detection_matches = []
        
        # Match OSM buildings to detections
        for i, building in enumerate(osm_buildings):
            if 'centroid' not in building:
                continue
                
            osm_centroid = (building['centroid']['lat'], building['centroid']['lon'])
            closest_detection_id, distance = self.find_closest_detection(osm_centroid, model_detections)
            
            building_match = BuildingMatch(
                osm_id=building['id'],
                osm_centroid=osm_centroid
            )
            
            if distance <= self.distance_threshold:
                building_match.matched_detection_id = closest_detection_id
                building_match.distance_to_match = distance
                building_match.is_matched = True
            
            building_matches.append(building_match)
        
        # Match detections to OSM buildings
        for detection in model_detections:
            detection_point = (detection['lat'], detection['lon'])
            closest_osm_id, distance = self.find_closest_osm_building(detection_point, osm_buildings)
            
            detection_match = DetectionMatch(
                detection_id=detection['id'],
                detection_point=detection_point
            )
            
            if distance <= self.distance_threshold:
                detection_match.matched_osm_id = closest_osm_id
                detection_match.distance_to_match = distance
                detection_match.is_matched = True
            
            detection_matches.append(detection_match)
        
        return building_matches, detection_matches

class EnhancedEvaluationVisualizer:
    """Creates enhanced visualizations with spatial matching results"""
    
    def __init__(self, distance_threshold: float = 25.0):
        self.matcher = SpatialMatcher(distance_threshold)
        self.distance_threshold = distance_threshold
    
    def calculate_metrics(self, building_matches: List[BuildingMatch], 
                         detection_matches: List[DetectionMatch]) -> Dict[str, float]:
        """Calculate precision, recall, and F1-score"""
        
        true_positives = len([bm for bm in building_matches if bm.is_matched])
        false_negatives = len([bm for bm in building_matches if not bm.is_matched])
        false_positives = len([dm for dm in detection_matches if not dm.is_matched])
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'true_positives': true_positives,
            'false_negatives': false_negatives,
            'false_positives': false_positives,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'total_osm_buildings': len(building_matches),
            'total_detections': len(detection_matches)
        }
    
    def create_enhanced_map(self, model_detections: List[Dict], osm_buildings: List[Dict], 
                           study_area_coords: List[List[float]], output_path: str) -> Dict:
        """Create an enhanced map with spatial matching visualization"""
        
        # Perform spatial matching
        building_matches, detection_matches = self.matcher.perform_spatial_matching(
            model_detections, osm_buildings
        )
        
        # Calculate metrics
        metrics = self.calculate_metrics(building_matches, detection_matches)
        
        # Calculate map center
        if study_area_coords:
            center_lat = sum(coord[1] for coord in study_area_coords) / len(study_area_coords)
            center_lon = sum(coord[0] for coord in study_area_coords) / len(study_area_coords)
        else:
            center_lat, center_lon = -7.8, 110.4
        
        # Create the map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles='OpenStreetMap'
        )
        
        # Add study area boundary
        if study_area_coords:
            folium.Polygon(
                locations=[[coord[1], coord[0]] for coord in study_area_coords],
                color='black',
                weight=3,
                fill=False,
                popup='Study Area Boundary'
            ).add_to(m)
        
        # Create building index for quick lookup
        osm_building_lookup = {building['id']: building for building in osm_buildings}
        
        # Add OSM buildings with improved color coding
        for i, building_match in enumerate(building_matches):
            building = osm_building_lookup.get(building_match.osm_id)
            if not building or 'geometry' not in building:
                continue
            
            # Determine color based on matching status
            if building_match.is_matched:
                fill_color = '#28a745'  # Green for successfully detected
                border_color = 'white'
                status = 'Successfully Detected'
                popup_text = f"🏠 OSM Building #{i+1}<br>📊 Status: <b>{status}</b><br>🎯 Matched to Detection ID: {building_match.matched_detection_id}<br>📏 Distance: {building_match.distance_to_match:.1f}m"
            else:
                fill_color = '#dc3545'  # Red for missed buildings
                border_color = 'white'
                status = 'MISSED by Model'
                popup_text = f"🏠 OSM Building #{i+1}<br>⚠️ Status: <b>{status}</b><br>❌ No nearby detection found"
            
            # Add building polygon with improved styling
            if building['geometry']['type'] == 'Polygon':
                coords = building['geometry']['coordinates'][0]
                folium.Polygon(
                    locations=[[coord[1], coord[0]] for coord in coords],
                    color=border_color,
                    weight=3,
                    fill=True,
                    fillColor=fill_color,
                    fillOpacity=0.6,
                    popup=popup_text
                ).add_to(m)
            
            # Add centroid marker with improved styling
            centroid = building_match.osm_centroid
            folium.CircleMarker(
                location=[centroid[0], centroid[1]],
                radius=4,
                color=border_color,
                weight=2,
                fill=True,
                fillColor=fill_color,
                fillOpacity=0.8,
                popup=popup_text
            ).add_to(m)
            
            # Add building number label with improved styling
            folium.Marker(
                location=[centroid[0], centroid[1]],
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 10px; font-weight: bold; color: white; background-color: {fill_color}; border-radius: 50%; padding: 2px; text-align: center; width: 16px; height: 16px;">{i+1}</div>',
                    icon_size=(16, 16),
                    icon_anchor=(8, 8)
                )
            ).add_to(m)
        
        # Add model detections with consistent blue color
        for detection_match in detection_matches:
            detection_point = detection_match.detection_point
            
            # All model detections use blue color
            detection_color = '#0066CC'  # Blue for all model detections
            
            # Determine status text based on matching
            if detection_match.is_matched:
                status = 'True Positive'
                popup_text = f"🎯 Model Detection ID: {detection_match.detection_id}<br>📊 Status: <b>{status}</b><br>🏠 Matched to OSM Building ID: {detection_match.matched_osm_id}<br>📏 Distance: {detection_match.distance_to_match:.1f}m"
            else:
                status = 'False Positive'
                popup_text = f"🎯 Model Detection ID: {detection_match.detection_id}<br>⚠️ Status: <b>{status}</b><br>❌ No nearby OSM building found"
            
            # Add detection marker with consistent blue styling
            folium.CircleMarker(
                location=[detection_point[0], detection_point[1]],
                radius=6,
                color='white',
                weight=2,
                fill=True,
                fillColor=detection_color,
                fillOpacity=0.8,
                popup=popup_text
            ).add_to(m)
        
        # Add enhanced legend with improved color scheme
        legend_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 320px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h4 style="margin-top: 0; color: #333;">🔍 Building Detection Evaluation</h4>
        <p><b>Distance Threshold:</b> {self.distance_threshold}m</p>
        
        <hr style="margin: 10px 0;">
        <h5 style="margin: 8px 0; color: #555;">📍 SUMBER DATA:</h5>
        <p style="margin: 4px 0;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #0066CC; border-radius: 50%; margin-right: 8px;"></span><b>Model Detections:</b> {metrics['total_detections']} titik</p>
        <p style="margin: 4px 0;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #28a745; margin-right: 8px;"></span><b>OSM Buildings:</b> {metrics['total_osm_buildings']} polygon</p>
        
        <hr style="margin: 10px 0;">
        <h5 style="margin: 8px 0; color: #555;">📊 STATUS MATCHING:</h5>
        <p style="margin: 4px 0;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #28a745; margin-right: 8px;"></span><b>OSM: Berhasil Terdeteksi:</b> {metrics['true_positives']}</p>
        <p style="margin: 4px 0;"><span style="display: inline-block; width: 12px; height: 12px; background-color: #dc3545; margin-right: 8px;"></span><b>OSM: Terlewat/Missed:</b> {metrics['false_negatives']}</p>
        
        <hr style="margin: 10px 0;">
        <h5 style="margin: 8px 0; color: #555;">📈 METRIK PERFORMA:</h5>
        <p style="margin: 2px 0;"><b>Precision:</b> {metrics['precision']:.3f}</p>
        <p style="margin: 2px 0;"><b>Recall:</b> {metrics['recall']:.3f}</p>
        <p style="margin: 2px 0;"><b>F1-Score:</b> {metrics['f1_score']:.3f}</p>
        
        <div style="margin-top: 12px; padding: 8px; background-color: #f8f9fa; border-radius: 4px; font-size: 12px;">
        🎯 <b>Akurasi:</b> {metrics['recall']*100:.1f}%<br>
        🏠 Building terlewat mudah diidentifikasi dengan warna merah
        </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save the map
        m.save(output_path)
        
        return {
            'metrics': metrics,
            'building_matches': [
                {
                    'osm_id': bm.osm_id,
                    'osm_centroid': bm.osm_centroid,
                    'is_matched': bm.is_matched,
                    'matched_detection_id': bm.matched_detection_id,
                    'distance_to_match': bm.distance_to_match
                }
                for bm in building_matches
            ],
            'detection_matches': [
                {
                    'detection_id': dm.detection_id,
                    'detection_point': dm.detection_point,
                    'is_matched': dm.is_matched,
                    'matched_osm_id': dm.matched_osm_id,
                    'distance_to_match': dm.distance_to_match
                }
                for dm in detection_matches
            ]
        }

def main():
    """Main execution function"""
    
    print("🔍 Enhanced Building Detection Evaluation")
    print("=" * 50)
    
    # File paths
    base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
    model_detections_file = base_dir / "output" / "buildings_simple.json"
    osm_buildings_file = base_dir / "output" / "osm_buildings_corrected.json"
    study_area_file = base_dir / "examples" / "sample_polygon.geojson"
    
    # Output files
    enhanced_map_file = base_dir / "output" / "enhanced_evaluation_map.html"
    detailed_results_file = base_dir / "output" / "detailed_evaluation_results.json"
    
    # Load data
    print("📂 Loading data files...")
    
    try:
        with open(model_detections_file, 'r') as f:
            model_detections_raw = json.load(f)
            # Handle different data structures
            if isinstance(model_detections_raw, list):
                model_detections = model_detections_raw
            elif isinstance(model_detections_raw, dict) and 'detections' in model_detections_raw:
                model_detections = model_detections_raw['detections']
            else:
                model_detections = model_detections_raw
        
        # Convert to expected format
        formatted_detections = []
        for detection in model_detections:
            formatted_detections.append({
                'id': detection['id'],
                'lat': detection['latitude'],
                'lon': detection['longitude']
            })
        model_detections = formatted_detections
        
        print(f"✅ Loaded {len(model_detections)} model detections")
        
        with open(osm_buildings_file, 'r') as f:
            osm_data = json.load(f)
            if 'buildings' in osm_data:
                osm_buildings = osm_data['buildings']
            elif 'features' in osm_data:
                # Handle GeoJSON format
                osm_buildings = []
                for i, feature in enumerate(osm_data['features']):
                    building = {
                        'id': feature['properties'].get('id', i),
                        'geometry': feature['geometry']
                    }
                    # Calculate centroid if not present
                    if 'centroid' not in building and feature['geometry']['type'] == 'Polygon':
                        coords = feature['geometry']['coordinates'][0]
                        avg_lat = sum(coord[1] for coord in coords) / len(coords)
                        avg_lon = sum(coord[0] for coord in coords) / len(coords)
                        building['centroid'] = {'lat': avg_lat, 'lon': avg_lon}
                    osm_buildings.append(building)
            else:
                osm_buildings = osm_data
                
        print(f"✅ Loaded {len(osm_buildings)} OSM buildings (filtered)")
        
        with open(study_area_file, 'r') as f:
            study_area = json.load(f)
            study_area_coords = study_area['features'][0]['geometry']['coordinates'][0]
        print(f"✅ Loaded study area with {len(study_area_coords)} coordinates")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Create enhanced visualization
    print("\n🎨 Creating enhanced visualization with spatial matching...")
    
    distance_threshold = 25.0  # meters
    visualizer = EnhancedEvaluationVisualizer(distance_threshold=distance_threshold)
    
    try:
        results = visualizer.create_enhanced_map(
            model_detections=model_detections,
            osm_buildings=osm_buildings,
            study_area_coords=study_area_coords,
            output_path=str(enhanced_map_file)
        )
        
        print(f"✅ Enhanced map saved to: {enhanced_map_file}")
        
        # Save detailed results
        with open(detailed_results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Detailed results saved to: {detailed_results_file}")
        
        # Print summary statistics
        metrics = results['metrics']
        print("\n📊 EVALUATION SUMMARY")
        print("=" * 30)
        print(f"Distance Threshold: {distance_threshold}m")
        print(f"Total OSM Buildings: {metrics['total_osm_buildings']}")
        print(f"Total Model Detections: {metrics['total_detections']}")
        print()
        print(f"🟢 Successfully Detected (TP): {metrics['true_positives']}")
        print(f"🟡 MISSED Buildings (FN): {metrics['false_negatives']}")
        print(f"🔴 False Detections (FP): {metrics['false_positives']}")
        print()
        print(f"Precision: {metrics['precision']:.3f}")
        print(f"Recall: {metrics['recall']:.3f}")
        print(f"F1-Score: {metrics['f1_score']:.3f}")
        
        # Generate and display detailed percentage comparison
        analyzer = PercentageComparisonAnalyzer()
        detailed_summary = analyzer.generate_simple_summary(metrics)
        print(detailed_summary)
        
        # Highlight missed buildings
        missed_buildings = [bm for bm in results['building_matches'] if not bm['is_matched']]
        if missed_buildings:
            print(f"\n⚠️  MISSED BUILDINGS (FN): {len(missed_buildings)} buildings")
            print("Missed OSM Building IDs:")
            for i, missed in enumerate(missed_buildings[:10]):  # Show first 10
                print(f"  - OSM ID: {missed['osm_id']}")
            if len(missed_buildings) > 10:
                print(f"  ... and {len(missed_buildings) - 10} more")
        
        print("\n🌐 Open the enhanced map to see color-coded results:")
        print(f"   file://{enhanced_map_file}")
        
    except Exception as e:
        print(f"❌ Error creating enhanced visualization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
