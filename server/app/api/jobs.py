from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl, Field, validator
from app.core.queue import job_queue
from app.core.clip_detector import ClipDetector
from sqlmodel import Session, select
from app.db.engine import engine
from app.db.models import Job
import asyncio
import re

router = APIRouter()

class JobRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    options: dict = Field(default_factory=dict, description="Processing options")
    
    @validator("url")
    def validate_youtube_url(cls, v):
        """Validate that URL is a YouTube URL."""
        youtube_pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        if not re.match(youtube_pattern, v) and not v.startswith("http"):
            raise ValueError("Invalid YouTube URL")
        return v

class MultiClipRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    max_clips: int = Field(default=5, ge=1, le=10, description="Maximum number of clips to generate")
    min_duration: float = Field(default=15.0, ge=5.0, le=60.0, description="Minimum clip duration in seconds")
    max_duration: float = Field(default=60.0, ge=15.0, le=120.0, description="Maximum clip duration in seconds")
    
    @validator("url")
    def validate_youtube_url(cls, v):
        youtube_pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        if not re.match(youtube_pattern, v) and not v.startswith("http"):
            raise ValueError("Invalid YouTube URL")
        return v

# Worker is started in main.py lifespan

@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(request: JobRequest):
    """Create a new video clipping job."""
    try:
        job_id = await job_queue.add_job(request.url, request.options)
        return {"job_id": job_id, "status": "queued", "message": "Job created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create job: {str(e)}")

@router.get("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def get_job_status(job_id: str):
    """Get the status of a specific job."""
    job = await job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.get("/jobs", status_code=status.HTTP_200_OK)
async def list_jobs(limit: int = 50, offset: int = 0):
    """List all jobs."""
    try:
        with Session(engine) as session:
            statement = select(Job).order_by(Job.created_at.desc()).limit(limit).offset(offset)
            jobs = session.exec(statement).all()
            
            return [{
                "id": job.id,
                "url": job.url,
                "status": job.status.value,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "output_url": job.output_url,
                "virality_score": job.virality_score
            } for job in jobs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list jobs: {str(e)}")

@router.post("/jobs/detect-clips", status_code=status.HTTP_200_OK)
async def detect_clips(request: MultiClipRequest):
    """Detect best clips from a video without processing them."""
    try:
        detector = ClipDetector()
        
        # Download video first
        from app.core.downloader import downloader
        temp_path = downloader.download(request.url)
        
        # Detect clips
        clips = detector.detect_best_clips(
            temp_path,
            max_clips=request.max_clips,
            min_duration=request.min_duration,
            max_duration=request.max_duration
        )
        
        # Cleanup
        import os
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        return {
            "clips": clips,
            "count": len(clips)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to detect clips: {str(e)}")
