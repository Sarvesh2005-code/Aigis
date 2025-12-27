from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from app.core.generation import ContentGenerator

router = APIRouter()
generator = ContentGenerator()

class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200, description="Topic for video generation")
    
    @validator("topic")
    def validate_topic(cls, v):
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def start_generation(req: GenerateRequest):
    """Create a new AI video generation job."""
    try:
        job_id = await generator.create_job(req.topic)
        return {"job_id": job_id, "status": "queued", "message": "Generation job created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create generation job: {str(e)}")

@router.get("/generate/jobs", status_code=status.HTTP_200_OK)
async def list_gen_jobs(limit: int = 50, offset: int = 0):
    """List all generation jobs."""
    try:
        jobs = await generator.list_jobs()
        return jobs[offset:offset+limit]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list jobs: {str(e)}")

@router.get("/generate/{job_id}", status_code=status.HTTP_200_OK)
async def get_gen_job(job_id: str):
    """Get the status of a specific generation job."""
    job = await generator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
