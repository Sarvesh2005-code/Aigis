import structlog
from moviepy.editor import VideoFileClip
from faster_whisper import WhisperModel
import os

logger = structlog.get_logger()

class ViralityScorer:
    """
    Scores video clips for virality potential based on various factors.
    Returns a score from 0-100.
    """
    
    def __init__(self):
        try:
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        except Exception as e:
            logger.warning("whisper_load_failed_for_scoring", error=str(e))
            self.whisper_model = None
    
    def score_clip(self, video_path: str) -> float:
        """
        Score a video clip for virality potential.
        
        Factors considered:
        - Hook quality (first 3 seconds)
        - Pacing (words per second)
        - Caption presence
        - Video length (optimal 15-60 seconds)
        - Engagement signals
        """
        if not os.path.exists(video_path):
            return 0.0
        
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            scores = {}
            
            # 1. Length score (optimal: 15-60 seconds for shorts)
            if 15 <= duration <= 60:
                scores["length"] = 25
            elif 10 <= duration < 15 or 60 < duration <= 90:
                scores["length"] = 15
            else:
                scores["length"] = 5
            
            # 2. Hook score (analyze first 3 seconds)
            hook_score = self._analyze_hook(clip)
            scores["hook"] = hook_score * 30  # 30 points max
            
            # 3. Pacing score (words per second)
            pacing_score = self._analyze_pacing(clip)
            scores["pacing"] = pacing_score * 20  # 20 points max
            
            # 4. Caption/transcription score
            caption_score = self._analyze_captions(video_path)
            scores["captions"] = caption_score * 15  # 15 points max
            
            # 5. Visual quality (basic check)
            visual_score = self._analyze_visual_quality(clip)
            scores["visual"] = visual_score * 10  # 10 points max
            
            total_score = sum(scores.values())
            clip.close()
            
            logger.info("virality_scored", video=video_path, score=total_score, breakdown=scores)
            return min(100.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error("virality_scoring_failed", error=str(e))
            return 50.0  # Default middle score on error
    
    def _analyze_hook(self, clip) -> float:
        """Analyze the first 3 seconds for hook quality."""
        try:
            hook_duration = min(3.0, clip.duration)
            hook_clip = clip.subclip(0, hook_duration)
            
            # Extract audio for analysis
            if hook_clip.audio:
                audio_path = "data/temp/hook_audio_temp.wav"
                os.makedirs("data/temp", exist_ok=True)
                hook_clip.audio.write_audiofile(audio_path, logger=None)
                
                if self.whisper_model and os.path.exists(audio_path):
                    segments, _ = self.whisper_model.transcribe(audio_path, beam_size=1)
                    text = " ".join([s.text for s in segments]).strip()
                    
                    # Cleanup
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                    
                    # Score based on hook characteristics
                    hook_indicators = ["!", "?", "watch", "you", "this", "amazing", "incredible", "secret", "shocking"]
                    score = 0.5  # Base score
                    
                    if len(text) > 10:  # Has substantial content
                        score += 0.2
                    if any(indicator in text.lower() for indicator in hook_indicators):
                        score += 0.3
                    
                    hook_clip.close()
                    return min(1.0, score)
            
            hook_clip.close()
            return 0.5  # Default score
        except Exception as e:
            logger.warning("hook_analysis_failed", error=str(e))
            return 0.5
    
    def _analyze_pacing(self, clip) -> float:
        """Analyze pacing (words per second). Optimal: 2-4 WPS."""
        try:
            if not clip.audio or not self.whisper_model:
                return 0.5
            
            audio_path = "data/temp/pacing_audio_temp.wav"
            os.makedirs("data/temp", exist_ok=True)
            clip.audio.write_audiofile(audio_path, logger=None)
            
            if os.path.exists(audio_path):
                segments, _ = self.whisper_model.transcribe(audio_path, beam_size=1)
                text = " ".join([s.text for s in segments])
                word_count = len(text.split())
                duration = clip.duration
                
                # Cleanup
                try:
                    os.remove(audio_path)
                except:
                    pass
                
                if duration > 0:
                    wps = word_count / duration
                    # Optimal: 2-4 words per second
                    if 2 <= wps <= 4:
                        return 1.0
                    elif 1.5 <= wps < 2 or 4 < wps <= 5:
                        return 0.7
                    else:
                        return 0.4
            
            return 0.5
        except Exception as e:
            logger.warning("pacing_analysis_failed", error=str(e))
            return 0.5
    
    def _analyze_captions(self, video_path: str) -> float:
        """Check if captions/subtitles exist."""
        srt_path = video_path.replace(".mp4", ".srt")
        if os.path.exists(srt_path):
            return 1.0
        return 0.3  # Partial score if no captions
    
    def _analyze_visual_quality(self, clip) -> float:
        """Basic visual quality check."""
        try:
            # Check resolution
            w, h = clip.size
            if min(w, h) >= 720:  # At least 720p
                return 1.0
            elif min(w, h) >= 480:
                return 0.7
            else:
                return 0.4
        except:
            return 0.5

