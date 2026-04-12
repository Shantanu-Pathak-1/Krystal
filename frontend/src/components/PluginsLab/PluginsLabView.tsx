import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Blocks, Zap, Globe, Music, Video, ShoppingCart,
  FileText, Cpu, Wifi, Database, Shield, Terminal,
  Settings, ExternalLink
} from 'lucide-react'

interface Plugin {
  id: string
  name: string
  description: string
  icon: any
  category: 'media' | 'web' | 'system' | 'data' | 'automation'
  active: boolean
  version: string
  author: string
  installed: boolean
}

const INITIAL_PLUGINS: Plugin[] = [
  {
    id: 'youtube_audio',
    name: 'YouTube Audio',
    description: 'Play songs and audio from YouTube directly',
    icon: Music,
    category: 'media',
    active: true,
    version: '1.2.0',
    author: 'Krystal Core',
    installed: true,
  },
  {
    id: 'web_scraper',
    name: 'Web Scraper',
    description: 'Extract data from websites and search results',
    icon: Globe,
    category: 'web',
    active: false,
    version: '0.9.5',
    author: 'Krystal Core',
    installed: true,
  },
  {
    id: 'auto_trader',
    name: 'Auto Trader',
    description: 'Monitor stocks and execute trading commands',
    icon: ShoppingCart,
    category: 'automation',
    active: false,
    version: '2.1.0',
    author: 'Community',
    installed: false,
  },
  {
    id: 'video_player',
    name: 'Video Controller',
    description: 'Control video playback across platforms',
    icon: Video,
    category: 'media',
    active: true,
    version: '1.0.3',
    author: 'Krystal Core',
    installed: true,
  },
  {
    id: 'file_manager',
    name: 'File Manager',
    description: 'Browse, organize and manage local files',
    icon: FileText,
    category: 'system',
    active: false,
    version: '1.5.0',
    author: 'Krystal Core',
    installed: true,
  },
  {
    id: 'system_monitor',
    name: 'System Monitor',
    description: 'Real-time CPU, memory and process tracking',
    icon: Cpu,
    category: 'system',
    active: true,
    version: '2.0.1',
    author: 'Krystal Core',
    installed: true,
  },
  {
    id: 'network_tools',
    name: 'Network Tools',
    description: 'Ping, traceroute and network diagnostics',
    icon: Wifi,
    category: 'system',
    active: false,
    version: '0.8.0',
    author: 'Community',
    installed: true,
  },
  {
    id: 'db_connector',
    name: 'Database Connector',
    description: 'Connect to external SQL and NoSQL databases',
    icon: Database,
    category: 'data',
    active: false,
    version: '1.1.0',
    author: 'Krystal Core',
    installed: false,
  },
  {
    id: 'security_scanner',
    name: 'Security Scanner',
    description: 'Scan for vulnerabilities and security issues',
    icon: Shield,
    category: 'system',
    active: false,
    version: '0.5.0',
    author: 'Community',
    installed: false,
  },
  {
    id: 'terminal_plus',
    name: 'Terminal Plus',
    description: 'Enhanced terminal with custom commands',
    icon: Terminal,
    category: 'system',
    active: true,
    version: '3.0.0',
    author: 'Krystal Core',
    installed: true,
  },
]

const categoryColors: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  media: { bg: 'rgba(236,72,153,0.1)', border: 'rgba(236,72,153,0.3)', text: '#f472b6', glow: 'rgba(236,72,153,0.4)' },
  web: { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.3)', text: '#60a5fa', glow: 'rgba(59,130,246,0.4)' },
  system: { bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)', text: '#34d399', glow: 'rgba(16,185,129,0.4)' },
  data: { bg: 'rgba(139,92,246,0.1)', border: 'rgba(139,92,246,0.3)', text: '#a78bfa', glow: 'rgba(139,92,246,0.4)' },
  automation: { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)', text: '#fbbf24', glow: 'rgba(245,158,11,0.4)' },
}

