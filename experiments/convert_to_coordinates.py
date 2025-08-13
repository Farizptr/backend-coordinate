#!/usr/bin/env python3
"""
Convert Building Detections to Coordinates
==========================================

Convert aggregated detections to useful formats:
1. Simple JSON coordinates (lat, lon)
2. GeoJSON format
3. Building statistics
"""

import json
import math
import os
from typing import List, Dict, Tuple

def tile2deg(x: int, y: int, z: int) -> Tuple[float, float, float, float]:
    """Convert tile coordinates to lat/lon bounds"""
    n = 2.0 ** z
    lon_deg_min = x / n * 360.0 - 180.0
    lat_rad_min = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
    lat_deg_min = math.degrees(lat_rad_min)
    
    lon_deg_max = (x + 1) / n * 360.0 - 180.0
    lat_rad_max = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg_max = math.degrees(lat_rad_max)
    
    return lon_deg_min, lat_deg_min, lon_deg_max, lat_deg_max

def pixel_to_latlng(pixel_x: float, pixel_y: float, tile_x: int, tile_y: int, zoom: int, tile_size: int = 256) -> Tuple[float, float]:
    """Convert pixel coordinates within a tile to lat/lng"""
    # Get tile bounds
    lon_min, lat_min, lon_max, lat_max = tile2deg(tile_x, tile_y, zoom)
    
    # Calculate pixel position within tile (0-1)
    pixel_ratio_x = pixel_x / tile_size
    pixel_ratio_y = pixel_y / tile_size
    
    # Convert to lat/lng
    longitude = lon_min + (lon_max - lon_min) * pixel_ratio_x
    latitude = lat_max + (lat_min - lat_max) * pixel_ratio_y  # Y is flipped
    
    return latitude, longitude

def box_to_coordinates(box: List[float], tile_info: str) -> Dict:
    """Convert detection box to geographic coordinates"""
    # Parse tile info: "18/209450/136320"
    parts = tile_info.split('/')
    if len(parts) != 3:
        return None
    
    zoom, tile_x, tile_y = map(int, parts)
    
    # Box format: [x1, y1, x2, y2] in pixels
    x1, y1, x2, y2 = box
    
    # Calculate center point
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Convert to lat/lng
    lat, lng = pixel_to_latlng(center_x, center_y, tile_x, tile_y, zoom)
    
    # Calculate corners for bounding box
    lat1, lng1 = pixel_to_latlng(x1, y1, tile_x, tile_y, zoom)
    lat2, lng2 = pixel_to_latlng(x2, y2, tile_x, tile_y, zoom)
    
    return {
        'center': {'latitude': lat, 'longitude': lng},
        'bbox': {
            'north': max(lat1, lat2),
            'south': min(lat1, lat2), 
            'east': max(lng1, lng2),
            'west': min(lng1, lng2)
        },
        'width_pixels': abs(x2 - x1),
        'height_pixels': abs(y2 - y1)
    }

