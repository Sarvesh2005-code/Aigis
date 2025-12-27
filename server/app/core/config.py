import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    GOOGLE_API_KEY: Optional[str] = None
    PEXELS_API_KEY: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    RENDER_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use GOOGLE_API_KEY as fallback for YOUTUBE_API_KEY
        if not self.YOUTUBE_API_KEY and self.GOOGLE_API_KEY:
            self.YOUTUBE_API_KEY = self.GOOGLE_API_KEY
    
    def get_allowed_origins(self) -> list:
        """Get list of allowed CORS origins."""
        origins = self.ALLOWED_ORIGINS.split(",")
        origins = [o.strip() for o in origins if o.strip()]
        # Add Render URL if available
        if self.RENDER_URL:
            origins.append(self.RENDER_URL)
        return origins
    
    def validate_required(self):
        """Validate that required API keys are present."""
        errors = []
        if not self.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required for script generation")
        if not self.PEXELS_API_KEY:
            errors.append("PEXELS_API_KEY is required for video fetching")
        return errors

settings = Settings()
