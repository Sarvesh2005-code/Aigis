import os
import yt_dlp
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
import uuid

logger = structlog.get_logger()

TEMP_DIR = "data/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'{TEMP_DIR}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def download(self, url: str) -> str:
        unique_id = str(uuid.uuid4())
        # Override template to use unique ID to avoid collisions
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = f'{TEMP_DIR}/{unique_id}.%(ext)s'

        logger.info("download_started", url=url)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info("download_complete", filename=filename)
                return filename
        except Exception as e:
            logger.error("download_failed", error=str(e))
            raise e

downloader = VideoDownloader()
