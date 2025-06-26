"""Response models for API endpoints"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from .job import JobStatus


class DetectionResponse(BaseModel):
    """Response model for synchronous detection"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    buildings: Optional[List[Dict[str, Any]]] = None
    total_buildings: Optional[int] = None
    execution_time: Optional[float] = None


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    model_loaded: bool
    timestamp: str


class JobSubmissionResponse(BaseModel):
    """Response when submitting a new job"""
    job_id: str
    status: JobStatus
    message: str
    submitted_at: str


class JobStatusResponse(BaseModel):
    """Response for job status checks"""
    job_id: str
    status: JobStatus
    progress: int
    stage: str
    buildings_found: int
    estimated_time_remaining: Optional[str] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None


class JobResultResponse(BaseModel):
    """Response for completed job results"""
    job_id: str
    status: JobStatus
    buildings: List[Dict[str, Any]]
    total_buildings: int
    execution_time: float 