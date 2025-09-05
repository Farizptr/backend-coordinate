"""Centralized logging configuration for Building Detection API"""

import logging
import sys
import time
from typing import Optional
from functools import wraps
from contextvars import ContextVar
from ..config import get_settings

# Context variable for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

class RequestIDFilter(logging.Filter):
    """Add request ID to log records"""
    
    def filter(self, record):
        record.request_id = request_id_context.get() or "system"
        return True

class PerformanceFormatter(logging.Formatter):
    """Custom formatter with performance timing"""
    
    def format(self, record):
        # Add timestamp
        record.timestamp = time.time()
        
        # Standard format with request ID
        log_format = "[%(asctime)s] %(levelname)s [%(request_id)s] %(name)s: %(message)s"
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        return formatter.format(record)

def setup_logging():
    """Setup centralized logging configuration"""
    settings = get_settings()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    console_handler.addFilter(RequestIDFilter())
    console_handler.setFormatter(PerformanceFormatter())
    
    root_logger.addHandler(console_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance with consistent configuration"""
    return logging.getLogger(name)

def set_request_id(request_id: str):
    """Set request ID for current context"""
    request_id_context.set(request_id)

def log_performance(operation_name: str):
    """Decorator to log operation performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(f"{func.__module__}.{func.__name__}")
            start_time = time.time()
            
            logger.info(f"Starting {operation_name}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Completed {operation_name} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed {operation_name} after {duration:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator

def log_memory_usage():
    """Log current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        logger = get_logger("system.memory")
        logger.info(f"Memory usage: RSS={memory_info.rss/1024/1024:.1f}MB, VMS={memory_info.vms/1024/1024:.1f}MB")
    except ImportError:
        pass  # psutil not available

# Initialize logging on import
setup_logging()