"""Premium Neural TTS module for Krystal's voice output using edge-tts."""

from __future__ import annotations

import re
import threading
import asyncio
import os
import time
import queue
from typing import Optional
from pathlib import Path

try:
    import edge_tts
    import pygame
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: edge-tts or pygame not available. Install with: pip install edge-tts pygame")


class VoiceOutput:
    """Handles neural text-to-speech conversion using a thread-safe worker."""
    
    def __init__(self):
        self.is_available = TTS_AVAILABLE
        self.voice = "en-US-AriaNeural"  # Premium female neural voice
        self.temp_dir = Path(__file__).parent.parent / "memory" / "voice_cache"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.audio_file = self.temp_dir / "speech_output.mp3"
        
        self.task_queue = queue.Queue()
        
        if self.is_available:
            try:
                pygame.mixer.init()
                # Start worker thread
                self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
                self.worker_thread.start()
            except Exception as e:
                print(f"Warning: Could not initialize pygame mixer: {e}")
                self.is_available = False
    
    def _clean_text(self, text: str) -> str:
        """Remove markdown symbols, emojis, and other formatting that shouldn't be spoken."""
        # Remove emojis
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
        text = re.sub(r'`(.*?)`', r'\1', text)        # `code`
        text = re.sub(r'#{1,6}\s*', '', text)        # # headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)   # ![alt](url)
        text = re.sub(r'https?://[^\s]+', '', text)   # standalone URLs
        text = re.sub(r'\n+', ' ', text)              # newlines to spaces
        text = re.sub(r'\s+', ' ', text)              # multiple spaces
        
        return text.strip()

    async def _generate_audio(self, text: str) -> bool:
        """Generate audio file using edge-tts."""
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(str(self.audio_file))
            return True
        except Exception as e:
            print(f"[VOICE] Error generating audio: {e}")
            return False

    def _play_audio(self):
        """Play generated audio using pygame."""
        try:
            # Unload before loading new one to avoid file access issues
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            pygame.mixer.music.load(str(self.audio_file))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[VOICE] Error playing audio: {e}")

    def _worker_loop(self) -> None:
        """Sequential worker loop to process TTS tasks one by one."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                text = self.task_queue.get()
                if text is None: break # Shutdown signal
                
                cleaned_text = self._clean_text(text)
                if cleaned_text:
                    success = loop.run_until_complete(self._generate_audio(cleaned_text))
                    if success:
                        self._play_audio()
                
                self.task_queue.task_done()
            except Exception as e:
                print(f"[VOICE] Worker error: {e}")
        
        loop.close()
    
    def speak_text(self, text: str) -> None:
        """
        Add text to the speech queue.
        """
        if not self.is_available or not text or not text.strip():
            return
            
        self.task_queue.put(text)


# Global instance
_voice_output: Optional[VoiceOutput] = None


def speak_text(text: str) -> None:
    """Global function to speak text."""
    global _voice_output
    if _voice_output is None:
        _voice_output = VoiceOutput()
    _voice_output.speak_text(text)
