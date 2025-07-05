#!/usr/bin/env python3
"""
Visual Evaluation Tool for Building Detection Accuracy

This script creates an interactive map to visually compare:
- Model detection results (red dots)
- OpenStreetMap ground truth buildings (blue polygons)
- Study area boundary (black outline)

Usage:
    python create_visual_comparison.py
"""

import json
import folium
import sys
from pathlib import Path
from folium import plugins

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def load_json_file(file_path):
    """Load JSON file with error handling."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None

def load_model_detections(file_path):
    """
    Load model detection results and filter valid entries.
    
    Args:
        file_path: Path to buildings_simple.json
        
    Returns:
        List of valid building detections
    """
    print(f"📄 Loading model detections from: {file_path}")
    
    data = load_json_file(file_path)
    if not data:
        return []
    
    # Filter valid entries (must have id, longitude, latitude)
    valid_detections = []
    invalid_count = 0
    
    for building in data:
        if (isinstance(building, dict) and 
            'id' in building and 
            'longitude' in building and 
            'latitude' in building and
            building['longitude'] is not None and
            building['latitude'] is not None):
            valid_detections.append(building)
        else:
            invalid_count += 1
    
    print(f"✅ Valid detections: {len(valid_detections)}")
    print(f"⚠️ Invalid/incomplete entries: {invalid_count}")
    
    return valid_detections

def load_osm_ground_truth(file_path):
    """
    Load OSM ground truth buildings.
    
    Args:
        file_path: Path to osm_buildings_corrected.json
        
    Returns:
        GeoJSON FeatureCollection of OSM buildings
    """
    print(f"📄 Loading OSM ground truth from: {file_path}")
    
    data = load_json_file(file_path)
    if not data or 'features' not in data:
        return {'type': 'FeatureCollection', 'features': []}
    
    print(f"✅ OSM buildings loaded: {len(data['features'])}")
    
    return data

def load_study_area(file_path):
    """
    Load study area polygon.
    
    Args:
        file_path: Path to sample_polygon.geojson
        
    Returns:
        GeoJSON polygon feature
    """
    print(f"📄 Loading study area from: {file_path}")
    
    data = load_json_file(file_path)
    if not data:
        return None
    
    # Extract polygon from FeatureCollection or Feature
    if data.get('type') == 'FeatureCollection' and data.get('features'):
        polygon = data['features'][0]
    elif data.get('type') == 'Feature':
        polygon = data
    else:
        polygon = data
    
    print("✅ Study area loaded")
    return polygon

def calculate_map_center(study_area):
    """Calculate center point for map from study area bounds."""
    if not study_area or 'geometry' not in study_area:
        # Default to Jakarta area
        return [-6.2175, 106.741]
    
    coords = study_area['geometry']['coordinates'][0]
    
    # Calculate bounds
    lats = [coord[1] for coord in coords]
    lons = [coord[0] for coord in coords]
    
    center_lat = (min(lats) + max(lats)) / 2
    center_lon = (min(lons) + max(lons)) / 2
    
    return [center_lat, center_lon]

def create_interactive_map(model_detections, osm_buildings, study_area):
    """
    Create interactive Folium map with all data layers.
    
    Args:
        model_detections: List of model detection points
        osm_buildings: GeoJSON of OSM buildings
        study_area: GeoJSON polygon of study area
        
    Returns:
        Folium map object
    """
    print("🗺️ Creating interactive map...")
    
    # Calculate map center and zoom
    center = calculate_map_center(study_area)
    
    # Create base map
    m = folium.Map(
        location=center,
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    
    # Add satellite layer as alternative
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add study area boundary (black outline)
    if study_area:
        folium.GeoJson(
            study_area,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'black',
                'weight': 3,
                'fillOpacity': 0.1
            },
            popup=folium.Popup("Study Area Boundary", parse_html=True),
            tooltip="Study Area"
        ).add_to(m)
    
    # Add OSM buildings (blue polygons with simple ID numbers)
    if osm_buildings and osm_buildings.get('features'):
        for idx, feature in enumerate(osm_buildings['features'], 1):
            # Create popup content
            props = feature.get('properties', {})
            popup_content = f"""
            <b>OSM Building #{idx}</b><br>
            OSM ID: {props.get('osm_id', 'N/A')}<br>
            Building Type: {props.get('building', 'N/A')}<br>
            Type: {props.get('osm_type', 'N/A')}
            """
            
            # Add building polygon
            folium.GeoJson(
                feature,
                style_function=lambda x: {
                    'fillColor': 'blue',
                    'color': 'darkblue',
                    'weight': 2,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(popup_content, parse_html=True),
                tooltip=f"OSM Building #{idx} (ID: {props.get('osm_id', 'N/A')})"
            ).add_to(m)
            
            # Calculate centroid for ID label
            if feature['geometry']['type'] == 'Polygon':
                coords = feature['geometry']['coordinates'][0]
                # Simple centroid calculation
                center_lon = sum(coord[0] for coord in coords) / len(coords)
                center_lat = sum(coord[1] for coord in coords) / len(coords)
                
                # Add simple sequential number as text label
                folium.Marker(
                    location=[center_lat, center_lon],
                    icon=folium.DivIcon(
                        html=f"""
                        <div style="
                            font-size: 10px;
                            font-weight: bold;
                            color: white;
                            background-color: blue;
                            border: 1px solid darkblue;
                            border-radius: 3px;
                            padding: 1px 3px;
                            text-align: center;
                            white-space: nowrap;
                            box-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                        ">{idx}</div>
                        """,
                        icon_size=(20, 12),
                        icon_anchor=(10, 6)
                    )
                ).add_to(m)
    
    # Add model detections (red dots with ID numbers)
    if model_detections:
        for detection in model_detections:
            # Add the red circle marker
            folium.CircleMarker(
                location=[detection['latitude'], detection['longitude']],
                radius=6,
                popup=folium.Popup(
                    f"<b>Model Detection</b><br>"
                    f"ID: {detection['id']}<br>"
                    f"Lat: {detection['latitude']:.6f}<br>"
                    f"Lon: {detection['longitude']:.6f}",
                    parse_html=True
                ),
                tooltip=f"Building ID: {detection['id']}",
                color='darkred',
                fillColor='red',
                fillOpacity=0.8,
                weight=2
            ).add_to(m)
            
            # Add building ID number as text label
            folium.Marker(
                location=[detection['latitude'], detection['longitude']],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: 10px;
                        font-weight: bold;
                        color: black;
                        background-color: white;
                        border: 1px solid black;
                        border-radius: 3px;
                        padding: 1px 3px;
                        text-align: center;
                        white-space: nowrap;
                        box-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                    ">{detection['id']}</div>
                    """,
                    icon_size=(30, 15),
                    icon_anchor=(15, 7)
                )
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 300px; height: 160px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>Legend</h4>
    <p><span style="color:red;">●</span> Model Detections ({} buildings)</p>
    <p><span style="background:white; border:1px solid black; padding:1px 3px; font-size:10px;">123</span> Model Building IDs</p>
    <p><span style="color:blue;">■</span> OSM Ground Truth ({} buildings)</p>
    <p><span style="background:blue; color:white; border:1px solid darkblue; padding:1px 3px; font-size:10px;">12</span> OSM Building Numbers</p>
    <p><span style="color:black;">▢</span> Study Area Boundary</p>
    </div>
    '''.format(len(model_detections), len(osm_buildings.get('features', [])))
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    print("✅ Interactive map created successfully")
    return m

def generate_evaluation_summary(model_detections, osm_buildings):
    """Generate basic statistics summary."""
    
    model_count = len(model_detections)
    osm_count = len(osm_buildings.get('features', []))
    
    summary = {
        "evaluation_summary": {
            "model_detections": model_count,
            "osm_ground_truth_buildings": osm_count,
            "detection_ratio": round(model_count / osm_count, 2) if osm_count > 0 else 0,
            "potential_over_detection": model_count > osm_count,
            "potential_under_detection": model_count < osm_count
        },
        "visual_analysis_notes": [
            "Red dots represent model detections",
            "Blue polygons represent OSM ground truth buildings",
            "Look for red dots inside blue polygons for accurate detections",
            "Red dots without nearby blue polygons may be false positives",
            "Blue polygons without nearby red dots may be missed detections"
        ]
    }
    
    return summary

def main():
    """Main function to create visual evaluation."""
    
    print("🏢 Building Detection - Visual Evaluation Tool")
    print("=" * 50)
    
    # File paths
    model_file = "output/buildings_simple.json"
    osm_file = "output/osm_buildings_corrected.json"
    area_file = "examples/sample_polygon.geojson"
    output_map = "output/visual_evaluation_map.html"
    output_summary = "output/evaluation_summary.json"
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Load data
    model_detections = load_model_detections(model_file)
    osm_buildings = load_osm_ground_truth(osm_file)
    study_area = load_study_area(area_file)
    
    if not model_detections:
        print("❌ No valid model detections found")
        return
    
    if not osm_buildings.get('features'):
        print("❌ No OSM ground truth buildings found")
        return
    
    # Create interactive map
    map_obj = create_interactive_map(model_detections, osm_buildings, study_area)
    
    # Save map
    map_obj.save(output_map)
    print(f"💾 Interactive map saved to: {output_map}")
    
    # Generate and save summary
    summary = generate_evaluation_summary(model_detections, osm_buildings)
    
    with open(output_summary, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"💾 Evaluation summary saved to: {output_summary}")
    
    # Print summary
    print("\n📊 Evaluation Summary:")
    print(f"  • Model detections: {summary['evaluation_summary']['model_detections']}")
    print(f"  • OSM ground truth: {summary['evaluation_summary']['osm_ground_truth_buildings']}")
    print(f"  • Detection ratio: {summary['evaluation_summary']['detection_ratio']} (Model/OSM)")
    
    if summary['evaluation_summary']['potential_over_detection']:
        print("  • ⚠️ Potential over-detection (model finds more buildings than OSM)")
    elif summary['evaluation_summary']['potential_under_detection']:
        print("  • ⚠️ Potential under-detection (model finds fewer buildings than OSM)")
    else:
        print("  • ✅ Similar detection count as OSM")
    
    print(f"\n🌐 Open the map in your browser: {output_map}")
    print("\n✅ Visual evaluation completed!")
    
    return map_obj, summary

if __name__ == "__main__":
    main()
