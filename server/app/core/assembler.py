from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
import structlog
import os
import random

logger = structlog.get_logger()

class VideoAssembler:
    def assemble(self, video_paths, audio_path, output_path, subtitles=[]):
        try:
            # Load Audio
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            
            # Load Videos
            clips = []
            current_time = 0
            
            # Loop video clips to match audio duration
            while current_time < duration:
                for v_path in video_paths:
                    if current_time >= duration: break
                    
                    clip = VideoFileClip(v_path)
                    # Resize to vertical 9:16 if needed (simple crop/resize)
                    clip = clip.resize(height=1920)
                    if clip.w > 1080:
                         clip = clip.crop(x1=(clip.w/2 - 540), width=1080, height=1920)
                    
                    # Cut clip to max 4 seconds or remaining duration
                    clip_dur = min(4, clip.duration, duration - current_time)
                    sub = clip.subclip(0, clip_dur)
                    clips.append(sub)
                    current_time += clip_dur
            
            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.set_audio(audio)
            
            # Add simple subtitles (Overlay text) - Requires ImageMagick
            # Skipping complex subtitles for now to ensure stability
            
            final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
            
            # Cleanup
            final_video.close()
            audio.close()
            for clip in clips:
                clip.close()
            
            return True
            
        except Exception as e:
            logger.error("assembly_failed", error=str(e))
            # Cleanup on error
            try:
                for clip in clips:
                    clip.close()
                if 'audio' in locals():
                    audio.close()
            except:
                pass
            raise e
