import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { usePerformance } from '../../context/PerformanceContext'
import {
  Database, Clock, Cpu, HardDrive, Wifi, Shield,
  Users, Brain, Zap, Activity, Server, RefreshCw,
  TrendingUp, AlertTriangle
} from 'lucide-react'

interface SystemStats {
  cpu_usage: number
  memory_usage: number
  memory_used_gb: number
  memory_total_gb: number
  disk_usage: number
  disk_used_gb: number
  disk_total_gb: number
  net_sent_mb: number
  net_recv_mb: number
  db_connected: boolean
  pinecone_active: boolean
  engine_loaded: boolean
  uptime: string
  total_memories: number
  active_sessions: number
  process_count: number
  cpu_temp: number | null
  api_requests_24h: number
  network_status: boolean
  system_health: 'healthy' | 'warning' | 'critical' | 'error'
  last_error: string | null
  timestamp: string
}

const INITIAL_STATS: SystemStats = {
  cpu_usage: 0, memory_usage: 0, disk_usage: 0,
  memory_used_gb: 0, memory_total_gb: 0,
  disk_used_gb: 0, disk_total_gb: 0,
  net_sent_mb: 0, net_recv_mb: 0,
  db_connected: false, pinecone_active: false, engine_loaded: false,
  uptime: '00:00:00', total_memories: 0, active_sessions: 0,
  process_count: 0, cpu_temp: null, api_requests_24h: 0,
  network_status: false, system_health: 'error', last_error: null,
  timestamp: '',
}

/* ── SVG Progress Ring ─────────────────────────────────────────────────── */
function RingMetric({
  value, label, sublabel, color, size = 120, strokeWidth = 6
}: {
  value: number; label: string; sublabel?: string
  color: string; size?: number; strokeWidth?: number
}) {
  const r = (size - strokeWidth * 2) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - Math.min(value, 100) / 100)

  const healthColor =
    value < 50 ? color :
    value < 80 ? '#f59e0b' :
    '#ef4444'

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Track */}
          <circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={strokeWidth}
          />
          {/* Bar */}
          <motion.circle
            cx={size / 2} cy={size / 2} r={r}
            fill="none"
            stroke={healthColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: [0.34, 1.56, 0.64, 1] }}
            style={{ filter: `drop-shadow(0 0 6px ${healthColor}90)` }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-bold leading-none"
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: size * 0.2,
              color: healthColor,
              textShadow: `0 0 12px ${healthColor}80`,
            }}
          >
            {value.toFixed(0)}%
          </span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-[11px] font-semibold text-white/80 tracking-wider uppercase">{label}</p>
        {sublabel && <p className="text-[10px] text-white/35 mt-0.5" style={{ fontFamily: 'JetBrains Mono, monospace' }}>{sublabel}</p>}
      </div>
    </div>
  )
}

/* ── Animated stat card ───────────────────────────────────────────────── */
function StatCard({
  icon: Icon, label, value, sub, accent, delay = 0
}: {
  icon: any; label: string; value: string | number; sub?: string
  accent: string; delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      whileHover={{ y: -3, transition: { duration: 0.2 } }}
      className="relative overflow-hidden rounded-2xl p-5 group cursor-default"
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.07)',
        backdropFilter: 'blur(12px)',
      }}
    >
      {/* Corner accent glow */}
      <div
        className="absolute -top-6 -right-6 w-20 h-20 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{ background: `radial-gradient(ellipse, ${accent}25 0%, transparent 70%)` }}
      />

      <div className="flex items-start justify-between mb-4">
        <div
          className="p-2 rounded-xl"
          style={{ background: `${accent}18`, border: `1px solid ${accent}30` }}
        >
          <Icon className="w-5 h-5" style={{ color: accent }} />
        </div>
        <motion.div
          key={String(value)}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-right"
        >
          <p
            className="text-2xl font-bold leading-none"
            style={{
              color: accent,
              fontFamily: 'JetBrains Mono, monospace',
              textShadow: `0 0 20px ${accent}60`,
            }}
          >
            {value}
          </p>
        </motion.div>
      </div>

      <p className="text-xs font-semibold text-white/50 tracking-widest uppercase">{label}</p>
      {sub && <p className="text-[10px] text-white/25 mt-1 font-mono">{sub}</p>}
    </motion.div>
  )
}

