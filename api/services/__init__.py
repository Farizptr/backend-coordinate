"""Services package for business logic"""

from .job_manager import JobManager, job_manager
from .validation import ValidationService, validation_service
from .detection import DetectionService, detection_service

__all__ = [
    'JobManager', 'job_manager',
    'ValidationService', 'validation_service', 
    'DetectionService', 'detection_service'
]
