import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity, Database, HardDrive, Zap,
  Globe, Server, Cloud, TrendingUp, Flame
} from 'lucide-react'

// ─── Exact schema from backend ────────────────────────────────────────────────

interface ProviderStats {
  daily_requests:     number
  daily_limit:        number
  daily_usage_percent: number
}

interface MongoDBStats {
  database_size_mb: number
  document_count:   number
}

interface PineconeStats {
  vector_count:          number
  index_fullness_percent: number
}

interface ApiStats {
  providers: {
    groq:        ProviderStats
    sambanova:   ProviderStats
    together:    ProviderStats
    openrouter:  ProviderStats
    fireworks:   ProviderStats
    gemini:      ProviderStats
    huggingface: ProviderStats
    ollama:      ProviderStats
  }
  storage: {
    mongodb:  MongoDBStats
    pinecone: PineconeStats
  }
  last_updated?: string
}

// ─── Provider metadata ────────────────────────────────────────────────────────

const PROVIDERS: {
  key: keyof ApiStats['providers']
  label: string
  color: string
  icon: JSX.Element
}[] = [
  { key: 'groq',        label: 'Groq',        color: '#10b981', icon: <Zap        className="w-5 h-5" /> },
  { key: 'sambanova',   label: 'SambaNova',   color: '#f59e0b', icon: <Server     className="w-5 h-5" /> },
  { key: 'together',    label: 'Together',    color: '#8b5cf6', icon: <Globe      className="w-5 h-5" /> },
  { key: 'openrouter',  label: 'OpenRouter',  color: '#06b6d4', icon: <Activity   className="w-5 h-5" /> },
  { key: 'fireworks',   label: 'Fireworks',   color: '#ef4444', icon: <Flame      className="w-5 h-5" /> },
  { key: 'gemini',      label: 'Gemini',      color: '#eab308', icon: <Cloud      className="w-5 h-5" /> },
  { key: 'huggingface', label: 'HuggingFace', color: '#f97316', icon: <TrendingUp className="w-5 h-5" /> },
  { key: 'ollama',      label: 'Ollama',      color: '#a78bfa', icon: <Database   className="w-5 h-5" /> },
]

// ─── Component ────────────────────────────────────────────────────────────────

