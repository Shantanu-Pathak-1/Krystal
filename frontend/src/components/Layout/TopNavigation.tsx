import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, RefreshCw, Shield, Zap, Eye, AlertTriangle, Cpu, Wifi, WifiOff } from 'lucide-react'
import { ViewMode, AutonomyMode } from '../../types'

interface TopNavigationProps {
  currentView: ViewMode
  onViewChange: (view: ViewMode) => void
  autonomyMode: AutonomyMode
  setAutonomyMode: (mode: AutonomyMode) => void
}

const VIEW_LABELS: Record<ViewMode, string> = {
  dashboard: 'Control Center',
  main:      'Neural Chat',
  heartbeat: 'Heartbeat',
  zen:       'Zen Voice',
  logs:      'System Logs',
  config:    'Configuration',
  memory:    'Memory Vault',
  diary:     "Krystal's Diary",
  security:  'Security & Guard',
  plugins:   'Plugins Lab',
}

const AUTONOMY_OPTIONS = [
  {
    value: 'safe' as AutonomyMode,
    label: 'Safe Mode',
    desc: 'Chat only — no system access',
    color: '#10b981',
    icon: Shield,
  },
  {
    value: 'agentic' as AutonomyMode,
    label: 'Agentic',
    desc: 'Default tool use enabled',
    color: '#f59e0b',
    icon: Zap,
  },
  {
    value: 'god' as AutonomyMode,
    label: 'God Mode',
    desc: 'Full OS · Trinetra access',
    color: '#ef4444',
    icon: Eye,
  },
]

function useOutsideClick(ref: React.RefObject<HTMLElement>, fn: () => void) {
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) fn()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [ref, fn])
}

