#!/usr/bin/env python3
"""
Stitched Map Creator - Generate satellite image stitched map without building detections

Creates a clean satellite image with only the study area polygon outline,
without any building detection results.

Usage:
    python create_stitched_map.py <geojson_path> [options]
    
Example:
    python create_stitched_map.py examples/sample_polygon.geojson --output stitched_area.png --zoom 18
"""

import sys
import argparse
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path as MplPath

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.geojson_utils import load_geojson, extract_polygon
from src.core.tile_utils import get_tiles_for_polygon, get_tile_image, create_stitched_image, get_tile_bounds


def create_stitched_visualization(geojson_path, output_path, zoom=18):
    """
    Create a stitched satellite map with only polygon outline.
    
    Args:
        geojson_path: Path to the GeoJSON file containing the study area
        output_path: Path to save the stitched map image
        zoom: Zoom level for satellite tiles (default: 18)
    """
    print(f"Loading GeoJSON from {geojson_path}...")
    
    # Load and extract polygon
    geojson_data = load_geojson(geojson_path)
    polygon_area = extract_polygon(geojson_data)
    
    print(f"Study area loaded. Bounds: {polygon_area.bounds}")
    
    # Create tiles for the polygon area
    print(f"Generating tiles for zoom level {zoom}...")
    tiles_data = get_tiles_for_polygon(polygon_area, zoom)
    
    print(f"Found {len(tiles_data)} tiles to download")
    
    # Download tile images and create raw tile data structure
    raw_tile_data = []
    for i, tile in enumerate(tiles_data):
        print(f"Processing tile {i+1}/{len(tiles_data)}: {tile.x},{tile.y}")
        
        # Download tile image
        image = get_tile_image(tile)
        
        # Get tile bounds
        bounds = get_tile_bounds(tile)
        
        # Create tile data structure compatible with existing stitching code
        tile_data = {
            'tile_x': tile.x,
            'tile_y': tile.y,
            'zoom': zoom,
            'bounds': bounds,
            'image': image
        }
        raw_tile_data.append(tile_data)
    
    # Create stitched image
    print("Creating stitched image...")
    if not any(d.get('image') for d in raw_tile_data):
        print("Warning: No tile images available. Creating bounds-only visualization.")
        create_bounds_only_visualization(polygon_area, output_path)
        return
    
    try:
        stitched_image, transform_params = create_stitched_image(raw_tile_data)
        
        # Create visualization
        create_final_visualization(
            stitched_image, 
            transform_params, 
            polygon_area, 
            geojson_data, 
            output_path
        )
        
    except Exception as e:
        print(f"Error creating stitched image: {e}")
        print("Falling back to bounds-only visualization.")
        create_bounds_only_visualization(polygon_area, output_path)


def create_polygon_mask(polygon_area, transform_params):
    """
    Create a mask for the polygon area on the stitched image.
    
    Args:
        polygon_area: Shapely polygon in geographic coordinates
        transform_params: Transform parameters from stitched image
        
    Returns:
        Boolean mask array where True = inside polygon, False = outside
    """
    # Get image dimensions from transform params
    width_pixels = transform_params['width_px']
    height_pixels = transform_params['height_px']
    
    print(f"DEBUG: Image dimensions: {width_pixels} x {height_pixels}")
    print(f"DEBUG: Transform bounds: west={transform_params['min_west']}, north={transform_params['max_north']}")
    print(f"DEBUG: Transform size: width_deg={transform_params['width_deg']}, height_deg={transform_params['height_deg']}")
    
    # Create coordinate grids
    x_coords = np.linspace(
        transform_params['min_west'], 
        transform_params['min_west'] + transform_params['width_deg'],
        width_pixels
    )
    # Y coordinates should go from north (top) to south (bottom) for image coordinates
    y_coords = np.linspace(
        transform_params['max_north'],
        transform_params['max_north'] - transform_params['height_deg'],
        height_pixels
    )
    
    print(f"DEBUG: X coords range: {x_coords[0]} to {x_coords[-1]}")
    print(f"DEBUG: Y coords range: {y_coords[0]} to {y_coords[-1]}")
    
    # Check polygon bounds
    polygon_bounds = polygon_area.bounds
    print(f"DEBUG: Polygon bounds: {polygon_bounds}")
    
    # Create meshgrid
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Convert polygon to path
    polygon_coords = list(polygon_area.exterior.coords)
    print(f"DEBUG: First few polygon coords: {polygon_coords[:3]}")
    
    polygon_path = MplPath(polygon_coords)
    
    # Create mask
    points = np.column_stack((X.ravel(), Y.ravel()))
    mask = polygon_path.contains_points(points)
    mask = mask.reshape(height_pixels, width_pixels)
    
    # Debug mask statistics
    mask_count = np.sum(mask)
    total_pixels = mask.size
    print(f"DEBUG: Mask coverage: {mask_count} pixels of {total_pixels} total ({100*mask_count/total_pixels:.1f}%)")
    
    if mask_count > 0:
        mask_indices = np.where(mask)
        min_y, max_y = mask_indices[0].min(), mask_indices[0].max()
        min_x, max_x = mask_indices[1].min(), mask_indices[1].max()
        print(f"DEBUG: Mask pixel bounds: x={min_x}-{max_x}, y={min_y}-{max_y}")
    else:
        print("DEBUG: WARNING - No pixels in mask!")
    
    return mask


