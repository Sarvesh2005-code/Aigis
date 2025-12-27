import requests
import random
import os
import uuid
from app.core.config import settings
import structlog

logger = structlog.get_logger()

TEMP_DIR = "data/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

class VisualsFetcher:
    def __init__(self):
        self.api_key = settings.PEXELS_API_KEY
        self.base_url = "https://api.pexels.com/videos/search"
    
    def _download_video(self, url: str, output_path: str) -> bool:
        """Download a video from URL to local file."""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("video_downloaded", path=output_path)
            return True
        except Exception as e:
            logger.error("video_download_failed", url=url, error=str(e))
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
    
    def fetch_videos(self, queries: list, min_duration=5):
        """
        Fetches vertical videos for the given queries and downloads them.
        Returns a list of local file paths.
        """
        if not self.api_key:
            logger.error("pexels_key_missing")
            return []

        headers = {"Authorization": self.api_key}
        video_paths = []
        
        for q in queries:
            try:
                params = {
                    "query": q,
                    "per_page": 5,
                    "orientation": "portrait"
                }
                response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "videos" in data and len(data["videos"]) > 0:
                    # Pick a random best quality link
                    video = random.choice(data["videos"])
                    # Find a link suitable for mobile
                    files = video.get("video_files", [])
                    if not files:
                        continue
                    # Sort by width (closest to 1080)
                    best_file = sorted(files, key=lambda x: abs(x.get("width", 1080) - 1080))[0]
                    video_url = best_file.get("link")
                    
                    if video_url:
                        # Download to local file
                        unique_id = str(uuid.uuid4())
                        file_ext = "mp4"  # Pexels videos are typically mp4
                        output_path = os.path.join(TEMP_DIR, f"pexels_{unique_id}.{file_ext}")
                        
                        if self._download_video(video_url, output_path):
                            video_paths.append(output_path)
            except Exception as e:
                logger.error("pexels_fetch_failed", query=q, error=str(e))
        
        return video_paths
