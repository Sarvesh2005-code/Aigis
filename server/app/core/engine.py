import cv2
import mediapipe as mp
import numpy as np
from moviepy.editor import VideoFileClip 
from moviepy.video.fx.all import crop
import structlog

logger = structlog.get_logger()

class AIEngine:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.detector = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    def detect_face_center(self, frame):
        """Returns the X coordinate (0.0 to 1.0) of the primary face center."""
        height, width, _ = frame.shape
        results = self.detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if results.detections:
            # Logic: Find the biggest face
            primary_face = max(results.detections, key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height)
            box = primary_face.location_data.relative_bounding_box
            center_x = box.xmin + (box.width / 2)
            return center_x
        return 0.5 # Default to center

    def process_clip(self, input_path: str, output_path: str, duration: int = 60):
        logger.info("processing_clip", input=input_path)
        try:
            clip = VideoFileClip(input_path)
            # Take a 60s slice (just the beginning for MVP)
            # In production, we'd find "interesting" parts.
            final_duration = min(clip.duration, duration)
            subclip = clip.subclip(0, final_duration)

            # Analyze a frame in the middle to find the crop center
            # A better approach runs this dynamically, but static crop is safer for v1
            mid_frame = subclip.get_frame(final_duration / 2)
            center_x_ratio = self.detect_face_center(mid_frame)
            
            # Application of 9:16 Crop
            w, h = subclip.size
            target_ratio = 9 / 16
            
            # Target width based on height
            target_w = h * target_ratio
            
            # Calculate x1, x2 ensuring we stay within bounds
            center_x_pixel = center_x_ratio * w
            x1 = center_x_pixel - (target_w / 2)
            x2 = center_x_pixel + (target_w / 2)
            
            if x1 < 0:
                x1 = 0
                x2 = target_w
            if x2 > w:
                x2 = w
                x1 = w - target_w
                
            # Use the imported crop function
            cropped_clip = crop(subclip, x1=x1, y1=0, x2=x2, y2=h)
            cropped_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger=None)
            
            clip.close()
            subclip.close()
            cropped_clip.close()
            return True

        except Exception as e:
            logger.error("processing_failed", error=str(e))
            raise e

ai_engine = AIEngine()
