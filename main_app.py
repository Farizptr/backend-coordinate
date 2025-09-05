"""
Main Application Entry Point
Building Detection API with modular architecture
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import os
import time
import tempfile

# Import existing detection system
from src.core.detection import load_model

# Import logging system
from api.utils.logging import get_logger, log_performance, setup_logging

# Import configuration and dependencies
from api.config import get_settings, validate_configuration, print_configuration
from api.dependencies import initialize_dependencies, cleanup_dependencies
from api.exceptions import register_exception_handlers

# Import routers
from api.routers import health_router, detection_router, jobs_router, jobs_list_router
from api.routers.websocket import router as websocket_router

# Get settings
settings = get_settings()

# Validate configuration on startup
validate_configuration()

# Global instances
model = None
executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_jobs)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler (replaces deprecated on_event)"""
    global model, executor
    
    # Setup logging first
    logger = get_logger(__name__)
    
    # Startup
    print_configuration()
    
    try:
        if os.path.exists(settings.model_path):
            logger.info(f"Loading YOLOv8 model from {settings.model_path}")
            model = load_model(settings.model_path)
            
            # Warm up model with dummy inference
            logger.info("Warming up model with test inference")
            try:
                # Create a small test image (256x256 RGB)
                import torch
                import numpy as np
                from PIL import Image
                
                test_img = Image.fromarray(np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8))
                start_time = time.time()
                
                # Run dummy prediction to warm up GPU/model
                model(test_img, conf=0.5, verbose=False)
                warmup_time = time.time() - start_time
                
                logger.info(f"Model warmup completed in {warmup_time:.2f}s")
            except Exception as warmup_error:
                logger.warning(f"Model warmup failed (non-critical): {warmup_error}")
            
            logger.info(f"Model loaded and ready for inference")
        else:
            logger.warning(f"Model file not found at {settings.model_path}")
            model = None
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        model = None
    
    # Initialize dependencies
    initialize_dependencies(model, executor, settings)
    
    # Configure routers with dependencies (legacy support)
    from api.routers.health import set_model, set_max_concurrent_jobs as set_health_max_jobs
    from api.routers.detection import set_dependencies  
    from api.routers.jobs import set_max_concurrent_jobs
    
    set_model(model)
    set_health_max_jobs(settings.max_concurrent_jobs)
    set_dependencies(model, executor, settings.max_concurrent_jobs)
    set_max_concurrent_jobs(settings.max_concurrent_jobs)
    
    print("🚀 Application startup completed")
    
    yield  # Application runs here
    
    # Shutdown
    cleanup_dependencies()
    print("🛑 Application shutdown completed")


# Create FastAPI application with lifespan handler
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    openapi_version="3.0.0",
    root_path="/ai"
)

# CORS middleware with configurable settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register exception handlers
register_exception_handlers(app)


# Include routers
app.include_router(health_router)
app.include_router(detection_router)
app.include_router(jobs_router)
app.include_router(jobs_list_router)
app.include_router(websocket_router)

# FastAPI will handle OpenAPI schema generation natively with openapi_version="3.0.0"


# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_app:app",  # Pass as string to enable reload
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    ) 