#!/usr/bin/env python3
"""
Debug Tile Download - Test manual download untuk troubleshooting
"""

import json
import requests
import mercantile
from PIL import Image
from io import BytesIO
from pathlib import Path

def test_tile_download():
    """Test download satu tile dari area sample polygon"""
    
    print("🔍 DEBUGGING TILE DOWNLOAD")
    print("=" * 40)
    
    # Load sample polygon coordinates
    polygon_file = Path("/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector/examples/sample_polygon.geojson")
    
    with open(polygon_file, 'r') as f:
        geojson_data = json.load(f)
    
    # Get polygon bounds
    coords = geojson_data['features'][0]['geometry']['coordinates'][0]
    lons = [coord[0] for coord in coords]
    lats = [coord[1] for coord in coords]
    
    minx, maxx = min(lons), max(lons)
    miny, maxy = min(lats), max(lats)
    
    print(f"📍 Polygon bounds:")
    print(f"   Lat: {miny:.6f} to {maxy:.6f}")
    print(f"   Lon: {minx:.6f} to {maxx:.6f}")
    
    # Get center point
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2
    print(f"   Center: ({center_lat:.6f}, {center_lon:.6f})")
    
    # Test different zoom levels
    zoom_levels = [16, 17, 18, 19]
    
    for zoom in zoom_levels:
        print(f"\n🎯 Testing zoom level {zoom}:")
        
        # Get tile for center point
        tile = mercantile.tile(center_lon, center_lat, zoom)
        print(f"   Tile coordinates: x={tile.x}, y={tile.y}, z={tile.z}")
        
        # Test OSM tile download
        osm_url = f"https://tile.openstreetmap.org/{tile.z}/{tile.x}/{tile.y}.png"
        print(f"   OSM URL: {osm_url}")
        
        try:
            headers = {'User-Agent': 'BuildingDetectionBot/1.0'}
            response = requests.get(osm_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ OSM download successful (size: {len(response.content)} bytes)")
                
                # Save image for inspection
                img = Image.open(BytesIO(response.content))
                output_file = f"/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector/debug_tile_osm_z{zoom}.png"
                img.save(output_file)
                print(f"   💾 Saved to: debug_tile_osm_z{zoom}.png")
                
            else:
                print(f"   ❌ OSM download failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ OSM download error: {e}")
        
        # Test Google Satellite for comparison
        google_url = f"https://mt1.google.com/vt/lyrs=s&x={tile.x}&y={tile.y}&z={tile.z}"
        print(f"   Google URL: {google_url}")
        
        try:
            response = requests.get(google_url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Google satellite download successful (size: {len(response.content)} bytes)")
                
                # Save image for comparison
                img = Image.open(BytesIO(response.content))
                output_file = f"/Users/farizputrahanggara/Documents/Tugas Akhir/building-detector/debug_tile_google_z{zoom}.png"
                img.save(output_file)
                print(f"   💾 Saved to: debug_tile_google_z{zoom}.png")
                
            else:
                print(f"   ❌ Google download failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Google download error: {e}")
    
    print(f"\n📋 SUMMARY:")
    print("=" * 20)
    print("📁 Check the generated debug_tile_*.png files to see:")
    print("   - OSM tiles (street map style)")
    print("   - Google satellite tiles (aerial imagery)")
    print("🔍 This will help identify which imagery shows buildings clearly")

if __name__ == "__main__":
    test_tile_download()
