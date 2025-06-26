#!/usr/bin/env python3
"""
Building Detector - Main Entry Point

A tool for detecting buildings in satellite/aerial imagery using YOLOv8.

Usage:
    python main.py <geojson_path> [options]
    
Example:
    python main.py examples/sample_polygon.geojson --output output/ --zoom 18
"""

import sys
import argparse
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.detection import load_model
from src.core.polygon_detection import detect_buildings_in_polygon
from src.utils.geojson_utils import create_example_geojson


def main():
    """Main entry point for building detection."""
    parser = argparse.ArgumentParser(
        description="Detect buildings in satellite imagery using YOLOv8",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py examples/sample_polygon.geojson
  python main.py examples/sample_polygon.geojson --output results/ --zoom 18 --conf 0.3
  python main.py examples/sample_polygon.geojson --no-merge --batch-size 10
        """
    )
    
    # Required arguments
    parser.add_argument(
        "geojson_path",
        nargs="?",
        help="Path to GeoJSON file containing polygon area (optional - will create example if not provided)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--model", "-m",
        default="best.pt",
        help="Path to YOLOv8 model file (default: best.pt)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Output directory for results (default: output)"
    )
    
    parser.add_argument(
        "--zoom", "-z",
        type=int,
        default=18,
        help="Zoom level for satellite tiles (default: 18)"
    )
    
    parser.add_argument(
        "--conf", "-c",
        type=float,
        default=0.25,
        help="Confidence threshold for detections (default: 0.25)"
    )
    
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=5,
        help="Number of tiles to process in each batch (default: 5)"
    )
    
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Disable merging of overlapping detections"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Disable resuming from saved tile results (start fresh)"
    )
    
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.1,
        help="IoU threshold for merging detections (default: 0.1)"
    )
    
    args = parser.parse_args()
    
    # Handle GeoJSON path
    if not args.geojson_path:
        print("No GeoJSON file provided, creating example...")
        args.geojson_path = create_example_geojson("examples/generated_example.geojson")
        print(f"Created example GeoJSON: {args.geojson_path}")
    
    # Validate inputs
    if not os.path.exists(args.geojson_path):
        print(f"Error: GeoJSON file '{args.geojson_path}' not found.")
        sys.exit(1)
    
    if not os.path.exists(args.model):
        print(f"Error: Model file '{args.model}' not found.")
        print("Please ensure the YOLOv8 model file is available.")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load model
    print(f"Loading YOLOv8 model from {args.model}...")
    try:
        model = load_model(args.model)
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
    
    # Configuration summary
    print("\n" + "="*60)
    print("BUILDING DETECTION CONFIGURATION")
    print("="*60)
    print(f"Input GeoJSON: {args.geojson_path}")
    print(f"Model: {args.model}")
    print(f"Output directory: {args.output}")
    print(f"Zoom level: {args.zoom}")
    print(f"Confidence threshold: {args.conf}")
    print(f"Batch size: {args.batch_size}")
    print(f"Merging enabled: {not args.no_merge}")
    if not args.no_merge:
        print(f"IoU threshold: {args.iou_threshold}")
    print(f"Resume from saved: {not args.no_resume}")
    print("="*60 + "\n")
    
    # Run detection
    try:
        results = detect_buildings_in_polygon(
            model=model,
            geojson_path=args.geojson_path,
            output_dir=args.output,
            zoom=args.zoom,
            conf=args.conf,
            batch_size=args.batch_size,
            enable_merging=not args.no_merge,
            merge_iou_threshold=args.iou_threshold,
            merge_touch_enabled=True,
            merge_min_edge_distance_deg=0.000001,
            resume_from_saved=not args.no_resume
        )
        
        # Success summary
        print("\n" + "="*60)
        print("DETECTION COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Total buildings detected: {results['total_buildings']}")
        print(f"Total tiles processed: {results['total_tiles']}")
        print(f"Execution time: {results['execution_time']:.2f} seconds")
        print(f"Results saved to: {args.output}/")
        print("="*60)
        
        # Output file summary
        print("\nOutput files:")
        output_files = [
            "detection_results.json",
            "buildings.json", 
            "buildings_simple.json",
            "polygon_visualization.png"
        ]
        
        for filename in output_files:
            filepath = os.path.join(args.output, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  ✓ {filename} ({size:,} bytes)")
            else:
                print(f"  ✗ {filename} (not found)")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during detection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 