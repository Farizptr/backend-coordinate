#!/usr/bin/env python3
"""
Test script untuk memvisualisasikan tile images yang didownload
"""

import json
import os
import sys
from pathlib import Path
import mercantile
import requests
from io import BytesIO
from PIL import Image

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from shapely.geometry import shape, Polygon
from src.core.tile_utils import get_tiles_for_polygon, get_tile_image, get_tile_bounds, create_stitched_image
import matplotlib.pyplot as plt

def load_sample_polygon():
    """Load polygon dari sample_polygon.geojson"""
    sample_path = Path(__file__).parent / "examples" / "sample_polygon.geojson"
    
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample polygon not found: {sample_path}")
    
    with open(sample_path, 'r') as f:
        geojson_data = json.load(f)
    
    # Get first feature
    first_feature = geojson_data['features'][0]
    polygon = shape(first_feature['geometry'])
    
    print(f"✓ Loaded polygon with bounds: {polygon.bounds}")
    return polygon

def test_get_tiles():
    """Test getting tiles for polygon"""
    print("\n=== Testing Tile Retrieval ===")
    
    # Load polygon
    polygon = load_sample_polygon()
    
    # Get tiles with zoom level 18 (high detail)
    zoom = 18
    tiles = get_tiles_for_polygon(polygon, zoom=zoom)
    
    print(f"✓ Found {len(tiles)} tiles at zoom level {zoom}")
    
    # Print tile information
    for i, tile in enumerate(tiles):
        bounds = get_tile_bounds(tile)
        print(f"  Tile {i+1}: z={tile.z}, x={tile.x}, y={tile.y}")
        print(f"    Bounds: {bounds}")
    
    return tiles

def test_download_images(tiles):
    """Test downloading and saving tile images"""
    print("\n=== Testing Image Download ===")
    
    # Create output directory
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    downloaded_tiles = []
    
    for i, tile in enumerate(tiles):
        try:
            print(f"📥 Downloading tile {i+1}/{len(tiles)}: z={tile.z}, x={tile.x}, y={tile.y}")
            
            # Download image
            img = get_tile_image(tile)
            
            # Save individual tile
            filename = f"tile_{tile.z}_{tile.x}_{tile.y}.png"
            filepath = output_dir / filename
            img.save(filepath)
            
            print(f"  ✓ Saved: {filename}")
            
            # Store tile info with image for stitching
            tile_data = {
                'tile': tile,
                'image': img,
                'bounds': get_tile_bounds(tile),
                'filepath': filepath
            }
            downloaded_tiles.append(tile_data)
            
        except Exception as e:
            print(f"  ❌ Failed to download tile {tile.z}/{tile.x}/{tile.y}: {e}")
    
    print(f"✓ Successfully downloaded {len(downloaded_tiles)} out of {len(tiles)} tiles")
    return downloaded_tiles

def test_stitch_images(downloaded_tiles):
    """Test stitching downloaded tile images into a single image"""
    print("\n=== Testing Image Stitching ===")
    
    if not downloaded_tiles:
        print("  ❌ No tiles to stitch")
        return
    
    # Get bounds for stitching
    bounds = [tile_data['bounds'] for tile_data in downloaded_tiles]
    min_x = min(bounds, key=lambda b: b[0])[0]
    min_y = min(bounds, key=lambda b: b[1])[1]
    max_x = max(bounds, key=lambda b: b[2])[2]
    max_y = max(bounds, key=lambda b: b[3])[3]
    
    # Define output stitched image path
    output_dir = Path(__file__).parent / "test_output"
    stitched_image_path = output_dir / "stitched_image.png"
    
    try:
        # Create stitched image
        stitched_image = create_stitched_image(downloaded_tiles, output_size=(800, 800))
        
        # Save stitched image
        stitched_image.save(stitched_image_path)
        print(f"✓ Stitched image saved: {stitched_image_path}")
        
        # Display stitched image
        plt.figure(figsize=(10, 10))
        plt.imshow(stitched_image)
        plt.title("Stitched Image")
        plt.axis("off")
        plt.show()
        
    except Exception as e:
        print(f"  ❌ Failed to stitch images: {e}")

