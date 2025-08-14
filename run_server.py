#!/usr/bin/env python3
"""
Production Server Entry Point
Building Detection AI Worker Service

Usage:
    python run_server.py
    
Environment Variables:
    HOST: Server host (default: 0.0.0.0)
    PORT: Server port (default: 5050)  
    MODEL_PATH: Path to model file (default: best.pt)
    MAX_CONCURRENT_JOBS: Max concurrent detection jobs (default: 2)
    DEBUG: Enable debug mode (default: False)
"""

import uvicorn
from api.config import get_settings


def main():
    """Start the production server"""
    settings = get_settings()
    
    print(f"🚀 Starting Building Detection AI Worker Service")
    print(f"📍 Server: http://{settings.host}:{settings.port}")
    print(f"📚 Docs: http://{settings.host}:{settings.port}/docs")
    print(f"🔍 Health: http://{settings.host}:{settings.port}/health")
    
    uvicorn.run(
        "main_app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()