def convert_detections_to_coordinates(input_file: str, output_dir: str = "output"):
    """Convert detections to coordinate formats"""
    
    print(f"🔄 Loading detections from {input_file}")
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return False
    
    detections = data.get('detections', [])
    print(f"📊 Processing {len(detections):,} detections")
    
    # Process detections
    buildings = []
    
    for i, detection in enumerate(detections):
        if i % 10000 == 0:
            print(f"   Processed {i:,} detections...")
        
        box = detection.get('box', [])
        tile = detection.get('tile', '')
        confidence = detection.get('confidence', 0)
        
        if not box or not tile:
            continue
        
        # Convert to coordinates
        coords = box_to_coordinates(box, tile)
        if coords is None:
            continue
        
        building = {
            'id': f"building_{i+1}",
            'latitude': coords['center']['latitude'],
            'longitude': coords['center']['longitude'],
            'confidence': confidence,
            'bbox': coords['bbox'],
            'size_pixels': {
                'width': coords['width_pixels'],
                'height': coords['height_pixels']
            },
            'tile': tile
        }
        
        buildings.append(building)
    
    print(f"✅ Converted {len(buildings):,} buildings to coordinates")
    
    # Create output files
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Simple coordinates JSON
    simple_coords = [
        {
            'id': b['id'],
            'latitude': b['latitude'],
            'longitude': b['longitude'],
            'confidence': b['confidence']
        }
        for b in buildings
    ]
    
    simple_file = os.path.join(output_dir, "central_jakarta_coordinates.json")
    with open(simple_file, 'w') as f:
        json.dump(simple_coords, f, indent=2)
    print(f"💾 Saved simple coordinates: {simple_file}")
    
    # 2. Detailed buildings JSON
    detailed_file = os.path.join(output_dir, "central_jakarta_buildings_detailed.json")
    with open(detailed_file, 'w') as f:
        json.dump({
            'area': 'Central Jakarta',
            'total_buildings': len(buildings),
            'processing_info': {
                'source': input_file,
                'total_detections': len(detections),
                'valid_buildings': len(buildings)
            },
            'buildings': buildings
        }, f, indent=2)
    print(f"💾 Saved detailed buildings: {detailed_file}")
    
    # 3. GeoJSON format
    features = []
    for building in buildings:
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [building['longitude'], building['latitude']]
            },
            'properties': {
                'id': building['id'],
                'confidence': building['confidence'],
                'tile': building['tile'],
                'size_pixels': building['size_pixels']
            }
        }
        features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    geojson_file = os.path.join(output_dir, "central_jakarta_buildings.geojson")
    with open(geojson_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    print(f"💾 Saved GeoJSON: {geojson_file}")
    
    # 4. Statistics
    high_conf = [b for b in buildings if b['confidence'] > 0.7]
    medium_conf = [b for b in buildings if 0.5 <= b['confidence'] <= 0.7]
    low_conf = [b for b in buildings if b['confidence'] < 0.5]
    
    stats = {
        'area': 'Central Jakarta',
        'total_buildings': len(buildings),
        'confidence_distribution': {
            'high_confidence (>0.7)': len(high_conf),
            'medium_confidence (0.5-0.7)': len(medium_conf),
            'low_confidence (<0.5)': len(low_conf)
        },
        'geographic_bounds': {
            'north': max(b['latitude'] for b in buildings),
            'south': min(b['latitude'] for b in buildings),
            'east': max(b['longitude'] for b in buildings),
            'west': min(b['longitude'] for b in buildings)
        }
    }
    
    stats_file = os.path.join(output_dir, "central_jakarta_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"💾 Saved statistics: {stats_file}")
    
    # Print final summary
    print(f"\n{'='*50}")
    print(f"CONVERSION COMPLETED")
    print(f"{'='*50}")
    print(f"Total buildings: {len(buildings):,}")
    print(f"High confidence (>0.7): {len(high_conf):,}")
    print(f"Medium confidence (0.5-0.7): {len(medium_conf):,}")
    print(f"Low confidence (<0.5): {len(low_conf):,}")
    print(f"Geographic bounds:")
    print(f"  North: {stats['geographic_bounds']['north']:.6f}")
    print(f"  South: {stats['geographic_bounds']['south']:.6f}")
    print(f"  East:  {stats['geographic_bounds']['east']:.6f}")
    print(f"  West:  {stats['geographic_bounds']['west']:.6f}")
    print(f"{'='*50}")
    
    return True

def main():
    """Main execution"""
    input_file = "output/central_jakarta_aggregated.json"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("Please run safe_aggregate_tiles.py first")
        return 1
    
    success = convert_detections_to_coordinates(input_file)
    
    if success:
        print(f"\n🎉 Conversion completed successfully!")
        return 0
    else:
        print(f"\n❌ Conversion failed!")
        return 1

if __name__ == "__main__":
    exit(main())
