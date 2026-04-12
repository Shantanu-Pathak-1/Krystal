import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Database, Brain, Shield, Eye, EyeOff, Save, RotateCcw,
  CheckCircle, AlertTriangle, Zap, Lock, Server, Cpu,
  ChevronDown, ChevronUp
} from 'lucide-react'

/* ────────────────────────────────────────────────────────────── types ── */
interface Config {
  mongodb_uri: string
  pinecone_api_key: string
  pinecone_environment: string
  pinecone_index: string
  system_prompt: string
  max_tokens: number
  temperature: number
  safe_mode: boolean
  god_mode: boolean
  enable_voice: boolean
  enable_webcam: boolean
  api_timeout: number
  openai_api_key: string
  groq_api_key: string
  anthropic_api_key: string
  log_level: string
}

const DEFAULT_CONFIG: Config = {
  mongodb_uri: 'mongodb://localhost:27017/krystal',
  pinecone_api_key: '',
  pinecone_environment: 'us-west1-gcp',
  pinecone_index: 'krystal-memory',
  system_prompt:
    'You are Krystal, an advanced AI assistant with access to system tools, memory, and real-time data. Be precise, insightful, and always act in the user\'s best interest.',
  max_tokens: 2048,
  temperature: 0.72,
  safe_mode: false,
  god_mode: false,
  enable_voice: true,
  enable_webcam: true,
  api_timeout: 30,
  openai_api_key: '',
  groq_api_key: '',
  anthropic_api_key: '',
  log_level: 'INFO',
}

/* ─────────────────────────────────────────────────── micro components ── */

/** Glowing section card */
function GlassCard({
  children,
  accent = '#8b5cf6',
  delay = 0,
}: {
  children: React.ReactNode
  accent?: string
  delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
      className="relative rounded-2xl overflow-hidden"
      style={{
        background: 'rgba(255,255,255,0.025)',
        border: `1px solid rgba(255,255,255,0.07)`,
        backdropFilter: 'blur(14px)',
      }}
    >
      {/* Corner accent glow */}
      <div
        className="absolute -top-12 -right-12 w-32 h-32 rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(ellipse, ${accent}18 0%, transparent 70%)`,
          filter: 'blur(20px)',
        }}
      />
      {children}
    </motion.div>
  )
}

/** Section header bar */
function SectionHeader({
  icon: Icon,
  title,
  subtitle,
  accent,
  open,
  onToggle,
}: {
  icon: any
  title: string
  subtitle: string
  accent: string
  open: boolean
  onToggle: () => void
}) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center gap-4 px-6 py-5 text-left transition-colors duration-200 hover:bg-white/[0.02]"
    >
      <div
        className="p-2.5 rounded-xl flex-shrink-0"
        style={{ background: `${accent}15`, border: `1px solid ${accent}30` }}
      >
        <Icon className="w-5 h-5" style={{ color: accent }} />
      </div>
      <div className="flex-1">
        <p
          className="text-sm font-bold tracking-wider uppercase"
          style={{ color: 'rgba(255,255,255,0.85)', fontFamily: 'Orbitron, monospace', fontSize: 11 }}
        >
          {title}
        </p>
        <p className="text-[11px] text-white/30 font-mono mt-0.5">{subtitle}</p>
      </div>
      <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.25 }}>
        <ChevronDown className="w-4 h-4 text-white/25" />
      </motion.div>
    </button>
  )
}

