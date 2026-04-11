import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Volume2, Brain } from 'lucide-react'
import { Canvas } from '@react-three/fiber'
import { Environment, OrbitControls } from '@react-three/drei'
import { VRMModel } from '../KrystalAvatar'
import { TTSPlayer } from '../../utils/audioProcessor'

export default function ZenVoiceMode() {
  const [isListening, setIsListening] = useState(false)
  const [userSpeech, setUserSpeech] = useState('')
  const [krystalResponse, setKrystalResponse] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [talkingAmplitude, setTalkingAmplitude] = useState(0)
  const [isKrystalSpeaking, setIsKrystalSpeaking] = useState(false)

  // TTS Player instance for lip sync
  const ttsPlayer = useRef(new TTSPlayer())

  // Simulate voice wave animation
  const [waveBars, setWaveBars] = useState(Array(20).fill(0))

  useEffect(() => {
    if (isListening) {
      const interval = setInterval(() => {
        setWaveBars(prev => prev.map(() => Math.random() * 100))
      }, 100)
      return () => clearInterval(interval)
    } else {
      setWaveBars(Array(20).fill(0))
    }
  }, [isListening])

  // Cleanup TTS player on unmount
  useEffect(() => {
    return () => {
      ttsPlayer.current?.stop()
    }
  }, [])

  const speakKrystalResponse = async (text: string) => {
    try {
      setIsKrystalSpeaking(true)
      await ttsPlayer.current.playTextWithLipSync(
        text,
        (amplitude: number) => {
          setTalkingAmplitude(amplitude)
        },
        'en-US-JennyNeural'
      )
    } catch (error) {
      console.error('TTS Error:', error)
      // Fallback to simulation
      simulateLipSync(text)
    } finally {
      setIsKrystalSpeaking(false)
      setTalkingAmplitude(0)
    }
  }

  const simulateLipSync = (text: string) => {
    const words = text.split(' ')
    let wordIndex = 0
    
    const speakWord = () => {
      if (wordIndex >= words.length) {
        setTalkingAmplitude(0)
        setIsKrystalSpeaking(false)
        return
      }

      const word = words[wordIndex]
      const duration = word.length * 150 // Rough timing
      
      // Simulate speaking with random amplitude
      const interval = setInterval(() => {
        const amplitude = Math.random() * 0.8 + 0.2
        setTalkingAmplitude(amplitude)
      }, 50)

      setTimeout(() => {
        clearInterval(interval)
        setTalkingAmplitude(0)
        wordIndex++
        setTimeout(speakWord, 200)
      }, duration)
    }

    setIsKrystalSpeaking(true)
    speakWord()
  }

  const toggleListening = () => {
    if (isListening) {
      // Stop listening and process
      setIsListening(false)
      setIsProcessing(true)
      
      // Simulate processing and generate Krystal response
      setTimeout(async () => {
        const response = 'I understand what you said. Let me help you with that. I can assist you with various tasks like system monitoring, voice commands, and much more.'
        setKrystalResponse(response)
        setIsProcessing(false)
        
        // Speak the response with lip sync
        await speakKrystalResponse(response)
      }, 2000)
    } else {
      // Start listening
      setIsListening(true)
      setUserSpeech('')
      setKrystalResponse('')
      
      // Simulate speech recognition
      setTimeout(() => {
        setUserSpeech('Hey Krystal, can you help me with something?')
      }, 3000)
    }
  }

  return (
    <div className="flex h-full bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        {/* Audio Wave Visualization */}
        <div className="mb-16">
          <div className="flex items-end justify-center space-x-1 h-32">
            {waveBars.map((height, index) => (
              <div
                key={index}
                className={`w-2 bg-gradient-to-t from-blue-400 to-cyan-300 rounded-full transition-all duration-100`}
                style={{ height: `${height}%` }}
              />
            ))}
          </div>
          <div className="flex items-center justify-center space-x-2 mt-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              isListening 
                ? 'bg-red-500 text-white animate-pulse' 
                : 'bg-gray-700 text-gray-300'
            }`}>
              {isListening ? 'Listening' : 'Idle'}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              isProcessing 
                ? 'bg-yellow-500 text-white animate-pulse' 
                : 'bg-gray-700 text-gray-300'
            }`}>
              {isProcessing ? 'Processing' : 'Ready'}
            </span>
          </div>
        </div>

        {/* 3D Avatar Canvas */}
        <div className="flex-1 relative">
          <Canvas
            camera={{ position: [0, 1.5, 3], fov: 45 }}
            style={{ background: 'linear-gradient(to bottom, #1a1a2e, #0f0f1e)' }}
          >
            {/* Lighting */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[5, 5, 5]} intensity={1} />
            
            {/* VRM Model */}
            <VRMModel 
              url="/models/shanvika_personal_dress_1.vrm" 
              talkingAmplitude={talkingAmplitude} 
            />
            
            {/* Environment and Controls */}
            <Environment preset="city" />
            <OrbitControls 
              enablePan={false}
              minDistance={2}
              maxDistance={5}
              minPolarAngle={Math.PI / 4}
              maxPolarAngle={Math.PI / 2}
            />
          </Canvas>

          {/* Control Overlay */}
          <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
            <div className="bg-krystal-dark/90 backdrop-blur rounded-lg p-4 border border-gray-800">
              <div className="flex items-center space-x-4">
                <button
                  onClick={toggleListening}
                  disabled={isProcessing || isKrystalSpeaking}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all ${
                    isListening
                      ? 'bg-red-500 hover:bg-red-600 text-white'
                      : 'bg-krystal-purple hover:bg-krystal-purple/90 text-white'
                  } ${isProcessing || isKrystalSpeaking ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                  <span>
                    {isProcessing ? 'Processing...' : 
                     isKrystalSpeaking ? 'Speaking...' :
                     isListening ? 'Stop Listening' : 'Start Listening'}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Side Panel */}
      <div className="w-80 bg-krystal-darker border-l border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Mode Status</h3>
        
        <div className="space-y-4">
          <div className="bg-krystal-dark rounded-lg p-4 border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Voice Input</span>
              <span className={`w-2 h-2 rounded-full ${isListening ? 'bg-red-400 animate-pulse' : 'bg-gray-400'}`}></span>
            </div>
            <p className="text-sm text-white">
              {isListening ? 'Active' : 'Inactive'}
            </p>
          </div>

          <div className="bg-krystal-dark rounded-lg p-4 border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Processing</span>
              <span className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-yellow-400 animate-pulse' : 'bg-gray-400'}`}></span>
            </div>
            <p className="text-sm text-white">
              {isProcessing ? 'Analyzing...' : 'Ready'}
            </p>
          </div>

          <div className="bg-krystal-dark rounded-lg p-4 border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Lip Sync</span>
              <span className={`w-2 h-2 rounded-full ${talkingAmplitude > 0.1 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></span>
            </div>
            <p className="text-sm text-white">
              {talkingAmplitude > 0.1 ? 'Active' : 'Idle'}
            </p>
          </div>
        </div>

        <div className="mt-6">
          <h4 className="text-md font-medium text-white mb-3">Voice Commands</h4>
          <div className="space-y-2 text-sm text-gray-400">
            <div className="flex items-center space-x-2">
              <Volume2 className="w-4 h-4" />
              <span>"Hey Krystal" - Wake up</span>
            </div>
            <div className="flex items-center space-x-2">
              <Volume2 className="w-4 h-4" />
              <span>"Stop" - End conversation</span>
            </div>
            <div className="flex items-center space-x-2">
              <Volume2 className="w-4 h-4" />
              <span>"Repeat" - Say again</span>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <h4 className="text-md font-medium text-white mb-3">Audio Amplitude</h4>
          <div className="bg-krystal-dark rounded-lg p-4 border border-gray-800">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-gray-400">Voice Level</span>
              <span className={`w-2 h-2 rounded-full ${talkingAmplitude > 0.1 ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></span>
            </div>
            {/* Amplitude Visualizer */}
            <div className="flex items-end justify-center space-x-1 h-16">
              {Array(20).fill(0).map((_, index) => (
                <div
                  key={index}
                  className={`w-1 bg-gradient-to-t from-green-400 to-cyan-300 rounded-full transition-all duration-75`}
                  style={{ 
                    height: `${talkingAmplitude > 0.1 ? 
                      Math.random() * talkingAmplitude * 100 : 
                      5}%` 
                  }}
                />
              ))}
            </div>
            <p className="text-xs text-gray-400 text-center mt-2">
              {talkingAmplitude > 0.1 ? 'Speaking' : 'Silent'}
            </p>
          </div>
        </div>

        <div className="mt-6">
          <h4 className="text-md font-medium text-white mb-3">3D Controls</h4>
          <div className="space-y-2 text-sm text-gray-400">
            <div className="flex items-center space-x-2">
              <span>Left Click + Drag - Rotate</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>Scroll - Zoom In/Out</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>Right Click - Pan</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
