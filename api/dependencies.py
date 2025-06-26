"""Dependency injection for Building Detection API"""

from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends, HTTPException

from .config import get_settings, Settings
from .services import job_manager


class AppDependencies:
    """Centralized dependency management"""
    
    def __init__(self):
        self.model = None
        self.executor = None
        self._settings = None
    
    def set_model(self, model):
        """Set the YOLOv8 model instance"""
        self.model = model
    
    def set_executor(self, executor: ThreadPoolExecutor):
        """Set the thread pool executor"""
        self.executor = executor
    
    def set_settings(self, settings: Settings):
        """Set the application settings"""
        self._settings = settings
    
    def get_model(self):
        """Get the YOLOv8 model instance"""
        if self.model is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. Please check server configuration."
            )
        return self.model
    
    def get_executor(self) -> ThreadPoolExecutor:
        """Get the thread pool executor"""
        if self.executor is None:
            raise HTTPException(
                status_code=503,
                detail="Executor not initialized. Please check server configuration."
            )
        return self.executor
    
    def get_settings(self) -> Settings:
        """Get application settings"""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings


# Global dependencies instance
app_dependencies = AppDependencies()


# Dependency functions for FastAPI
def get_model():
    """Dependency function to get model"""
    return app_dependencies.get_model()


def get_executor() -> ThreadPoolExecutor:
    """Dependency function to get executor"""
    return app_dependencies.get_executor()


def get_app_settings() -> Settings:
    """Dependency function to get settings"""
    return app_dependencies.get_settings()


def get_job_manager():
    """Dependency function to get job manager"""
    return job_manager


def validate_model_loaded():
    """Dependency to validate model is loaded"""
    model = app_dependencies.model
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please check server configuration."
        )
    return model


def validate_server_capacity(settings: Settings = Depends(get_app_settings)):
    """Dependency to validate server capacity for new jobs"""
    active_count = job_manager.get_active_job_count()
    if active_count >= settings.max_concurrent_jobs:
        raise HTTPException(
            status_code=429,
            detail=f"Server at capacity. Maximum {settings.max_concurrent_jobs} concurrent jobs allowed. Currently processing: {active_count}"
        )
    return True


# Utility dependencies
def get_background_processor():
    """Dependency to get background processing function"""
    def submit_job_to_background_processing(job_id: str):
        """Submit job to background processing queue"""
        from .services.detection import detection_service
        
        print(f"🔄 Submitting job {job_id} to background processing queue")
        
        # Get dependencies
        model = app_dependencies.get_model()
        executor = app_dependencies.get_executor()
        
        # Submit real processing to thread pool
        future = executor.submit(detection_service.process_detection_job, job_id, model)
        
        # Store future reference in job for potential cancellation
        job = job_manager.get_job(job_id)
        if job:
            job.request_params['_future'] = future
    
    return submit_job_to_background_processing


class ConfigurableDefaults:
    """Dependency class for configurable default values"""
    
    def __init__(self, settings: Settings = Depends(get_app_settings)):
        self.settings = settings
    
    @property
    def zoom(self) -> int:
        return self.settings.default_zoom
    
    @property
    def confidence(self) -> float:
        return self.settings.default_confidence
    
    @property
    def batch_size(self) -> int:
        return self.settings.default_batch_size
    
    @property
    def enable_merging(self) -> bool:
        return self.settings.default_enable_merging
    
    @property
    def merge_iou_threshold(self) -> float:
        return self.settings.default_merge_iou_threshold
    
    @property
    def merge_touch_enabled(self) -> bool:
        return self.settings.default_merge_touch_enabled
    
    @property
    def merge_min_edge_distance_deg(self) -> float:
        return self.settings.default_merge_min_edge_distance_deg


def get_configurable_defaults() -> ConfigurableDefaults:
    """Dependency function to get configurable defaults"""
    return ConfigurableDefaults()


# Initialization functions
def initialize_dependencies(model, executor: ThreadPoolExecutor, settings: Settings):
    """Initialize all dependencies"""
    app_dependencies.set_model(model)
    app_dependencies.set_executor(executor)
    app_dependencies.set_settings(settings)
    
    print("✅ Dependencies initialized successfully")


def cleanup_dependencies():
    """Cleanup dependencies on shutdown"""
    if app_dependencies.executor:
        app_dependencies.executor.shutdown(wait=True)
        print("🧹 Executor shutdown completed")
    
    print("✅ Dependencies cleaned up successfully") 