/** Futuristic text input */
function NeonInput({
  label,
  value,
  onChange,
  placeholder,
  description,
  secret,
  mono,
  type = 'text',
  accent = '#8b5cf6',
}: {
  label: string
  value: string | number
  onChange: (v: string) => void
  placeholder?: string
  description?: string
  secret?: boolean
  mono?: boolean
  type?: string
  accent?: string
}) {
  const [visible, setVisible] = useState(false)
  const [focused, setFocused] = useState(false)
  const inputType = secret ? (visible ? 'text' : 'password') : type

  return (
    <div>
      <label
        className="block text-[11px] font-semibold tracking-widest uppercase mb-2"
        style={{ color: focused ? accent : 'rgba(255,255,255,0.4)', fontFamily: 'JetBrains Mono, monospace' }}
      >
        {label}
      </label>
      <div className="relative">
        <input
          type={inputType}
          value={value}
          onChange={e => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          className="w-full px-4 py-3 text-sm bg-transparent rounded-xl outline-none transition-all duration-200"
          style={{
            background: focused ? `${accent}08` : 'rgba(255,255,255,0.025)',
            border: `1px solid ${focused ? `${accent}50` : 'rgba(255,255,255,0.08)'}`,
            color: 'rgba(255,255,255,0.85)',
            fontFamily: mono ? 'JetBrains Mono, monospace' : 'Syne, sans-serif',
            fontSize: mono ? 12 : 14,
            boxShadow: focused ? `0 0 0 3px ${accent}12, 0 0 20px ${accent}08` : 'none',
            paddingRight: secret ? 48 : undefined,
          }}
        />
        {secret && (
          <button
            type="button"
            onClick={() => setVisible(v => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg transition-colors"
            style={{ color: visible ? accent : 'rgba(255,255,255,0.25)' }}
          >
            {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
      {description && (
        <p className="text-[10px] text-white/20 font-mono mt-1.5 px-1">{description}</p>
      )}
    </div>
  )
}

/** Futuristic textarea */
function NeonTextarea({
  label,
  value,
  onChange,
  rows = 5,
  accent = '#8b5cf6',
  description,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  rows?: number
  accent?: string
  description?: string
}) {
  const [focused, setFocused] = useState(false)
  return (
    <div>
      <label
        className="block text-[11px] font-semibold tracking-widest uppercase mb-2"
        style={{ color: focused ? accent : 'rgba(255,255,255,0.4)', fontFamily: 'JetBrains Mono, monospace' }}
      >
        {label}
      </label>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        rows={rows}
        className="w-full px-4 py-3 text-sm rounded-xl outline-none resize-none transition-all duration-200"
        style={{
          background: focused ? `${accent}08` : 'rgba(255,255,255,0.025)',
          border: `1px solid ${focused ? `${accent}50` : 'rgba(255,255,255,0.08)'}`,
          color: 'rgba(255,255,255,0.82)',
          fontFamily: 'Syne, sans-serif',
          boxShadow: focused ? `0 0 0 3px ${accent}12, 0 0 20px ${accent}08` : 'none',
        }}
      />
      {description && (
        <p className="text-[10px] text-white/20 font-mono mt-1.5 px-1">{description}</p>
      )}
    </div>
  )
}

/** Dial/slider component */
function NeonSlider({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  format,
  accent = '#8b5cf6',
}: {
  label: string
  value: number
  min: number
  max: number
  step?: number
  onChange: (v: number) => void
  format?: (v: number) => string
  accent?: string
}) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label
          className="text-[11px] font-semibold tracking-widest uppercase"
          style={{ color: 'rgba(255,255,255,0.4)', fontFamily: 'JetBrains Mono, monospace' }}
        >
          {label}
        </label>
        <span
          className="text-sm font-bold"
          style={{ color: accent, fontFamily: 'JetBrains Mono, monospace', textShadow: `0 0 10px ${accent}60` }}
        >
          {format ? format(value) : value}
        </span>
      </div>
      <div className="relative">
        {/* Track */}
        <div
          className="h-1.5 rounded-full relative overflow-hidden"
          style={{ background: 'rgba(255,255,255,0.06)' }}
        >
          {/* Fill */}
          <motion.div
            className="absolute left-0 top-0 h-full rounded-full"
            style={{
              width: `${pct}%`,
              background: `linear-gradient(90deg, ${accent}80, ${accent})`,
              boxShadow: `0 0 8px ${accent}60`,
            }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.15 }}
          />
        </div>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
      </div>
    </div>
  )
}

/** Toggle switch */
function NeonToggle({
  label,
  value,
  onChange,
  description,
  accent = '#8b5cf6',
  danger,
}: {
  label: string
  value: boolean
  onChange: (v: boolean) => void
  description?: string
  accent?: string
  danger?: boolean
}) {
  const color = danger ? '#ef4444' : (value ? accent : 'rgba(255,255,255,0.15)')
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex-1">
        <p className="text-sm font-semibold text-white/75">{label}</p>
        {description && <p className="text-[10px] text-white/25 font-mono mt-0.5">{description}</p>}
      </div>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className="relative flex-shrink-0 w-12 h-6 rounded-full transition-all duration-300"
        style={{
          background: value ? `${danger ? '#ef4444' : accent}30` : 'rgba(255,255,255,0.06)',
          border: `1px solid ${value ? (danger ? 'rgba(239,68,68,0.5)' : `${accent}50`) : 'rgba(255,255,255,0.1)'}`,
          boxShadow: value ? `0 0 14px ${danger ? 'rgba(239,68,68,0.4)' : `${accent}40`}` : 'none',
        }}
      >
        <motion.div
          className="absolute top-0.5 w-5 h-5 rounded-full"
          animate={{ left: value ? 'calc(100% - 22px)' : '2px' }}
          transition={{ type: 'spring', stiffness: 500, damping: 35 }}
          style={{
            background: value
              ? `linear-gradient(135deg, ${danger ? '#f87171' : '#fff'}, ${danger ? '#ef4444' : accent})`
              : 'rgba(255,255,255,0.25)',
            boxShadow: value ? `0 0 10px ${danger ? 'rgba(239,68,68,0.6)' : `${accent}80`}` : 'none',
          }}
        />
      </button>
    </div>
  )
}

/** Select dropdown */
function NeonSelect({
  label,
  value,
  options,
  onChange,
  accent = '#8b5cf6',
}: {
  label: string
  value: string
  options: { value: string; label: string }[]
  onChange: (v: string) => void
  accent?: string
}) {
  const [focused, setFocused] = useState(false)
  return (
    <div>
      <label
        className="block text-[11px] font-semibold tracking-widest uppercase mb-2"
        style={{ color: focused ? accent : 'rgba(255,255,255,0.4)', fontFamily: 'JetBrains Mono, monospace' }}
      >
        {label}
      </label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className="w-full px-4 py-3 text-sm rounded-xl outline-none transition-all duration-200 appearance-none cursor-pointer"
        style={{
          background: focused ? `${accent}08` : 'rgba(255,255,255,0.025)',
          border: `1px solid ${focused ? `${accent}50` : 'rgba(255,255,255,0.08)'}`,
          color: 'rgba(255,255,255,0.85)',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: 12,
          boxShadow: focused ? `0 0 0 3px ${accent}12` : 'none',
        }}
      >
        {options.map(o => (
          <option key={o.value} value={o.value} style={{ background: '#06090f', color: 'white' }}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  )
}

/* ─────────────────────────────────────────────────────── main view ── */
export default function ConfigView() {
  const [config, setConfig] = useState<Config>(DEFAULT_CONFIG)
  const [hasChanges, setHasChanges] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [open, setOpen] = useState<Record<string, boolean>>({
    database: true,
    vector: true,
    personality: true,
    autonomy: true,
    api: false,
    system: false,
  })

  // Load config from localStorage and backend on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        // First try to load from localStorage
        const localConfig = localStorage.getItem('krystal_config')
        if (localConfig) {
          const parsed = JSON.parse(localConfig)
          setConfig(prev => ({ ...prev, ...parsed }))
        }
        
        // Then try to fetch from backend
        const res = await fetch('http://localhost:8000/api/config')
        if (res.ok) {
          const data = await res.json()
          if (data.config) {
            setConfig(prev => ({ ...prev, ...data.config }))
          }
        }
      } catch (e) {
        setLoadError('Failed to load configuration from server')
      }
    }
    
    loadConfig()
  }, [])

  const update = <K extends keyof Config>(key: K, val: Config[K]) => {
    setConfig(prev => ({ ...prev, [key]: val }))
    setHasChanges(true)
    setSaved(false)
  }

  const toggle = (section: string) =>
    setOpen(prev => ({ ...prev, [section]: !prev[section] }))

  const handleSave = async () => {
    setSaving(true)
    setLoadError(null)
    
    try {
      // Save to localStorage
      localStorage.setItem('krystal_config', JSON.stringify(config))
      
      // Save to backend
      const res = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      
      if (!res.ok) {
        throw new Error('Failed to save to backend')
      }
      
      setSaving(false)
      setSaved(true)
      setHasChanges(false)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      setSaving(false)
      setLoadError('Failed to save configuration. Changes saved locally only.')
      // Still mark as saved locally
      setSaved(true)
      setHasChanges(false)
      setTimeout(() => setSaved(false), 3000)
    }
  }

  const handleReset = () => {
    setConfig(DEFAULT_CONFIG)
    localStorage.removeItem('krystal_config')
    setHasChanges(false)
    setSaved(false)
  }

  return (
    <div
      className="relative h-full overflow-y-auto"
      style={{ background: 'linear-gradient(160deg, #03050e 0%, #060916 100%)' }}
    >
      {/* Background grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(rgba(139,92,246,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.03) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />
      {/* Ambient glows */}
      <div
        className="absolute top-0 right-0 w-80 h-80 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(139,92,246,0.07) 0%, transparent 65%)', filter: 'blur(50px)' }}
      />
      <div
        className="absolute bottom-0 left-0 w-64 h-64 pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(6,182,212,0.06) 0%, transparent 65%)', filter: 'blur(50px)' }}
      />

      <div className="relative z-10 max-w-3xl mx-auto px-6 py-8">

        {/* ── Header ── */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1
              className="text-2xl font-bold"
              style={{
                fontFamily: 'Orbitron, monospace',
                background: 'linear-gradient(135deg, #e2e8f0 0%, #a78bfa 55%, #22d3ee 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              System Config
            </h1>
            <p className="text-[11px] text-white/25 font-mono mt-1">
              Krystal AI core settings & integrations
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Reset */}
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleReset}
              disabled={!hasChanges}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm transition-all"
              style={{
                background: hasChanges ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.08)',
                color: hasChanges ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.18)',
                cursor: hasChanges ? 'pointer' : 'not-allowed',
              }}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="text-xs font-mono">Reset</span>
            </motion.button>

            {/* Save button */}
            <motion.button
              whileHover={hasChanges && !saving ? { scale: 1.04, y: -2 } : {}}
              whileTap={hasChanges && !saving ? { scale: 0.96 } : {}}
              onClick={handleSave}
              disabled={!hasChanges || saving}
              className="relative flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-sm font-semibold overflow-hidden transition-all"
              style={{
                background: saved
                  ? 'rgba(16,185,129,0.15)'
                  : hasChanges
                    ? 'linear-gradient(135deg, rgba(139,92,246,0.8), rgba(109,40,217,0.8))'
                    : 'rgba(255,255,255,0.04)',
                border: saved
                  ? '1px solid rgba(16,185,129,0.4)'
                  : hasChanges
                    ? '1px solid rgba(139,92,246,0.5)'
                    : '1px solid rgba(255,255,255,0.06)',
                color: saved ? '#34d399' : hasChanges ? 'white' : 'rgba(255,255,255,0.2)',
                boxShadow: hasChanges && !saved
                  ? '0 0 24px rgba(139,92,246,0.35), 0 0 60px rgba(139,92,246,0.12)'
                  : saved
                    ? '0 0 16px rgba(16,185,129,0.3)'
                    : 'none',
                cursor: hasChanges && !saving ? 'pointer' : 'not-allowed',
              }}
            >
              {/* Shimmer on active */}
              {hasChanges && !saving && !saved && (
                <motion.div
                  className="absolute inset-0"
                  style={{
                    background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.08) 50%, transparent 60%)',
                    backgroundSize: '200% 100%',
                  }}
                  animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
                  transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
                />
              )}

              <AnimatePresence mode="wait">
                {saving ? (
                  <motion.div
                    key="saving"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    <motion.div
                      className="w-3.5 h-3.5 rounded-full border-2 border-t-transparent border-white"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                    />
                    <span>Saving…</span>
                  </motion.div>
                ) : saved ? (
                  <motion.div
                    key="saved"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Saved</span>
                  </motion.div>
                ) : (
                  <motion.div
                    key="default"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Config</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          </div>
        </motion.div>

        {/* ── Unsaved changes banner ── */}
        <AnimatePresence>
          {hasChanges && (
            <motion.div
              initial={{ opacity: 0, height: 0, marginBottom: 0 }}
              animate={{ opacity: 1, height: 'auto', marginBottom: 24 }}
              exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              className="flex items-center gap-3 px-4 py-3 rounded-xl"
              style={{ background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.18)' }}
            >
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <p className="text-xs text-amber-300/70 font-mono">You have unsaved changes — save before leaving this page.</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Error banner ── */}
        <AnimatePresence>
          {loadError && (
            <motion.div
              initial={{ opacity: 0, height: 0, marginBottom: 0 }}
              animate={{ opacity: 1, height: 'auto', marginBottom: 24 }}
              exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              className="flex items-center gap-3 px-4 py-3 rounded-xl"
              style={{ background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.18)' }}
            >
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <p className="text-xs text-red-300/70 font-mono">{loadError}</p>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="space-y-4">

          {/* ═══════════════════ DATABASE CONNECTIONS ═══════════════════ */}
          <GlassCard accent="#06b6d4" delay={0.05}>
            <SectionHeader
              icon={Database}
              title="Database Connections"
              subtitle="MongoDB · persistent chat & memory storage"
              accent="#06b6d4"
              open={open.database}
              onToggle={() => toggle('database')}
            />
            <AnimatePresence>
              {open.database && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                  className="overflow-hidden"
                >
                  <div
                    className="px-6 pb-6 pt-1 space-y-5"
                    style={{ borderTop: '1px solid rgba(6,182,212,0.08)' }}
                  >
                    <NeonInput
                      label="MongoDB URI"
                      value={config.mongodb_uri}
                      onChange={v => update('mongodb_uri', v)}
                      placeholder="mongodb://localhost:27017/krystal"
                      description="Full connection string — supports Atlas, replica sets, and auth URIs."
                      mono
                      accent="#06b6d4"
                    />
                    <div className="flex items-center gap-3 px-4 py-3 rounded-xl"
                      style={{ background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.1)' }}
                    >
                      <motion.div
                        className="w-2 h-2 rounded-full bg-cyan-400 flex-shrink-0"
                        animate={{ opacity: [1, 0.3, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        style={{ boxShadow: '0 0 8px rgba(6,182,212,0.9)' }}
                      />
                      <p className="text-[10px] text-cyan-400/60 font-mono">
                        Connection will be tested on save. Ensure the DB is reachable from the API host.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

          {/* ═══════════════════ VECTOR MEMORY ═══════════════════════════ */}
          <GlassCard accent="#8b5cf6" delay={0.1}>
            <SectionHeader
              icon={Brain}
              title="Vector Memory"
              subtitle="Pinecone · long-term semantic memory store"
              accent="#8b5cf6"
              open={open.vector}
              onToggle={() => toggle('vector')}
            />
            <AnimatePresence>
              {open.vector && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                  className="overflow-hidden"
                >
                  <div
                    className="px-6 pb-6 pt-1 space-y-5"
                    style={{ borderTop: '1px solid rgba(139,92,246,0.08)' }}
                  >
                    <NeonInput
                      label="Pinecone API Key"
                      value={config.pinecone_api_key}
                      onChange={v => update('pinecone_api_key', v)}
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      description="Found in your Pinecone console → API Keys."
                      secret
                      mono
                      accent="#8b5cf6"
                    />
                    <div className="grid grid-cols-2 gap-4">
                      <NeonSelect
                        label="Environment"
                        value={config.pinecone_environment}
                        onChange={v => update('pinecone_environment', v)}
                        options={[
                          { value: 'us-west1-gcp', label: 'US West 1 (GCP)' },
                          { value: 'us-east1-gcp', label: 'US East 1 (GCP)' },
                          { value: 'eu-west1-gcp', label: 'EU West 1 (GCP)' },
                          { value: 'gcp-starter',  label: 'GCP Starter' },
                        ]}
                        accent="#8b5cf6"
                      />
                      <NeonInput
                        label="Index Name"
                        value={config.pinecone_index}
                        onChange={v => update('pinecone_index', v)}
                        placeholder="krystal-memory"
                        mono
                        accent="#8b5cf6"
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

          {/* ═══════════════════ CORE PERSONALITY ════════════════════════ */}
          <GlassCard accent="#a78bfa" delay={0.15}>
            <SectionHeader
              icon={Cpu}
              title="Core Personality"
              subtitle="System prompt · model params · behavioral tuning"
              accent="#a78bfa"
              open={open.personality}
              onToggle={() => toggle('personality')}
            />
            <AnimatePresence>
              {open.personality && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                  className="overflow-hidden"
                >
                  <div
                    className="px-6 pb-6 pt-1 space-y-5"
                    style={{ borderTop: '1px solid rgba(167,139,250,0.08)' }}
                  >
                    <NeonTextarea
                      label="System Prompt Override"
                      value={config.system_prompt}
                      onChange={v => update('system_prompt', v)}
                      rows={5}
                      accent="#a78bfa"
                      description="Defines Krystal's core identity, constraints, and reasoning style."
                    />
                    <div className="grid grid-cols-2 gap-6">
                      <NeonSlider
                        label="Temperature"
                        value={config.temperature}
                        min={0}
                        max={2}
                        step={0.01}
                        onChange={v => update('temperature', v)}
                        format={v => v.toFixed(2)}
                        accent="#a78bfa"
                      />
                      <NeonSlider
                        label="Max Tokens"
                        value={config.max_tokens}
                        min={256}
                        max={8192}
                        step={128}
                        onChange={v => update('max_tokens', v)}
                        format={v => v.toLocaleString()}
                        accent="#a78bfa"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      <NeonSlider
                        label="API Timeout (s)"
                        value={config.api_timeout}
                        min={5}
                        max={120}
                        step={5}
                        onChange={v => update('api_timeout', v)}
                        format={v => `${v}s`}
                        accent="#a78bfa"
                      />
                      <NeonSelect
                        label="Log Level"
                        value={config.log_level}
                        onChange={v => update('log_level', v)}
                        options={[
                          { value: 'DEBUG',   label: 'DEBUG — verbose' },
                          { value: 'INFO',    label: 'INFO — default' },
                          { value: 'WARNING', label: 'WARNING' },
                          { value: 'ERROR',   label: 'ERROR — silent' },
                        ]}
                        accent="#a78bfa"
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

          {/* ═══════════════════ AUTONOMY MODE ═══════════════════════════ */}
          <GlassCard accent="#ef4444" delay={0.2}>
            <SectionHeader
              icon={Shield}
              title="Autonomy Mode"
              subtitle="Safe mode · God mode · system access levels"
              accent={config.god_mode ? '#ef4444' : '#10b981'}
              open={open.autonomy}
              onToggle={() => toggle('autonomy')}
            />
            <AnimatePresence>
              {open.autonomy && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                  className="overflow-hidden"
                >
                  <div
                    className="px-6 pb-6 pt-1 space-y-4"
                    style={{ borderTop: '1px solid rgba(239,68,68,0.08)' }}
                  >
                    <NeonToggle
                      label="Safe Mode"
                      value={config.safe_mode}
                      onChange={v => { update('safe_mode', v); if (v) update('god_mode', false) }}
                      description="Restricts Krystal to chat-only. No system access, no tool calls."
                      accent="#10b981"
                    />
                    <NeonToggle
                      label="Voice Input"
                      value={config.enable_voice}
                      onChange={v => update('enable_voice', v)}
                      description="Allow microphone access for voice commands."
                      accent="#06b6d4"
                    />
                    <NeonToggle
                      label="Webcam Access"
                      value={config.enable_webcam}
                      onChange={v => update('enable_webcam', v)}
                      description="Allow camera access for visual context."
                      accent="#06b6d4"
                    />

                    {/* God Mode — danger zone */}
                    <div
                      className="pt-3 mt-3"
                      style={{ borderTop: '1px solid rgba(239,68,68,0.12)' }}
                    >
                      <div
                        className="p-4 rounded-xl space-y-3"
                        style={{
                          background: config.god_mode ? 'rgba(239,68,68,0.06)' : 'rgba(255,255,255,0.02)',
                          border: `1px solid ${config.god_mode ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.06)'}`,
                          transition: 'all 0.3s ease',
                        }}
                      >
                        <AnimatePresence>
                          {config.god_mode && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              className="flex items-center gap-2"
                            >
                              <AlertTriangle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                              <p className="text-[10px] text-red-400/70 font-mono">
                                God Mode active — Krystal has unrestricted OS and Trinetra access.
                              </p>
                            </motion.div>
                          )}
                        </AnimatePresence>
                        <NeonToggle
                          label="God Mode"
                          value={config.god_mode}
                          onChange={v => { update('god_mode', v); if (v) update('safe_mode', false) }}
                          description="Full OS access, file system, network, and Trinetra visual engine."
                          accent="#ef4444"
                          danger
                        />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

          {/* ═══════════════════ API KEYS (collapsible) ═══════════════════ */}
          <GlassCard accent="#f59e0b" delay={0.25}>
            <SectionHeader
              icon={Lock}
              title="API Keys"
              subtitle="LLM providers — OpenAI · Groq · Anthropic"
              accent="#f59e0b"
              open={open.api}
              onToggle={() => toggle('api')}
            />
            <AnimatePresence>
              {open.api && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                  className="overflow-hidden"
                >
                  <div
                    className="px-6 pb-6 pt-1 space-y-5"
                    style={{ borderTop: '1px solid rgba(245,158,11,0.08)' }}
                  >
                    <NeonInput
                      label="OpenAI API Key"
                      value={config.openai_api_key}
                      onChange={v => update('openai_api_key', v)}
                      placeholder="sk-..."
                      secret mono accent="#f59e0b"
                    />
                    <NeonInput
                      label="Groq API Key"
                      value={config.groq_api_key}
                      onChange={v => update('groq_api_key', v)}
                      placeholder="gsk_..."
                      secret mono accent="#f59e0b"
                    />
                    <NeonInput
                      label="Anthropic API Key"
                      value={config.anthropic_api_key}
                      onChange={v => update('anthropic_api_key', v)}
                      placeholder="sk-ant-..."
                      secret mono accent="#f59e0b"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

        </div>

        {/* ── Footer save bar ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 flex items-center justify-between px-5 py-4 rounded-2xl"
          style={{
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <div className="flex items-center gap-2.5">
            <motion.div
              className="w-2 h-2 rounded-full"
              animate={hasChanges ? { opacity: [1, 0.3, 1] } : { opacity: 1 }}
              transition={{ duration: 1.5, repeat: Infinity }}
              style={{
                background: hasChanges ? '#f59e0b' : saved ? '#10b981' : 'rgba(255,255,255,0.15)',
                boxShadow: hasChanges
                  ? '0 0 8px rgba(245,158,11,0.8)'
                  : saved
                    ? '0 0 8px rgba(16,185,129,0.8)'
                    : 'none',
              }}
            />
            <span className="text-xs font-mono text-white/30">
              {hasChanges ? 'Unsaved changes' : saved ? 'All changes saved' : 'Config up to date'}
            </span>
          </div>
          <span className="text-[10px] text-white/15 font-mono">
            {new Date().toLocaleDateString()} · Krystal Config v1.0
          </span>
        </motion.div>

        {/* bottom padding */}
        <div className="h-8" />
      </div>
    </div>
  )
}