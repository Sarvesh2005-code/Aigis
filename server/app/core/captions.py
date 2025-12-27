import structlog
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from faster_whisper import WhisperModel
import os

logger = structlog.get_logger()

class CaptionGenerator:
    """Generate animated captions for videos."""
    
    def __init__(self):
        try:
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        except Exception as e:
            logger.warning("whisper_load_failed_for_captions", error=str(e))
            self.whisper_model = None
    
    def generate_animated_captions(self, video_path: str, output_path: str, style: dict = None) -> bool:
        """
        Generate animated captions overlay on video.
        
        Args:
            video_path: Input video file
            output_path: Output video file with captions
            style: Caption style options (font, color, size, position)
        """
        if not self.whisper_model:
            logger.error("whisper_not_available")
            return False
        
        try:
            clip = VideoFileClip(video_path)
            
            # Extract audio for transcription
            if not clip.audio:
                logger.error("no_audio_in_video")
                clip.close()
                return False
            
            audio_path = "data/temp/caption_audio_temp.wav"
            os.makedirs("data/temp", exist_ok=True)
            clip.audio.write_audiofile(audio_path, logger=None)
            
            # Transcribe with word-level timestamps
            segments, _ = self.whisper_model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=True
            )
            
            # Cleanup audio
            try:
                os.remove(audio_path)
            except:
                pass
            
            # Default style
            default_style = {
                "fontsize": 60,
                "color": "white",
                "font": "Arial-Bold",
                "stroke_color": "black",
                "stroke_width": 2,
                "position": ("center", "bottom"),
                "method": "caption"
            }
            if style:
                default_style.update(style)
            
            # Create text clips for each word
            text_clips = []
            for segment in segments:
                for word_info in segment.words:
                    word = word_info.word.strip()
                    if not word:
                        continue
                    
                    start = word_info.start
                    end = word_info.end
                    
                    # Create text clip
                    try:
                        txt_clip = TextClip(
                            word,
                            fontsize=default_style["fontsize"],
                            color=default_style["color"],
                            font=default_style.get("font", "Arial-Bold"),
                            stroke_color=default_style.get("stroke_color", "black"),
                            stroke_width=default_style.get("stroke_width", 2),
                            method=default_style.get("method", "caption")
                        ).set_position(
                            default_style.get("position", ("center", "bottom")),
                            relative=True
                        ).set_start(start).set_duration(end - start)
                        
                        text_clips.append(txt_clip)
                    except Exception as e:
                        logger.warning("text_clip_creation_failed", word=word, error=str(e))
                        continue
            
            if not text_clips:
                logger.warning("no_captions_generated")
                clip.close()
                return False
            
            # Composite video with captions
            final_video = CompositeVideoClip([clip] + text_clips)
            
            # Write output
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=24,
                logger=None
            )
            
            # Cleanup
            clip.close()
            final_video.close()
            for txt_clip in text_clips:
                txt_clip.close()
            
            logger.info("animated_captions_generated", output=output_path)
            return True
            
        except Exception as e:
            logger.error("caption_generation_failed", error=str(e))
            return False
    
    def generate_srt(self, video_path: str, srt_path: str) -> bool:
        """Generate SRT subtitle file from video."""
        if not self.whisper_model:
            return False
        
        try:
            clip = VideoFileClip(video_path)
            if not clip.audio:
                clip.close()
                return False
            
            audio_path = "data/temp/srt_audio_temp.wav"
            os.makedirs("data/temp", exist_ok=True)
            clip.audio.write_audiofile(audio_path, logger=None)
            clip.close()
            
            segments, _ = self.whisper_model.transcribe(audio_path, beam_size=5)
            
            # Write SRT file
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(segments, start=1):
                    start_time = self._format_timestamp(segment.start)
                    end_time = self._format_timestamp(segment.end)
                    text = segment.text.strip()
                    f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
            
            # Cleanup
            try:
                os.remove(audio_path)
            except:
                pass
            
            return True
        except Exception as e:
            logger.error("srt_generation_failed", error=str(e))
            return False
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format."""
        import datetime
        dt = datetime.datetime.utcfromtimestamp(seconds)
        return dt.strftime('%H:%M:%S,%f')[:-3]

