#!/usr/bin/env python3
"""
Automated Synchronized Building Detection Evaluation

One-command solution that automatically handles spatial synchronization
"""

import json
import requests
import subprocess
import sys
import math
from pathlib import Path

def check_sync_status():
    """Check if OSM buildings are synchronized with study area"""
    print("🔍 Checking spatial synchronization...")
    
    base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
    
    try:
        # Load study area center
        with open(base_dir / "examples" / "sample_polygon.geojson", 'r') as f:
            study_area = json.load(f)
            coords = study_area['features'][0]['geometry']['coordinates'][0]
            study_lat = sum(coord[1] for coord in coords) / len(coords)
            study_lon = sum(coord[0] for coord in coords) / len(coords)
        
        # Load OSM buildings center
        try:
            with open(base_dir / "output" / "osm_buildings_corrected.json", 'r') as f:
                osm_data = json.load(f)
                
                if 'features' in osm_data and osm_data['features']:
                    osm_lats, osm_lons = [], []
                    for feature in osm_data['features']:
                        if feature['geometry']['type'] == 'Polygon':
                            coords = feature['geometry']['coordinates'][0]
                            avg_lat = sum(coord[1] for coord in coords) / len(coords)
                            avg_lon = sum(coord[0] for coord in coords) / len(coords)
                            osm_lats.append(avg_lat)
                            osm_lons.append(avg_lon)
                    
                    if osm_lats:
                        osm_lat = sum(osm_lats) / len(osm_lats)
                        osm_lon = sum(osm_lons) / len(osm_lons)
                        
                        # Calculate distance
                        lat1, lon1, lat2, lon2 = map(math.radians, [study_lat, study_lon, osm_lat, osm_lon])
                        dlat, dlon = lat2 - lat1, lon2 - lon1
                        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                        distance_km = 6371 * 2 * math.asin(math.sqrt(a))
                        
                        return distance_km < 1.0, distance_km
                        
        except FileNotFoundError:
            pass
        
        return False, float('inf')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, float('inf')

def download_osm_buildings():
    """Download OSM buildings from study area"""
    print("🌐 Downloading OSM buildings...")
    
    base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
    
    try:
        # Get study area bounds
        with open(base_dir / "examples" / "sample_polygon.geojson", 'r') as f:
            study_area = json.load(f)
            coords = study_area['features'][0]['geometry']['coordinates'][0]
            min_lat = min(coord[1] for coord in coords)
            max_lat = max(coord[1] for coord in coords)
            min_lon = min(coord[0] for coord in coords)
            max_lon = max(coord[0] for coord in coords)
        
        # Overpass query
        query = f"""
        [out:json][timeout:60];
        (
          way["building"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out geom;
        """
        
        response = requests.post("http://overpass-api.de/api/interpreter", data=query, timeout=120)
        response.raise_for_status()
        osm_data = response.json()
        
        # Convert to GeoJSON
        features = []
        for element in osm_data.get('elements', []):
            if element.get('type') == 'way' and 'geometry' in element:
                coords = [[node['lon'], node['lat']] for node in element['geometry']]
                if coords and coords[0] != coords[-1]:
                    coords.append(coords[0])
                
                if len(coords) >= 4:
                    features.append({
                        "type": "Feature",
                        "properties": {"id": element.get('id')},
                        "geometry": {"type": "Polygon", "coordinates": [coords]}
                    })
        
        # Save
        geojson_data = {"type": "FeatureCollection", "features": features}
        with open(base_dir / "output" / "osm_buildings_corrected.json", 'w') as f:
            json.dump(geojson_data, f, indent=2)
        
        print(f"✅ Downloaded {len(features)} OSM buildings")
        return True
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def run_evaluation():
    """Run enhanced evaluation"""
    print("🎨 Running enhanced evaluation...")
    
    base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
    
    try:
        result = subprocess.run([
            sys.executable, str(base_dir / "create_enhanced_evaluation.py")
        ], capture_output=True, text=True, cwd=base_dir)
        
        if result.returncode == 0:
            print("✅ Evaluation completed")
            return True
        else:
            print(f"❌ Evaluation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Synchronized Evaluation")
    parser.add_argument("--force-sync", "-f", action="store_true", 
                       help="Force re-download OSM buildings")
    args = parser.parse_args()
    
    print("🤖 AUTOMATED SYNCHRONIZED EVALUATION")
    print("=" * 50)
    
    # Check sync status
    is_synced, distance = check_sync_status()
    print(f"📊 Sync Status: {'✅ Synchronized' if is_synced else '❌ Not Synchronized'}")
    print(f"📏 Distance: {distance:.3f}km")
    
    # Sync if needed or forced
    if not is_synced or args.force_sync:
        if args.force_sync:
            print("🔄 Force sync requested")
        else:
            print(f"🔧 Synchronization needed ({distance:.1f}km apart)")
        
        if not download_osm_buildings():
            print("❌ Synchronization failed")
            return False
        print("✅ Synchronization completed")
    else:
        print("✅ Already synchronized")
    
    # Run evaluation
    success = run_evaluation()
    
    if success:
        base_dir = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector")
        map_file = base_dir / "output" / "enhanced_evaluation_map.html"
        print(f"\n🌐 View results: file://{map_file}")
        print("✅ Automated evaluation completed!")
    else:
        print("❌ Automated evaluation failed")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
