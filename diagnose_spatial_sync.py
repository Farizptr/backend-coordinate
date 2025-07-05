#!/usr/bin/env python3
"""
Spatial Synchronization Diagnostic Tool
Analyzes coordinate systems and spatial alignment between model detections and OSM data
"""

import json
from pathlib import Path
import math

def analyze_coordinate_ranges(data, data_type, coord_key_lat, coord_key_lon):
    """Analyze coordinate ranges for a dataset"""
    if not data:
        return None
    
    lats = []
    lons = []
    
    for item in data:
        if data_type == "model":
            lats.append(item[coord_key_lat])
            lons.append(item[coord_key_lon])
        elif data_type == "osm":
            if 'centroid' in item:
                lats.append(item['centroid']['lat'])
                lons.append(item['centroid']['lon'])
    
    if not lats or not lons:
        return None
    
    return {
        'lat_min': min(lats),
        'lat_max': max(lats),
        'lat_center': sum(lats) / len(lats),
        'lon_min': min(lons),
        'lon_max': max(lons),
        'lon_center': sum(lons) / len(lons),
        'count': len(lats)
    }

def analyze_study_area_polygon(polygon_coords):
    """Analyze study area polygon coordinates"""
    if not polygon_coords:
        return None
    
    lats = [coord[1] for coord in polygon_coords]
    lons = [coord[0] for coord in polygon_coords]
    
    return {
        'lat_min': min(lats),
        'lat_max': max(lats),
        'lat_center': sum(lats) / len(lats),
        'lon_min': min(lons),
        'lon_max': max(lons),
        'lon_center': sum(lons) / len(lons),
        'area_points': len(polygon_coords)
    }