def create_test_polygons():
    """Create test polygons for different urban areas with buildings"""
    
    test_areas = {
        "jakarta_central": {
            "name": "Jakarta Central (Bundaran HI)",
            "polygon": Polygon([
                [106.8229, -6.1944],   # SW
                [106.8229, -6.1920],   # NW  
                [106.8260, -6.1920],   # NE
                [106.8260, -6.1944],   # SE
                [106.8229, -6.1944]    # SW (close)
            ])
        },
        "jakarta_south": {
            "name": "Jakarta South (Senayan)",
            "polygon": Polygon([
                [106.7990, -6.2380],   # SW
                [106.7990, -6.2350],   # NW
                [106.8020, -6.2350],   # NE
                [106.8020, -6.2380],   # SE
                [106.7990, -6.2380]    # SW (close)
            ])
        },
        "original_sample": {
            "name": "Original Sample Area",
            "polygon": load_sample_polygon()
        }
    }
    
    return test_areas

def test_multiple_areas_and_zooms():
    """Test multiple areas with different zoom levels"""
    print("\n=== Testing Multiple Areas and Zoom Levels ===")
    
    test_areas = create_test_polygons()
    zoom_levels = [16, 17, 18]  # Different zoom levels to compare
    
    all_results = []
    
    for area_key, area_info in test_areas.items():
        print(f"\n🏙️  Testing area: {area_info['name']}")
        
        for zoom in zoom_levels:
            print(f"  📏 Zoom level: {zoom}")
            
            # Get tiles for this area and zoom
            tiles = get_tiles_for_polygon(area_info['polygon'], zoom=zoom)
            print(f"    Found {len(tiles)} tiles")
            
            # Download first few tiles (limit to avoid too many downloads)
            max_tiles = min(3, len(tiles))
            
            for i in range(max_tiles):
                tile = tiles[i]
                try:
                    # Download image
                    img = get_tile_image(tile)
                    
                    # Save with descriptive filename
                    filename = f"tile_{area_key}_z{zoom}_{tile.x}_{tile.y}.png"
                    output_dir = Path(__file__).parent / "test_output"
                    output_dir.mkdir(exist_ok=True)
                    filepath = output_dir / filename
                    img.save(filepath)
                    
                    print(f"    ✓ Saved: {filename}")
                    
                    result = {
                        'area': area_info['name'],
                        'zoom': zoom,
                        'tile': tile,
                        'filename': filename,
                        'bounds': get_tile_bounds(tile)
                    }
                    all_results.append(result)
                    
                except Exception as e:
                    print(f"    ❌ Failed: {e}")
    
    return all_results