export default function ApiDashboardView() {
  const [stats, setStats]   = useState<ApiStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState<string | null>(null)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/resources/stats')
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data: ApiStats = await res.json()
        setStats(data)
      } catch (e: any) {
        console.error('[ApiDashboard] fetch error:', e)
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    )
  }

  // ── Error ────────────────────────────────────────────────────────────────────
  if (error || !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl font-semibold text-red-400 mb-2">Failed to load usage data</p>
          <p className="text-sm text-gray-400">{error ?? 'No data returned'}</p>
        </div>
      </div>
    )
  }

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="h-full w-full overflow-y-auto p-6 pb-32">

      {/* ── Page header ── */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">API & Resource Dashboard</h1>
        <p className="text-gray-400">Monitor your AI provider usage and storage statistics</p>
      </motion.div>

      {/* ── Provider cards grid ── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8"
      >
        {PROVIDERS.map(({ key, label, color, icon }, index) => {
          const ps      = stats.providers[key]
          const today   = ps?.daily_requests      ?? 0
          const limit   = ps?.daily_limit         ?? 0
          const percent = ps?.daily_usage_percent ?? 0

          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.07 }}
              className="relative group"
              style={{
                background:     'rgba(6,9,20,0.8)',
                backdropFilter: 'blur(20px)',
                border:         `1px solid ${color}30`,
                borderRadius:   '16px',
                padding:        '20px',
              }}
            >
              {/* Hover glow overlay */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
                style={{
                  background:   `linear-gradient(135deg, ${color}18, transparent)`,
                  border:       `1px solid ${color}40`,
                  borderRadius: '16px',
                }}
              />

              <div className="relative z-10">
                {/* Card header */}
                <div className="flex items-center gap-2 mb-4">
                  <div
                    className="p-2 rounded-lg"
                    style={{ backgroundColor: `${color}20`, color }}
                  >
                    {icon}
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{label}</h3>
                    <p className="text-xs text-gray-400">AI Provider</p>
                  </div>
                </div>

                {/* Stats */}
                <div className="space-y-3">
                  {/* Today's requests — exact path: stats.providers[key].daily_requests */}
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">Today's Requests</span>
                    <span className="text-sm font-semibold text-white">{today}</span>
                  </div>

                  {/* Daily limit — exact path: stats.providers[key].daily_limit */}
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">Daily Limit</span>
                    <span className="text-sm font-semibold text-white">
                      {limit === 999999 ? '∞' : limit.toLocaleString()}
                    </span>
                  </div>

                  {/* Progress bar — exact path: stats.providers[key].daily_usage_percent */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-400">Usage</span>
                      <span className="text-xs text-gray-300">
                        {today} / {limit === 999999 ? '∞' : limit.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                      <motion.div
                        className="h-full rounded-full"
                        style={{ backgroundColor: color }}
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(percent, 100)}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                      />
                    </div>
                    <div className="text-xs text-gray-400 mt-1 text-right">
                      {percent.toFixed(2)}% used
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )
        })}
      </motion.div>

      {/* ── Storage cards ── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* ── MongoDB ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
          className="relative group"
          style={{
            background:     'rgba(6,9,20,0.8)',
            backdropFilter: 'blur(20px)',
            border:         '1px solid rgba(34,197,94,0.3)',
            borderRadius:   '16px',
            padding:        '24px',
          }}
        >
          <div
            className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
            style={{
              background:   'linear-gradient(135deg, rgba(34,197,94,0.18), transparent)',
              border:       '1px solid rgba(34,197,94,0.4)',
              borderRadius: '16px',
            }}
          />

          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(34,197,94,0.15)' }}>
                <Database className="w-6 h-6" style={{ color: '#22c55e' }} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">MongoDB</h3>
                <p className="text-sm text-gray-400">Chat History Database</p>
              </div>
            </div>

            <div className="space-y-4">
              {/* exact path: stats.storage.mongodb.database_size_mb */}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Database Size</span>
                <span className="text-lg font-semibold text-white">
                  {(stats.storage.mongodb.database_size_mb ?? 0).toFixed(2)} MB
                </span>
              </div>

              {/* exact path: stats.storage.mongodb.document_count */}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Document Count</span>
                <span className="text-lg font-semibold text-white">
                  {(stats.storage.mongodb.document_count ?? 0).toLocaleString()}
                </span>
              </div>

              {/* Visual fill bar — uses document_count as a proxy (capped at 10k) */}
              <div>
                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden mt-2">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: '#22c55e' }}
                    initial={{ width: 0 }}
                    animate={{
                      width: `${Math.min(
                        (stats.storage.mongodb.document_count / 10000) * 100,
                        100
                      )}%`,
                    }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1 text-right">
                  {stats.storage.mongodb.document_count} / 10,000 docs
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── Pinecone ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.5 }}
          className="relative group"
          style={{
            background:     'rgba(6,9,20,0.8)',
            backdropFilter: 'blur(20px)',
            border:         '1px solid rgba(139,92,246,0.3)',
            borderRadius:   '16px',
            padding:        '24px',
          }}
        >
          <div
            className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
            style={{
              background:   'linear-gradient(135deg, rgba(139,92,246,0.18), transparent)',
              border:       '1px solid rgba(139,92,246,0.4)',
              borderRadius: '16px',
            }}
          />

          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl" style={{ backgroundColor: 'rgba(139,92,246,0.15)' }}>
                <HardDrive className="w-6 h-6" style={{ color: '#8b5cf6' }} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Pinecone</h3>
                <p className="text-sm text-gray-400">Vector Memory Store</p>
              </div>
            </div>

            <div className="space-y-4">
              {/* exact path: stats.storage.pinecone.vector_count */}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Vector Count</span>
                <span className="text-lg font-semibold text-white">
                  {(stats.storage.pinecone.vector_count ?? 0).toLocaleString()}
                </span>
              </div>

              {/* exact path: stats.storage.pinecone.index_fullness_percent */}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Index Fullness</span>
                <span className="text-lg font-semibold text-white">
                  {(stats.storage.pinecone.index_fullness_percent ?? 0).toFixed(2)}%
                </span>
              </div>

              {/* Fullness progress bar */}
              <div>
                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden mt-2">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: '#8b5cf6' }}
                    initial={{ width: 0 }}
                    animate={{
                      width: `${Math.min(
                        stats.storage.pinecone.index_fullness_percent ?? 0,
                        100
                      )}%`,
                    }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1 text-right">
                  {(stats.storage.pinecone.index_fullness_percent ?? 0).toFixed(2)}% of index capacity
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* ── Footer timestamp ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.9 }}
        className="text-center text-sm text-gray-500 mt-8"
      >
        Last updated:{' '}
        {stats.last_updated
          ? new Date(stats.last_updated).toLocaleString()
          : new Date().toLocaleString()}
      </motion.div>
    </div>
  )
}