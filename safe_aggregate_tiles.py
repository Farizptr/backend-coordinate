#!/usr/bin/env python3
"""
Safe Tiles Aggregation Script
=============================

Safely aggregate tile results to avoid segmentation faults.
Includes memory management and error handling.
"""

import json
import glob
import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_load_tile(tile_file):
    """Safely load a tile file with error handling"""
    try:
        with open(tile_file, 'r') as f:
            data = json.load(f)
        
        # Handle different formats
        if isinstance(data, list):
            # Simple format - skip for now
            return None
        elif isinstance(data, dict):
            # Standard format
            return data
        else:
            logger.warning(f"Unknown format in {tile_file}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading {tile_file}: {e}")
        return None

def aggregate_tiles_safe(tiles_dir, output_file, area_name="Central Jakarta"):
    """Safely aggregate tiles with memory management"""
    
    # Find all tile files (not simple format)
    tile_pattern = os.path.join(tiles_dir, "tile_*.json")
    tile_files = [f for f in glob.glob(tile_pattern) if not f.endswith('_simple.json')]
    
    logger.info(f"Found {len(tile_files)} tile files to process")
    
    all_detections = []
    total_tiles = 0
    processed_tiles = 0
    
    # Process tiles in batches to manage memory
    batch_size = 100
    
    for i in range(0, len(tile_files), batch_size):
        batch_files = tile_files[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch_files)} files)")
        
        batch_detections = []
        
        for tile_file in batch_files:
            tile_data = safe_load_tile(tile_file)
            
            if tile_data is None:
                continue
                
            total_tiles += 1
            
            # Extract detections from tile
            if 'boxes' in tile_data and 'confidences' in tile_data:
                boxes = tile_data.get('boxes', [])
                confidences = tile_data.get('confidences', [])
                bounds = tile_data.get('bounds', [])
                
                if len(boxes) > 0:
                    processed_tiles += 1
                    
                    # Add detections with tile info
                    for j, (box, conf) in enumerate(zip(boxes, confidences)):
                        detection = {
                            'tile': tile_data.get('tile', ''),
                            'detection_id': j,
                            'box': box,
                            'confidence': conf,
                            'bounds': bounds
                        }
                        batch_detections.append(detection)
        
        # Add batch to main collection
        all_detections.extend(batch_detections)
        logger.info(f"Batch processed: {len(batch_detections)} detections found")
        
        # Memory cleanup
        del batch_detections
    
    # Create summary
    summary = {
        'area_name': area_name,
        'total_tiles_processed': total_tiles,
        'tiles_with_detections': processed_tiles,
        'total_detections': len(all_detections),
        'detections': all_detections
    }
    
    # Save results
    logger.info(f"Saving {len(all_detections)} detections to {output_file}")
    
    try:
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"✅ Successfully saved results to {output_file}")
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"AGGREGATION COMPLETED")
        print(f"{'='*50}")
        print(f"Area: {area_name}")
        print(f"Total tiles processed: {total_tiles:,}")
        print(f"Tiles with detections: {processed_tiles:,}")
        print(f"Total detections found: {len(all_detections):,}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*50}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return False

def main():
    """Main execution"""
    
    tiles_dir = "output/tiles"
    output_file = "output/central_jakarta_aggregated.json"
    
    if not os.path.exists(tiles_dir):
        print(f"❌ Tiles directory not found: {tiles_dir}")
        return 1
    
    print(f"🔄 Starting safe tiles aggregation...")
    print(f"Input: {tiles_dir}")
    print(f"Output: {output_file}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Run aggregation
    success = aggregate_tiles_safe(tiles_dir, output_file, "Central Jakarta")
    
    if success:
        print(f"\n🎉 Aggregation completed successfully!")
        return 0
    else:
        print(f"\n❌ Aggregation failed!")
        return 1

if __name__ == "__main__":
    exit(main())
