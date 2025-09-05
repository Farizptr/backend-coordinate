"""Configuration management for Building Detection API"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = Field(default="Building Detection API", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION") 
    app_description: str = Field(
        default="Asynchronous building detection using YOLOv8",
        env="APP_DESCRIPTION"
    )
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=5050, env="PORT")
    reload: bool = Field(default=True, env="RELOAD")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Model Configuration
    model_path: str = Field(default="best.pt", env="MODEL_PATH")
    model_type: str = Field(default="YOLOv8", env="MODEL_TYPE")
    
    # Job Processing Configuration
    max_concurrent_jobs: int = Field(default=2, env="MAX_CONCURRENT_JOBS")
    job_cleanup_interval_hours: float = Field(default=1.0, env="JOB_CLEANUP_INTERVAL_HOURS")
    
    # Detection Default Parameters
    default_zoom: int = Field(default=18, env="DEFAULT_ZOOM")
    default_confidence: float = Field(default=0.25, env="DEFAULT_CONFIDENCE")
    default_batch_size: int = Field(default=5, env="DEFAULT_BATCH_SIZE")
    default_enable_merging: bool = Field(default=True, env="DEFAULT_ENABLE_MERGING")
    default_merge_iou_threshold: float = Field(default=0.1, env="DEFAULT_MERGE_IOU_THRESHOLD")
    default_merge_touch_enabled: bool = Field(default=True, env="DEFAULT_MERGE_TOUCH_ENABLED")
    default_merge_min_edge_distance_deg: float = Field(
        default=0.00001, 
        env="DEFAULT_MERGE_MIN_EDGE_DISTANCE_DEG"
    )
    
    # Job ID Validation Configuration
    job_id_min_length: int = Field(default=3, env="JOB_ID_MIN_LENGTH")
    job_id_max_length: int = Field(default=50, env="JOB_ID_MAX_LENGTH")
    
    # Temporary Files Configuration
    temp_dir_prefix: str = Field(default="detection_", env="TEMP_DIR_PREFIX")
    cleanup_temp_files: bool = Field(default=True, env="CLEANUP_TEMP_FILES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    """Database configuration (for future use)"""
    
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class SecuritySettings(BaseSettings):
    """Security configuration (for future use)"""
    
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instances
settings = Settings()
db_settings = DatabaseSettings()
security_settings = SecuritySettings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def get_db_settings() -> DatabaseSettings:
    """Get database settings"""
    return db_settings


def get_security_settings() -> SecuritySettings:
    """Get security settings"""
    return security_settings


# Configuration validation
def validate_configuration():
    """Validate configuration on startup"""
    errors = []
    
    # Validate model path
    if not os.path.exists(settings.model_path):
        errors.append(f"Model file not found at {settings.model_path}")
    
    # Validate port range
    if not (1 <= settings.port <= 65535):
        errors.append(f"Invalid port number: {settings.port}")
    
    # Validate concurrent jobs
    if settings.max_concurrent_jobs <= 0:
        errors.append(f"Max concurrent jobs must be positive: {settings.max_concurrent_jobs}")
    
    # Validate job ID length constraints
    if settings.job_id_min_length >= settings.job_id_max_length:
        errors.append("Job ID min length must be less than max length")
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValueError(error_msg)
    
    return True


def print_configuration():
    """Print current configuration (excluding sensitive data)"""
    print("🔧 Building Detection API Configuration:")
    print(f"   App: {settings.app_name} v{settings.app_version}")
    print(f"   Host: {settings.host}:{settings.port}")
    print(f"   Model: {settings.model_path} ({settings.model_type})")
    print(f"   Max Jobs: {settings.max_concurrent_jobs}")
    print(f"   Debug: {settings.debug}")
    print(f"   Log Level: {settings.log_level}")
    print("=" * 50) 