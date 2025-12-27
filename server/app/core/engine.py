import cv2
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip 
from moviepy.video.fx.crop import crop
from faster_whisper import WhisperModel
import structlog
import os
import datetime

logger = structlog.get_logger()

# Try to import mediapipe, but handle if it's not available
MEDIAPIPE_AVAILABLE = False
detector = None

try:
    import mediapipe as mp
    # Try different import methods for different mediapipe versions
    try:
        from mediapipe.python.solutions import face_detection as fd
        MEDIAPIPE_AVAILABLE = True
        mp_face_detection = fd
    except ImportError:
        try:
            mp_face_detection = mp.solutions.face_detection
            MEDIAPIPE_AVAILABLE = True
        except AttributeError:
            MEDIAPIPE_AVAILABLE = False
            logger.warning("mediapipe_import_failed", msg="Face detection will use center framing")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("mediapipe_not_installed", msg="Face detection will use center framing")

def format_timestamp(seconds: float):
    dt = datetime.datetime.utcfromtimestamp(seconds)
    return dt.strftime('%H:%M:%S,%f')[:-3]

class AigisEngine:
    def __init__(self):
        self.detector = None
        if MEDIAPIPE_AVAILABLE:
            try:
                self.detector = mp_face_detection.FaceDetection(
                    model_selection=1, 
                    min_detection_confidence=0.5
                )
                logger.info("mediapipe_initialized", msg="Face detection enabled")
            except Exception as e:
                logger.warning("mediapipe_init_failed", error=str(e))
                self.detector = None
        else:
            logger.info("mediapipe_unavailable", msg="Using center framing fallback")
        # Load local whisper model (tiny is fast on CPU)
        try:
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        except Exception as e:
            logger.error("whisper_load_failed", error=str(e))
            self.whisper_model = None

    def generate_srt(self, audio_path, srt_path):
        if not self.whisper_model:
            return False
        
        segments, info = self.whisper_model.transcribe(audio_path, beam_size=5)
        
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                text = segment.text.strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        return True

    def detect_face_center(self, frame):
        """
        Detects faces in a frame and returns the center X position as a ratio (0.0 to 1.0).
        Returns 0.5 (center) if no face is detected.
        """
        if not self.detector:
            # MediaPipe not available, return center
            return 0.5
        
        try:
            # Convert frame to RGB (MediaPipe requires RGB)
            # MediaPipe expects RGB, but OpenCV uses BGR, so we need to convert
            if len(frame.shape) == 3:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_frame = frame
            
            results = self.detector.process(rgb_frame)
            
            if results.detections and len(results.detections) > 0:
                # Get the first (largest) detection
                detection = results.detections[0]
                bbox = detection.location_data.relative_bounding_box
                
                # Calculate center X as ratio
                center_x = bbox.xmin + (bbox.width / 2)
                return max(0.0, min(1.0, center_x))  # Clamp between 0 and 1
            else:
                # No face detected, return center
                return 0.5
        except Exception as e:
            logger.warning("face_detection_failed", error=str(e))
            return 0.5  # Default to center on error

    def analyze_tracking(self, clip):
        """
        Scans the video to find the primary face center over time.
        Returns a sorted list of (t, center_x_ratio).
        """
        tracking_points = []
        # Analyze 1 frame every 0.5 seconds for speed
        duration = clip.duration
        step = 0.5 
        for t in np.arange(0, duration, step):
            frame = clip.get_frame(t)
            center_x = self.detect_face_center(frame)
            tracking_points.append((t, center_x))
        
        # Add the last frame
        tracking_points.append((duration, self.detect_face_center(clip.get_frame(duration-0.1))))
        return tracking_points

    def get_interpolated_center(self, t, tracking_points):
        """
        Returns smooth center_x_ratio for a given time t.
        Uses linear interpolation between tracking points.
        """
        times = [p[0] for p in tracking_points]
        centers = [p[1] for p in tracking_points]
        return np.interp(t, times, centers)

    def process_clip(self, input_path: str, output_path: str, duration: int = 60):
        logger.info("processing_clip", input=input_path)
        try:
            clip = VideoFileClip(input_path)
            final_duration = min(clip.duration, duration)
            subclip = clip.subclip(0, final_duration)

            # 1. Analyze tracking points (Dynamic "Camera Shift")
            logger.info("analyzing_faces", duration=final_duration)
            tracking_points = self.analyze_tracking(subclip)
            
            # 2. Define dynamic crop function
            def crop_region(t):
                w, h = subclip.size
                target_ratio = 9 / 16
                target_w = h * target_ratio
                
                # Get the center for this timestamp
                center_x_ratio = self.get_interpolated_center(t, tracking_points)
                center_x_pixel = center_x_ratio * w
                
                # Calculate coordinates
                x1 = center_x_pixel - (target_w / 2)
                x2 = center_x_pixel + (target_w / 2)
                
                # Bounds checking (clamping)
                if x1 < 0:
                    x1 = 0
                    x2 = target_w
                if x2 > w:
                    x2 = w
                    x1 = w - target_w
                    
                return x1, 0, x2, h

            # 3. Apply Dynamic Crop
            target_ratio = 9 / 16
            target_w = subclip.h * target_ratio
            
            cropped_clip = crop(subclip, x1=lambda t: crop_region(t)[0], y1=0, width=target_w, height=subclip.h)
            
            # Write video
            cropped_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None, preset="ultrafast")

            # 4. Generate Captions (SRT)
            if self.whisper_model:
                try:
                    # Extract audio for transcription
                    audio_filename = output_path.replace(".mp4", ".mp3")
                    srt_filename = output_path.replace(".mp4", ".srt")
                    
                    subclip.audio.write_audiofile(audio_filename, logger=None)
                    
                    self.generate_srt(audio_filename, srt_filename)
                    if os.path.exists(audio_filename):
                        os.remove(audio_filename) # Cleanup audio
                        
                except Exception as e:
                    logger.error("caption_generation_failed", error=str(e))
            
            clip.close()
            subclip.close()
            cropped_clip.close()
            return True

        except Exception as e:
            logger.error("processing_failed", error=str(e))
            raise e

ai_engine = AigisEngine()