/* ── Service status pill ──────────────────────────────────────────────── */
function ServiceBadge({ label, online, sub }: { label: string; online: boolean; sub: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center justify-between px-4 py-3 rounded-xl"
      style={{
        background: online ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
        border: `1px solid ${online ? 'rgba(16,185,129,0.18)' : 'rgba(239,68,68,0.18)'}`,
      }}
    >
      <div className="flex items-center gap-3">
        <motion.div
          className="w-2 h-2 rounded-full"
          animate={online ? { opacity: [1, 0.3, 1] } : {}}
          transition={{ duration: 1.8, repeat: Infinity }}
          style={{
            background: online ? '#10b981' : '#ef4444',
            boxShadow: online ? '0 0 8px rgba(16,185,129,0.9)' : '0 0 8px rgba(239,68,68,0.6)',
          }}
        />
        <div>
          <p className="text-sm font-semibold text-white/80">{label}</p>
          <p className="text-[10px] text-white/30 font-mono">{sub}</p>
        </div>
      </div>
      <span
        className="text-[10px] font-bold tracking-widest uppercase px-2 py-1 rounded-lg"
        style={{
          background: online ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
          color: online ? '#34d399' : '#f87171',
          fontFamily: 'JetBrains Mono, monospace',
        }}
      >
        {online ? 'ONLINE' : 'OFFLINE'}
      </span>
    </motion.div>
  )
}

/* ── Container stagger ─────────────────────────────────────────────────── */
const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } }
}

