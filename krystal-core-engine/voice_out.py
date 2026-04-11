"""Text-to-Speech module for Krystal's voice output using pyttsx3."""

from __future__ import annotations

import re
import threading
from typing import Optional

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: pyttsx3 not available. Install with: pip install pyttsx3")


class VoiceOutput:
    """Handles text-to-speech conversion in a separate daemon thread."""
    
    def __init__(self):
        self.engine = None
        self.is_available = False
        
        if not TTS_AVAILABLE:
            return
            
        try:
            self.engine = pyttsx3.init()
            # Set female voice
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > 1:
                # Usually index 1 is female on Windows systems
                self.engine.setProperty('voice', voices[1].id)
            self.is_available = True
        except Exception as e:
            print(f"Warning: Could not initialize TTS engine: {e}")
            self.is_available = False
    
    def _clean_text(self, text: str) -> str:
        """Remove markdown symbols and other formatting that shouldn't be spoken."""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'`(.*?)`', r'\1', text)        # `code`
        text = re.sub(r'#{1,6}\s*', '', text)        # # headers
        text = re.sub(r'#{1,6}\s*', '', text)        # # headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)   # ![alt](url)
        text = re.sub(r'\n+', ' ', text)              # newlines to spaces
        text = re.sub(r'\s+', ' ', text)              # multiple spaces
        
        return text.strip()
    
    def _speak_worker(self, text: str) -> None:
        """Worker function that runs in a separate thread."""
        if not self.is_available or not self.engine:
            return
            
        try:
            cleaned_text = self._clean_text(text)
            if cleaned_text:
                self.engine.say(cleaned_text)
                self.engine.runAndWait()
        except Exception as e:
            print(f"Warning: TTS error: {e}")
    
    def speak_text(self, text: str) -> None:
        """
        Speak text using a daemon thread to avoid blocking the main terminal.
        
        Args:
            text: The text to speak
        """
        if not self.is_available or not text or not text.strip():
            return
            
        # Start speaking in a daemon thread
        thread = threading.Thread(target=self._speak_worker, args=(text,), daemon=True)
        thread.start()


# Global instance for easy access
_voice_output: Optional[VoiceOutput] = None


def speak_text(text: str) -> None:
    """
    Global function to speak text using the voice output system.
    
    Args:
        text: The text to speak
    """
    global _voice_output
    
    if _voice_output is None:
        _voice_output = VoiceOutput()
    
    _voice_output.speak_text(text)


def initialize_voice() -> VoiceOutput:
    """
    Initialize the voice output system.
    
    Returns:
        The VoiceOutput instance
    """
    global _voice_output
    
    if _voice_output is None:
        _voice_output = VoiceOutput()
    
    return _voice_output
