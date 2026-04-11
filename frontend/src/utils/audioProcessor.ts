// Audio processing utilities for real-time amplitude detection and lip sync

export class AudioProcessor {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private source: MediaElementAudioSourceNode | null = null;
  private amplitudeCallback: ((amplitude: number) => void) | null = null;
  private isAnalyzing: boolean = false;
  private animationId: number | null = null;

  constructor() {
    this.initializeAudioContext();
  }

  private initializeAudioContext() {
    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;
    } catch (error) {
      console.error('Failed to initialize AudioContext:', error);
    }
  }

  public connectAudioElement(audioElement: HTMLAudioElement, amplitudeCallback: (amplitude: number) => void) {
    if (!this.audioContext || !this.analyser) {
      console.error('AudioContext not initialized');
      return;
    }

    this.amplitudeCallback = amplitudeCallback;

    // Create source from audio element
    try {
      this.source = this.audioContext.createMediaElementSource(audioElement);
      this.source.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
    } catch (error) {
      console.error('Failed to connect audio element:', error);
    }
  }

  public startAnalysis() {
    if (!this.analyser || this.isAnalyzing) return;

    this.isAnalyzing = true;
    this.analyzeAmplitude();
  }

  public stopAnalysis() {
    this.isAnalyzing = false;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  private analyzeAmplitude() {
    if (!this.isAnalyzing || !this.analyser) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.analyser.getByteFrequencyData(dataArray);

    // Calculate RMS (Root Mean Square) for amplitude
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i] * dataArray[i];
    }
    const rms = Math.sqrt(sum / bufferLength);
    const amplitude = rms / 255; // Normalize to 0-1 range

    // Apply smoothing and threshold
    const smoothedAmplitude = this.smoothAmplitude(amplitude);
    const thresholdedAmplitude = smoothedAmplitude > 0.05 ? smoothedAmplitude : 0;

    if (this.amplitudeCallback) {
      this.amplitudeCallback(thresholdedAmplitude);
    }

    this.animationId = requestAnimationFrame(() => this.analyzeAmplitude());
  }

  private smoothAmplitude(amplitude: number): number {
    // Apply exponential smoothing
    const smoothingFactor = 0.3;
    return amplitude * smoothingFactor;
  }

  public disconnect() {
    this.stopAnalysis();
    
    if (this.source) {
      try {
        this.source.disconnect();
      } catch (error) {
        console.error('Failed to disconnect source:', error);
      }
      this.source = null;
    }

    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch (error) {
        console.error('Failed to close AudioContext:', error);
      }
      this.audioContext = null;
    }
  }
}

// Text-to-Speech utility with amplitude tracking
export class TTSPlayer {
  private audioProcessor: AudioProcessor;
  private currentAudio: HTMLAudioElement | null = null;
  private isPlaying: boolean = false;

  constructor() {
    this.audioProcessor = new AudioProcessor();
  }

  public async playTextWithLipSync(
    text: string, 
    onAmplitudeUpdate: (amplitude: number) => void,
    voice: string = 'en-US-JennyNeural'
  ): Promise<void> {
    try {
      // Stop any currently playing audio
      this.stop();

      // Create audio element
      this.currentAudio = new Audio();
      
      // Generate speech using Web Speech API
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = this.getVoiceByName(voice);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      // Convert speech to audio blob (simplified approach)
      const audioBlob = await this.synthesizeSpeechToBlob(utterance);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      this.currentAudio.src = audioUrl;
      
      // Connect to audio processor for amplitude analysis
      this.audioProcessor.connectAudioElement(this.currentAudio, onAmplitudeUpdate);
      
      // Start analysis before playing
      this.audioProcessor.startAnalysis();
      
      // Play the audio
      await this.currentAudio.play();
      this.isPlaying = true;

      // Clean up when audio finishes
      this.currentAudio.addEventListener('ended', () => {
        this.stop();
        onAmplitudeUpdate(0); // Reset amplitude when done
      });

    } catch (error) {
      console.error('Failed to play text with lip sync:', error);
      // Fallback: simulate lip sync with random amplitude
      this.simulateLipSync(text, onAmplitudeUpdate);
    }
  }

