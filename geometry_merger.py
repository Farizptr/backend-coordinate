#!/usr/bin/env python3
"""
Geometry Merger Script
=====================

Merge individual building detections into clustered geometries.
Uses spatial clustering and buffer union to create building footprints.
"""

import json
import os
import sys
import logging
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Default parameters
DEFAULT_CONFIG = {
    'clustering_distance_degrees': 0.0005,  # ~50 meters at Jakarta latitude
    'min_samples_per_cluster': 2,           # minimum detections per cluster
    'buffer_radius_degrees': 0.00015,       # ~15 meters buffer
    'confidence_threshold': 0.7,            # filter low confidence detections
    'geometry_type': 'buffer_union'         # 'convex_hull' or 'buffer_union'
}

def check_dependencies():
    """Check if required libraries are available"""
    try:
        from sklearn.cluster import DBSCAN
        from shapely.geometry import Point, Polygon, MultiPolygon
        from shapely.ops import unary_union
        import geopandas as gpd
        return True
    except ImportError as e:
        logger.error(f"Missing required dependencies: {e}")
        logger.info("Please install: pip install scikit-learn shapely geopandas")
        return False

def load_coordinate_data(input_file):
    """Load coordinate data from JSON file"""
    logger.info(f"Loading coordinate data from {input_file}")
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            buildings = data
        else:
            logger.error(f"Unexpected data format in {input_file}")
            return None
            
        logger.info(f"Loaded {len(buildings)} building coordinates")
        return buildings
        
    except Exception as e:
        logger.error(f"Error loading coordinate data: {e}")
        return None

def filter_buildings_by_confidence(buildings, threshold=0.7):
    """Filter buildings by confidence threshold"""
    filtered = [b for b in buildings if b.get('confidence', 0) >= threshold]
    logger.info(f"Filtered {len(buildings)} → {len(filtered)} buildings (confidence >= {threshold})")
    return filtered

def spatial_clustering(buildings, eps=0.0005, min_samples=2):
    """Perform spatial clustering on building coordinates"""
    from sklearn.cluster import DBSCAN
    
    # Extract coordinates
    coords = np.array([[b['longitude'], b['latitude']] for b in buildings])
    
    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    labels = clustering.labels_
    
    # Group buildings by cluster
    clusters = {}
    noise_points = []
    
    for i, (building, label) in enumerate(zip(buildings, labels)):
        if label == -1:  # Noise point
            noise_points.append(building)
        else:
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(building)
    
    logger.info(f"Found {len(clusters)} clusters and {len(noise_points)} noise points")
    return clusters, noise_points

def create_buffer_union_geometry(buildings, buffer_radius=0.00015):
    """Create buffer union geometry from building cluster"""
    from shapely.geometry import Point
    from shapely.ops import unary_union
    
    # Create buffered points
    points = [Point(b['longitude'], b['latitude']).buffer(buffer_radius) for b in buildings]
    
    # Create union of all buffered points
    union_geom = unary_union(points)
    
    return union_geom

def create_convex_hull_geometry(buildings):
    """Create convex hull geometry from building cluster"""
    from shapely.geometry import Point, MultiPoint
    
    points = [Point(b['longitude'], b['latitude']) for b in buildings]
    multipoint = MultiPoint(points)
    
    return multipoint.convex_hull

def geometry_to_geojson_feature(geometry, cluster_id, buildings):
    """Convert shapely geometry to GeoJSON feature"""
    from shapely.geometry import mapping
    
    # Calculate cluster statistics
    confidences = [b['confidence'] for b in buildings]
    
    properties = {
        'cluster_id': int(cluster_id),
        'building_count': len(buildings),
        'avg_confidence': np.mean(confidences),
        'min_confidence': np.min(confidences),
        'max_confidence': np.max(confidences),
        'building_ids': [b.get('id', f'building_{i}') for i, b in enumerate(buildings)]
    }
    
    feature = {
        'type': 'Feature',
        'geometry': mapping(geometry),
        'properties': properties
    }
    
    return feature

def merge_geometries(input_file, output_file, config=None):
    """Main geometry merging function"""
    
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    logger.info("Starting geometry merging process")
    logger.info(f"Config: {config}")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Load coordinate data
    buildings = load_coordinate_data(input_file)
    if buildings is None:
        return False
    
    # Filter by confidence
    buildings = filter_buildings_by_confidence(
        buildings, 
        config['confidence_threshold']
    )
    
    if len(buildings) == 0:
        logger.error("No buildings remaining after confidence filtering")
        return False
    
    # Perform spatial clustering
    clusters, noise_points = spatial_clustering(
        buildings,
        config['clustering_distance_degrees'],
        config['min_samples_per_cluster']
    )
    
    # Create geometries for each cluster
    features = []
    
    for cluster_id, cluster_buildings in clusters.items():
        logger.info(f"Processing cluster {cluster_id} with {len(cluster_buildings)} buildings")
        
        if config['geometry_type'] == 'buffer_union':
            geometry = create_buffer_union_geometry(
                cluster_buildings, 
                config['buffer_radius_degrees']
            )
        else:  # convex_hull
            geometry = create_convex_hull_geometry(cluster_buildings)
        
        feature = geometry_to_geojson_feature(geometry, cluster_id, cluster_buildings)
        features.append(feature)
    
    # Add noise points as individual features
    for i, building in enumerate(noise_points):
        from shapely.geometry import Point
        
        point_geom = Point(building['longitude'], building['latitude'])
        if config['geometry_type'] == 'buffer_union':
            geometry = point_geom.buffer(config['buffer_radius_degrees'])
        else:
            geometry = point_geom
        
        feature = geometry_to_geojson_feature(
            geometry, 
            f"noise_{i}", 
            [building]
        )
        features.append(feature)
    
    # Create GeoJSON output
    geojson_output = {
        'type': 'FeatureCollection',
        'features': features,
        'properties': {
            'total_clusters': len(clusters),
            'total_noise_points': len(noise_points),
            'total_buildings_processed': len(buildings),
            'config': config
        }
    }
    
    # Save results
    try:
        with open(output_file, 'w') as f:
            json.dump(geojson_output, f, indent=2)
        
        logger.info(f"✅ Successfully saved merged geometries to {output_file}")
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"GEOMETRY MERGING COMPLETED")
        print(f"{'='*50}")
        print(f"Input buildings: {len(buildings):,}")
        print(f"Clusters created: {len(clusters):,}")
        print(f"Noise points: {len(noise_points):,}")
        print(f"Total features: {len(features):,}")
        print(f"Geometry type: {config['geometry_type']}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*50}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return False

def main():
    """Main execution"""
    
    input_file = "output/central_jakarta_coordinates.json"
    output_file = "output/central_jakarta_merged_geometries.geojson"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return 1
    
    print(f"🔄 Starting geometry merging...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Run geometry merging with default config
    success = merge_geometries(input_file, output_file, DEFAULT_CONFIG)
    
    if success:
        print(f"\n🎉 Geometry merging completed successfully!")
        return 0
    else:
        print(f"\n❌ Geometry merging failed!")
        return 1

if __name__ == "__main__":
    exit(main())
