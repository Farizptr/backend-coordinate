"""Routers package for API endpoints"""

from .health import router as health_router
from .detection import router as detection_router  
from .jobs import router as jobs_router, jobs_list_router

__all__ = [
    'health_router',
    'detection_router', 
    'jobs_router',
    'jobs_list_router'
]
