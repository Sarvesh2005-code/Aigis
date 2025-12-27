import edge_tts
import asyncio
import structlog

logger = structlog.get_logger()

class AudioGenerator:
    async def generate_audio(self, text: str, output_path: str, voice="en-US-ChristopherNeural"):
        """
        Generates TTS audio using free Edge-TTS.
        """
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            return True
        except Exception as e:
            logger.error("tts_failed", error=str(e))
            return False
