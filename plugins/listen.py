"""Speech-to-text plugin for Krystal's ears using SpeechRecognition."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: SpeechRecognition not available. Install with: pip install SpeechRecognition")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available. Install with: pip install pyaudio")

NAME = "/listen"
DESCRIPTION = "Records microphone audio and converts it to text."


def run(query, **kwargs):
    """
    Listen to microphone and transcribe speech to text.
    
    Args:
        query: Ignored for this plugin
        **kwargs: Additional arguments (ignored)
    
    Returns:
        Transcribed text from microphone
    """
    _ = kwargs
    
    if not SPEECH_RECOGNITION_AVAILABLE or not PYAUDIO_AVAILABLE:
        return "Error: Speech recognition not available. Install with: pip install SpeechRecognition pyaudio"
    
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        print("Listening... (Speak now)")
        
        # Adjust for ambient noise
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Listen for audio
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        
        print("Processing speech...")
        
        # Recognize speech using Google's API
        text = recognizer.recognize_google(audio)
        
        if text and text.strip():
            return f"You said: {text}"
        else:
            return "No speech detected. Please try again."
            
    except sr.WaitTimeoutError:
        return "Listening timeout. No speech detected."
    except sr.UnknownValueError:
        return "Could not understand speech. Please try again."
    except sr.RequestError as e:
        return f"Speech recognition service error: {e}"
    except Exception as e:
        return f"Microphone error: {type(e).__name__}: {e}"
