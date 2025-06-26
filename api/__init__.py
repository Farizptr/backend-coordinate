"""Building Detection API Package"""

from .config import get_settings, settings
from .dependencies import (
    get_model, get_executor, get_app_settings, get_job_manager,
    validate_model_loaded, validate_server_capacity
)
from .exceptions import register_exception_handlers

__version__ = "2.0.0"
__title__ = "Building Detection API"
__description__ = "Modular FastAPI building detection service using YOLOv8"

__all__ = [
    "get_settings",
    "settings", 
    "get_model",
    "get_executor",
    "get_app_settings",
    "get_job_manager",
    "validate_model_loaded",
    "validate_server_capacity",
    "register_exception_handlers",
]
