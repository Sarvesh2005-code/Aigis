from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.core.queue import job_queue
import asyncio

router = APIRouter()

class JobRequest(BaseModel):
    url: str
    options: dict = {}

@router.on_event("startup")
async def startup_event():
    # Start the worker loop in the background
    asyncio.create_task(job_queue.worker())

@router.post("/jobs")
async def create_job(request: JobRequest):
    job_id = await job_queue.add_job(request.url, request.options)
    return {"job_id": job_id, "status": "queued"}

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = await job_queue.get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    return job

@router.get("/jobs")
async def list_jobs():
    return job_queue.active_jobs