def apply_polygon_mask(stitched_image, mask):
    """
    Apply polygon mask to stitched image.
    
    Args:
        stitched_image: PIL Image
        mask: Boolean mask array
        
    Returns:
        Masked image as numpy array with transparent areas outside polygon
    """
    # Convert PIL Image to numpy array
    image_array = np.array(stitched_image)
    
    # Convert to RGBA if RGB
    if image_array.shape[2] == 3:
        rgba_image = np.zeros((*image_array.shape[:2], 4), dtype=image_array.dtype)
        rgba_image[:, :, :3] = image_array
        rgba_image[:, :, 3] = 255  # Full alpha
    else:
        rgba_image = image_array.copy()
    
    # Apply mask - set areas outside polygon to transparent
    rgba_image[~mask, 3] = 0  # Set alpha to 0 for areas outside polygon
    
    return rgba_image


def create_final_visualization(stitched_image, transform_params, polygon_area, geojson_data, output_path):
    """Create the final visualization with stitched image and polygon overlay."""
    
    # Create polygon mask
    print("Creating polygon mask...")
    mask = create_polygon_mask(polygon_area, transform_params)
    
    # Apply mask to stitched image
    print("Applying polygon mask to image...")
    masked_image = apply_polygon_mask(stitched_image, mask)
    
    fig, ax = plt.subplots(1, figsize=(15, 15))
    
    # Display masked stitched image
    ax.imshow(masked_image, extent=[
        transform_params['min_west'], 
        transform_params['min_west'] + transform_params['width_deg'],
        transform_params['max_north'] - transform_params['height_deg'],
        transform_params['max_north']
    ])
    
    # Set limits to polygon bounds for cropping effect
    minx, miny, maxx, maxy = polygon_area.bounds
    padding = 0.0001  # Small padding to ensure polygon is visible
    ax.set_xlim(minx - padding, maxx + padding)
    ax.set_ylim(miny - padding, maxy + padding)
    
    # Plot polygon outline
    plot_polygon_outline(ax, geojson_data, polygon_area)
    
    # Configure plot appearance
    ax.set_title("Cropped Satellite Map (Polygon Area Only)", fontsize=16, color='black', weight='bold')
    ax.set_xlabel("Longitude", fontsize=12, color='black')
    ax.set_ylabel("Latitude", fontsize=12, color='black')
    
    # Style the plot
    ax.tick_params(axis='both', which='major', labelsize=10, colors='black')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='red', lw=3, label='Study Area Boundary')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize='small')
    
    plt.tight_layout(pad=1.5)
    
    # Save the plot
    plt.savefig(output_path, bbox_inches='tight', dpi=300, facecolor='white')
    print(f"Cropped stitched map saved to {output_path}")
    plt.close()


def create_bounds_only_visualization(polygon_area, output_path):
    """Create a simple visualization with just polygon bounds when no tiles are available."""
    
    fig, ax = plt.subplots(1, figsize=(15, 15))
    
    # Set bounds
    minx, miny, maxx, maxy = polygon_area.bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    
    # Plot polygon outline
    x_coords, y_coords = polygon_area.exterior.xy
    ax.plot(x_coords, y_coords, color='red', linewidth=3, alpha=0.8, label='Study Area')
    
    # Configure plot
    ax.set_title("Study Area (No Satellite Data)", fontsize=16)
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Bounds-only map saved to {output_path}")
    plt.close()


def plot_polygon_outline(ax, geojson_data, polygon_area):
    """Plot the polygon outline on the map."""
    
    if geojson_data['type'] == 'FeatureCollection':
        for i, feature in enumerate(geojson_data['features']):
            from shapely.geometry import shape
            geom = shape(feature['geometry'])
            if geom.geom_type in ['Polygon', 'MultiPolygon']:
                plot_single_polygon(ax, geom, 'red')
    else:  # Single Polygon
        x_coords, y_coords = polygon_area.exterior.xy
        ax.plot(x_coords, y_coords, color='red', linewidth=3, alpha=0.8)


def plot_single_polygon(ax, geom, color):
    """Plot a single polygon geometry."""
    if geom.geom_type == 'Polygon':
        x_coords, y_coords = geom.exterior.xy
        ax.plot(x_coords, y_coords, color=color, linewidth=3, alpha=0.8)
    elif geom.geom_type == 'MultiPolygon':
        for poly_part in geom.geoms:
            x_coords, y_coords = poly_part.exterior.xy
            ax.plot(x_coords, y_coords, color=color, linewidth=3, alpha=0.8)


def main():
    """Main entry point for stitched map creation."""
    parser = argparse.ArgumentParser(
        description="Create stitched satellite map without building detections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_stitched_map.py examples/sample_polygon.geojson
  python create_stitched_map.py examples/sample_polygon.geojson --output maps/area.png --zoom 18
        """
    )
    
    # Required arguments
    parser.add_argument(
        "geojson_path",
        help="Path to GeoJSON file containing study area polygon"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output", "-o",
        default="stitched_map.png",
        help="Output path for the stitched map image (default: stitched_map.png)"
    )
    
    parser.add_argument(
        "--zoom", "-z",
        type=int,
        default=18,
        help="Zoom level for satellite tiles (default: 18)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.geojson_path):
        print(f"Error: GeoJSON file '{args.geojson_path}' not found.")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Configuration summary
    print("\n" + "="*60)
    print("STITCHED MAP CREATION")
    print("="*60)
    print(f"Input GeoJSON: {args.geojson_path}")
    print(f"Output image: {args.output}")
    print(f"Zoom level: {args.zoom}")
    print("="*60 + "\n")
    
    try:
        create_stitched_visualization(args.geojson_path, args.output, args.zoom)
        
        print("\n" + "="*60)
        print("STITCHED MAP CREATION COMPLETED")
        print("="*60)
        print(f"Map saved to: {args.output}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during map creation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
