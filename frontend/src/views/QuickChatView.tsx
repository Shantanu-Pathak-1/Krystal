import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Search, Eye, Paperclip, Mic, Send, Sparkles } from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function QuickChatView() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Superpower toggles
  const [webSearchEnabled, setWebSearchEnabled] = useState(false)
  const [visionMode, setVisionMode] = useState<'none' | 'screen' | 'webcam'>('none')
  const [fileUploadEnabled, setFileUploadEnabled] = useState(false)
  const [voiceModeEnabled, setVoiceModeEnabled] = useState(false)

  // Auto-scroll to bottom
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
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.content,
          mode: 'Agentic',
          model_id: null,
          session_id: 'quick_chat',
          use_web: webSearchEnabled,
          use_vision: visionMode !== 'none',
          file: fileUploadEnabled ? 'pending' : null,
        }),
      })

      if (!res.ok) {
        const errorText = await res.text()
        console.error(`[QuickChat] HTTP ${res.status} Error:`, errorText)
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }

      const data = await res.json()
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      console.error('[QuickChat] Error:', err)
      let errorMsg = '⚠️ Unable to reach Krystal Engine. Is the backend running on port 8000?'
      if (err instanceof Error) {
        errorMsg = `⚠️ ${err.message}`
      }
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: errorMsg,
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleClose = () => {
    // Send IPC signal to hide the window
    try {
      const { ipcRenderer } = require('electron')
      ipcRenderer.send('quick-chat-hide')
    } catch (e) {
      window.close()
    }
  }

  const handleMinimize = () => {
    // Send IPC signal to minimize the window
    try {
      const { ipcRenderer } = require('electron')
      ipcRenderer.send('quick-chat-minimize')
    } catch (e) {
      console.error('Failed to minimize:', e)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
  }

  return (
    <div
      className="flex flex-col h-screen"
      style={{
        background: 'rgba(3, 7, 18, 0.95)',
        backdropFilter: 'blur(24px)',
        border: '1px solid rgba(16, 185, 129, 0.4)',
        borderRadius: '12px',
      }}
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{
          WebkitAppRegion: 'drag' as any,
          borderBottom: '1px solid rgba(16, 185, 129, 0.2)',
          background: 'rgba(3, 7, 18, 0.8)',
        }}
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <span
            className="text-sm font-medium"
            style={{
              fontFamily: 'Orbitron, monospace',
              color: 'rgba(16, 185, 129, 0.9)',
            }}
          >
            Krystal Quick Chat
          </span>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={handleMinimize}
            className="p-1.5 rounded-lg transition-all duration-200"
            style={{
              WebkitAppRegion: 'no-drag' as any,
              background: 'rgba(59, 130, 246, 0.2)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              color: 'rgba(96, 165, 250, 0.9)',
            }}
            title="Minimize"
          >
            <span className="text-lg font-bold leading-none">−</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={handleClose}
            className="p-1.5 rounded-lg transition-all duration-200"
            style={{
              WebkitAppRegion: 'no-drag' as any,
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: 'rgba(248, 113, 113, 0.9)',
            }}
            title="Close"
          >
            <X className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {/* ── Chat Area ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-2xl mx-auto space-y-4">
          {/* Welcome state */}
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center py-12 text-center"
            >
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                style={{
                  background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2))',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                }}
              >
                <Sparkles className="w-8 h-8 text-emerald-400" />
              </div>
              <p
                className="text-sm font-medium mb-1"
                style={{ color: 'rgba(16, 185, 129, 0.9)', fontFamily: 'Orbitron, monospace' }}
              >
                Quick Chat
              </p>
              <p className="text-xs text-white/40">Rapid-fire commands ready</p>
            </motion.div>
          )}

          {/* Messages */}
          {messages.map((msg, i) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: i * 0.05 }}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className="px-3 py-2 rounded-xl text-sm max-w-[85%]"
                style={
                  msg.type === 'user'
                    ? {
                        background: 'rgba(16, 185, 129, 0.2)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        color: 'rgba(16, 185, 129, 0.95)',
                      }
                    : {
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        color: 'rgba(255, 255, 255, 0.85)',
                      }
                }
              >
                <p className="whitespace-pre-wrap break-words">{msg.content}</p>
              </div>
            </motion.div>
          ))}

          {/* Typing indicator */}
          <AnimatePresence>
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                className="flex justify-start"
              >
                <div
                  className="px-3 py-2 rounded-xl"
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  <div className="flex items-center gap-1">
                    {[0, 0.15, 0.3].map((delay, i) => (
                      <motion.div
                        key={i}
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ background: 'rgba(16, 185, 129, 0.7)' }}
                        animate={{ scale: [1, 1.4, 1], opacity: [0.4, 1, 0.4] }}
                        transition={{ duration: 0.8, delay, repeat: Infinity, ease: 'easeInOut' }}
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ── Input Area ────────────────────────────────────────────────── */}
      <div
        className="px-4 py-3"
        style={{
          borderTop: '1px solid rgba(16, 185, 129, 0.2)',
          background: 'rgba(3, 7, 18, 0.8)',
        }}
      >
        <div className="max-w-2xl mx-auto">
          {/* Action Bar */}
          <div className="flex items-center gap-2 mb-2">
            {/* Web Search */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setWebSearchEnabled(!webSearchEnabled)}
              className="p-2 rounded-lg transition-all duration-200"
              style={
                webSearchEnabled
                  ? {
                      background: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: 'rgba(16, 185, 129, 0.95)',
                    }
                  : {
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      color: 'rgba(255, 255, 255, 0.4)',
                    }
              }
              title="Web Search"
            >
              <Search className="w-4 h-4" />
            </motion.button>

            {/* Vision Mode */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setVisionMode(visionMode === 'none' ? 'screen' : 'none')}
              className="p-2 rounded-lg transition-all duration-200"
              style={
                visionMode !== 'none'
                  ? {
                      background: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: 'rgba(16, 185, 129, 0.95)',
                    }
                  : {
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      color: 'rgba(255, 255, 255, 0.4)',
                    }
              }
              title="Vision Mode"
            >
              <Eye className="w-4 h-4" />
            </motion.button>

            {/* File Upload */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setFileUploadEnabled(!fileUploadEnabled)}
              className="p-2 rounded-lg transition-all duration-200"
              style={
                fileUploadEnabled
                  ? {
                      background: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: 'rgba(16, 185, 129, 0.95)',
                    }
                  : {
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      color: 'rgba(255, 255, 255, 0.4)',
                    }
              }
              title="File Upload"
            >
              <Paperclip className="w-4 h-4" />
            </motion.button>

            {/* Voice Mode */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setVoiceModeEnabled(!voiceModeEnabled)}
              className="p-2 rounded-lg transition-all duration-200"
              style={
                voiceModeEnabled
                  ? {
                      background: 'rgba(16, 185, 129, 0.2)',
                      border: '1px solid rgba(16, 185, 129, 0.4)',
                      color: 'rgba(16, 185, 129, 0.95)',
                    }
                  : {
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.08)',
                      color: 'rgba(255, 255, 255, 0.4)',
                    }
              }
              title="Voice Mode"
            >
              <Mic className="w-4 h-4" />
            </motion.button>
          </div>

          {/* Input Field */}
          <div
            className="flex items-end gap-2 p-2 rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Quick command..."
              disabled={isLoading}
              rows={1}
              className="flex-1 bg-transparent text-white/85 placeholder-white/30 resize-none outline-none text-sm leading-relaxed py-2 px-1"
              style={{
                fontFamily: 'Syne, sans-serif',
                minHeight: 36,
                maxHeight: 120,
              }}
            />
            <motion.button
              whileHover={inputValue.trim() && !isLoading ? { scale: 1.05 } : {}}
              whileTap={inputValue.trim() && !isLoading ? { scale: 0.95 } : {}}
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              className="p-2 rounded-lg transition-all duration-200"
              style={
                inputValue.trim() && !isLoading
                  ? {
                      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.8), rgba(6, 182, 212, 0.8))',
                      border: '1px solid rgba(16, 185, 129, 0.5)',
                      color: 'white',
                    }
                  : {
                      background: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      color: 'rgba(255, 255, 255, 0.2)',
                    }
              }
            >
              <Send className="w-4 h-4" />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  )
}
