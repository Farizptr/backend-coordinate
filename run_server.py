#!/usr/bin/env python3
"""
Building Detection API Server
Run this script to start the FastAPI backend server
"""

import uvicorn
import os
import sys

def main():
    """Start the FastAPI server"""
    
    # Check if model file exists
    model_path = "best.pt"
    if not os.path.exists(model_path):
        print(f"⚠️  Warning: Model file '{model_path}' not found!")
        print(f"   The API will start but detection endpoints may not work.")
        print(f"   Please ensure the YOLOv8 model file is in the project root.")
        print()
    
    print("🚀 Starting Building Detection API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print()
    print("Press CTRL+C to stop the server")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 