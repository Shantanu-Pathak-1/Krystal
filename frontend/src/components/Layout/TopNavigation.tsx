import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, RefreshCw, Camera, Shield, Mic, Zap, Eye, AlertTriangle } from 'lucide-react'
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
        {[
          { icon: RefreshCw, title: 'Clear Context',  action: () => {} },
          { icon: Camera,    title: 'Webcam Capture', action: () => {} },
          { icon: Shield,    title: 'Security Status', action: () => {} },
          ...(currentView === 'main' ? [{ icon: Mic, title: 'Voice Input', action: () => {} }] : []),
        ].map(({ icon: Icon, title, action }) => (
          <motion.button
            key={title}
            whileHover={{ scale: 1.08, backgroundColor: 'rgba(255,255,255,0.07)' }}
            whileTap={{ scale: 0.93 }}
            onClick={action}
            title={title}
            className="p-2 rounded-xl transition-colors duration-200"
            style={{
              color: 'rgba(255,255,255,0.35)',
              border: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <Icon className="w-4 h-4" />
          </motion.button>
        ))}
      </div>
    </motion.header>
  )
}