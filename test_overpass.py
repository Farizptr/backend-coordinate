#!/usr/bin/env python3
"""
Test script for Overpass API client.

This script tests the OverpassClient with the sample polygon
and displays the results.
"""

import sys
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from evaluation.overpass_client import OverpassClient


def load_sample_polygon(polygon_path: str):
    """Load sample polygon from GeoJSON file."""
    try:
        with open(polygon_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading polygon: {e}")
        return None


def test_with_sample_polygon():
    """Test OverpassClient with the actual sample polygon."""
    
    print("🏢 Building Detection - Overpass API Client Test")
    print("=" * 50)
    
    # Load sample polygon
    polygon_path = "examples/sample_polygon.geojson"
    polygon_data = load_sample_polygon(polygon_path)
    
    if not polygon_data:
        print("❌ Failed to load sample polygon")
        return
    
    print(f"✅ Loaded polygon from: {polygon_path}")
    
    # Initialize client
    client = OverpassClient()
    
    try:
        print("🌐 Fetching building data from OpenStreetMap...")
        result = client.get_buildings_in_polygon(polygon_data)
        
        # Display results
        print("\n📊 Results:")
        print(f"  • Original buildings found: {result['metadata']['original_buildings']}")
        print(f"  • Buildings after filtering: {result['metadata']['filtered_buildings']}")
        print(f"  • Buildings removed (edge cases): {result['metadata']['buildings_removed']}")
        print(f"  • Filtering method: {result['metadata']['filtering_method']}")
        print(f"  • Data source: {result['metadata']['source']}")
        print(f"  • Query time: {result['metadata']['query_time']}")
        
        # Show sample buildings
        if result['features']:
            print("\n🏠 Sample buildings (first 3):")
            for i, feature in enumerate(result['features'][:3]):
                props = feature['properties']
                building_type = props.get('building', 'unknown')
                osm_id = props.get('osm_id', 'unknown')
                print(f"  {i+1}. OSM ID: {osm_id}, Type: {building_type}")
        
        # Save results
        output_path = "output/osm_buildings_ground_truth.json"
        Path("output").mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
        print("\n✅ Test completed successfully!")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None


if __name__ == "__main__":
    test_with_sample_polygon()
