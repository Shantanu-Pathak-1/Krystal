import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Mic, MicOff, Sparkles, User, Copy, Check, Volume2, VolumeX } from 'lucide-react'
import { useAutonomy } from '../../context/AutonomyContext'

// Global state for selected model
let globalSelectedModel: string | null = null

// SpeechRecognition types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognition
}

declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionConstructor
    webkitSpeechRecognition: SpeechRecognitionConstructor
  }
}

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <motion.button
      onClick={copy}
      whileTap={{ scale: 0.9 }}
      className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 rounded-lg"
      style={{ color: 'rgba(255,255,255,0.3)' }}
      title="Copy"
    >
      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
    </motion.button>
  )
}

function MessageBubble({ message, index }: { message: Message; index: number }) {
  const isUser = message.type === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35, delay: index * 0.03, ease: [0.4, 0, 0.2, 1] }}
      className={`flex items-end gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* Avatar — assistant */}
      {!isUser && (
        <div
          className="w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center"
          style={{
            background: 'linear-gradient(135deg, rgba(139,92,246,0.4) 0%, rgba(6,182,212,0.3) 100%)',
            border: '1px solid rgba(139,92,246,0.3)',
            boxShadow: '0 0 12px rgba(139,92,246,0.2)',
          }}
        >
          <Sparkles className="w-4 h-4 text-purple-300" />
        </div>
      )}

      {/* Bubble */}
      <div className={`group relative max-w-[72%]`}>
        <div
          className="px-4 py-3 rounded-2xl text-sm leading-relaxed"
          style={
            isUser
              ? {
                  background: 'linear-gradient(135deg, rgba(139,92,246,0.25) 0%, rgba(109,40,217,0.2) 100%)',
                  border: '1px solid rgba(139,92,246,0.3)',
                  color: 'rgba(255,255,255,0.9)',
                  boxShadow: '0 4px 20px rgba(139,92,246,0.1)',
                  borderBottomRightRadius: 6,
                }
              : {
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: 'rgba(255,255,255,0.82)',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                  borderBottomLeftRadius: 6,
                }
          }
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Timestamp + copy */}
        <div className={`flex items-center gap-2 mt-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span
            className="text-[10px] text-white/20"
            style={{ fontFamily: 'JetBrains Mono, monospace' }}
          >
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {!isUser && <CopyButton text={message.content} />}
        </div>
      </div>

      {/* Avatar — user */}
      {isUser && (
        <div
          className="w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center"
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <User className="w-4 h-4 text-white/50" />
        </div>
      )}
    </motion.div>
  )
}

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="flex items-end gap-3"
    >
      <div
        className="w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center"
        style={{
          background: 'linear-gradient(135deg, rgba(139,92,246,0.3) 0%, rgba(6,182,212,0.2) 100%)',
          border: '1px solid rgba(139,92,246,0.25)',
        }}
      >
        <Sparkles className="w-4 h-4 text-purple-300" />
      </div>
      <div
        className="px-4 py-3 rounded-2xl rounded-bl-md"
        style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <div className="flex items-center gap-1.5">
          {[0, 0.15, 0.3].map((delay, i) => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: 'rgba(139,92,246,0.7)' }}
              animate={{ scale: [1, 1.6, 1], opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 0.8, delay, repeat: Infinity, ease: 'easeInOut' }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default function MainChat() {
  const { autonomyMode } = useAutonomy()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const lockedVoiceRef = useRef<SpeechSynthesisVoice | null>(null)
  const lastSpokenMessageIdRef = useRef<string | null>(null)

  // Load chat history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/chat/history')
        if (res.ok) {
          const data = await res.json()
          if (data.messages && Array.isArray(data.messages)) {
            const historyMessages: Message[] = data.messages.map((msg: any) => ({
              id: msg.id || Date.now().toString(),
              type: msg.type as 'user' | 'assistant',
              content: msg.content,
              timestamp: new Date(msg.timestamp || Date.now()),
            }))
            setMessages(historyMessages)
          }
        }
      } catch {
        // Silent fail - app works without history
      }
    }
    loadHistory()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInputValue('')
    setIsLoading(true)

    try {
      // Map autonomy mode to backend format (capitalize first letter)
      const modeMap: Record<string, string> = {
        safe: 'Safe',
        agentic: 'Agentic',
        god: 'God Mode'
      }
      const mode = modeMap[autonomyMode] || 'Agentic'

      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, mode, model_id: globalSelectedModel }),
      })
      const data = await res.json()
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response || 'Response received.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMsg])
      // TTS is handled by useEffect above to prevent double-firing
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '⚠️ Unable to reach Krystal Engine. Is the backend running on port 8000?',
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  // Robust voice selection function - locks voice in ref
  const selectAndLockVoice = useCallback(() => {
    if (lockedVoiceRef.current) return lockedVoiceRef.current
    if (!('speechSynthesis' in window)) return null
    
    const voices = window.speechSynthesis.getVoices()
    if (voices.length === 0) return null
    
    // Priority order for voice selection
    const preferredVoiceNames = [
      'Google UK English Female',
      'Microsoft Zira',
      'Microsoft Zira - English (United States)',
      'Samantha',
      'Google US English',
      'Google UK English'
    ]
    
    // Try exact matches first
    for (const name of preferredVoiceNames) {
      const voice = voices.find(v => v.name === name)
      if (voice) {
        lockedVoiceRef.current = voice
        return voice
      }
    }
    
    // Fallback: first en-US or en-GB female voice
    const femaleVoice = voices.find(v => 
      (v.lang.startsWith('en-US') || v.lang.startsWith('en-GB')) &&
      (v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('zira') || v.name.toLowerCase().includes('samantha'))
    )
    if (femaleVoice) {
      lockedVoiceRef.current = femaleVoice
      return femaleVoice
    }
    
    // Final fallback: any en-US voice
    const usVoice = voices.find(v => v.lang.startsWith('en-US'))
    if (usVoice) {
      lockedVoiceRef.current = usVoice
      return usVoice
    }
    
    // Last resort: first available voice
    lockedVoiceRef.current = voices[0]
    return voices[0]
  }, [])

  // Initialize speech synthesis voices
  useEffect(() => {
    if ('speechSynthesis' in window) {
      // Load voices (needed for some browsers)
      const voices = window.speechSynthesis.getVoices()
      if (voices.length > 0) {
        selectAndLockVoice()
      }
      
      // Some browsers load voices asynchronously
      if ('onvoiceschanged' in window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = () => {
          selectAndLockVoice()
        }
      }
    }
  }, [selectAndLockVoice])

  // Text-to-speech effect - only speaks when new assistant message arrives
  useEffect(() => {
    if (!ttsEnabled || !('speechSynthesis' in window)) return
    
    // Find the last assistant message
    const lastAssistantMessage = [...messages].reverse().find(m => m.type === 'assistant')
    if (!lastAssistantMessage) return
    
    // Prevent double-firing: only speak if we haven't spoken this message ID
    if (lastAssistantMessage.id === lastSpokenMessageIdRef.current) return
    lastSpokenMessageIdRef.current = lastAssistantMessage.id
    
    // Cancel any ongoing speech before speaking
    window.speechSynthesis.cancel()
    
    const utterance = new SpeechSynthesisUtterance(lastAssistantMessage.content)
    utterance.rate = 1
    utterance.pitch = 1
    utterance.volume = 1
    
    // Use locked voice
    const voice = selectAndLockVoice()
    if (voice) {
      utterance.voice = voice
    }
    
    window.speechSynthesis.speak(utterance)
  }, [messages, ttsEnabled, selectAndLockVoice])

  // Speech recognition setup
  useEffect(() => {
    if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
      return
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'
    
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = ''
      let interimTranscript = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }
      
      if (finalTranscript) {
        setInputValue(finalTranscript)
        // Auto-send when speech is finalized
        setTimeout(() => {
          setIsRecording(false)
          handleSendWithText(finalTranscript)
        }, 500)
      } else if (interimTranscript) {
        setInputValue(interimTranscript)
      }
    }
    
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error)
      setIsRecording(false)
    }
    
    recognition.onend = () => {
      setIsRecording(false)
    }
    
    recognitionRef.current = recognition
  }, [])

  // Handle send with specific text (for voice input)
  const handleSendWithText = async (text: string) => {
    if (!text.trim() || isLoading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: text.trim(),
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInputValue('')
    setIsLoading(true)

    try {
      const modeMap: Record<string, string> = {
        safe: 'Safe',
        agentic: 'Agentic',
        god: 'God Mode'
      }
      const mode = modeMap[autonomyMode] || 'Agentic'

      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, mode, model_id: globalSelectedModel }),
      })
      const data = await res.json()
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response || 'Response received.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMsg])
      // TTS is handled by useEffect above to prevent double-firing
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '⚠️ Unable to reach Krystal Engine. Is the backend running on port 8000?',
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  // Toggle speech recognition
  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser')
      return
    }
    
    if (isRecording) {
      recognitionRef.current.stop()
      setIsRecording(false)
    } else {
      try {
        recognitionRef.current.start()
        setIsRecording(true)
      } catch (err) {
        console.error('Failed to start recording:', err)
      }
    }
  }

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`
  }

  return (
    <div
      className="flex flex-col h-full"
      style={{ background: 'linear-gradient(160deg, #04070f 0%, #060a16 100%)' }}
    >
      {/* Grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(139,92,246,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.03) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* ── Messages ─────────────────────────────────────────────────── */}
      <div className="relative flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-5">

          {/* Welcome state */}
          <AnimatePresence>
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col items-center justify-center py-20 text-center"
              >
                {/* Animated logo */}
                <div className="relative mb-6">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-0 rounded-2xl"
                    style={{
                      background: 'conic-gradient(from 0deg, rgba(139,92,246,0.5), rgba(6,182,212,0.5), rgba(139,92,246,0.5))',
                      filter: 'blur(8px)',
                    }}
                  />
                  <div
                    className="relative w-20 h-20 rounded-2xl flex items-center justify-center"
                    style={{ background: 'linear-gradient(135deg, #1a0a3e, #0a1a3e)' }}
                  >
                    <Sparkles className="w-10 h-10 text-purple-300" />
                  </div>
                </div>

                <h2
                  className="text-2xl font-bold mb-2"
                  style={{
                    fontFamily: 'Orbitron, monospace',
                    background: 'linear-gradient(135deg, #e2e8f0, #a78bfa, #22d3ee)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                  }}
                >
                  Krystal AI
                </h2>
                <p className="text-sm text-white/30 max-w-xs leading-relaxed">
                  Neural interface ready. Type a message or activate voice mode to begin.
                </p>

                {/* Prompt suggestions */}
                <div className="grid grid-cols-2 gap-3 mt-8 max-w-lg">
                  {[
                    'What can you do?',
                    'Show system status',
                    'Run a security scan',
                    'How\'s my memory vault?',
                  ].map(suggestion => (
                    <motion.button
                      key={suggestion}
                      whileHover={{ y: -2, borderColor: 'rgba(139,92,246,0.4)' }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => { setInputValue(suggestion); inputRef.current?.focus() }}
                      className="px-4 py-3 rounded-xl text-sm text-white/50 text-left transition-all duration-200"
                      style={{
                        background: 'rgba(255,255,255,0.025)',
                        border: '1px solid rgba(255,255,255,0.07)',
                      }}
                    >
                      {suggestion}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Messages */}
          {messages.map((msg, i) => (
            <MessageBubble key={msg.id} message={msg} index={i} />
          ))}

          {/* Typing indicator */}
          <AnimatePresence>
            {isLoading && <TypingIndicator />}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ── Input area ────────────────────────────────────────────────── */}
      <div
        className="relative px-4 py-4"
        style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
      >
        {/* Glow line above input */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 h-px w-48 pointer-events-none"
          style={{ background: 'linear-gradient(90deg, transparent, rgba(139,92,246,0.5), rgba(6,182,212,0.5), transparent)' }}
        />

        <div className="max-w-3xl mx-auto">
          <div
            className="flex items-end gap-3 p-2 rounded-2xl transition-all duration-200"
            style={{
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
            onFocus={() => {}}
          >
            {/* Mic button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.93 }}
              onClick={toggleRecording}
              className="flex-shrink-0 p-3 rounded-xl transition-all duration-200"
              style={
                isRecording
                  ? { background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)', color: '#f87171' }
                  : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.35)' }
              }
            >
              {isRecording
                ? <MicOff className="w-5 h-5" />
                : <Mic className="w-5 h-5" />
              }
            </motion.button>

            {/* TTS toggle */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.93 }}
              onClick={() => setTtsEnabled(e => !e)}
              className="flex-shrink-0 p-3 rounded-xl transition-all duration-200"
              style={
                ttsEnabled
                  ? { background: 'rgba(139,92,246,0.2)', border: '1px solid rgba(139,92,246,0.4)', color: '#a78bfa' }
                  : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.35)' }
              }
              title={ttsEnabled ? 'Text-to-speech on' : 'Text-to-speech off'}
            >
              {ttsEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
            </motion.button>

            {/* Textarea */}
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Message Krystal…"
              disabled={isLoading}
              rows={1}
              className="flex-1 bg-transparent text-white/85 placeholder-white/20 resize-none outline-none text-sm leading-relaxed py-2.5 px-1"
              style={{
                fontFamily: 'Syne, sans-serif',
                minHeight: 40,
                maxHeight: 140,
              }}
            />

            {/* Send button */}
            <motion.button
              whileHover={inputValue.trim() && !isLoading ? { scale: 1.05 } : {}}
              whileTap={inputValue.trim() && !isLoading ? { scale: 0.93 } : {}}
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              className="flex-shrink-0 p-3 rounded-xl transition-all duration-200"
              style={
                inputValue.trim() && !isLoading
                  ? {
                      background: 'linear-gradient(135deg, rgba(139,92,246,0.8), rgba(109,40,217,0.8))',
                      border: '1px solid rgba(139,92,246,0.5)',
                      boxShadow: '0 0 20px rgba(139,92,246,0.3)',
                      color: 'white',
                    }
                  : {
                      background: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(255,255,255,0.06)',
                      color: 'rgba(255,255,255,0.2)',
                    }
              }
            >
              <Send className="w-5 h-5" />
            </motion.button>
          </div>

          {/* Recording indicator */}
          <AnimatePresence>
            {isRecording && (
              <motion.p
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-center gap-2 text-xs text-red-400/70 font-mono mt-2 px-2"
              >
                <motion.span
                  className="w-1.5 h-1.5 rounded-full bg-red-500"
                  animate={{ opacity: [1, 0.2, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
                Recording — press mic to stop
              </motion.p>
            )}
          </AnimatePresence>

          <p className="text-center text-[10px] text-white/15 font-mono mt-2">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}