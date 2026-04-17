"""Webcam plugin for Krystal's eyes using OpenCV."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

NAME = "/webcam"
DESCRIPTION = "Takes a picture using physical webcam and analyzes it."


def run(query, **kwargs):
    """
    Capture image from webcam and analyze it.
    
    Args:
        query: Ignored for this plugin
        **kwargs: Additional arguments (ignored)
    
    Returns:
        Visual analysis of captured image
    """
    _ = kwargs
    
    # Dynamic import: Only load OpenCV when this tool is actually called
    try:
        import cv2
    except ImportError:
        return "Error: OpenCV not available. Install with: pip install opencv-python"
    
    try:
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return "Error: Could not access webcam. Please check camera permissions."
        
        print("Capturing image from webcam...")
        
        # Read a single frame
        ret, frame = cap.read()
        
        if not ret or frame is None:
            cap.release()
            return "Error: Could not capture frame from webcam."
        
        # Get VisionProcessor for analysis
        root = Path(__file__).resolve().parent.parent
        engine_dir = root / "krystal-core-engine"
        if str(engine_dir) not in sys.path:
            sys.path.insert(0, str(engine_dir))
        
        from api_router import KeyManager
        from vision_processor import VisionProcessor
        
        env_file = root / ".env"
        keys = KeyManager(env_path=env_file if env_file.is_file() else None)
        vp = VisionProcessor(keys)
        
        # First, save temporarily for categorization
        temp_dir = root / "memory" / "vision_cache"
        temp_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = temp_dir / f"temp_webcam_{timestamp}.png"
        
        # Save temporary image for categorization
        success = cv2.imwrite(str(temp_path), frame)
        if not success:
            cap.release()
            return f"Error: Could not save temporary webcam image"
        
        # Categorize the image
        categorization_prompt = """Is this image purely technical/work (like code, IDE, terminal) or is it personal/memorable (a face, a nice view, a personal chat)? 
        Respond with ONLY one word: "technical" or "memorable"."""
        
        categorization = vp.analyze_image(temp_path, prompt=categorization_prompt).strip().lower()
        is_memorable = "memorable" in categorization
        
        # Determine final save location based on categorization
        if is_memorable:
            # Save to diary_photos for memorable images
            diary_dir = root / "memory" / "diary_photos"
            diary_dir.mkdir(parents=True, exist_ok=True)
            image_path = diary_dir / f"memorable_{timestamp}.png"
            print(f"Memorable photo saved to diary: {image_path}")
        else:
            # Save to regular cache for technical images
            cache_dir = root / "memory" / "vision_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            image_path = cache_dir / f"webcam_capture_{timestamp}.png"
        
        # Move/rename to final location
        temp_path.rename(image_path)
        cap.release()
        
        print(f"Webcam image saved: {image_path}")
        
        # Analyze the captured image with context
        analysis_prompt = "What do you see in front of you?"
        analysis = vp.analyze_image(image_path, prompt=analysis_prompt)
        
        result = f"Webcam Analysis:\n\n{analysis}"
        if is_memorable:
            result += f"\n\n[This image was saved as memorable in the diary]"
        
        return result
        
    except Exception as e:
        return f"Webcam error: {type(e).__name__}: {e}"