/* ── Main Dashboard ─────────────────────────────────────────────────────── */
export default function DashboardView() {
  const { pollingInterval, enableAnimations } = usePerformance()
  const [stats, setStats] = useState<SystemStats>(INITIAL_STATS)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/dashboard/stats')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStats(data)
      setError(null)
      setLastRefresh(new Date())
    } catch (e) {
      setError('Cannot reach API — is the backend running on :8000?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    const id = setInterval(fetchStats, pollingInterval)
    return () => clearInterval(id)
  }, [pollingInterval])

  const healthColor =
    stats.system_health === 'healthy'  ? '#10b981' :
    stats.system_health === 'warning'  ? '#f59e0b' :
    stats.system_health === 'critical' ? '#ef4444' : '#6b7280'

  return (
    <div
      className="relative h-full overflow-y-auto scrollbar-none"
      style={{ background: 'linear-gradient(160deg, #04070f 0%, #060a16 100%)' }}
    >
      {/* Grid background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(139,92,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.04) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />
      {/* Ambient glows */}
      <div className="absolute top-0 right-0 w-96 h-96 pointer-events-none" style={{ background: 'radial-gradient(ellipse at top right, rgba(139,92,246,0.08) 0%, transparent 60%)', filter: 'blur(40px)' }} />
      <div className="absolute bottom-0 left-0 w-80 h-80 pointer-events-none" style={{ background: 'radial-gradient(ellipse at bottom left, rgba(6,182,212,0.07) 0%, transparent 60%)', filter: 'blur(40px)' }} />

      <div className="relative z-10 p-7">

        {/* ── Header ── */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-start justify-between mb-8"
        >
          <div>
            <h1
              className="text-3xl font-bold tracking-tight"
              style={{
                fontFamily: 'Orbitron, monospace',
                background: 'linear-gradient(135deg, #e2e8f0 0%, #a78bfa 50%, #22d3ee 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              AI Control Center
            </h1>
            <p className="text-sm text-white/35 mt-1 font-mono">
              Live metrics refreshing every {pollingInterval / 1000}s ·{' '}
              <span style={{ color: healthColor }}>
                {stats.system_health.toUpperCase()}
              </span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Health badge */}
            <div
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
              style={{
                background: `${healthColor}12`,
                border: `1px solid ${healthColor}30`,
                color: healthColor,
                fontFamily: 'JetBrains Mono, monospace',
                textShadow: `0 0 10px ${healthColor}60`,
              }}
            >
              <motion.div
                className="w-2 h-2 rounded-full"
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                style={{ background: healthColor, boxShadow: `0 0 8px ${healthColor}` }}
              />
              {stats.system_health}
            </div>

            {/* Refresh indicator */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={fetchStats}
              className="p-2 rounded-xl transition-colors"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
              title="Refresh now"
            >
              <motion.div
                animate={loading ? { rotate: 360 } : {}}
                transition={{ duration: 1, repeat: loading ? Infinity : 0, ease: 'linear' }}
              >
                <RefreshCw className="w-4 h-4 text-white/40" />
              </motion.div>
            </motion.button>
          </div>
        </motion.div>

        {/* ── Error banner ── */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="flex items-center gap-3 px-4 py-3 rounded-xl mb-6"
              style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
            >
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <p className="text-sm text-red-300/80 font-mono">{error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Top stat cards ── */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          <StatCard icon={Brain}     label="Vector Memories"  value={stats.total_memories}      sub="Stored embeddings"   accent="#8b5cf6" delay={0.0} />
          <StatCard icon={Users}     label="Active Sessions"  value={stats.active_sessions}     sub="Current connections" accent="#06b6d4" delay={0.07} />
          <StatCard icon={Clock}     label="Uptime"           value={stats.uptime}              sub="Since last restart"  accent="#a78bfa" delay={0.14} />
          <StatCard icon={Zap}       label="API Requests"     value={stats.api_requests_24h}    sub="This session"        accent="#f59e0b" delay={0.21} />
        </motion.div>

        {/* ── Resource rings + service status ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

          {/* Ring metrics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="lg:col-span-2 rounded-2xl p-6"
            style={{
              background: 'rgba(255,255,255,0.025)',
              border: '1px solid rgba(255,255,255,0.07)',
              backdropFilter: 'blur(12px)',
            }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-sm font-bold tracking-widest uppercase text-white/50" style={{ fontFamily: 'Orbitron, monospace' }}>
                System Resources
              </h2>
              <Activity className="w-4 h-4 text-white/25" />
            </div>

            <div className="grid grid-cols-3 gap-6">
              <RingMetric
                value={stats.cpu_usage}
                label="CPU"
                sublabel={stats.cpu_temp ? `${stats.cpu_temp}°C` : `${stats.process_count} procs`}
                color="#8b5cf6"
                size={130}
              />
              <RingMetric
                value={stats.memory_usage}
                label="Memory"
                sublabel={`${stats.memory_used_gb} / ${stats.memory_total_gb} GB`}
                color="#06b6d4"
                size={130}
              />
              <RingMetric
                value={stats.disk_usage}
                label="Disk"
                sublabel={`${stats.disk_used_gb} / ${stats.disk_total_gb} GB`}
                color="#10b981"
                size={130}
              />
            </div>

            {/* Network row */}
            <div className="grid grid-cols-2 gap-4 mt-6 pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <div className="flex items-center gap-3">
                <TrendingUp className="w-4 h-4 text-white/30" />
                <div>
                  <p className="text-[10px] text-white/30 uppercase tracking-widest">Sent</p>
                  <p className="text-sm font-bold font-mono text-white/70">{stats.net_sent_mb.toFixed(1)} MB</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <TrendingUp className="w-4 h-4 text-white/30 scale-y-[-1]" />
                <div>
                  <p className="text-[10px] text-white/30 uppercase tracking-widest">Received</p>
                  <p className="text-sm font-bold font-mono text-white/70">{stats.net_recv_mb.toFixed(1)} MB</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Service status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="rounded-2xl p-6 flex flex-col gap-4"
            style={{
              background: 'rgba(255,255,255,0.025)',
              border: '1px solid rgba(255,255,255,0.07)',
              backdropFilter: 'blur(12px)',
            }}
          >
            <h2 className="text-sm font-bold tracking-widest uppercase text-white/50 mb-2" style={{ fontFamily: 'Orbitron, monospace' }}>
              Services
            </h2>
            <ServiceBadge label="Krystal Engine" online={stats.engine_loaded} sub="Core AI runtime" />
            <ServiceBadge label="MongoDB"        online={stats.db_connected}  sub="Chat history store" />
            <ServiceBadge label="Pinecone"       online={stats.pinecone_active} sub="Vector database" />
            <ServiceBadge label="Network"        online={stats.network_status}  sub="Internet connectivity" />
          </motion.div>
        </div>

        {/* ── Quick actions ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h2 className="text-sm font-bold tracking-widest uppercase text-white/40 mb-4" style={{ fontFamily: 'Orbitron, monospace' }}>
            Quick Actions
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: Shield,   label: 'Security Scan',  sub: 'Run system check',  color: '#06b6d4' },
              { icon: Database, label: 'Backup Data',    sub: 'Export history',    color: '#10b981' },
              { icon: Brain,    label: 'Clear Memory',   sub: 'Reset vector store', color: '#8b5cf6' },
              { icon: Server,   label: 'Diagnostics',    sub: 'Full health check',  color: '#f59e0b' },
            ].map(({ icon: Icon, label, sub, color }, i) => (
              <motion.button
                key={label}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.55 + i * 0.06 }}
                whileHover={{ y: -3, transition: { duration: 0.2 } }}
                whileTap={{ scale: 0.97 }}
                className="text-left p-5 rounded-2xl transition-all duration-300 group"
                style={{
                  background: 'rgba(255,255,255,0.025)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  backdropFilter: 'blur(8px)',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.borderColor = `${color}40`
                  ;(e.currentTarget as HTMLElement).style.boxShadow = `0 8px 30px ${color}12`
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.06)'
                  ;(e.currentTarget as HTMLElement).style.boxShadow = 'none'
                }}
              >
                <div
                  className="p-2.5 rounded-xl inline-flex mb-3 transition-all duration-300"
                  style={{ background: `${color}15`, border: `1px solid ${color}25` }}
                >
                  <Icon className="w-5 h-5" style={{ color }} />
                </div>
                <p className="text-sm font-semibold text-white/80">{label}</p>
                <p className="text-[11px] text-white/30 mt-0.5 font-mono">{sub}</p>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Last update timestamp */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-center text-[10px] text-white/15 font-mono mt-8 pb-2"
        >
          Last updated: {lastRefresh.toLocaleTimeString()} · Auto-refresh every 3s
        </motion.p>
      </div>
    </div>
  )
}