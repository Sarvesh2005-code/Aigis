from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, DateTime
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(SQLModel, table=True):
    """Model for video clipping jobs."""
    id: Optional[str] = Field(default=None, primary_key=True)
    url: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    output_file: Optional[str] = None
    output_url: Optional[str] = None
    error: Optional[str] = None
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    virality_score: Optional[float] = None

class GenerationJob(SQLModel, table=True):
    """Model for AI-generated video jobs."""
    id: Optional[str] = Field(default=None, primary_key=True)
    topic: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    output_url: Optional[str] = None
    error: Optional[str] = None
    script: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    logs: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))
    virality_score: Optional[float] = None