const dropdownVariants = {
  hidden: { opacity: 0, y: -8, scale: 0.96 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring' as const, stiffness: 400, damping: 28 } },
  exit:    { opacity: 0, y: -8, scale: 0.96, transition: { duration: 0.15 } },
}

// Model selection dropdown
function ModelSelector() {
  const [selectedModel, setSelectedModel] = useState<string>('groq')
  const [isOpen, setIsOpen] = useState(false)

  const models = [
    { value: 'groq', label: 'Groq', color: '#10b981' },
    { value: 'gemini', label: 'Gemini', color: '#f59e0b' },
    { value: 'sambanova', label: 'SambaNova', color: '#f59e0b' },
    { value: 'together', label: 'Together', color: '#8b5cf6' },
    { value: 'fireworks', label: 'Fireworks', color: '#ef4444' },
    { value: 'ollama', label: 'Local Ollama', color: '#8b5cf6' }
  ]

  const currentModel = models.find(m => m.value === selectedModel) || models[0]

  return (
    <div className="relative">
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-semibold transition-all duration-200"
        style={{
          background: `${currentModel.color}15`,
          border: `1px solid ${currentModel.color}40`,
          color: currentModel.color,
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: 11,
          letterSpacing: '0.1em',
        }}
      >
        <Cpu className="w-3.5 h-3.5" />
        <span>{currentModel.label}</span>
        <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-3.5 h-3.5" />
        </motion.div>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            variants={dropdownVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="absolute top-full left-0 mt-2 w-48 rounded-2xl overflow-hidden z-50"
            style={{
              background: 'rgba(6,9,20,0.97)',
              border: '1px solid rgba(255,255,255,0.08)',
              backdropFilter: 'blur(24px)',
              boxShadow: '0 20px 60px rgba(0,0,0,0.7)',
            }}
          >
            {models.map((model, index) => (
              <motion.button
                key={model.value}
                variants={{
                  hidden: { opacity: 0, x: -10 },
                  visible: { opacity: 1, x: 0 },
                  exit: { opacity: 0, x: 10 }
                }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => {
                  setSelectedModel(model.value)
                  setIsOpen(false)
                }}
                className="w-full text-left px-4 py-3 flex items-center gap-3 transition-colors duration-200"
                style={{
                  color: selectedModel === model.value ? model.color : 'rgba(255,255,255,0.7)',
                  backgroundColor: selectedModel === model.value ? `${model.color}20` : 'transparent'
                }}
              >
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: model.color }}
                />
                <div>
                  <div className="text-sm font-semibold">{model.label}</div>
                  <div className="text-xs text-gray-400">AI Provider</div>
                </div>
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Model status component
function ModelStatus() {
  const [modelStatus, setModelStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchModelStatus = async () => {
      try {
        const response = await fetch('/api/model/status')
        const data = await response.json()
        setModelStatus(data)
      } catch (error) {
        console.error('Failed to fetch model status:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchModelStatus()
    const interval = setInterval(fetchModelStatus, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading || !modelStatus) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
           style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
        <Cpu className="w-3.5 h-3.5 animate-pulse" style={{ color: 'rgba(255,255,255,0.4)' }} />
        <span className="text-xs font-mono" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Loading...
        </span>
      </div>
    )
  }

  const getModelColor = (provider: string) => {
    const colors: Record<string, string> = {
      groq: '#10b981',
      gemini: '#f59e0b', 
      ollama: '#8b5cf6',
      glm: '#06b6d4',
      none: '#ef4444'
    }
    return colors[provider] || '#6b7280'
  }

  const getModelLabel = (provider: string, model: string) => {
    if (provider === 'none') return 'No Models'
    if (provider === 'ollama') return `Local: ${model.split(':')[0]}`
    return `${provider.charAt(0).toUpperCase() + provider.slice(1)}: ${model.split('-')[0]}`
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
         style={{ 
           background: `${getModelColor(modelStatus.current_provider)}15`,
           border: `1px solid ${getModelColor(modelStatus.current_provider)}40`
         }}>
      {modelStatus.internet_connected ? (
        <Wifi className="w-3.5 h-3.5" style={{ color: getModelColor(modelStatus.current_provider) }} />
      ) : (
        <WifiOff className="w-3.5 h-3.5" style={{ color: '#f59e0b' }} />
      )}
      <span className="text-xs font-mono font-semibold" 
            style={{ color: getModelColor(modelStatus.current_provider) }}>
        {getModelLabel(modelStatus.current_provider, modelStatus.current_model)}
      </span>
    </div>
  )
}

export default function TopNavigation({
  currentView, onViewChange, autonomyMode, setAutonomyMode
}: TopNavigationProps) {
  const [autonomyOpen, setAutonomyOpen] = useState(false)
  const autonomyRef = useRef<HTMLDivElement>(null!)

  useOutsideClick(autonomyRef, () => setAutonomyOpen(false))

  const currentAutonomy = AUTONOMY_OPTIONS.find(o => o.value === autonomyMode)!

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="relative flex items-center justify-between px-6 flex-shrink-0"
      style={{
        height: 60,
        background: 'rgba(3,5,14,0.9)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      {/* Gradient accent line */}
      <div
        className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
        style={{
          background: 'linear-gradient(90deg, transparent, rgba(139,92,246,0.3), rgba(6,182,212,0.3), transparent)',
        }}
      />

      {/* ── Left: current view label ── */}
      <div className="flex items-center gap-3">
        <AnimatePresence mode="wait">
          <motion.h2
            key={currentView}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.2 }}
            className="text-sm font-bold tracking-widest uppercase"
            style={{
              fontFamily: 'Orbitron, monospace',
              color: 'rgba(255,255,255,0.6)',
            }}
          >
            {VIEW_LABELS[currentView]}
          </motion.h2>
        </AnimatePresence>
      </div>

      {/* ── Right: controls ── */}
      <div className="flex items-center gap-2">

        {/* Model selection dropdown */}
        <ModelSelector />

        {/* Model status indicator */}
        <ModelStatus />

        {/* Autonomy mode dropdown */}
        <div ref={autonomyRef} className="relative">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => setAutonomyOpen(o => !o)}
            className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all duration-200"
            style={{
              background: `${currentAutonomy.color}10`,
              border: `1px solid ${currentAutonomy.color}30`,
              color: currentAutonomy.color,
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 11,
              letterSpacing: '0.1em',
            }}
          >
            <currentAutonomy.icon className="w-3.5 h-3.5" />
            <span>{currentAutonomy.label}</span>
            <motion.div animate={{ rotate: autonomyOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
              <ChevronDown className="w-3.5 h-3.5" />
            </motion.div>
          </motion.button>

          <AnimatePresence>
            {autonomyOpen && (
              <motion.div
                variants={dropdownVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="absolute top-full right-0 mt-2 w-64 rounded-2xl overflow-hidden z-50"
                style={{
                  background: 'rgba(6,9,20,0.97)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  backdropFilter: 'blur(24px)',
                  boxShadow: '0 20px 60px rgba(0,0,0,0.7)',
                }}
              >
                {autonomyMode === 'god' && (
                  <div
                    className="flex items-center gap-2 px-4 py-2.5 text-xs"
                    style={{ background: 'rgba(239,68,68,0.08)', borderBottom: '1px solid rgba(239,68,68,0.15)' }}
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                    <span className="text-red-400/80 font-mono">Full system access active</span>
                  </div>
                )}
                <div className="p-2">
                  {AUTONOMY_OPTIONS.map(option => {
                    const Icon = option.icon
                    const active = autonomyMode === option.value
                    return (
                      <motion.button
                        key={option.value}
                        whileHover={{ x: 3 }}
                        onClick={() => { setAutonomyMode(option.value); setAutonomyOpen(false) }}
                        className="w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-150"
                        style={
                          active
                            ? { background: `${option.color}12`, border: `1px solid ${option.color}25` }
                            : { background: 'transparent', border: '1px solid transparent' }
                        }
                      >
                        <div
                          className="p-1.5 rounded-lg"
                          style={{ background: `${option.color}15` }}
                        >
                          <Icon className="w-3.5 h-3.5" style={{ color: option.color }} />
                        </div>
                        <div className="text-left flex-1">
                          <p className="text-sm font-semibold" style={{ color: active ? option.color : 'rgba(255,255,255,0.7)' }}>
                            {option.label}
                          </p>
                          <p className="text-[10px] text-white/30 font-mono mt-0.5">{option.desc}</p>
                        </div>
                        {active && (
                          <div
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ background: option.color, boxShadow: `0 0 6px ${option.color}` }}
                          />
                        )}
                      </motion.button>
                    )
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Divider */}
        <div className="w-px h-5" style={{ background: 'rgba(255,255,255,0.08)' }} />

        {/* Action icon buttons */}
        <motion.button
          whileHover={{ scale: 1.08, backgroundColor: 'rgba(255,255,255,0.07)' }}
          whileTap={{ scale: 0.93 }}
          onClick={() => {
            // Clear chat context - call backend and reload page to clear state
            fetch('/api/clear', { method: 'POST' })
              .then(() => window.location.reload())
              .catch(() => window.location.reload())
          }}
          title="Clear Context"
          className="p-2 rounded-xl transition-colors duration-200"
          style={{
            color: 'rgba(255,255,255,0.35)',
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <RefreshCw className="w-4 h-4" />
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.08, backgroundColor: 'rgba(255,255,255,0.07)' }}
          whileTap={{ scale: 0.93 }}
          onClick={() => onViewChange('security')}
          title="Security & Guard"
          className="p-2 rounded-xl transition-colors duration-200"
          style={{
            color: currentView === 'security' ? '#10b981' : 'rgba(255,255,255,0.35)',
            border: `1px solid ${currentView === 'security' ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.06)'}`,
            background: currentView === 'security' ? 'rgba(16,185,129,0.1)' : 'transparent',
          }}
        >
          <Shield className="w-4 h-4" />
        </motion.button>
      </div>
    </motion.header>
  )
}