def diagnostic_tile_analysis():
    """Analyze tiles in detail to understand why some don't show buildings"""
    print("\n=== DIAGNOSTIC: Tile Analysis ===")
    
    # Focus on Jakarta Central area with zoom 18 where issues were observed
    jakarta_central = Polygon([
        [106.8229, -6.1944],   # SW
        [106.8229, -6.1920],   # NW  
        [106.8260, -6.1920],   # NE
        [106.8260, -6.1944],   # SE
        [106.8229, -6.1944]    # SW (close)
    ])
    
    tiles = get_tiles_for_polygon(jakarta_central, zoom=18)
    print(f"📊 Found {len(tiles)} tiles for Jakarta Central at zoom 18")
    
    output_dir = Path(__file__).parent / "diagnostic_output"
    output_dir.mkdir(exist_ok=True)
    
    analysis_results = []
    
    for i, tile in enumerate(tiles):
        bounds = get_tile_bounds(tile)
        
        print(f"\n🔍 Tile {i+1}/{len(tiles)}: z={tile.z}, x={tile.x}, y={tile.y}")
        print(f"   Bounds: [{bounds[0]:.6f}, {bounds[1]:.6f}, {bounds[2]:.6f}, {bounds[3]:.6f}]")
        
        # Calculate tile center
        center_lon = (bounds[0] + bounds[2]) / 2
        center_lat = (bounds[1] + bounds[3]) / 2
        print(f"   Center: ({center_lon:.6f}, {center_lat:.6f})")
        
        # Generate tile URL for verification
        url = f"https://tile.openstreetmap.org/{tile.z}/{tile.x}/{tile.y}.png"
        print(f"   URL: {url}")
        
        try:
            # Download and analyze tile
            img = get_tile_image(tile)
            
            # Save with detailed filename
            filename = f"diagnostic_tile_{i+1}_z{tile.z}_x{tile.x}_y{tile.y}.png"
            filepath = output_dir / filename
            img.save(filepath)
            
            # Basic image analysis - check if it's mostly roads/empty
            import numpy as np
            img_array = np.array(img)
            
            # Calculate color diversity (more diverse = more likely to have buildings)
            unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
            avg_brightness = np.mean(img_array)
            
            result = {
                'tile_number': i+1,
                'tile': tile,
                'bounds': bounds,
                'center': (center_lon, center_lat),
                'url': url,
                'filename': filename,
                'unique_colors': unique_colors,
                'avg_brightness': avg_brightness,
                'likely_has_buildings': unique_colors > 100 and avg_brightness < 200
            }
            
            analysis_results.append(result)
            
            status = "🏢 Likely has buildings" if result['likely_has_buildings'] else "🛣️  Likely roads/empty"
            print(f"   Status: {status} (colors: {unique_colors}, brightness: {avg_brightness:.1f})")
            print(f"   ✓ Saved: {filename}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Summary analysis
    print(f"\n📋 SUMMARY:")
    building_tiles = [r for r in analysis_results if r['likely_has_buildings']]
    empty_tiles = [r for r in analysis_results if not r['likely_has_buildings']]
    
    print(f"   🏢 Tiles likely with buildings: {len(building_tiles)}")
    print(f"   🛣️  Tiles likely empty/roads: {len(empty_tiles)}")
    
    if empty_tiles:
        print(f"\n🔎 Empty tiles details:")
        for tile in empty_tiles:
            print(f"   - Tile {tile['tile_number']}: center ({tile['center'][0]:.6f}, {tile['center'][1]:.6f})")
    
    return analysis_results

def test_alternative_tile_sources():
    """Test alternative tile sources to compare data quality"""
    print("\n=== Testing Alternative Tile Sources ===")
    
    # Use one problematic tile coordinate for comparison
    tile = mercantile.Tile(x=208858, y=135589, z=18)  # From Jakarta Central
    bounds = get_tile_bounds(tile)
    
    print(f"🧪 Testing tile z={tile.z}, x={tile.x}, y={tile.y}")
    print(f"   Bounds: {bounds}")
    
    # Different tile sources
    tile_sources = {
        'osm_standard': f"https://tile.openstreetmap.org/{tile.z}/{tile.x}/{tile.y}.png",
        'osm_hot': f"https://tile-a.openstreetmap.fr/hot/{tile.z}/{tile.x}/{tile.y}.png",
        'cartodb': f"https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{tile.z}/{tile.x}/{tile.y}.png"
    }
    
    output_dir = Path(__file__).parent / "diagnostic_output"
    output_dir.mkdir(exist_ok=True)
    
    for source_name, url in tile_sources.items():
        try:
            print(f"📥 Downloading from {source_name}...")
            headers = {'User-Agent': 'BuildingDetectionBot/1.0'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content)).convert('RGB')
                filename = f"comparison_{source_name}_z{tile.z}_x{tile.x}_y{tile.y}.png"
                filepath = output_dir / filename
                img.save(filepath)
                print(f"   ✓ Saved: {filename}")
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_specific_polygon():
    """Test the specific polygon coordinates provided by user"""
    print("\n=== Testing User-Specified Polygon ===")
    
    # Create polygon from user coordinates
    specific_polygon = Polygon([
        [106.6957666989224, -6.2583292723158905],    # SW
        [106.6957666989224, -6.258918583726057],     # NW
        [106.69643904398265, -6.258918583726057],    # NE
        [106.69643904398265, -6.2583292723158905],   # SE
        [106.6957666989224, -6.2583292723158905]     # SW (close)
    ])
    
    print(f"📍 Testing polygon bounds: {specific_polygon.bounds}")
    area_width = specific_polygon.bounds[2] - specific_polygon.bounds[0]
    area_height = specific_polygon.bounds[3] - specific_polygon.bounds[1]
    print(f"📏 Area size: {area_width:.7f}° x {area_height:.7f}° (~{area_width*111000:.1f}m x {area_height*111000:.1f}m)")
    
    zoom_levels = [16, 17, 18]
    output_dir = Path(__file__).parent / "specific_test_output"
    output_dir.mkdir(exist_ok=True)
    
    all_results = []
    
    for zoom in zoom_levels:
        print(f"\n🔍 Testing zoom level {zoom}")
        
        tiles = get_tiles_for_polygon(specific_polygon, zoom=zoom)
        print(f"   Found {len(tiles)} tiles")
        
        for i, tile in enumerate(tiles):
            bounds = get_tile_bounds(tile)
            center_lon = (bounds[0] + bounds[2]) / 2
            center_lat = (bounds[1] + bounds[3]) / 2
            
            print(f"\n   📋 Tile {i+1}: z={tile.z}, x={tile.x}, y={tile.y}")
            print(f"      Bounds: [{bounds[0]:.6f}, {bounds[1]:.6f}, {bounds[2]:.6f}, {bounds[3]:.6f}]")
            print(f"      Center: ({center_lon:.6f}, {center_lat:.6f})")
            
            try:
                # Download tile
                img = get_tile_image(tile)
                
                # Detailed analysis
                import numpy as np
                img_array = np.array(img)
                
                # Enhanced building detection analysis
                unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
                avg_brightness = np.mean(img_array)
                
                # Calculate color variance (more variance = more diverse structures)
                color_variance = np.var(img_array)
                
                # Check for rectangular patterns (buildings often have rectangular shapes)
                gray = np.mean(img_array, axis=2)
                edges = np.abs(np.diff(gray, axis=0)).sum() + np.abs(np.diff(gray, axis=1)).sum()
                edge_density = edges / (gray.shape[0] * gray.shape[1])
                
                # More sophisticated building likelihood
                building_score = 0
                if unique_colors > 50:
                    building_score += 1
                if avg_brightness < 230:  # Not too bright (not empty)
                    building_score += 1
                if color_variance > 1000:  # Good color variety
                    building_score += 1
                if edge_density > 10:  # Good edge definition
                    building_score += 1
                
                has_buildings = building_score >= 2
                
                # Save with detailed filename
                filename = f"specific_z{zoom}_x{tile.x}_y{tile.y}_score{building_score}.png"
                filepath = output_dir / filename
                img.save(filepath)
                
                result = {
                    'zoom': zoom,
                    'tile': tile,
                    'bounds': bounds,
                    'center': (center_lon, center_lat),
                    'filename': filename,
                    'unique_colors': unique_colors,
                    'avg_brightness': avg_brightness,
                    'color_variance': color_variance,
                    'edge_density': edge_density,
                    'building_score': building_score,
                    'has_buildings': has_buildings
                }
                all_results.append(result)
                
                status_icon = "🏢" if has_buildings else "🛣️"
                status_text = "HAS BUILDINGS" if has_buildings else "roads/empty"
                
                print(f"      {status_icon} Analysis: {status_text} (score: {building_score}/4)")
                print(f"         - Colors: {unique_colors}")
                print(f"         - Brightness: {avg_brightness:.1f}")
                print(f"         - Variance: {color_variance:.1f}")
                print(f"         - Edge density: {edge_density:.1f}")
                print(f"      ✓ Saved: {filename}")
                
            except Exception as e:
                print(f"      ❌ Failed: {e}")
    
    # Summary
    print(f"\n📊 ANALYSIS SUMMARY:")
    building_tiles = [r for r in all_results if r['has_buildings']]
    empty_tiles = [r for r in all_results if not r['has_buildings']]
    
    print(f"   🏢 Tiles with buildings: {len(building_tiles)}")
    print(f"   🛣️  Tiles without buildings: {len(empty_tiles)}")
    
    if building_tiles:
        print(f"\n✅ Buildings detected in:")
        for tile in building_tiles:
            print(f"   - Zoom {tile['zoom']}: {tile['filename']} (score: {tile['building_score']}/4)")
    
    if empty_tiles:
        print(f"\n❓ No buildings detected in:")
        for tile in empty_tiles:
            print(f"   - Zoom {tile['zoom']}: {tile['filename']} (score: {tile['building_score']}/4)")
    
    return all_results

