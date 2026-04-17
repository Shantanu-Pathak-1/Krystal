import os
import sys
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import threading
import requests
import time
import gc
from enum import Enum
from pathlib import Path
import asyncio
import edge_tts

# Optional whisper import for better speech recognition
try:
    import whisper
    import numpy as np
    WHISPER_AVAILABLE = True
    WHISPER_NP = np
    print("[VOICE] Whisper imported successfully")
except ImportError as e:
    WHISPER_AVAILABLE = False
    WHISPER_NP = None
    print(f"[VOICE] Whisper import failed: {e}")
    print("[VOICE] Whisper not available, using Vosk only")

# Add parent directory to path for importing orchestrator modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import TaskMemory
from voice_out import speak_text

class VoiceState(Enum):
    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"

class KrystalVoiceSystem:
    def __init__(self):
        # Set model path to Krystal root directory
        script_dir = Path(__file__).parent.parent
        self.model_path = script_dir / "model"  # Points to d:\Krystal\model
        self.model_ready = False

        print(f"[VOICE] Initializing voice system...")
        print(f"[VOICE] Model path: {self.model_path}")
        print(f"[VOICE] Model exists: {os.path.exists(self.model_path)}")

        if not os.path.exists(self.model_path):
            print(f"[VOICE] ERROR: Vosk model not found at '{self.model_path}'")
            print("[VOICE] Please download a model from https://alphacephei.com/vosk/models")
        else:
            self.model_ready = True
            print(f"[VOICE] Model found successfully at {self.model_path}")

        # Load Whisper model for better speech recognition (if available)
        self.whisper_model = None
        if WHISPER_AVAILABLE:
            print(f"[VOICE] Loading Whisper model...")
            try:
                self.whisper_model = whisper.load_model("base")  # Use base model for balance of speed/accuracy
                print(f"[VOICE] Whisper model loaded successfully")
            except Exception as e:
                print(f"[VOICE] ERROR: Failed to load Whisper model: {e}")
                self.whisper_model = None
        else:
            print(f"[VOICE] Whisper not available, using Vosk only")
        
        self.q = queue.Queue()
        self.audio_buffer = []  # Buffer for Whisper transcription
        self.buffer_duration = 3.0  # Seconds of audio to collect for Whisper

        self.wake_words = [
            "hello krystal", "hey krystal", "wake up krystal",
            "krystal are you online", "krystal start listening",
            "krystal activate now", "krystal are you ready for input",
            "krystal are you ready", "hey krystal are you there",
            "krystal can we talk", "hey krystal i need you",
            "krystal come here", "krystal run voice protocol", "krystal boot up",
            # Phonetic variations that Vosk might recognize better
            "hello", "hey", "wake up", "are you online", "are you there",
            "can you hear me", "are you listening", "can we talk",
            "i need you", "come here", "activate", "start listening"
        ]
        
        self.state = VoiceState.PASSIVE
        self.last_active_timestamp = time.time()
        self.keep_alive_duration = 300  # 5 minutes
        
        # Audio Settings
        try:
            print(f"[VOICE] Querying audio input devices...")
            self.device_info = sd.query_devices(None, 'input')
            self.samplerate = int(self.device_info['default_samplerate'])
            print(f"[VOICE] Audio device found: {self.device_info['name']}")
            print(f"[VOICE] Sample rate: {self.samplerate} Hz")
        except Exception as e:
            print(f"[VOICE] ERROR: Audio input device not found: {e}")
            print(f"[VOICE] Falling back to default sample rate: 16000 Hz")
            self.samplerate = 16000

        # Start background monitor thread
        self.monitor_thread = threading.Thread(target=self.auto_sleep_monitor, daemon=True)
        self.monitor_thread.start()

    async def play_audio_cue(self, text: str):
        """Play a quick non-blocking audio cue using edge-tts."""
        try:
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            await communicate.save("temp_audio.mp3")
            # Play the audio file (non-blocking)
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load("temp_audio.mp3")
            pygame.mixer.music.play()
            # Clean up the temp file
            os.remove("temp_audio.mp3")
        except Exception as e:
            print(f"[VOICE] Audio cue error: {e}")

    def play_audio_cue_thread(self, text: str):
        """Run audio cue in a separate thread to avoid blocking."""
        try:
            asyncio.run(self.play_audio_cue(text))
        except Exception as e:
            print(f"[VOICE] Audio cue thread error: {e}")

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def auto_sleep_monitor(self):
        """Background thread to monitor activity and trigger auto-sleep."""
        while True:
            if self.state == VoiceState.ACTIVE:
                elapsed = time.time() - self.last_active_timestamp
                if elapsed > self.keep_alive_duration:
                    print(f"[VOICE] Auto-sleep triggered after {elapsed:.1f}s of inactivity")
                    self.transition_to_passive()
            time.sleep(10)  # Check every 10 seconds

    def transition_to_active(self):
        """Switch to ACTIVE state with greeting and UI update."""
        self.state = VoiceState.ACTIVE
        self.last_active_timestamp = time.time()
        self.notify_status("active")

        # Play immediate acoustic feedback
        print(f"[VOICE] Playing acoustic feedback cue...")
        audio_thread = threading.Thread(target=self.play_audio_cue_thread, args=("Yes?",))
        audio_thread.start()

        # Then speak the greeting
        self.speak("I'm here, Boss.")

    def transition_to_passive(self):
        """Switch to PASSIVE state with notification and UI update."""
        self.state = VoiceState.PASSIVE
        self.notify_status("passive")
        self.speak("Entering standby mode.")
        
        # 5-Minute Memory Wipe: Clear orchestrator task memory and free RAM
        try:
            task_memory = TaskMemory()
            task_memory.reset_memory()
            print("[VOICE] TaskMemory cleared - agent_memory.json wiped")
        except Exception as e:
            print(f"[VOICE] Error clearing TaskMemory: {e}")
        
        # Aggressive garbage collection to free RAM from dynamically loaded tools
        try:
            gc.collect()
            print("[VOICE] Garbage collection completed - freed RAM from dynamic tool imports")
        except Exception as e:
            print(f"[VOICE] Error during garbage collection: {e}")

    def notify_status(self, status):
        """Send status update to the backend API."""
        try:
            requests.post("http://localhost:8000/api/system/voice-status", 
                         json={"status": status}, timeout=1)
        except Exception as e:
            print(f"[VOICE] Failed to notify API: {e}")

    def listen_loop(self):
        if not self.model_ready:
            print("[VOICE] ERROR: Listener cannot start without a valid model.")
            return

        try:
            print(f"[VOICE] Loading Vosk model from {self.model_path}...")
            model = Model(str(self.model_path))
            print(f"[VOICE] Vosk model loaded successfully")
            # Use limited grammar for PASSIVE mode if possible, but Vosk handles it well even without
            rec = KaldiRecognizer(model, self.samplerate)
            print(f"[VOICE] Kaldi recognizer initialized with sample rate: {self.samplerate}")

            print(f"[VOICE] Starting audio input stream...")
            with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=None,
                                   dtype='int16', channels=1, callback=self.callback):
                print(f"[VOICE] Audio stream started successfully")
                print(f"[VOICE] Krystal Background Listener Active ({self.state.value} Mode)...")

                # Hybrid approach: Vosk for wake word detection, Whisper for accurate transcription
                while True:
                    data = self.q.get()

                    if self.state == VoiceState.PASSIVE:
                        # Use Vosk for fast wake word detection
                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            text = result.get("text", "").lower()

                            if text:
                                print(f"[VOICE] Recognized: {text}")

                            if any(ww in text for ww in self.wake_words):
                                print(f"[VOICE] Wake Word Detected: {text}")
                                self.transition_to_active()
                        else:
                            partial = json.loads(rec.PartialResult())
                            partial_text = partial.get("partial", "").lower()

                            if partial_text and len(partial_text) > 3:
                                print(f"[VOICE] Partial: {partial_text}")

                            if any(ww in partial_text for ww in self.wake_words):
                                print(f"[VOICE] Wake Word Detected (Partial): {partial_text}")
                                self.transition_to_active()
                    else:
                        # ACTIVE state: Collect audio for Whisper transcription
                        self.audio_buffer.append(data)

                        # Check if we have enough audio for Whisper (3 seconds)
                        if len(self.audio_buffer) >= int(self.buffer_duration * self.samplerate / 8000):
                            # Convert buffer to audio for Whisper
                            audio_data = b''.join(self.audio_buffer)

                            # Transcribe with Whisper (if available)
                            if self.whisper_model and WHISPER_NP:
                                try:
                                    audio_array = WHISPER_NP.frombuffer(audio_data, dtype=WHISPER_NP.int16).astype(WHISPER_NP.float32) / 32768.0
                                    result = self.whisper_model.transcribe(audio_array, fp16=False)
                                    text = result["text"].lower().strip()

                                    if text:
                                        print(f"[VOICE] Whisper Transcribed: {text}")
                                        self.handle_user_input(text)
                                except Exception as e:
                                    print(f"[VOICE] Whisper transcription error: {e}")
                                    # Fallback to Vosk
                                    if rec.AcceptWaveform(audio_data):
                                        vosk_result = json.loads(rec.Result())
                                        vosk_text = vosk_result.get("text", "").lower()
                                        if vosk_text:
                                            print(f"[VOICE] Vosk Fallback: {vosk_text}")
                                            self.handle_user_input(vosk_text)
                            else:
                                # Use Vosk directly if Whisper not available
                                if rec.AcceptWaveform(audio_data):
                                    vosk_result = json.loads(rec.Result())
                                    vosk_text = vosk_result.get("text", "").lower()
                                    if vosk_text:
                                        print(f"[VOICE] Vosk Recognized: {vosk_text}")
                                        self.handle_user_input(vosk_text)

                            # Clear buffer
                            self.audio_buffer = []

        except Exception as e:
            print(f"[VOICE] System Error: {e}")

    def handle_user_input(self, text):
        """Process user input in ACTIVE state."""
        print(f"[VOICE] User: {text}")

        # Post-processing to fix common misrecognitions
        text = self._fix_common_misrecognitions(text)
        print(f"[VOICE] Corrected: {text}")

        # Reset keep-alive timer on any active input, especially if "krystal" is mentioned
        self.last_active_timestamp = time.time()

        if "stop listening" in text or "goodbye" in text or "go to sleep" in text:
            self.transition_to_passive()
            return

        # Send to LLM Engine
        response = self.get_llm_response(text)
        self.speak(response)

        # Reset timer again after responding
        self.last_active_timestamp = time.time()

    def _fix_common_misrecognitions(self, text):
        """Fix common speech recognition errors, especially for Indian accent."""
        # Fix common misrecognitions
        corrections = {
            "daniel": "open",
            "been you": "for you",
            "you do": "you to",
            "can you open you do": "can you open youtube",
            "can you open your": "can you open youtube",
            "open your": "open youtube",
            "youtube": "youtube",
            "you tube": "youtube",
            "utube": "youtube",
        }

        corrected = text
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)

        return corrected

    def get_llm_response(self, text):
        try:
            res = requests.post("http://localhost:8000/api/chat", 
                              json={"message": text, "mode": "Agentic"}, timeout=15)
            return res.json().get("response", "I encountered an error processing that.")
        except Exception as e:
            print(f"[VOICE] LLM Error: {e}")
            return "I can't connect to my brain right now."

    def speak(self, text):
        """Neural TTS Output."""
        print(f"[VOICE] Krystal: {text}")
        try:
            speak_text(text)
        except Exception as e:
            print(f"[VOICE] Neural TTS Error: {e}")

if __name__ == "__main__":
    voice_system = KrystalVoiceSystem()
    voice_system.listen_loop()
