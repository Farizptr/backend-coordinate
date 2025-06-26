"""Job-related models and enums"""

from pydantic import BaseModel
from typing import Dict, Any, Optional
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobInfo(BaseModel):
    """Job information model"""
    job_id: str
    status: JobStatus
    progress: int = 0  # 0-100
    stage: str = "Initializing"
    buildings_found: int = 0
    start_time: float
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    polygon: Dict[str, Any]
    request_params: Dict[str, Any] 