def manual_visual_inspection():
    """Manual visual inspection tool - let user validate what's actually in the tiles"""
    print("\n=== MANUAL VISUAL INSPECTION ===")
    print("🔍 Let's manually check what's actually in the tiles...")
    
    # Load the specific polygon test results
    output_dir = Path(__file__).parent / "specific_test_output"
    
    if not output_dir.exists():
        print("❌ No specific test results found. Run test_specific_polygon() first.")
        return
    
    tile_files = list(output_dir.glob("*.png"))
    
    print(f"📁 Found {len(tile_files)} tile images to inspect:")
    
    for i, filepath in enumerate(sorted(tile_files)):
        filename = filepath.name
        
        # Extract info from filename
        parts = filename.replace('.png', '').split('_')
        zoom = parts[1][1:]  # Remove 'z' prefix
        x = parts[2][1:]     # Remove 'x' prefix  
        y = parts[3][1:]     # Remove 'y' prefix
        
        print(f"\n📷 Image {i+1}: {filename}")
        print(f"   Zoom: {zoom}, X: {x}, Y: {y}")
        print(f"   Path: {filepath}")
        
        # Ask user to manually inspect
        print("   👁️  Please manually check this image and tell me:")
        print("      - Are there any buildings visible? (houses, apartments, commercial buildings)")
        print("      - What do you see? (roads, trees, empty land, etc.)")
        print("      - Quality of the image for building detection?")
        print("")
    
    print("💡 RECOMMENDATIONS for better building detection:")
    print("   1. Use pre-trained building detection models (like YOLO trained on buildings)")
    print("   2. Use satellite imagery instead of map tiles (better building visibility)")
    print("   3. Manual labeling for training custom detection models")
    print("   4. Use higher resolution imagery sources")
    print("   5. Focus on visual features specific to buildings (rectangular shapes, shadows, etc.)")

