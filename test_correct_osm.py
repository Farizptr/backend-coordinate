#!/usr/bin/env python3
"""
Test script to verify OSM fetching with correct polygon
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from evaluation.overpass_client import OverpassClient

def test_osm_with_correct_polygon():
    """Test OSM fetching using the same study area polygon"""
    
    print("🔍 Testing OSM Fetching with Correct Polygon")
    print("=" * 50)
    
    # File paths
    base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
    study_area_file = base_dir / "examples" / "sample_polygon.geojson"
    
    # Load study area polygon
    with open(study_area_file, 'r') as f:
        study_area = json.load(f)
    
    print("📍 Study area polygon loaded:")
    coords = study_area['features'][0]['geometry']['coordinates'][0]
    print(f"   Coordinates: {len(coords)} points")
    for i, coord in enumerate(coords):
        print(f"   Point {i+1}: ({coord[1]:.6f}, {coord[0]:.6f})")
    
    # Calculate bounding box
    lats = [coord[1] for coord in coords]
    lons = [coord[0] for coord in coords]
    print(f"\n📊 Study area bounds:")
    print(f"   Latitude:  {min(lats):.6f} to {max(lats):.6f}")
    print(f"   Longitude: {min(lons):.6f} to {max(lons):.6f}")
    print(f"   Center:    ({sum(lats)/len(lats):.6f}, {sum(lons)/len(lons):.6f})")
    
    # Test OSM client
    print(f"\n🌐 Fetching OSM data for this polygon...")
    
    try:
        client = OverpassClient(timeout=60)
        osm_data = client.get_buildings_in_polygon(study_area)
        
        print(f"✅ OSM fetch successful!")
        print(f"   Buildings found: {len(osm_data['features'])}")
        
        if osm_data['features']:
            # Analyze first few buildings
            sample_building = osm_data['features'][0]
            if 'properties' in sample_building and 'centroid_lat' in sample_building['properties']:
                print(f"   Sample building centroid: ({sample_building['properties']['centroid_lat']:.6f}, {sample_building['properties']['centroid_lon']:.6f})")
            
            # Calculate OSM data bounds
            osm_lats = []
            osm_lons = []
            for feature in osm_data['features']:
                if 'properties' in feature:
                    if 'centroid_lat' in feature['properties']:
                        osm_lats.append(feature['properties']['centroid_lat'])
                        osm_lons.append(feature['properties']['centroid_lon'])
            
            if osm_lats:
                print(f"\n📊 OSM buildings bounds:")
                print(f"   Latitude:  {min(osm_lats):.6f} to {max(osm_lats):.6f}")
                print(f"   Longitude: {min(osm_lons):.6f} to {max(osm_lons):.6f}")
                print(f"   Center:    ({sum(osm_lats)/len(osm_lats):.6f}, {sum(osm_lons)/len(osm_lons):.6f})")
                
                # Check if within study area
                study_center_lat = sum(lats)/len(lats)
                study_center_lon = sum(lons)/len(lons)
                osm_center_lat = sum(osm_lats)/len(osm_lats)
                osm_center_lon = sum(osm_lons)/len(osm_lons)
                
                lat_diff = abs(study_center_lat - osm_center_lat)
                lon_diff = abs(study_center_lon - osm_center_lon)
                
                print(f"\n🎯 Alignment Check:")
                print(f"   Center difference: Lat {lat_diff:.6f}°, Lon {lon_diff:.6f}°")
                
                if lat_diff < 0.001 and lon_diff < 0.001:
                    print("   ✅ OSM data properly aligned with study area!")
                else:
                    print("   ❌ OSM data NOT aligned with study area!")
        
        # Save corrected OSM data
        output_file = base_dir / "output" / "osm_buildings_corrected.json"
        with open(output_file, 'w') as f:
            json.dump(osm_data, f, indent=2)
        
        print(f"\n💾 Corrected OSM data saved to: {output_file}")
        
        # Show metadata
        if 'metadata' in osm_data:
            metadata = osm_data['metadata']
            print(f"\n📋 Metadata:")
            print(f"   Query time: {metadata.get('query_time', 'Unknown')}")
            print(f"   Original buildings: {metadata.get('original_buildings', 'Unknown')}")
            print(f"   Filtered buildings: {metadata.get('filtered_buildings', 'Unknown')}")
            print(f"   Buildings removed: {metadata.get('buildings_removed', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_osm_with_correct_polygon()