  private async synthesizeSpeechToBlob(utterance: SpeechSynthesisUtterance): Promise<Blob> {
    return new Promise((resolve) => {
      // This is a simplified version - in production, you'd use a proper TTS API
      // For now, we'll create a dummy audio blob
      const audioContext = new AudioContext();
      const sampleRate = audioContext.sampleRate;
      const duration = utterance.text.length * 0.1; // Rough estimate
      const numSamples = sampleRate * duration;
      
      const buffer = audioContext.createBuffer(1, numSamples, sampleRate);
      const channel = buffer.getChannelData(0);
      
      // Generate some dummy audio data with speech-like patterns
      for (let i = 0; i < numSamples; i++) {
        const t = i / sampleRate;
        // Create speech-like waveform with varying amplitude
        const envelope = Math.exp(-t * 0.5) * (0.5 + 0.5 * Math.sin(2 * Math.PI * 440 * t));
        channel[i] = envelope * (Math.random() - 0.5) * 0.3;
      }
      
      // Convert to WAV blob
      const wav = this.audioBufferToWav(buffer);
      resolve(new Blob([wav], { type: 'audio/wav' }));
    });
  }

  private audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
    const length = buffer.length * buffer.numberOfChannels * 2 + 44;
    const arrayBuffer = new ArrayBuffer(length);
    const view = new DataView(arrayBuffer);
    const channels: Float32Array[] = [];
    let offset = 0;
    let pos = 0;

    // Write WAV header
    const setUint16 = (data: number) => {
      view.setUint16(pos, data, true);
      pos += 2;
    };
    const setUint32 = (data: number) => {
      view.setUint32(pos, data, true);
      pos += 4;
    };

    // RIFF identifier
    setUint32(0x46464952);
    // file length
    setUint32(length - 8);
    // RIFF type
    setUint32(0x57415645);
    // format chunk identifier
    setUint32(0x666d7420);
    // format chunk length
    setUint32(16);
    // sample format (raw)
    setUint16(1);
    // channel count
    setUint16(buffer.numberOfChannels);
    // sample rate
    setUint32(buffer.sampleRate);
    // byte rate
    setUint32(buffer.sampleRate * 2 * buffer.numberOfChannels);
    // block align
    setUint16(buffer.numberOfChannels * 2);
    // bits per sample
    setUint16(16);
    // data chunk identifier
    setUint32(0x64617461);
    // data chunk length
    setUint32(length - pos - 4);

    // Write interleaved data
    for (let i = 0; i < buffer.numberOfChannels; i++) {
      channels.push(buffer.getChannelData(i));
    }

    while (pos < length) {
      for (let i = 0; i < buffer.numberOfChannels; i++) {
        let sample = Math.max(-1, Math.min(1, channels[i][offset]));
        sample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        view.setInt16(pos, sample, true);
        pos += 2;
      }
      offset++;
    }

    return arrayBuffer;
  }

  private getVoiceByName(voiceName: string): SpeechSynthesisVoice | null {
    const voices = speechSynthesis.getVoices();
    return voices.find(voice => voice.name === voiceName) || voices[0];
  }

  private simulateLipSync(text: string, onAmplitudeUpdate: (amplitude: number) => void) {
    // Fallback simulation when TTS fails
    const words = text.split(' ');
    let wordIndex = 0;
    
    const speakWord = () => {
      if (wordIndex >= words.length) {
        onAmplitudeUpdate(0);
        return;
      }

      const word = words[wordIndex];
      const duration = word.length * 100; // Rough timing
      
      // Simulate speaking with random amplitude
      const interval = setInterval(() => {
        const amplitude = Math.random() * 0.8 + 0.2; // Random between 0.2 and 1.0
        onAmplitudeUpdate(amplitude);
      }, 50);

      setTimeout(() => {
        clearInterval(interval);
        onAmplitudeUpdate(0); // Pause between words
        wordIndex++;
        setTimeout(speakWord, 200); // Small pause between words
      }, duration);
    };

    speakWord();
  }

  public stop() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      URL.revokeObjectURL(this.currentAudio.src);
      this.currentAudio = null;
    }
    
    this.audioProcessor.stopAnalysis();
    this.isPlaying = false;
  }

  public getIsPlaying(): boolean {
    return this.isPlaying;
  }
}
