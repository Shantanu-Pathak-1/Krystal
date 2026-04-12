import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Book, Calendar, Clock, Heart, Star,
  MessageCircle, Brain, Sparkles, Filter
} from 'lucide-react'

interface DiaryEntry {
  id: string
  date: string
  title: string
  summary: string
  mood: 'happy' | 'reflective' | 'focused' | 'creative' | 'neutral'
  interactions: number
  keyTopics: string[]
  highlight?: string
}

const moodColors: Record<string, { bg: string; border: string; text: string; glow: string }> = {
  happy: { bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)', text: '#34d399', glow: 'rgba(16,185,129,0.4)' },
  reflective: { bg: 'rgba(139,92,246,0.1)', border: 'rgba(139,92,246,0.3)', text: '#a78bfa', glow: 'rgba(139,92,246,0.4)' },
  focused: { bg: 'rgba(6,182,212,0.1)', border: 'rgba(6,182,212,0.3)', text: '#22d3ee', glow: 'rgba(6,182,212,0.4)' },
  creative: { bg: 'rgba(236,72,153,0.1)', border: 'rgba(236,72,153,0.3)', text: '#f472b6', glow: 'rgba(236,72,153,0.4)' },
  neutral: { bg: 'rgba(156,163,175,0.1)', border: 'rgba(156,163,175,0.3)', text: '#9ca3af', glow: 'rgba(156,163,175,0.4)' },
}

const moodLabels: Record<string, string> = {
  happy: 'Joyful',
  reflective: 'Reflective',
  focused: 'Focused',
  creative: 'Creative',
  neutral: 'Neutral',
}

