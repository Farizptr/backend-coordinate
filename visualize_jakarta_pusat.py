#!/usr/bin/env python3
"""
Jakarta Pusat Buildings Visualization
====================================

This script creates a simple web map visualization showing building coordinates
from Jakarta Pusat dataset as red markers on an interactive map.

Features:
- Data sampling for optimal performance
- Red markers for each building location
- Interactive Folium map
- Clean HTML output

Author: Building Detection System
Created: August 2025
"""

import json
import folium
import os
from typing import List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JakartaPusatVisualizer:
    """Visualizer for Jakarta Pusat building coordinates"""
    
    def __init__(self, data_file: str, output_dir: str = "output"):
        """
        Initialize visualizer
        
        Args:
            data_file: Path to Jakarta Pusat JSON data file
            output_dir: Directory to save output files
        """
        self.data_file = data_file
        self.output_dir = output_dir
        self.data = []
        
        # Jakarta Pusat center coordinates (approximate)
        self.center_lat = -6.1754
        self.center_lon = 106.8272
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def load_data(self, sample_rate: int = 1) -> List[Dict]:
        """
        Load all JSON data points without sampling
        
        Args:
            sample_rate: Not used, kept for compatibility (default: 1 for all points)
            
        Returns:
            List of all coordinate data
        """
        try:
            logger.info(f"Loading data from {self.data_file}")
            
            with open(self.data_file, 'r', encoding='utf-8') as file:
                raw_data = json.load(file)
            
            # Use all data points
            all_data = raw_data
            
            logger.info(f"Loaded {len(raw_data):,} total records")
            logger.info(f"Using all {len(all_data):,} records (no sampling)")
            
            self.data = all_data
            return all_data
            
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def create_map(self) -> folium.Map:
        """
        Create Folium map centered on Jakarta Pusat
        
        Returns:
            Configured Folium map object
        """
        logger.info("Creating base map")
        
        # Create map with optimal settings for Jakarta Pusat
        m = folium.Map(
            location=[self.center_lat, self.center_lon],
            zoom_start=12,
            tiles='OpenStreetMap',
            control_scale=True,
            prefer_canvas=True  # Better performance for many markers
        )
        
        # Add map title
        title_html = '''
        <h3 align="center" style="font-size:16px; margin-top:0;">
        <b>Jakarta Pusat - Building Locations</b>
        </h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        return m
    
    def add_markers(self, map_obj: folium.Map) -> folium.Map:
        """
        Add red markers for each building location
        
        Args:
            map_obj: Folium map object
            
        Returns:
            Map with added markers
        """
        logger.info(f"Adding {len(self.data):,} red markers to map")
        
        # Add markers efficiently
        for i, building in enumerate(self.data):
            try:
                lat = float(building['latitude'])
                lon = float(building['longitude'])
                building_id = building.get('id', f'building_{i}')
                
                # Add simple red marker
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=3,
                    popup=f"Building ID: {building_id}",
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.7,
                    weight=1
                ).add_to(map_obj)
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid coordinate at index {i}: {e}")
                continue
        
        logger.info("Successfully added all markers")
        return map_obj
    
    def save_map(self, map_obj: folium.Map, filename: str = "jakarta_pusat_buildings.html") -> str:
        """
        Save map to HTML file
        
        Args:
            map_obj: Folium map object
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            map_obj.save(output_path)
            logger.info(f"Map saved successfully to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving map: {e}")
            raise
    
    def create_visualization(self, sample_rate: int = 1, filename: str = "jakarta_pusat_buildings.html") -> str:
        """
        Complete workflow to create building visualization with all data points
        
        Args:
            sample_rate: Not used, kept for compatibility
            filename: Output HTML filename
            
        Returns:
            Path to generated HTML file
        """
        logger.info("Starting Jakarta Pusat buildings visualization with ALL data points")
        
        # Load all data
        self.load_data(sample_rate=sample_rate)
        
        # Create base map
        map_obj = self.create_map()
        
        # Add building markers
        map_obj = self.add_markers(map_obj)
        
        # Save map
        output_path = self.save_map(map_obj, filename)
        
        logger.info("Visualization completed successfully!")
        logger.info(f"Open {output_path} in your web browser to view the map")
        
        return output_path

def main():
    """Main execution function"""
    # Configuration
    data_file = "results/jakarta-pusat.json"
    output_dir = "output"
    sample_rate = 1  # Use all data points (no sampling)
    
    try:
        # Create visualizer
        visualizer = JakartaPusatVisualizer(data_file, output_dir)
        
        # Generate visualization with all data points
        output_path = visualizer.create_visualization(
            sample_rate=sample_rate,
            filename="jakarta_pusat_buildings_all.html"
        )
        
        print(f"\n🎉 Success! Map created at: {output_path}")
        print(f"📊 Showing ALL {len(visualizer.data):,} building locations as red markers")
        print(f"🌐 Open the file in your web browser to explore the map")
        print(f"⚠️  Note: This may take time to load due to large number of markers")
        
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
