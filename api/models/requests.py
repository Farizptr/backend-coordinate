"""Request models for API endpoints"""

from pydantic import BaseModel, validator
from typing import Dict, Any, Optional


def validate_job_id_format(job_id: str) -> bool:
    """
    Validate job ID format
    
    Rules:
    - 3-50 characters long
    - Alphanumeric, hyphens, underscores only
    - Must start with letter or number
    - Cannot end with hyphen or underscore
    """
    if not job_id or len(job_id) < 3 or len(job_id) > 50:
        return False
    
    # Check start and end characters
    if not (job_id[0].isalnum() and job_id[-1].isalnum()):
        return False
    
    # Check all characters are allowed (alphanumeric, hyphen, underscore)
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed_chars for c in job_id):
        return False
    
    return True


class PolygonRequest(BaseModel):
    """Request model for polygon detection"""
    job_id: Optional[str] = None  # Optional custom job ID
    polygon: Dict[str, Any]  # GeoJSON polygon
    zoom: Optional[int] = 18
    confidence: Optional[float] = 0.25
    batch_size: Optional[int] = 5
    enable_merging: Optional[bool] = True
    merge_iou_threshold: Optional[float] = 0.1
    merge_touch_enabled: Optional[bool] = True
    merge_min_edge_distance_deg: Optional[float] = 0.00001

    @validator('job_id')
    def validate_job_id_if_provided(cls, v):
        """Validate job_id format if provided (uniqueness checked later)"""
        if v is not None and not validate_job_id_format(v):
            raise ValueError("job_id must be 3-50 characters, alphanumeric with hyphens/underscores, cannot start/end with special characters")
        return v 