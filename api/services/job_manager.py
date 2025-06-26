"""Job management service for handling job lifecycle and storage"""

import time
import threading
from typing import Dict, Any, Optional, List
from api.models import JobInfo, JobStatus


class JobManager:
    """Centralized job management service"""
    
    def __init__(self):
        self.active_jobs: Dict[str, JobInfo] = {}
        self.job_lock = threading.Lock()
    
    def create_job(self, job_id: str, polygon: Dict[str, Any], request_params: Dict[str, Any]) -> JobInfo:
        """Create a new job with initial status"""
        job_info = JobInfo(
            job_id=job_id,
            status=JobStatus.QUEUED,
            progress=0,
            stage="Job queued for processing",
            buildings_found=0,
            start_time=time.time(),
            polygon=polygon,
            request_params=request_params
        )
        
        with self.job_lock:
            self.active_jobs[job_id] = job_info
        
        print(f"📝 Created job {job_id} - Status: {job_info.status}")
        return job_info
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information by ID"""
        with self.job_lock:
            return self.active_jobs.get(job_id)
    
    def update_job_progress(self, job_id: str, progress: int, stage: str, buildings_found: int = 0):
        """Update job progress and stage"""
        with self.job_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.progress = progress
                job.stage = stage
                job.buildings_found = buildings_found
                job.status = JobStatus.PROCESSING
                print(f"📊 Job {job_id}: {progress}% - {stage} - Buildings: {buildings_found}")
    
    def complete_job(self, job_id: str, result_data: Dict[str, Any]):
        """Mark job as completed with results"""
        with self.job_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = JobStatus.COMPLETED
                job.progress = 100
                job.stage = "Completed successfully"
                job.end_time = time.time()
                job.execution_time = job.end_time - job.start_time
                
                # Store result data in job
                job.request_params['result_data'] = result_data
                
                print(f"✅ Job {job_id} completed in {job.execution_time:.2f} seconds")
    
    def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed with error message"""
        with self.job_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.end_time = time.time()
                job.execution_time = job.end_time - job.start_time
                
                print(f"❌ Job {job_id} failed: {error_message}")
    
    def cancel_job(self, job_id: str):
        """Cancel a job"""
        with self.job_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = JobStatus.CANCELLED
                job.stage = "Job cancelled by user"
                job.end_time = time.time()
                job.execution_time = job.end_time - job.start_time
                job.error_message = "Job was cancelled by user request"
                
                print(f"🚫 Job {job_id} cancelled by user")
    
    def cleanup_old_jobs(self, max_age_hours: int = 1):
        """Clean up jobs older than specified hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.job_lock:
            jobs_to_remove = []
            for job_id, job in self.active_jobs.items():
                if job.end_time and (current_time - job.end_time) > max_age_seconds:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
                print(f"🗑️ Cleaned up old job: {job_id}")
    
    def get_active_job_count(self) -> int:
        """Get count of currently processing jobs"""
        with self.job_lock:
            return len([job for job in self.active_jobs.values() 
                       if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]])
    
    def is_job_id_available(self, job_id: str) -> bool:
        """Check if job ID is not already in use"""
        with self.job_lock:
            return job_id not in self.active_jobs
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get summary of all jobs"""
        jobs_summary = []
        
        with self.job_lock:
            for job_id, job in self.active_jobs.items():
                jobs_summary.append({
                    "job_id": job_id,
                    "status": job.status,
                    "progress": job.progress,
                    "stage": job.stage,
                    "buildings_found": job.buildings_found,
                    "start_time": job.start_time,
                    "execution_time": job.execution_time
                })
        
        # Sort by start time (newest first)
        jobs_summary.sort(key=lambda x: x["start_time"], reverse=True)
        return jobs_summary


# Global job manager instance
job_manager = JobManager() 