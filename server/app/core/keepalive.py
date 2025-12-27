import asyncio
import httpx
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings

logger = structlog.get_logger()

scheduler = AsyncIOScheduler()
is_running = False

async def ping_health():
    """Ping the health endpoint to keep the service alive."""
    try:
        # Get the service URL from environment or use localhost
        base_url = settings.RENDER_URL or "http://localhost:8000"
        if not base_url.startswith("http"):
            base_url = f"http://{base_url}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                logger.info("keepalive_success", status=response.status_code)
            else:
                logger.warning("keepalive_warning", status=response.status_code)
    except Exception as e:
        logger.error("keepalive_failed", error=str(e))

def start_keepalive():
    """Start the keep-alive scheduler."""
    global is_running
    if is_running:
        logger.warning("keepalive_already_running")
        return
    
    # Schedule ping every 14 minutes (840 seconds)
    scheduler.add_job(
        ping_health,
        "interval",
        seconds=840,  # 14 minutes
        id="keepalive",
        replace_existing=True
    )
    scheduler.start()
    is_running = True
    logger.info("keepalive_started", interval_seconds=840)

def stop_keepalive():
    """Stop the keep-alive scheduler."""
    global is_running
    if scheduler.running:
        scheduler.shutdown()
    is_running = False
    logger.info("keepalive_stopped")

