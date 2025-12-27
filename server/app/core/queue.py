import asyncio
from typing import Dict, Any, Optional
import uuid
from sqlmodel import Session, select
from app.db.engine import engine
from app.db.models import Job, JobStatus
from datetime import datetime
import structlog
import os

logger = structlog.get_logger()

class JobQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.is_running = False

    async def add_job(self, url: str, options: Dict[str, Any] = None) -> str:
        job_id = str(uuid.uuid4())
        
        with Session(engine) as session:
            job = Job(
                id=job_id,
                url=url,
                status=JobStatus.PENDING,
                progress=0,
                options=options or {}
            )
            session.add(job)
            session.commit()
            session.refresh(job)
        
        await self.queue.put(job_id)
        logger.info("job_created", job_id=job_id, url=url)
        return job_id

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with Session(engine) as session:
            job = session.get(Job, job_id)
            if not job:
                return None
            
            return {
                "id": job.id,
                "url": job.url,
                "status": job.status.value,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "output_file": job.output_file,
                "output_url": job.output_url,
                "error": job.error,
                "options": job.options or {},
                "virality_score": job.virality_score
            }

    def _update_job(self, job_id: str, **kwargs):
        """Update job in database."""
        with Session(engine) as session:
            job = session.get(Job, job_id)
            if not job:
                return
            
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()

    async def worker(self):
        self.is_running = True
        logger.info("worker_started")
        while self.is_running:
            job_id = await self.queue.get()
            try:
                logger.info("processing_job", job_id=job_id)
                self._update_job(job_id, status=JobStatus.DOWNLOADING)
                
                # Import here to avoid circular dependencies
                from app.core.downloader import downloader
                from app.core.engine import ai_engine
                from app.core.virality import ViralityScorer
                
                # Get job from DB
                job_data = await self.get_job(job_id)
                if not job_data:
                    logger.error("job_not_found", job_id=job_id)
                    continue
                
                url = job_data["url"]
                
                # 1. Download
                input_path = downloader.download(url)
                self._update_job(job_id, progress=30)
                
                # 2. Process (AI Crop)
                self._update_job(job_id, status=JobStatus.PROCESSING)
                output_filename = f"clip_{job_id}.mp4"
                output_dir = "data/outputs"
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, output_filename)
                
                success = ai_engine.process_clip(input_path, output_path)
                
                if success:
                    # Calculate virality score
                    try:
                        scorer = ViralityScorer()
                        score = scorer.score_clip(output_path)
                        self._update_job(
                            job_id,
                            progress=100,
                            status=JobStatus.COMPLETED,
                            output_file=output_filename,
                            output_url=f"/outputs/{output_filename}",
                            completed_at=datetime.utcnow(),
                            virality_score=score
                        )
                    except Exception as e:
                        logger.warning("virality_scoring_failed", error=str(e))
                        self._update_job(
                            job_id,
                            progress=100,
                            status=JobStatus.COMPLETED,
                            output_file=output_filename,
                            output_url=f"/outputs/{output_filename}",
                            completed_at=datetime.utcnow()
                        )
                    
                    # Cleanup temp file
                    if os.path.exists(input_path):
                        try:
                            os.remove(input_path)
                        except:
                            pass
                else:
                    raise Exception("AI Processing returned false")
                
            except Exception as e:
                logger.error("job_failed", job_id=job_id, error=str(e))
                self._update_job(
                    job_id,
                    status=JobStatus.FAILED,
                    error=str(e)
                )
            finally:
                self.queue.task_done()

job_queue = JobQueue()
