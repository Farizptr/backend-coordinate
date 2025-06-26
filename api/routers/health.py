"""Health check and system info endpoints"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from api.models import HealthResponse
from api.services import job_manager

# Create router instance
router = APIRouter(tags=["health"])

# Global instances (will be set by main app)
model = None
max_concurrent_jobs = 10  # Default value

def set_model(model_instance):
    """Set the model instance for this router"""
    global model
    model = model_instance

def set_max_concurrent_jobs(max_jobs):
    """Set the max concurrent jobs for this router"""
    global max_concurrent_jobs
    max_concurrent_jobs = max_jobs

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        timestamp=datetime.now().isoformat()
    )

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Building Detection API",
        "version": "2.0.0",  # Updated version for async support
        "description": "Asynchronous building detection using YOLOv8",
        "endpoints": {
            "health": "/health",
            "detect_sync": "/detect/sync",  # Fixed path
            "detect_async": "/detect/async",  # New asynchronous endpoint
            "job_status": "/job/{job_id}",  # Fixed path
            "job_result": "/job/{job_id}/result",  # Get final results
            "jobs_list": "/jobs",  # List all jobs
            "docs": "/docs"
        },
        "concurrent_jobs": {
            "max_allowed": max_concurrent_jobs,
            "currently_active": job_manager.get_active_job_count()
        }
    }

@router.get("/model/info")
async def model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_loaded": True,
        "model_type": "YOLOv8", 
        "model_file": "best.pt"
    } 