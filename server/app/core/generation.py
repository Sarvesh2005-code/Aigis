import structlog
import uuid
import os
import asyncio
from datetime import datetime
from sqlmodel import Session
from app.db.engine import engine
from app.db.models import GenerationJob, JobStatus
from app.core.gen_script import ScriptGenerator
from app.core.gen_visuals import VisualsFetcher
from app.core.gen_audio import AudioGenerator
from app.core.assembler import VideoAssembler
from app.core.virality import ViralityScorer

logger = structlog.get_logger()

class ContentGenerator:
    def __init__(self):
        self.script_gen = ScriptGenerator()
        self.visuals_gen = VisualsFetcher()
        self.audio_gen = AudioGenerator()
        self.assembler = VideoAssembler()
        self.output_dir = "data/outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    async def create_job(self, topic: str):
        job_id = str(uuid.uuid4())
        
        with Session(engine) as session:
            job = GenerationJob(
                id=job_id,
                topic=topic,
                status=JobStatus.PENDING,
                progress=0,
                logs=[]
            )
            session.add(job)
            session.commit()
        
        # Start background processing
        asyncio.create_task(self.process_job(job_id, topic))
        logger.info("generation_job_created", job_id=job_id, topic=topic)
        return job_id

    def _update_job(self, job_id: str, **kwargs):
        """Update generation job in database."""
        with Session(engine) as session:
            job = session.get(GenerationJob, job_id)
            if not job:
                return
            
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()

    async def process_job(self, job_id, topic):
        try:
            self._update_job(job_id, status=JobStatus.PROCESSING)
            self._add_log(job_id, "Generating script...")
            
            # 1. Generate Script
            script_data = await self.script_gen.generate_script(topic)
            self._update_job(job_id, script=script_data, progress=20)
            
            # 2. Fetch Visuals
            self._add_log(job_id, "Fetching visuals...")
            keywords = script_data.get("keywords", [topic])
            video_paths = self.visuals_gen.fetch_videos(keywords)
            if not video_paths:
                raise Exception("No visuals found")
            self._update_job(job_id, progress=40)
            
            # 3. Generate Audio
            self._add_log(job_id, "Generating audio...")
            audio_path = os.path.join(self.output_dir, f"{job_id}.mp3")
            success = await self.audio_gen.generate_audio(script_data["script"], audio_path)
            if not success:
                raise Exception("Audio generation failed")
            self._update_job(job_id, progress=60)
            
            # 4. Assemble Video
            self._add_log(job_id, "Assembling video...")
            output_path = os.path.join(self.output_dir, f"{job_id}.mp4")
            
            # Run in thread executor as MoviePy is CPU heavy/blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.assembler.assemble, video_paths, audio_path, output_path)
            
            # Calculate virality score
            try:
                scorer = ViralityScorer()
                score = scorer.score_clip(output_path)
                self._update_job(
                    job_id,
                    progress=100,
                    status=JobStatus.COMPLETED,
                    output_url=f"/outputs/{job_id}.mp4",
                    completed_at=datetime.utcnow(),
                    virality_score=score
                )
            except Exception as e:
                logger.warning("virality_scoring_failed", error=str(e))
                self._update_job(
                    job_id,
                    progress=100,
                    status=JobStatus.COMPLETED,
                    output_url=f"/outputs/{job_id}.mp4",
                    completed_at=datetime.utcnow()
                )
            
            # Cleanup temp files
            self._cleanup_temp_files(video_paths, audio_path)
            
        except Exception as e:
            logger.error("job_failed", job_id=job_id, error=str(e))
            self._update_job(
                job_id,
                status=JobStatus.FAILED,
                error=str(e)
            )

    def _add_log(self, job_id: str, message: str):
        """Add a log message to the job."""
        with Session(engine) as session:
            job = session.get(GenerationJob, job_id)
            if job:
                if not job.logs:
                    job.logs = []
                job.logs.append(message)
                session.add(job)
                session.commit()

    def _cleanup_temp_files(self, video_paths: list, audio_path: str):
        """Clean up temporary files."""
        for path in video_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

    async def get_job(self, job_id: str):
        """Get job from database."""
        with Session(engine) as session:
            job = session.get(GenerationJob, job_id)
            if not job:
                return None
            
            return {
                "id": job.id,
                "topic": job.topic,
                "status": job.status.value,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "output_url": job.output_url,
                "error": job.error,
                "script": job.script,
                "logs": job.logs or [],
                "virality_score": job.virality_score
            }

    async def list_jobs(self):
        """List all generation jobs."""
        with Session(engine) as session:
            from sqlmodel import select
            statement = select(GenerationJob).order_by(GenerationJob.created_at.desc())
            jobs = session.exec(statement).all()
            
            return [{
                "id": job.id,
                "topic": job.topic,
                "status": job.status.value,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "output_url": job.output_url,
                "virality_score": job.virality_score
            } for job in jobs]
