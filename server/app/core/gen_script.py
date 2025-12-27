import google.generativeai as genai
from app.core.config import settings
import json
import structlog

logger = structlog.get_logger()

# Configure Gemini
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)

class ScriptGenerator:
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model, trying different model names."""
        if not settings.GOOGLE_API_KEY:
            logger.warning("no_google_api_key", msg="Script generation will fail")
            return
        
        # Try different model names in order of preference
        model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'models/gemini-1.5-flash']
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info("gemini_model_initialized", model=model_name)
                return
            except Exception as e:
                logger.debug("model_init_failed", model=model_name, error=str(e))
                continue
        
        # Last resort: try to list and use any available model
        try:
            models = genai.list_models()
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1]
                    self.model = genai.GenerativeModel(model_name)
                    logger.info("gemini_model_fallback", model=model_name)
                    return
        except Exception as e:
            logger.error("gemini_model_list_failed", error=str(e))
        
        logger.error("no_gemini_model_available", msg="Script generation will fail")

    async def generate_script(self, topic: str):
        if not self.model:
            raise Exception("Gemini model not initialized. Check GOOGLE_API_KEY and model availability.")
        
        prompt = f"""
        You are a viral YouTube Shorts scriptwriter. Create a 30-40 second engaging script about: "{topic}".
        
        Output STRICT JSON format with these keys:
        - "title": A viral title.
        - "description": A short video description with hashtags.
        - "script": The spoken script text.
        - "keywords": Array of 5 visual search terms for stock footage (e.g. ["futuristic city", "ai robot"]).
        - "sentences": Array of strings, splitting the script into sentence-level chunks for timing.

        Do not output markdown code blocks. Just the raw JSON string.
        """
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw_text)
            return data
        except Exception as e:
            logger.error("script_generation_failed", error=str(e))
            raise e