const categoryLabels: Record<string, string> = {
  media: 'Media',
  web: 'Web',
  system: 'System',
  data: 'Data',
  automation: 'Auto',
}

/* ── Glass Card ────────────────────────────────────────────────────────── */
function GlassCard({
  children,
  accent = '#f97316',
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

/* ── Toggle Switch ───────────────────────────────────────────────────────── */
function Toggle({
  enabled,
  onChange,
  activeColor = '#10b981',
}: {
  enabled: boolean
  onChange: () => void
  activeColor?: string
}) {
  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={onChange}
      className="relative w-11 h-6 rounded-full transition-colors duration-300"
      style={{
        background: enabled ? `${activeColor}30` : 'rgba(255,255,255,0.1)',
        border: `1px solid ${enabled ? activeColor : 'rgba(255,255,255,0.1)'}`,
      }}
    >
      <motion.div
        animate={{ x: enabled ? 22 : 2 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        className="absolute top-1 w-4 h-4 rounded-full"
        style={{
          background: enabled ? activeColor : 'rgba(255,255,255,0.4)',
          boxShadow: enabled ? `0 0 10px ${activeColor}` : 'none',
        }}
      />
    </motion.button>
  )
}

/* ── Plugin Card ─────────────────────────────────────────────────────────── */
function PluginCard({
  plugin,
  onToggle,
  index,
}: {
  plugin: Plugin
  onToggle: () => void
  index: number
}) {
  const Icon = plugin.icon
  const colors = categoryColors[plugin.category]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="relative p-4 rounded-xl group"
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: `1px solid ${plugin.active ? colors.border : 'rgba(255,255,255,0.06)'}`,
        boxShadow: plugin.active ? `0 0 20px ${colors.glow}30` : 'none',
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div
          className="p-2.5 rounded-xl"
          style={{
            background: plugin.active ? colors.bg : 'rgba(255,255,255,0.05)',
            border: `1px solid ${plugin.active ? colors.border : 'rgba(255,255,255,0.08)'}`,
          }}
        >
          <Icon className="w-5 h-5" style={{ color: plugin.active ? colors.text : 'rgba(255,255,255,0.4)' }} />
        </div>
        <div className="flex items-center gap-2">
          {plugin.installed ? (
            <Toggle enabled={plugin.active} onChange={onToggle} activeColor={colors.text} />
          ) : (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium"
              style={{
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                color: colors.text,
              }}
            >
              Install
            </motion.button>
          )}
        </div>
      </div>

      {/* Content */}
      <h3 className="text-sm font-semibold text-white/80 mb-1">{plugin.name}</h3>
      <p className="text-xs text-white/40 mb-3 line-clamp-2">{plugin.description}</p>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <span
          className="text-[10px] px-2 py-0.5 rounded-full font-medium"
          style={{
            background: colors.bg,
            color: colors.text,
            border: `1px solid ${colors.border}`,
          }}
        >
          {categoryLabels[plugin.category]}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-white/30 font-mono">v{plugin.version}</span>
          {plugin.installed && plugin.active && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="w-2 h-2 rounded-full"
              style={{ background: colors.text, boxShadow: `0 0 8px ${colors.text}` }}
            />
          )}
        </div>
      </div>

      {/* Hover Overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 1 }}
        className="absolute inset-0 rounded-xl pointer-events-none"
        style={{
          background: `linear-gradient(135deg, ${colors.bg}00 0%, ${colors.bg}30 100%)`,
        }}
      />
    </motion.div>
  )
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function PluginsLabView() {
  const [plugins, setPlugins] = useState<Plugin[]>(INITIAL_PLUGINS)
  const [activeCategory, setActiveCategory] = useState<string>('all')

  const togglePlugin = (id: string) => {
    setPlugins(prev =>
      prev.map(p => (p.id === id ? { ...p, active: !p.active } : p))
    )
  }

  const filteredPlugins = activeCategory === 'all'
    ? plugins
    : plugins.filter(p => p.category === activeCategory)

  const activeCount = plugins.filter(p => p.active).length
  const installedCount = plugins.filter(p => p.installed).length

  const categories = [
    { id: 'all', label: 'All', count: plugins.length },
    { id: 'media', label: 'Media', count: plugins.filter(p => p.category === 'media').length },
    { id: 'web', label: 'Web', count: plugins.filter(p => p.category === 'web').length },
    { id: 'system', label: 'System', count: plugins.filter(p => p.category === 'system').length },
    { id: 'data', label: 'Data', count: plugins.filter(p => p.category === 'data').length },
    { id: 'automation', label: 'Auto', count: plugins.filter(p => p.category === 'automation').length },
  ]

  return (
    <div className="h-full overflow-y-auto p-6 scrollbar-none">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-xl"
              style={{ background: 'rgba(251,146,60,0.15)', border: '1px solid rgba(251,146,60,0.3)' }}
            >
              <Blocks className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <h1
                className="text-xl font-bold tracking-wider uppercase"
                style={{ fontFamily: 'Orbitron, monospace', color: 'rgba(255,255,255,0.9)' }}
              >
                Plugins Lab
              </h1>
              <p className="text-xs text-white/40 font-mono">Manage Extensions & Integrations</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-bold" style={{ color: '#fb923c', fontFamily: 'JetBrains Mono' }}>
                {activeCount} / {installedCount}
              </p>
              <p className="text-[10px] text-white/30">Active / Installed</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Category Tabs */}
      <GlassCard accent="#f97316" delay={0.1}>
        <div className="p-2 flex flex-wrap gap-1">
          {categories.map((cat) => {
            const isActive = activeCategory === cat.id
            const colors = cat.id === 'all' 
              ? { bg: 'rgba(251,146,60,0.15)', border: 'rgba(251,146,60,0.3)', text: '#fb923c' }
              : categoryColors[cat.id] || categoryColors.media
            
            return (
              <motion.button
                key={cat.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveCategory(cat.id)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-200"
                style={{
                  background: isActive ? colors.bg : 'transparent',
                  border: `1px solid ${isActive ? colors.border : 'transparent'}`,
                  color: isActive ? colors.text : 'rgba(255,255,255,0.5)',
                }}
              >
                {cat.label}
                <span
                  className="px-1.5 py-0.5 rounded-full text-[10px]"
                  style={{
                    background: isActive ? `${colors.text}20` : 'rgba(255,255,255,0.1)',
                    color: isActive ? colors.text : 'rgba(255,255,255,0.4)',
                  }}
                >
                  {cat.count}
                </span>
              </motion.button>
            )
          })}
        </div>
      </GlassCard>

      {/* Plugins Grid */}
      <div className="mt-4 grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        <AnimatePresence>
          {filteredPlugins.map((plugin, idx) => (
            <PluginCard
              key={plugin.id}
              plugin={plugin}
              onToggle={() => togglePlugin(plugin.id)}
              index={idx}
            />
          ))}
        </AnimatePresence>
      </div>

      {filteredPlugins.length === 0 && (
        <div className="text-center py-12">
          <Zap className="w-12 h-12 text-white/10 mx-auto mb-3" />
          <p className="text-sm text-white/40">No plugins in this category</p>
        </div>
      )}

      {/* Info Section */}
      <GlassCard accent="#8b5cf6" delay={0.4}>
        <div className="p-4 mt-4">
          <div className="flex items-start gap-3">
            <div
              className="p-2 rounded-lg flex-shrink-0"
              style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)' }}
            >
              <ExternalLink className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white/70">Plugin Development</p>
              <p className="text-xs text-white/40 mt-1">
                Create custom plugins using the Krystal Plugin API. 
                Enable powerful integrations with external services and system tools.
              </p>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="mt-3 px-3 py-1.5 rounded-lg text-xs font-medium inline-flex items-center gap-2"
                style={{
                  background: 'rgba(139,92,246,0.1)',
                  border: '1px solid rgba(139,92,246,0.2)',
                  color: '#a78bfa',
                }}
              >
                <Settings className="w-3 h-3" />
                Developer Docs
              </motion.button>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
