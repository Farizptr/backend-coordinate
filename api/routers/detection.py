"""Detection endpoints for building detection"""

import os
import json
import uuid
import tempfile
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from concurrent.futures import ThreadPoolExecutor

from api.models import PolygonRequest, DetectionResponse, JobSubmissionResponse
from api.services import job_manager, validation_service, detection_service
from src.core.polygon_detection import detect_buildings_in_polygon
from src.utils.geojson_utils import load_geojson

# Create router instance
router = APIRouter(tags=["detection"])

# Global instances (will be set by main app)
model = None
executor = None
MAX_CONCURRENT_JOBS = None

def set_dependencies(model_instance, executor_instance, max_concurrent_jobs):
    """Set dependencies for this router"""
    global model, executor, MAX_CONCURRENT_JOBS
    model = model_instance
    executor = executor_instance
    MAX_CONCURRENT_JOBS = max_concurrent_jobs

@router.post("/detect/sync", response_model=DetectionResponse)
async def detect_buildings_sync(
    request: PolygonRequest, 
    background_tasks: BackgroundTasks
):
    """
    Main endpoint for building detection
    
    Accepts a GeoJSON polygon and returns detected buildings
    """
    if model is None:
        raise HTTPException(
            status_code=503, 
            detail="Model not loaded. Please check server configuration."
        )
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    temp_dir = None
    
    try:
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp(prefix=f"detection_{session_id}_")
        
        # Create temporary GeoJSON file
        geojson_path = os.path.join(temp_dir, "input_polygon.geojson")
        with open(geojson_path, 'w') as f:
            json.dump(request.polygon, f, indent=2)
        
        # Validate GeoJSON
        try:
            test_load = load_geojson(geojson_path)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid GeoJSON format: {str(e)}"
            )
        
        # Output directory for results
        output_dir = os.path.join(temp_dir, "results")
        
        # Run building detection
        detection_result = detect_buildings_in_polygon(
            model=model,
            geojson_path=geojson_path,
            output_dir=output_dir,
            zoom=request.zoom,
            conf=request.confidence,
            batch_size=request.batch_size,
            enable_merging=request.enable_merging,
            merge_iou_threshold=request.merge_iou_threshold,
            merge_touch_enabled=request.merge_touch_enabled,
            merge_min_edge_distance_deg=request.merge_min_edge_distance_deg,
            resume_from_saved=False  # Don't use resume for API calls
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
        
        # Schedule cleanup in background
        background_tasks.add_task(detection_service.cleanup_temp_files, temp_dir)
        
        return DetectionResponse(
            success=True,
            message="Building detection completed successfully",
            data=None,  # Remove complex detection data
            buildings=buildings_data,  # Only simple format: id, longitude, latitude
            total_buildings=len(buildings_data),  # Count from actual buildings_data
            execution_time=detection_result.get('execution_time', 0)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        if temp_dir:
            background_tasks.add_task(detection_service.cleanup_temp_files, temp_dir)
        raise
        
    except Exception as e:
        # Clean up on error
        if temp_dir:
            background_tasks.add_task(detection_service.cleanup_temp_files, temp_dir)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during detection: {str(e)}"
        )

@router.post("/detect/async", response_model=JobSubmissionResponse)
async def submit_detection_job(request: PolygonRequest):
    """
    Submit building detection job for asynchronous processing
    
    Supports custom job IDs or auto-generation:
    - Custom job_id: 3-50 characters, alphanumeric with hyphens/underscores
    - Auto job_id: Leave job_id empty for UUID auto-generation
    
    Returns job_id immediately without waiting for processing to complete.
    Use /job/{job_id}/status to track progress and /job/{job_id}/result to get results.
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please check server configuration."
        )
    
    # Check if we're at max capacity
    active_count = job_manager.get_active_job_count()
    if active_count >= MAX_CONCURRENT_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Server at capacity. Maximum {MAX_CONCURRENT_JOBS} concurrent jobs allowed. Currently processing: {active_count}"
        )
    
    # Validate and get job ID (custom or auto-generated)
    job_id = validation_service.validate_and_get_job_id(request.job_id)
    
    # Prepare request parameters
    request_params = {
        "zoom": request.zoom,
        "confidence": request.confidence,
        "batch_size": request.batch_size,
        "enable_merging": request.enable_merging,
        "merge_iou_threshold": request.merge_iou_threshold,
        "merge_touch_enabled": request.merge_touch_enabled,
        "merge_min_edge_distance_deg": request.merge_min_edge_distance_deg
    }
    
    try:
        # Validate GeoJSON polygon before creating job
        temp_geojson_path = tempfile.mktemp(suffix='.geojson')
        with open(temp_geojson_path, 'w') as f:
            json.dump(request.polygon, f, indent=2)
        
        # Test load to validate format
        test_load = load_geojson(temp_geojson_path)
        os.unlink(temp_geojson_path)  # Clean up temp file
        
    except Exception as e:
        if os.path.exists(temp_geojson_path):
            os.unlink(temp_geojson_path)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GeoJSON format: {str(e)}"
        )
    
    # Create job in system
    job = job_manager.create_job(job_id, request.polygon, request_params)
    
    # Submit to background processing
    submit_job_to_background_processing(job_id)
    
    # Return immediately with job info
    return JobSubmissionResponse(
        job_id=job_id,
        status=job.status,
        message="Detection job submitted successfully. Use /job/{job_id}/status to track progress.",
        submitted_at=datetime.now().isoformat()
    )

def submit_job_to_background_processing(job_id: str):
    """
    Submit job to background processing queue
    """
    print(f"🔄 Submitting job {job_id} to background processing queue")
    
    # Submit real processing to thread pool
    future = executor.submit(detection_service.process_detection_job, job_id, model)
    
    # Store future reference in job for potential cancellation
    job = job_manager.get_job(job_id)
    if job:
        job.request_params['_future'] = future 