/* ── Glass Card ────────────────────────────────────────────────────────── */
function GlassCard({
  children,
  accent = '#ec4899',
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

/* ── Entry Card ─────────────────────────────────────────────────────────── */
function EntryCard({
  entry,
  index,
  isSelected,
  onClick,
}: {
  entry: DiaryEntry
  index: number
  isSelected: boolean
  onClick: () => void
}) {
  const mood = moodColors[entry.mood]

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      whileHover={{ x: 4, transition: { duration: 0.2 } }}
      onClick={onClick}
      className={`relative p-4 rounded-xl cursor-pointer transition-all duration-300 ${
        isSelected ? 'ring-1' : ''
      }`}
      style={{
        background: isSelected ? mood.bg : 'rgba(255,255,255,0.03)',
        border: `1px solid ${isSelected ? mood.border : 'rgba(255,255,255,0.06)'}`,
        boxShadow: isSelected ? `0 0 20px ${mood.glow}` : 'none',
      }}
    >
      <div className="flex items-start gap-3">
        {/* Date Badge */}
        <div
          className="flex-shrink-0 w-12 h-12 rounded-xl flex flex-col items-center justify-center"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
        >
          <span className="text-[10px] text-white/40 uppercase">
            {new Date(entry.date).toLocaleDateString('en-US', { month: 'short' })}
          </span>
          <span className="text-sm font-bold" style={{ color: mood.text }}>
            {new Date(entry.date).getDate()}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white/80 truncate">{entry.title}</h3>
          <p className="text-xs text-white/40 mt-1 line-clamp-2">{entry.summary}</p>
          
          <div className="flex items-center gap-3 mt-2">
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{ background: mood.bg, color: mood.text, border: `1px solid ${mood.border}` }}
            >
              {moodLabels[entry.mood]}
            </span>
            <span className="text-[10px] text-white/30 flex items-center gap-1">
              <MessageCircle className="w-3 h-3" />
              {entry.interactions}
            </span>
          </div>
        </div>
      </div>

      {entry.highlight && (
        <div
          className="mt-3 p-2 rounded-lg text-xs italic"
          style={{ background: 'rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.5)' }}
        >
          <Star className="w-3 h-3 inline mr-1" style={{ color: mood.text }} />
          {entry.highlight}
        </div>
      )}
    </motion.div>
  )
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function DiaryView() {
  const [entries, setEntries] = useState<DiaryEntry[]>([])
  const [selectedEntry, setSelectedEntry] = useState<DiaryEntry | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch diary entries from chat history
    const fetchEntries = async () => {
      try {
        const res = await fetch('/api/chat/history?limit=50')
        if (res.ok) {
          const data = await res.json()
          
          // Group messages by date and create diary entries
          const groupedByDate = (data.messages || []).reduce((acc: any, msg: any) => {
            const date = new Date(msg.timestamp).toDateString()
            if (!acc[date]) {
              acc[date] = []
            }
            acc[date].push(msg)
            return acc
          }, {})

          const diaryEntries: DiaryEntry[] = Object.entries(groupedByDate)
            .map(([date, messages]: [string, any], idx) => {
              const userMessages = messages.filter((m: any) => m.type === 'user')
              const firstMsg = userMessages[0]?.content || 'Conversation'
              
              return {
                id: `entry-${idx}`,
                date,
                title: firstMsg.slice(0, 40) + (firstMsg.length > 40 ? '...' : ''),
                summary: `${userMessages.length} interactions, covering various topics`,
                mood: ['happy', 'reflective', 'focused', 'creative', 'neutral'][Math.floor(Math.random() * 5)] as any,
                interactions: messages.length,
                keyTopics: ['AI', 'Coding', 'Life'],
                highlight: userMessages.length > 5 ? 'Active conversation day' : undefined,
              }
            })
            .slice(0, 20) // Last 20 days

          setEntries(diaryEntries)
          if (diaryEntries.length > 0) {
            setSelectedEntry(diaryEntries[0])
          }
        }
      } catch (error) {
        console.error('Error fetching diary:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchEntries()
  }, [])

  const filteredEntries = filter === 'all' 
    ? entries 
    : entries.filter(e => e.mood === filter)

  const stats = {
    totalDays: entries.length,
    totalInteractions: entries.reduce((sum, e) => sum + e.interactions, 0),
    avgMood: entries.length > 0 
      ? entries.reduce((sum, e) => {
          const moodValues = { happy: 4, creative: 3, focused: 3, reflective: 2, neutral: 1 }
          return sum + (moodValues[e.mood] || 1)
        }, 0) / entries.length 
      : 0,
  }

  return (
    <div className="h-full overflow-hidden flex">
      {/* Left Sidebar - Entry List */}
      <div className="w-80 flex-shrink-0 border-r border-white/5 overflow-y-auto scrollbar-none">
        {/* Header */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3 mb-4">
            <div
              className="p-2 rounded-xl"
              style={{ background: 'rgba(236,72,153,0.15)', border: '1px solid rgba(236,72,153,0.3)' }}
            >
              <Book className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <h1
                className="text-lg font-bold tracking-wider uppercase"
                style={{ fontFamily: 'Orbitron, monospace', color: 'rgba(255,255,255,0.9)' }}
              >
                Krystal's Diary
              </h1>
              <p className="text-[10px] text-white/40 font-mono">Long-term Memory Timeline</p>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
              <p className="text-lg font-bold" style={{ color: '#ec4899', fontFamily: 'JetBrains Mono' }}>
                {stats.totalDays}
              </p>
              <p className="text-[10px] text-white/40">Days</p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
              <p className="text-lg font-bold" style={{ color: '#8b5cf6', fontFamily: 'JetBrains Mono' }}>
                {stats.totalInteractions}
              </p>
              <p className="text-[10px] text-white/40">Messages</p>
            </div>
          </div>
        </div>

        {/* Filter */}
        <div className="px-4 py-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-white/30" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="flex-1 bg-transparent text-xs text-white/60 focus:outline-none cursor-pointer"
              style={{ fontFamily: 'JetBrains Mono' }}
            >
              <option value="all" className="bg-[#0a0f1c]">All Moods</option>
              <option value="happy" className="bg-[#0a0f1c]">Joyful</option>
              <option value="focused" className="bg-[#0a0f1c]">Focused</option>
              <option value="creative" className="bg-[#0a0f1c]">Creative</option>
              <option value="reflective" className="bg-[#0a0f1c]">Reflective</option>
            </select>
          </div>
        </div>

        {/* Entry List */}
        <div className="p-4 space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-8 h-8 rounded-full border-2 border-rose-500/30 border-t-rose-500"
              />
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="w-10 h-10 text-white/10 mx-auto mb-2" />
              <p className="text-xs text-white/40">No entries yet</p>
            </div>
          ) : (
            <AnimatePresence>
              {filteredEntries.map((entry, idx) => (
                <EntryCard
                  key={entry.id}
                  entry={entry}
                  index={idx}
                  isSelected={selectedEntry?.id === entry.id}
                  onClick={() => setSelectedEntry(entry)}
                />
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Main Content - Selected Entry Detail */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-none">
        {selectedEntry ? (
          <motion.div
            key={selectedEntry.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {/* Date Header */}
            <GlassCard accent={moodColors[selectedEntry.mood].text} delay={0}>
              <div className="p-6">
                <div className="flex items-center gap-4 mb-4">
                  <div
                    className="p-3 rounded-2xl"
                    style={{
                      background: moodColors[selectedEntry.mood].bg,
                      border: `1px solid ${moodColors[selectedEntry.mood].border}`,
                    }}
                  >
                    <Heart className="w-6 h-6" style={{ color: moodColors[selectedEntry.mood].text }} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white/90">{selectedEntry.title}</h2>
                    <p className="text-sm text-white/40">
                      {new Date(selectedEntry.date).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span
                    className="px-3 py-1 rounded-full text-sm font-medium"
                    style={{
                      background: moodColors[selectedEntry.mood].bg,
                      color: moodColors[selectedEntry.mood].text,
                      border: `1px solid ${moodColors[selectedEntry.mood].border}`,
                    }}
                  >
                    {moodLabels[selectedEntry.mood]}
                  </span>
                  <span className="text-sm text-white/40 flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {selectedEntry.interactions} interactions
                  </span>
                </div>
              </div>
            </GlassCard>

            {/* Topics */}
            <GlassCard accent="#8b5cf6" delay={0.1}>
              <div className="p-6 mt-4">
                <h3 className="text-sm font-bold text-white/60 tracking-wider uppercase mb-3 flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  Key Topics
                </h3>
                <div className="flex flex-wrap gap-2">
                  {selectedEntry.keyTopics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 rounded-full text-xs"
                      style={{
                        background: 'rgba(139,92,246,0.1)',
                        border: '1px solid rgba(139,92,246,0.2)',
                        color: '#a78bfa',
                      }}
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            </GlassCard>

            {/* Summary */}
            <GlassCard accent="#06b6d4" delay={0.2}>
              <div className="p-6 mt-4">
                <h3 className="text-sm font-bold text-white/60 tracking-wider uppercase mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Day Summary
                </h3>
                <p className="text-sm text-white/70 leading-relaxed">{selectedEntry.summary}</p>
                
                {selectedEntry.highlight && (
                  <div
                    className="mt-4 p-3 rounded-xl"
                    style={{
                      background: 'rgba(245,158,11,0.1)',
                      border: '1px solid rgba(245,158,11,0.2)',
                    }}
                  >
                    <p className="text-sm flex items-center gap-2">
                      <Star className="w-4 h-4 text-amber-400" />
                      <span className="text-amber-200/80">{selectedEntry.highlight}</span>
                    </p>
                  </div>
                )}
              </div>
            </GlassCard>
          </motion.div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Book className="w-16 h-16 text-white/10 mx-auto mb-4" />
              <p className="text-white/40">Select a day to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
