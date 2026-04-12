import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Database, Search, Brain, Server,
  Cpu, Network, Layers,
  X, Sparkles
} from 'lucide-react'

interface MemoryNode {
  id: string
  content: string
  timestamp: string
  type: 'conversation' | 'personal_fact' | 'system_event' | 'memory'
  similarity?: number
}

interface VectorStats {
  total_vectors: number
  dimension: number
  index_name: string
  namespace: string
  status: 'healthy' | 'degraded' | 'offline'
}

const INITIAL_STATS: VectorStats = {
  total_vectors: 0,
  dimension: 1536,
  index_name: 'krystal-memory',
  namespace: 'default',
  status: 'offline',
}

/* ── Glass Card Component ─────────────────────────────────────────────── */
function GlassCard({
  children,
  accent = '#8b5cf6',
  delay = 0,
  className = '',
}: {
  children: React.ReactNode
  accent?: string
  delay?: number
  className?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
      className={`relative rounded-2xl overflow-hidden ${className}`}
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

/* ── Stat Card ───────────────────────────────────────────────────────── */
function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  accent,
  delay = 0,
}: {
  icon: any
  label: string
  value: string | number
  sub?: string
  accent: string
  delay?: number
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

/* ── Memory Node Card ─────────────────────────────────────────────────── */
function MemoryNodeCard({
  node,
  index,
}: {
  node: MemoryNode
  index: number
}) {
  const typeColors: Record<string, string> = {
    conversation: '#8b5cf6',
    personal_fact: '#ec4899',
    system_event: '#10b981',
    memory: '#f59e0b',
  }

  const typeLabels: Record<string, string> = {
    conversation: 'Chat',
    personal_fact: 'Fact',
    system_event: 'System',
    memory: 'Memory',
  }

  const accent = typeColors[node.type] || '#8b5cf6'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
      className="relative p-4 rounded-xl group cursor-pointer"
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="p-1.5 rounded-lg flex-shrink-0"
          style={{ background: `${accent}15`, border: `1px solid ${accent}25` }}
        >
          <Sparkles className="w-3.5 h-3.5" style={{ color: accent }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white/80 line-clamp-2 leading-relaxed">{node.content}</p>
          <div className="flex items-center gap-3 mt-2">
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{
                background: `${accent}15`,
                color: accent,
                border: `1px solid ${accent}30`,
              }}
            >
              {typeLabels[node.type]}
            </span>
            <span className="text-[10px] text-white/30 font-mono">
              {new Date(node.timestamp).toLocaleDateString()}
            </span>
            {node.similarity !== undefined && (
              <span className="text-[10px] text-white/40 font-mono">
                {(node.similarity * 100).toFixed(1)}% match
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function MemoryVaultView() {
  const [stats, setStats] = useState<VectorStats>(INITIAL_STATS)
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [memories, setMemories] = useState<MemoryNode[]>([])
  const [loading, setLoading] = useState(true)

  // Fetch stats and recent memories on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch stats from API
        const statsRes = await fetch('/api/dashboard/stats')
        if (statsRes.ok) {
          const data = await statsRes.json()
          setStats(prev => ({
            ...prev,
            total_vectors: data.total_memories || 0,
            status: data.pinecone_active ? 'healthy' : 'offline',
          }))
        }

        // Fetch recent chat history as memories
        const historyRes = await fetch('/api/chat/history?limit=20')
        if (historyRes.ok) {
          const data = await historyRes.json()
          const mappedMemories: MemoryNode[] = data.messages?.map((msg: any, idx: number) => ({
            id: `mem-${idx}`,
            content: msg.content,
            timestamp: msg.timestamp,
            type: msg.type === 'user' ? 'conversation' : 'memory',
          })) || []
          setMemories(mappedMemories)
        }
      } catch (error) {
        console.error('Error fetching memory data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setIsSearching(true)
    
    try {
      // In a real implementation, this would call the vector search API
      // For now, we'll filter local memories
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Simulate search results with similarity scores
      const filtered = memories
        .filter(m => m.content.toLowerCase().includes(searchQuery.toLowerCase()))
        .map(m => ({ ...m, similarity: 0.85 + Math.random() * 0.14 }))
        .sort((a, b) => (b.similarity || 0) - (a.similarity || 0))
      
      setMemories(filtered)
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    // Reload original data
    setLoading(true)
    fetch('/api/chat/history?limit=20')
      .then(res => res.json())
      .then(data => {
        const mappedMemories = data.messages?.map((msg: any, idx: number) => ({
          id: `mem-${idx}`,
          content: msg.content,
          timestamp: msg.timestamp,
          type: msg.type === 'user' ? 'conversation' : 'memory',
        })) || []
        setMemories(mappedMemories)
      })
      .finally(() => setLoading(false))
  }

  return (
    <div className="h-full overflow-y-auto p-6 scrollbar-none">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div
            className="p-2 rounded-xl"
            style={{ background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)' }}
          >
            <Database className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h1
              className="text-xl font-bold tracking-wider uppercase"
              style={{ fontFamily: 'Orbitron, monospace', color: 'rgba(255,255,255,0.9)' }}
            >
              Memory Vault
            </h1>
            <p className="text-xs text-white/40 font-mono">Vector Database & Semantic Search</p>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={Layers}
          label="Total Vectors"
          value={stats.total_vectors.toLocaleString()}
          sub={stats.status === 'healthy' ? 'Pinecone Active' : 'Offline'}
          accent="#8b5cf6"
          delay={0.1}
        />
        <StatCard
          icon={Cpu}
          label="Dimensions"
          value={stats.dimension}
          sub="Embedding Size"
          accent="#06b6d4"
          delay={0.2}
        />
        <StatCard
          icon={Server}
          label="Index"
          value={stats.index_name}
          sub={stats.namespace}
          accent="#10b981"
          delay={0.3}
        />
        <StatCard
          icon={Network}
          label="Status"
          value={stats.status === 'healthy' ? 'Online' : 'Offline'}
          sub={stats.status === 'healthy' ? 'Connected' : 'Check API Key'}
          accent={stats.status === 'healthy' ? '#10b981' : '#ef4444'}
          delay={0.4}
        />
      </div>

      {/* Search Bar */}
      <GlassCard accent="#8b5cf6" delay={0.5} className="mb-6">
        <div className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search memories... (semantic search)"
                className="w-full bg-transparent border border-white/10 rounded-xl py-2.5 pl-10 pr-10 text-sm text-white/80 placeholder:text-white/30 focus:outline-none focus:border-violet-500/50 transition-colors"
                style={{ fontFamily: 'JetBrains Mono, monospace' }}
              />
              {searchQuery && (
                <button
                  onClick={clearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <X className="w-3.5 h-3.5 text-white/40" />
                </button>
              )}
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
              className="px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 disabled:opacity-50"
              style={{
                background: 'rgba(139,92,246,0.15)',
                border: '1px solid rgba(139,92,246,0.3)',
                color: '#a78bfa',
              }}
            >
              {isSearching ? 'Searching...' : 'Search'}
            </motion.button>
          </div>
        </div>
      </GlassCard>

      {/* Memory Nodes List */}
      <GlassCard accent="#8b5cf6" delay={0.6}>
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2
              className="text-sm font-bold tracking-wider uppercase"
              style={{ fontFamily: 'Orbitron, monospace', color: 'rgba(255,255,255,0.7)' }}
            >
              Recent Memories
            </h2>
            <span className="text-xs text-white/40 font-mono">{memories.length} nodes</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-8 h-8 rounded-full border-2 border-violet-500/30 border-t-violet-500"
              />
            </div>
          ) : memories.length === 0 ? (
            <div className="text-center py-12">
              <Brain className="w-12 h-12 text-white/10 mx-auto mb-3" />
              <p className="text-sm text-white/40">No memories found</p>
              <p className="text-xs text-white/25 mt-1">Start a conversation to create memories</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto scrollbar-none pr-1">
              <AnimatePresence>
                {memories.map((node, idx) => (
                  <MemoryNodeCard key={node.id} node={node} index={idx} />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  )
}
