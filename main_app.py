"""
Main Application Entry Point
Building Detection API with modular architecture
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import os

# Import existing detection system
from src.core.detection import load_model

# Import configuration and dependencies
from api.config import get_settings, validate_configuration, print_configuration
from api.dependencies import initialize_dependencies, cleanup_dependencies
from api.exceptions import register_exception_handlers

# Import routers
from api.routers import health_router, detection_router, jobs_router, jobs_list_router

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
    
    # Startup
    print_configuration()
    
    try:
        if os.path.exists(settings.model_path):
            model = load_model(settings.model_path)
            print(f"✅ Model loaded successfully from {settings.model_path}")
        else:
            print(f"⚠️ Model file not found at {settings.model_path}")
            model = None
    except Exception as e:
        print(f"❌ Error loading model: {e}")
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