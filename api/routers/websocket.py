"""WebSocket support for real-time job progress updates"""

import json
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..utils.logging import get_logger
from ..services.job_manager import job_manager

router = APIRouter()
logger = get_logger(__name__)

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.job_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str = None):
        """Accept WebSocket connection and optionally subscribe to job updates"""
        await websocket.accept()
        
        # Add to general connections
        if "general" not in self.active_connections:
            self.active_connections["general"] = set()
        self.active_connections["general"].add(websocket)
        
        # Add to job-specific connections if job_id provided
        if job_id:
            if job_id not in self.job_connections:
                self.job_connections[job_id] = set()
            self.job_connections[job_id].add(websocket)
            
        logger.info(f"WebSocket connected for job: {job_id or 'general'}")

    def disconnect(self, websocket: WebSocket, job_id: str = None):
        """Remove WebSocket connection"""
        # Remove from general connections
        if "general" in self.active_connections:
            self.active_connections["general"].discard(websocket)
        
        # Remove from job-specific connections
        if job_id and job_id in self.job_connections:
            self.job_connections[job_id].discard(websocket)
            if not self.job_connections[job_id]:
                del self.job_connections[job_id]
                
        logger.info(f"WebSocket disconnected for job: {job_id or 'general'}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")

    async def send_job_update(self, job_id: str, message: dict):
        """Send update to all WebSockets subscribed to specific job"""
        if job_id in self.job_connections:
            disconnected = []
            for connection in self.job_connections[job_id].copy():
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.job_connections[job_id].discard(connection)

    async def broadcast(self, message: dict):
        """Broadcast message to all active connections"""
        if "general" in self.active_connections:
            disconnected = []
            for connection in self.active_connections["general"].copy():
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections["general"].discard(connection)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_general_endpoint(websocket: WebSocket):
    """General WebSocket endpoint for system updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/job/{job_id}")
async def websocket_job_endpoint(websocket: WebSocket, job_id: str):
    """Job-specific WebSocket endpoint for progress updates"""
    await manager.connect(websocket, job_id)
    
    try:
        # Send current job status immediately upon connection
        job = job_manager.get_job(job_id)
        if job:
            initial_status = {
                "type": "job_status",
                "job_id": job_id,
                "status": job.status.value,
                "progress": job.progress,
                "stage": job.stage,
                "buildings_found": job.buildings_found,
                "execution_time": job.execution_time
            }
            await manager.send_personal_message(initial_status, websocket)
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": f"Job {job_id} not found"
            }, websocket)
        
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            elif message.get("type") == "get_status":
                # Send current job status
                job = job_manager.get_job(job_id)
                if job:
                    status_update = {
                        "type": "job_status",
                        "job_id": job_id,
                        "status": job.status.value,
                        "progress": job.progress,
                        "stage": job.stage,
                        "buildings_found": job.buildings_found,
                        "execution_time": job.execution_time
                    }
                    await manager.send_personal_message(status_update, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        manager.disconnect(websocket, job_id)

# Function to be called when job progress is updated
async def notify_job_progress(job_id: str, status: str, progress: int, stage: str, buildings_found: int, execution_time: float = None):
    """Send job progress update to all subscribed WebSocket clients"""
    message = {
        "type": "job_progress",
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "stage": stage,
        "buildings_found": buildings_found,
        "execution_time": execution_time,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_job_update(job_id, message)

# Function to be called when job is completed
async def notify_job_completion(job_id: str, total_buildings: int, execution_time: float):
    """Send job completion notification to all subscribed WebSocket clients"""
    message = {
        "type": "job_completed",
        "job_id": job_id,
        "total_buildings": total_buildings,
        "execution_time": execution_time,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_job_update(job_id, message)

# Function to be called when job fails
async def notify_job_failure(job_id: str, error_message: str):
    """Send job failure notification to all subscribed WebSocket clients"""
    message = {
        "type": "job_failed",
        "job_id": job_id,
        "error_message": error_message,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_job_update(job_id, message)

# Export the manager for use in other modules
__all__ = ['router', 'notify_job_progress', 'notify_job_completion', 'notify_job_failure', 'manager']