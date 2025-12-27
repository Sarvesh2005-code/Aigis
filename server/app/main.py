from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import structlog
import os
import asyncio
from app.db.engine import create_db_and_tables
from app.core.config import settings
from app.core.keepalive import start_keepalive, stop_keepalive

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("startup", msg="Initializing Aigis...")
    
    # Validate configuration
    config_errors = settings.validate_required()
    if config_errors:
        logger.warning("config_warnings", errors=config_errors)
    
    # Initialize database
    logger.info("startup", msg="Initializing Database...")
    create_db_and_tables()
    logger.info("startup", msg="Database Ready.")
    
    # Start keep-alive service
    logger.info("startup", msg="Starting keep-alive service...")
    start_keepalive()
    
    # Start job queue worker
    logger.info("startup", msg="Starting job queue worker...")
    from app.core.queue import job_queue
    asyncio.create_task(job_queue.worker())
    
    logger.info("startup", msg="Aigis Ready.")
    yield
    
    # Shutdown
    logger.info("shutdown", msg="Shutting down...")
    stop_keepalive()
    logger.info("shutdown", msg="Aigis Shut Down.")

app = FastAPI(title="Aigis AI Core", lifespan=lifespan)

# CORS (Allow Frontend)
origins = settings.get_allowed_origins()
# Add common localhost variants
origins.extend([
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://localhost:3000",
    "http://localhost:3001"
])
# Remove duplicates
origins = list(set(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "online", "system": "Aigis AI Core"}

from app.api import jobs
from app.api import generation
from app.api import health

app.include_router(jobs.router, prefix="/api")
app.include_router(generation.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# Serve generated outputs
os.makedirs("data/outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="data/outputs"), name="outputs")

# Serve static Next.js build files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "client", "out")
if os.path.exists(static_dir):
    # Serve static files
    app.mount("/static", StaticFiles(directory=os.path.join(static_dir, "_next", "static")), name="static")
    
    # Serve SPA - catch all routes and serve index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't serve API routes or outputs as static
        if full_path.startswith("api/") or full_path.startswith("outputs/"):
            return {"error": "Not found"}, 404
        
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not built"}, 404
