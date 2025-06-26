"""Custom exceptions and exception handlers for Building Detection API"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from typing import Any, Dict
import logging


# Custom exceptions
class ModelNotLoadedException(Exception):
    """Raised when YOLOv8 model is not loaded"""
    pass


class JobNotFoundException(Exception):
    """Raised when job ID is not found"""
    pass


class JobValidationException(Exception):
    """Raised when job validation fails"""
    pass


class ServerCapacityException(Exception):
    """Raised when server is at capacity"""
    pass


class DetectionProcessingException(Exception):
    """Raised when detection processing fails"""
    pass


class ConfigurationException(Exception):
    """Raised when configuration is invalid"""
    pass


# Exception handlers
async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedException):
    """Handle model not loaded exception"""
    return JSONResponse(
        status_code=503,
        content={
            "error": "Model Not Available",
            "message": "YOLOv8 model is not loaded. Please check server configuration.",
            "detail": str(exc),
            "type": "model_error"
        }
    )


async def job_not_found_handler(request: Request, exc: JobNotFoundException):
    """Handle job not found exception"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Job Not Found",
            "message": "The requested job ID was not found.",
            "detail": str(exc),
            "type": "job_error"
        }
    )


async def job_validation_handler(request: Request, exc: JobValidationException):
    """Handle job validation exception"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Job Validation Error",
            "message": "Job validation failed.",
            "detail": str(exc),
            "type": "validation_error"
        }
    )


async def server_capacity_handler(request: Request, exc: ServerCapacityException):
    """Handle server capacity exception"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Server at Capacity",
            "message": "Server is currently processing the maximum number of concurrent jobs.",
            "detail": str(exc),
            "type": "capacity_error"
        }
    )


async def detection_processing_handler(request: Request, exc: DetectionProcessingException):
    """Handle detection processing exception"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Detection Processing Error",
            "message": "An error occurred during building detection processing.",
            "detail": str(exc),
            "type": "processing_error"
        }
    )


async def configuration_handler(request: Request, exc: ConfigurationException):
    """Handle configuration exception"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Configuration Error",
            "message": "Server configuration is invalid.",
            "detail": str(exc),
            "type": "config_error"
        }
    )


# Default FastAPI exception handlers
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Enhanced HTTP exception handler with better error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "type": "http_error",
            "path": str(request.url)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Enhanced validation exception handler"""
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(x) for x in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Request validation failed",
            "detail": errors,
            "type": "validation_error"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled exceptions"""
    # Log the full traceback for debugging
    logging.error(f"Unhandled exception: {exc}")
    logging.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc),
            "type": "server_error"
        }
    )


# Exception mapping
EXCEPTION_HANDLERS = {
    ModelNotLoadedException: model_not_loaded_handler,
    JobNotFoundException: job_not_found_handler,
    JobValidationException: job_validation_handler,
    ServerCapacityException: server_capacity_handler,
    DetectionProcessingException: detection_processing_handler,
    ConfigurationException: configuration_handler,
    StarletteHTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    Exception: general_exception_handler,
}


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    for exception_type, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception_type, handler)
    
    print("✅ Exception handlers registered successfully")


# Utility functions for raising exceptions
def raise_job_not_found(job_id: str):
    """Raise job not found exception"""
    raise JobNotFoundException(f"Job '{job_id}' not found")


def raise_model_not_loaded():
    """Raise model not loaded exception"""
    raise ModelNotLoadedException("YOLOv8 model is not loaded")


def raise_server_at_capacity(current: int, maximum: int):
    """Raise server capacity exception"""
    raise ServerCapacityException(
        f"Server at capacity: {current}/{maximum} jobs currently processing"
    )


def raise_job_validation_error(message: str):
    """Raise job validation exception"""
    raise JobValidationException(message)


def raise_detection_processing_error(message: str):
    """Raise detection processing exception"""
    raise DetectionProcessingException(message)


def raise_configuration_error(message: str):
    """Raise configuration exception"""
    raise ConfigurationException(message) 