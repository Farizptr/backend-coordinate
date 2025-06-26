"""Detection service for building detection processing"""

import os
import json
import tempfile
import shutil
from typing import Dict, Any, Optional
from .job_manager import job_manager
from src.utils.geojson_utils import load_geojson


class DetectionService:
    """Service for detection processing logic"""
    
    @staticmethod
    def process_detection_job(job_id: str, model):
        """
        Real building detection processing using YOLOv8
        """
        job = job_manager.get_job(job_id)
        if not job:
            print(f"❌ Job {job_id} not found for processing")
            return
        
        temp_dir = None
        try:
            # Update status to processing
            job_manager.update_job_progress(job_id, 5, "Initializing detection process", 0)
            
            # Create temporary directory for this job
            temp_dir = tempfile.mkdtemp(prefix=f"async_detection_{job_id}_")
            
            # Create temporary GeoJSON file
            geojson_path = os.path.join(temp_dir, "input_polygon.geojson")
            with open(geojson_path, 'w') as f:
                json.dump(job.polygon, f, indent=2)
            
            job_manager.update_job_progress(job_id, 10, "Created temporary files", 0)
            
            # Validate GeoJSON
            try:
                test_load = load_geojson(geojson_path)
            except Exception as e:
                job_manager.fail_job(job_id, f"Invalid GeoJSON format: {str(e)}")
                return
            
            job_manager.update_job_progress(job_id, 15, "Validated input polygon", 0)
            
            # Output directory for results
            output_dir = os.path.join(temp_dir, "results")
            
            job_manager.update_job_progress(job_id, 20, "Preparing for tile processing", 0)
            
            # Extract parameters from job
            params = job.request_params
            
            # Run building detection with progress tracking
            detection_result = DetectionService.detect_buildings_with_progress(
                model=model,
                geojson_path=geojson_path,
                output_dir=output_dir,
                zoom=params.get('zoom', 18),
                conf=params.get('confidence', 0.25),
                batch_size=params.get('batch_size', 5),
                enable_merging=params.get('enable_merging', True),
                merge_iou_threshold=params.get('merge_iou_threshold', 0.1),
                merge_touch_enabled=params.get('merge_touch_enabled', True),
                merge_min_edge_distance_deg=params.get('merge_min_edge_distance_deg', 0.00001),
                resume_from_saved=False,  # Don't use resume for async jobs
                job_id=job_id  # Pass job_id for progress tracking
            )
            
            # Read buildings_simple.json if it exists
            buildings_simple_path = os.path.join(output_dir, "buildings_simple.json")
            buildings_data = []
            
            if os.path.exists(buildings_simple_path):
                with open(buildings_simple_path, 'r') as f:
                    buildings_simple = json.load(f)
                    # Handle both list format and dict format
                    if isinstance(buildings_simple, list):
                        buildings_data = buildings_simple
                    elif isinstance(buildings_simple, dict):
                        buildings_data = buildings_simple.get('buildings', [])
                    else:
                        buildings_data = []
            
            job_manager.update_job_progress(job_id, 95, "Finalizing results", len(buildings_data))
            
            # Complete job with results
            result_data = {
                'buildings': buildings_data,
                'total_buildings': len(buildings_data),
                'execution_time': detection_result.get('execution_time', 0),
                'detection_summary': {
                    'total_tiles': detection_result.get('total_tiles', 0),
                    'zoom': params.get('zoom', 18),
                    'confidence_threshold': params.get('confidence', 0.25),
                    'merging_enabled': params.get('enable_merging', True)
                }
            }
            
            job_manager.complete_job(job_id, result_data)
            
            print(f"✅ Job {job_id} completed successfully with {len(buildings_data)} buildings")
            
        except Exception as e:
            job_manager.fail_job(job_id, f"Detection processing failed: {str(e)}")
            print(f"❌ Job {job_id} failed: {str(e)}")
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print(f"🗑️ Cleaned up temp directory for job {job_id}")
                except Exception as cleanup_error:
                    print(f"⚠️ Warning: Failed to cleanup temp directory for job {job_id}: {cleanup_error}")
    
    @staticmethod
    def detect_buildings_with_progress(model, geojson_path, output_dir, zoom=18, conf=0.25, batch_size=5,
                                      enable_merging=True, merge_iou_threshold=0.1, merge_touch_enabled=True, 
                                      merge_min_edge_distance_deg=0.00001, resume_from_saved=False, job_id=None):
        """
        Wrapper around detect_buildings_in_polygon that provides progress tracking for async jobs
        """
        if job_id:
            job_manager.update_job_progress(job_id, 25, "Loading tiles and preparing detection", 0)
        
        # Import the detection function here to avoid circular imports
        from src.core.polygon_detection import (
            _initialize_detection_session, _load_and_prepare_data, _handle_resume_logic,
            _execute_tile_processing, _process_merging_phase, _process_no_merging_phase,
            _create_results_payload, _generate_visualization, _save_output_files, _finalize_session
        )
        
        try:
            # Initialize session
            start_time = _initialize_detection_session(output_dir)
            
            # Load and prepare data
            tiles = _load_and_prepare_data(geojson_path, zoom)
            
            if job_id:
                job_manager.update_job_progress(job_id, 30, f"Found {len(tiles)} tiles to process", 0)
            
            # Handle resume logic
            all_detections_raw_per_tile, tiles_to_process = _handle_resume_logic(resume_from_saved, output_dir, tiles)
            
            if job_id:
                job_manager.update_job_progress(job_id, 35, f"Processing {len(tiles_to_process)} tiles", 0)
            
            # Execute tile processing with progress tracking
            all_detections_raw_per_tile = _execute_tile_processing(
                tiles_to_process, batch_size, model, conf, output_dir, all_detections_raw_per_tile
            )
            
            if job_id:
                # Update progress during tile processing
                processed_tiles = len(all_detections_raw_per_tile)
                total_tiles = len(tiles_to_process) + len(all_detections_raw_per_tile)
                progress = 35 + int(40 * processed_tiles / max(total_tiles, 1))  # Progress from 35% to 75%
                job_manager.update_job_progress(job_id, min(progress, 75), f"Processed {processed_tiles} tiles", 0)
            
            if job_id:
                # Count total buildings found so far
                total_buildings_so_far = sum(len(tile_data.get('boxes', [])) for tile_data in all_detections_raw_per_tile)
                job_manager.update_job_progress(job_id, 80, "Processing and merging detections", total_buildings_so_far)
            
            # Process results based on merging setting
            if enable_merging:
                final_detections_for_json, final_merged_shapely_objects, total_buildings_final = _process_merging_phase(
                    all_detections_raw_per_tile, merge_iou_threshold, merge_touch_enabled, merge_min_edge_distance_deg)
            else:
                final_detections_for_json, final_merged_shapely_objects, total_buildings_final = _process_no_merging_phase(
                    all_detections_raw_per_tile)
            
            if job_id:
                job_manager.update_job_progress(job_id, 85, "Creating final results", total_buildings_final)
            
            # Create results payload
            json_results_payload = _create_results_payload(
                total_buildings_final, tiles, zoom, conf, enable_merging, 
                merge_iou_threshold, merge_touch_enabled, merge_min_edge_distance_deg, 
                final_detections_for_json, start_time)
            
            if job_id:
                job_manager.update_job_progress(job_id, 90, "Skipping visualization for background job", total_buildings_final)
            
            # Skip visualization for background jobs to avoid GUI thread issues
            if not job_id:
                # Generate visualization only for sync processing
                _generate_visualization(geojson_path, output_dir, total_buildings_final, tiles, zoom, conf, final_merged_shapely_objects, all_detections_raw_per_tile)
            
            # Save output files
            results_path = _save_output_files(output_dir, json_results_payload, geojson_path)
            
            # Finalize session
            _finalize_session(output_dir, results_path, total_buildings_final, json_results_payload['execution_time'])
            
            return json_results_payload
            
        except Exception as e:
            if job_id:
                job_manager.fail_job(job_id, f"Detection processing failed: {str(e)}")
            raise
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str):
        """Clean up temporary files and directory"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")


# Global detection service instance
detection_service = DetectionService() 