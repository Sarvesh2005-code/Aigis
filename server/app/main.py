from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from app.db.engine import create_db_and_tables

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("startup", msg="Initializing Nexus Database...")
    create_db_and_tables()
    logger.info("startup", msg="Nexus Database Ready.")
    yield
    # Shutdown
    logger.info("shutdown", msg="Nexus Shutting Down...")

app = FastAPI(title="Aigis AI Core", lifespan=lifespan)

# CORS (Allow Frontend)
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "online", "system": "Nexus AI Core"}

from app.api import jobs
app.include_router(jobs.router, prefix="/api")