def create_improved_detection_approach():
    """Outline improved approach for building detection"""
    print("\n=== IMPROVED BUILDING DETECTION APPROACH ===")
    
    print("🎯 BETTER METHODS:")
    print("   1. Pre-trained Models:")
    print("      - YOLOv8 trained on aerial/satellite building datasets")
    print("      - Mask R-CNN for building segmentation")
    print("      - DeepLab for semantic segmentation")
    
    print("   2. Better Data Sources:")
    print("      - Google Satellite imagery (higher resolution)")
    print("      - Bing aerial imagery")
    print("      - Planet or Sentinel satellite data")
    
    print("   3. Improved Image Analysis:")
    print("      - Edge detection + shape analysis for rectangular structures")
    print("      - Shadow detection (buildings cast shadows)")
    print("      - Texture analysis (building rooftops have different textures)")
    print("      - Color clustering for building materials")
    
    print("   4. Multi-scale Analysis:")
    print("      - Combine multiple zoom levels")
    print("      - Use context from surrounding areas")
    
    print("\n❌ Why Simple Metrics Failed:")
    print("   - unique_colors: Roads and vegetation also have varied colors")
    print("   - brightness: Empty areas can also have low brightness")
    print("   - edge_density: Roads and natural features create edges too")
    print("   - color_variance: Not specific to buildings")

if __name__ == "__main__":
    try:
        print("🚀 Manual Visual Inspection Tool...")
        
        # Manual inspection of tiles
        manual_visual_inspection()
        
        # Show improved detection approaches
        create_improved_detection_approach()
        
        print(f"\n✅ Inspection tool completed!")
        print(f"🔍 Please manually check the images in specific_test_output/ folder")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
