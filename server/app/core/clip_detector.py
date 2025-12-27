import structlog
from moviepy.editor import VideoFileClip
from faster_whisper import WhisperModel
import numpy as np
import os

logger = structlog.get_logger()

class ClipDetector:
    """
    Intelligently detects the best moments/clips from a long video.
    Similar to Opus Clip's clip detection feature.
    """
    
    def __init__(self):
        try:
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        except Exception as e:
            logger.warning("whisper_load_failed_for_detection", error=str(e))
            self.whisper_model = None
    
    def detect_best_clips(self, video_path: str, max_clips: int = 5, min_duration: float = 15.0, max_duration: float = 60.0) -> list:
        """
        Detect the best clips from a video.
        
        Returns:
            List of dicts with keys: start_time, end_time, score, reason
        """
        if not os.path.exists(video_path):
            return []
        
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            if duration < min_duration:
                clip.close()
                return [{"start_time": 0, "end_time": duration, "score": 50, "reason": "Video too short"}]
            
            # Analyze video for engagement points
            engagement_points = self._analyze_engagement(clip)
            
            # Find best segments
            best_clips = self._find_best_segments(engagement_points, duration, min_duration, max_duration, max_clips)
            
            clip.close()
            return best_clips
            
        except Exception as e:
            logger.error("clip_detection_failed", error=str(e))
            return []
    
    def _analyze_engagement(self, clip) -> list:
        """Analyze video for engagement points (speaker changes, emotion, pacing)."""
        engagement_points = []
        
        try:
            # Extract audio for analysis
            if not clip.audio:
                # If no audio, sample frames evenly
                duration = clip.duration
                for t in np.arange(0, duration, 10):  # Every 10 seconds
                    engagement_points.append({
                        "time": t,
                        "score": 50,  # Default score
                        "reason": "no_audio"
                    })
                return engagement_points
            
            audio_path = "data/temp/engagement_audio_temp.wav"
            os.makedirs("data/temp", exist_ok=True)
            clip.audio.write_audiofile(audio_path, logger=None)
            
            if not self.whisper_model or not os.path.exists(audio_path):
                clip.close()
                return engagement_points
            
            # Transcribe with timestamps
            segments, _ = self.whisper_model.transcribe(audio_path, beam_size=5)
            
            # Analyze segments for engagement
            for segment in segments:
                score = 50  # Base score
                reasons = []
                
                # Check for questions (high engagement)
                if "?" in segment.text:
                    score += 20
                    reasons.append("question")
                
                # Check for exclamations
                if "!" in segment.text:
                    score += 15
                    reasons.append("exclamation")
                
                # Check for key engagement words
                engagement_words = ["you", "this", "watch", "amazing", "incredible", "secret", "shocking", "important"]
                if any(word in segment.text.lower() for word in engagement_words):
                    score += 10
                    reasons.append("engagement_words")
                
                # Check segment length (optimal: 5-15 seconds)
                seg_duration = segment.end - segment.start
                if 5 <= seg_duration <= 15:
                    score += 10
                    reasons.append("optimal_length")
                
                engagement_points.append({
                    "time": segment.start,
                    "score": min(100, score),
                    "reason": "_".join(reasons) if reasons else "normal",
                    "text": segment.text[:50]  # First 50 chars
                })
            
            # Cleanup
            try:
                os.remove(audio_path)
            except:
                pass
            
        except Exception as e:
            logger.warning("engagement_analysis_failed", error=str(e))
        
        return engagement_points
    
    def _find_best_segments(self, engagement_points: list, total_duration: float, 
                           min_duration: float, max_duration: float, max_clips: int) -> list:
        """Find the best segments based on engagement scores."""
        if not engagement_points:
            # Default: return evenly spaced clips
            clips = []
            clip_duration = min(max_duration, total_duration / max_clips)
            for i in range(max_clips):
                start = i * clip_duration
                end = min(start + clip_duration, total_duration)
                if end - start >= min_duration:
                    clips.append({
                        "start_time": start,
                        "end_time": end,
                        "score": 50,
                        "reason": "evenly_spaced"
                    })
            return clips[:max_clips]
        
        # Sort by score
        engagement_points.sort(key=lambda x: x["score"], reverse=True)
        
        clips = []
        used_times = []
        
        for point in engagement_points[:max_clips * 3]:  # Consider top candidates
            start_time = max(0, point["time"] - (min_duration / 2))
            end_time = min(total_duration, start_time + min_duration)
            
            # Adjust to max_duration if needed
            if end_time - start_time > max_duration:
                end_time = start_time + max_duration
            
            # Check for overlaps
            overlap = False
            for used_start, used_end in used_times:
                if not (end_time <= used_start or start_time >= used_end):
                    overlap = True
                    break
            
            if not overlap and end_time - start_time >= min_duration:
                clips.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "score": point["score"],
                    "reason": point.get("reason", "high_engagement")
                })
                used_times.append((start_time, end_time))
                
                if len(clips) >= max_clips:
                    break
        
        # If we don't have enough clips, fill with evenly spaced ones
        if len(clips) < max_clips:
            remaining = max_clips - len(clips)
            clip_duration = min(max_duration, total_duration / (remaining + 1))
            for i in range(remaining):
                start = (i + 1) * clip_duration
                end = min(start + clip_duration, total_duration)
                if end - start >= min_duration:
                    clips.append({
                        "start_time": start,
                        "end_time": end,
                        "score": 40,
                        "reason": "fallback"
                    })
        
        return sorted(clips, key=lambda x: x["score"], reverse=True)[:max_clips]

