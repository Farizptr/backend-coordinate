"""Job management endpoints"""

import time
from datetime import datetime
from fastapi import APIRouter, HTTPException

from api.models import JobStatusResponse, JobResultResponse, JobStatus
from api.services import job_manager

# Create router instances
router = APIRouter(prefix="/job", tags=["jobs"])
jobs_list_router = APIRouter(tags=["jobs"])

# Global configuration
MAX_CONCURRENT_JOBS = None

def set_max_concurrent_jobs(max_jobs):
    """Set max concurrent jobs configuration"""
    global MAX_CONCURRENT_JOBS
    MAX_CONCURRENT_JOBS = max_jobs

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get current status and progress of a detection job
    
    Returns real-time progress information including:
    - Current progress percentage (0-100)
    - Processing stage description
    - Buildings found so far
    - Estimated time remaining
    - Error message if failed
    """
    # Get job from storage
    job = job_manager.get_job(job_id)
    
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found. It may have been completed and cleaned up, or the job ID is invalid."
        )
    
    # Calculate estimated time remaining
    estimated_time_remaining = None
    if job.status == JobStatus.PROCESSING and job.progress > 0:
        elapsed_time = time.time() - job.start_time
        if job.progress > 5:  # Only estimate after some progress
            total_estimated_time = (elapsed_time / job.progress) * 100
            remaining_time = total_estimated_time - elapsed_time
            if remaining_time > 0:
                estimated_time_remaining = f"{int(remaining_time)} seconds"
    
    # Return current job status
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        stage=job.stage,
        buildings_found=job.buildings_found,
        estimated_time_remaining=estimated_time_remaining,
        execution_time=job.execution_time,
        error_message=job.error_message
    )

@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    """
    Get final results of a completed detection job
    
    Returns the detected buildings data for completed jobs.
    For jobs that are still processing, failed, or not found, returns appropriate error.
    """
    # Get job from storage
    job = job_manager.get_job(job_id)
    
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found. It may have been completed and cleaned up, or the job ID is invalid."
        )
    
    # Check job status
    if job.status == JobStatus.QUEUED:
        raise HTTPException(
            status_code=202,  # 202 Accepted (still processing)
            detail=f"Job '{job_id}' is still queued for processing. Please wait and try again later."
        )
    
    if job.status == JobStatus.PROCESSING:
        raise HTTPException(
            status_code=202,  # 202 Accepted (still processing)
            detail=f"Job '{job_id}' is still processing ({job.progress}% complete). Please wait and try again later."
        )
    
    if job.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=422,  # 422 Unprocessable Entity
            detail=f"Job '{job_id}' failed during processing: {job.error_message}"
        )
    
    if job.status == JobStatus.CANCELLED:
        raise HTTPException(
            status_code=410,  # 410 Gone
            detail=f"Job '{job_id}' was cancelled before completion."
        )
    
    # Job must be completed - extract result data
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=500,
            detail=f"Job '{job_id}' has unexpected status: {job.status}"
        )
    
    # Get result data from job
    result_data = job.request_params.get('result_data', {})
    buildings_data = result_data.get('buildings', [])
    total_buildings = result_data.get('total_buildings', len(buildings_data))
    
    if not buildings_data:
        # Handle case where no buildings were detected
        buildings_data = []
        total_buildings = 0
    
    return JobResultResponse(
        job_id=job.job_id,
        status=job.status,
        buildings=buildings_data,
        total_buildings=total_buildings,
        execution_time=job.execution_time or 0
     )

@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a queued or processing job
    
    Jobs that are already completed or failed cannot be cancelled.
    """
    # Get job from storage
    job = job_manager.get_job(job_id)
    
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found."
        )
    
    # Check if job can be cancelled
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=409,  # 409 Conflict
            detail=f"Job '{job_id}' cannot be cancelled. Current status: {job.status}"
        )
    
    # Cancel the job using service
    job_manager.cancel_job(job_id)
    
    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job has been cancelled successfully",
        "cancelled_at": datetime.now().isoformat()
    }

# Jobs list endpoint on separate router
@jobs_list_router.get("/jobs")
async def list_all_jobs():
    """
    List all jobs in the system (for debugging and monitoring)
    
    Returns summary of all jobs with their current status
    """
    jobs_summary = job_manager.get_all_jobs()
    
    return {
        "total_jobs": len(jobs_summary),
        "active_jobs": job_manager.get_active_job_count(),
        "max_concurrent": MAX_CONCURRENT_JOBS or 10,
        "jobs": jobs_summary
     } 