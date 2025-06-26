"""Validation service for job IDs and other validation logic"""

import uuid
from typing import Optional
from fastapi import HTTPException
from ..config import get_settings
from .job_manager import job_manager


class ValidationService:
    """Service for validation logic"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def validate_job_id_format(self, job_id: str) -> bool:
        """
        Validate job ID format using configurable rules
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not job_id:
            return False
        
        if len(job_id) < self.settings.job_id_min_length:
            return False
        
        if len(job_id) > self.settings.job_id_max_length:
            return False
        
        # Check first and last characters
        if not (job_id[0].isalnum() and job_id[-1].isalnum()):
            return False
        
        # Check all characters
        for char in job_id:
            if not (char.isalnum() or char in ['-', '_']):
                return False
        
        return True
    
    def validate_and_get_job_id(self, requested_job_id: Optional[str]) -> str:
        """
        Validate custom job ID or generate auto job ID
        
        Returns:
            str: Valid job ID (custom or auto-generated)
            
        Raises:
            HTTPException: If custom job_id is invalid or already exists
        """
        if requested_job_id is None:
            # Auto-generate UUID if no custom job_id provided
            return str(uuid.uuid4())
        
        # Validate custom job_id format
        if not self.validate_job_id_format(requested_job_id):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job_id format. Must be {self.settings.job_id_min_length}-{self.settings.job_id_max_length} characters, alphanumeric with hyphens/underscores, cannot start/end with special characters. Got: '{requested_job_id}'"
            )
        
        # Check if job_id is already in use
        if not job_manager.is_job_id_available(requested_job_id):
            raise HTTPException(
                status_code=409,
                detail=f"Job ID '{requested_job_id}' already exists. Please choose a different job_id or omit it for auto-generation."
            )
        
        return requested_job_id
    
    @staticmethod
    def validate_job_exists(job_id: str):
        """
        Validate that a job exists
        
        Raises:
            HTTPException: If job doesn't exist
        """
        job = job_manager.get_job(job_id)
        if job is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job '{job_id}' not found. It may have been completed and cleaned up, or the job ID is invalid."
            )
        return job


# Global validation service instance
validation_service = ValidationService() 