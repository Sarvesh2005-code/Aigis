import asyncio
from typing import Dict, Any
import uuid
from sqlmodel import Session, select
from app.db.engine import engine
from datetime import datetime

class JobQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.active_jobs: Dict[str, Any] = {}
        self.is_running = False

    async def add_job(self, url: str, options: Dict[str, Any] = None) -> str:
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "url": url,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "options": options or {}
        }
        self.active_jobs[job_id] = job_data
        await self.queue.put(job_id)
        return job_id

    async def get_job(self, job_id: str):
        return self.active_jobs.get(job_id)

    async def worker(self):
        self.is_running = True
        print("Worker started...")
        while self.is_running:
            job_id = await self.queue.get()
            try:
                print(f"Processing job {job_id}")
                self.active_jobs[job_id]["status"] = "downloading"
                
                # Import here to avoid circular dependencies if any
                from app.core.downloader import downloader
                from app.core.engine import ai_engine
                
                url = self.active_jobs[job_id]["url"]
                
                # 1. Download
                input_path = downloader.download(url)
                self.active_jobs[job_id]["progress"] = 30
                
                # 2. Process (AI Crop)
                self.active_jobs[job_id]["status"] = "processing"
                output_filename = f"clip_{job_id}.mp4"
                output_path = f"data/{output_filename}"
                
                success = ai_engine.process_clip(input_path, output_path)
                
                if success:
                    self.active_jobs[job_id]["progress"] = 100
                    self.active_jobs[job_id]["status"] = "completed"
                    self.active_jobs[job_id]["output_file"] = output_filename
                else:
                    raise Exception("AI Processing returned false")
                
            except Exception as e:
                print(f"Job failed: {e}")
                self.active_jobs[job_id]["status"] = "failed"
                self.active_jobs[job_id]["error"] = str(e)
            finally:
                self.queue.task_done()

job_queue = JobQueue()
