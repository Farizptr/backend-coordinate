"""Models package - contains all Pydantic models for the API"""

from .job import JobStatus, JobInfo
from .requests import PolygonRequest, validate_job_id_format
from .responses import (
    DetectionResponse,
    HealthResponse,
    JobSubmissionResponse,
    JobStatusResponse,
    JobResultResponse
)

__all__ = [
    # Job models
    "JobStatus",
    "JobInfo",
    
    # Request models
    "PolygonRequest",
    "validate_job_id_format",
    
    # Response models
    "DetectionResponse",
    "HealthResponse", 
    "JobSubmissionResponse",
    "JobStatusResponse",
    "JobResultResponse"
]
