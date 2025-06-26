from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import os
import tempfile
import uuid
from datetime import datetime
import shutil

# Import existing detection system
from src.core.polygon_detection import detect_buildings_in_polygon
from src.core.detection import load_model
from src.utils.geojson_utils import load_geojson

app = FastAPI(
    title="Building Detection API",
    description="Backend service for building detection using YOLOv8",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model = None

# Pydantic models for request/response
class PolygonRequest(BaseModel):
    polygon: Dict[str, Any]  # GeoJSON polygon
    zoom: Optional[int] = 18
    confidence: Optional[float] = 0.25
    batch_size: Optional[int] = 5
    enable_merging: Optional[bool] = True
    merge_iou_threshold: Optional[float] = 0.1
    merge_touch_enabled: Optional[bool] = True
    merge_min_edge_distance_deg: Optional[float] = 0.00001

class DetectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    buildings: Optional[List[Dict[str, Any]]] = None
    total_buildings: Optional[int] = None
    execution_time: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: str

@app.on_event("startup")
async def startup_event():
    """Load YOLOv8 model on startup"""
    global model
    try:
        model_path = "best.pt"
        if os.path.exists(model_path):
            model = load_model(model_path)
            print(f"✅ Model loaded successfully from {model_path}")
        else:
            print(f"⚠️ Model file not found at {model_path}")
            model = None
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        model = None

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        timestamp=datetime.now().isoformat()
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Building Detection API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "detect": "/detect",
            "docs": "/docs"
        }
    }

def cleanup_temp_files(temp_dir: str):
    """Clean up temporary files and directory"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")

@app.post("/detect", response_model=DetectionResponse)
async def detect_buildings(
    request: PolygonRequest, 
    background_tasks: BackgroundTasks
):
    """
    Main endpoint for building detection
    
    Accepts a GeoJSON polygon and returns detected buildings
    """
    if model is None:
        raise HTTPException(
            status_code=503, 
            detail="Model not loaded. Please check server configuration."
        )
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    temp_dir = None
    
    try:
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp(prefix=f"detection_{session_id}_")
        
        # Create temporary GeoJSON file
        geojson_path = os.path.join(temp_dir, "input_polygon.geojson")
        with open(geojson_path, 'w') as f:
            json.dump(request.polygon, f, indent=2)
        
        # Validate GeoJSON
        try:
            test_load = load_geojson(geojson_path)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid GeoJSON format: {str(e)}"
            )
        
        # Output directory for results
        output_dir = os.path.join(temp_dir, "results")
        
        # Run building detection
        detection_result = detect_buildings_in_polygon(
            model=model,
            geojson_path=geojson_path,
            output_dir=output_dir,
            zoom=request.zoom,
            conf=request.confidence,
            batch_size=request.batch_size,
            enable_merging=request.enable_merging,
            merge_iou_threshold=request.merge_iou_threshold,
            merge_touch_enabled=request.merge_touch_enabled,
            merge_min_edge_distance_deg=request.merge_min_edge_distance_deg,
            resume_from_saved=False  # Don't use resume for API calls
        )
        
        # Read buildings_simple.json if it exists
        buildings_simple_path = os.path.join(output_dir, "buildings_simple.json")
        buildings_data = []
        
        if os.path.exists(buildings_simple_path):
            with open(buildings_simple_path, 'r') as f:
                buildings_simple = json.load(f)
                # Handle both list format and dict format
                if isinstance(buildings_simple, list):
                    buildings_data = buildings_simple
                elif isinstance(buildings_simple, dict):
                    buildings_data = buildings_simple.get('buildings', [])
                else:
                    buildings_data = []
        
        # Schedule cleanup in background
        background_tasks.add_task(cleanup_temp_files, temp_dir)
        
        return DetectionResponse(
            success=True,
            message="Building detection completed successfully",
            data=None,  # Remove complex detection data
            buildings=buildings_data,  # Only simple format: id, longitude, latitude
            total_buildings=len(buildings_data),  # Count from actual buildings_data
            execution_time=detection_result.get('execution_time', 0)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        if temp_dir:
            background_tasks.add_task(cleanup_temp_files, temp_dir)
        raise
        
    except Exception as e:
        # Clean up on error
        if temp_dir:
            background_tasks.add_task(cleanup_temp_files, temp_dir)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during detection: {str(e)}"
        )

@app.get("/models/info")
async def model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_loaded": True,
        "model_type": "YOLOv8",
        "model_file": "best.pt"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    ) 