def diagnose_spatial_sync():
    """Main diagnostic function"""
    
    print("🔍 SPATIAL SYNCHRONIZATION DIAGNOSTIC")
    print("=" * 50)
    
    # File paths
    base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
    model_file = base_dir / "output" / "buildings_simple.json"
    osm_file = base_dir / "output" / "osm_buildings_corrected.json" 
    study_area_file = base_dir / "examples" / "sample_polygon.geojson"
    
    # Load and analyze data
    try:
        # Model detections
        with open(model_file, 'r') as f:
            model_data = json.load(f)
        model_stats = analyze_coordinate_ranges(model_data, "model", "latitude", "longitude")
        
        # OSM buildings
        with open(osm_file, 'r') as f:
            osm_data = json.load(f)
            if 'features' in osm_data:
                osm_buildings = []
                for feature in osm_data['features']:
                    building = {'id': feature['properties'].get('id', 0)}
                    if feature['geometry']['type'] == 'Polygon':
                        coords = feature['geometry']['coordinates'][0]
                        avg_lat = sum(coord[1] for coord in coords) / len(coords)
                        avg_lon = sum(coord[0] for coord in coords) / len(coords)
                        building['centroid'] = {'lat': avg_lat, 'lon': avg_lon}
                    osm_buildings.append(building)
            else:
                osm_buildings = osm_data
        
        osm_stats = analyze_coordinate_ranges(osm_buildings, "osm", "lat", "lon")
        
        # Study area
        with open(study_area_file, 'r') as f:
            study_area = json.load(f)
            study_coords = study_area['features'][0]['geometry']['coordinates'][0]
        study_stats = analyze_study_area_polygon(study_coords)
        
        # Display analysis
        print("\n📊 COORDINATE ANALYSIS")
        print("=" * 30)
        
        print(f"\n🎯 MODEL DETECTIONS ({model_stats['count']} points):")
        print(f"   Latitude:  {model_stats['lat_min']:.6f} to {model_stats['lat_max']:.6f}")
        print(f"   Longitude: {model_stats['lon_min']:.6f} to {model_stats['lon_max']:.6f}")
        print(f"   Center:    ({model_stats['lat_center']:.6f}, {model_stats['lon_center']:.6f})")
        
        print(f"\n🏠 OSM BUILDINGS ({osm_stats['count']} buildings):")
        print(f"   Latitude:  {osm_stats['lat_min']:.6f} to {osm_stats['lat_max']:.6f}")
        print(f"   Longitude: {osm_stats['lon_min']:.6f} to {osm_stats['lon_max']:.6f}")
        print(f"   Center:    ({osm_stats['lat_center']:.6f}, {osm_stats['lon_center']:.6f})")
        
        print(f"\n📍 STUDY AREA POLYGON ({study_stats['area_points']} points):")
        print(f"   Latitude:  {study_stats['lat_min']:.6f} to {study_stats['lat_max']:.6f}")
        print(f"   Longitude: {study_stats['lon_min']:.6f} to {study_stats['lon_max']:.6f}")
        print(f"   Center:    ({study_stats['lat_center']:.6f}, {study_stats['lon_center']:.6f})")
        
        # Calculate differences
        print(f"\n⚠️  SPATIAL ALIGNMENT ANALYSIS")
        print("=" * 35)
        
        # Center point differences
        model_osm_lat_diff = abs(model_stats['lat_center'] - osm_stats['lat_center'])
        model_osm_lon_diff = abs(model_stats['lon_center'] - osm_stats['lon_center'])
        
        print(f"📏 Model vs OSM Center Distance:")
        print(f"   Lat difference: {model_osm_lat_diff:.6f} degrees")
        print(f"   Lon difference: {model_osm_lon_diff:.6f} degrees")
        
        # Rough distance calculation
        lat_dist_m = model_osm_lat_diff * 111000  # 1 degree lat ≈ 111km
        lon_dist_m = model_osm_lon_diff * 111000 * math.cos(math.radians(model_stats['lat_center']))
        total_dist_m = math.sqrt(lat_dist_m**2 + lon_dist_m**2)
        
        print(f"   Approximate distance: {total_dist_m:.1f} meters")
        
        # Coverage analysis
        print(f"\n📊 COVERAGE ANALYSIS:")
        
        # Check if model detections fall within study area
        model_in_study = (
            model_stats['lat_min'] >= study_stats['lat_min'] and
            model_stats['lat_max'] <= study_stats['lat_max'] and
            model_stats['lon_min'] >= study_stats['lon_min'] and
            model_stats['lon_max'] <= study_stats['lon_max']
        )
        
        # Check if OSM buildings fall within study area  
        osm_in_study = (
            osm_stats['lat_min'] >= study_stats['lat_min'] and
            osm_stats['lat_max'] <= study_stats['lat_max'] and
            osm_stats['lon_min'] >= study_stats['lon_min'] and
            osm_stats['lon_max'] <= study_stats['lon_max']
        )
        
        print(f"   Model detections within study area: {'✅ YES' if model_in_study else '❌ NO'}")
        print(f"   OSM buildings within study area: {'✅ YES' if osm_in_study else '❌ NO'}")
        
        # Issue identification
        print(f"\n🚨 POTENTIAL ISSUES IDENTIFIED:")
        print("=" * 35)
        
        issues_found = False
        
        if total_dist_m > 100:
            print(f"❌ CENTER MISMATCH: Model and OSM centers are {total_dist_m:.1f}m apart!")
            issues_found = True
        
        if not model_in_study:
            print("❌ MODEL OUT OF BOUNDS: Model detections extend outside study area")
            issues_found = True
            
        if not osm_in_study:
            print("❌ OSM OUT OF BOUNDS: OSM buildings extend outside study area")
            issues_found = True
        
        # Check coordinate range differences
        lat_range_diff = abs((model_stats['lat_max'] - model_stats['lat_min']) - 
                           (osm_stats['lat_max'] - osm_stats['lat_min']))
        lon_range_diff = abs((model_stats['lon_max'] - model_stats['lon_min']) - 
                           (osm_stats['lon_max'] - osm_stats['lon_min']))
        
        if lat_range_diff > 0.001 or lon_range_diff > 0.001:
            print(f"⚠️  COVERAGE DIFFERENCE: Different geographic spans detected")
            print(f"   Model covers: {(model_stats['lat_max'] - model_stats['lat_min']):.6f}° lat, {(model_stats['lon_max'] - model_stats['lon_min']):.6f}° lon")
            print(f"   OSM covers: {(osm_stats['lat_max'] - osm_stats['lat_min']):.6f}° lat, {(osm_stats['lon_max'] - osm_stats['lon_min']):.6f}° lon")
            issues_found = True
        
        if not issues_found:
            print("✅ No major spatial alignment issues detected")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("=" * 20)
        
        if total_dist_m > 100:
            print("🔧 Consider adjusting study area polygon to better center both datasets")
        
        if not model_in_study or not osm_in_study:
            print("🔧 Expand study area polygon to fully contain both datasets")
            print("🔧 Or filter datasets to only include points within study area")
        
        if lat_range_diff > 0.001 or lon_range_diff > 0.001:
            print("🔧 Investigate why model and OSM have different geographic coverage")
            print("🔧 Check if model was trained on different area or time period")
        
        return {
            'model_stats': model_stats,
            'osm_stats': osm_stats,
            'study_stats': study_stats,
            'center_distance_m': total_dist_m,
            'model_in_study': model_in_study,
            'osm_in_study': osm_in_study
        }
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    diagnose_spatial_sync()
