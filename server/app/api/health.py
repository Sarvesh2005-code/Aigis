from fastapi import APIRouter
from sqlmodel import Session, select
from app.db.engine import engine
from app.db.models import Job, GenerationJob
from app.core.config import settings
import os
import shutil

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check database
    try:
        with Session(engine) as session:
            # Try a simple query
            statement = select(Job).limit(1)
            session.exec(statement)
            health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check disk space
    try:
        data_dir = "data"
        if os.path.exists(data_dir):
            total, used, free = shutil.disk_usage(data_dir)
            free_gb = free / (1024**3)
            health_status["checks"]["disk_space_gb"] = round(free_gb, 2)
            if free_gb < 0.1:  # Less than 100MB
                health_status["status"] = "degraded"
                health_status["checks"]["disk_space"] = "low"
            else:
                health_status["checks"]["disk_space"] = "ok"
        else:
            health_status["checks"]["disk_space"] = "data directory not found"
    except Exception as e:
        health_status["checks"]["disk_space"] = f"error: {str(e)}"
    
    # Check API keys
    api_keys_status = {}
    if settings.GOOGLE_API_KEY:
        api_keys_status["google"] = "configured"
    else:
        api_keys_status["google"] = "missing"
        health_status["status"] = "degraded"
    
    if settings.PEXELS_API_KEY:
        api_keys_status["pexels"] = "configured"
    else:
        api_keys_status["pexels"] = "missing"
        health_status["status"] = "degraded"
    
    health_status["checks"]["api_keys"] = api_keys_status
    
    return health_status

