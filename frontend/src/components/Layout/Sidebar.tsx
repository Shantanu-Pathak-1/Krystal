import { motion } from 'framer-motion'
import {
  MessageSquare, Brain, Heart, Shield, Database,
  Book, LayoutDashboard, Terminal, Settings, Zap, Blocks, Key, TrendingUp
} from 'lucide-react'
import { ViewMode } from '../../types'

interface SidebarProps {
  currentView: ViewMode
  onViewChange: (view: ViewMode) => void
}

const primaryNav = [
  { id: 'dashboard', label: 'Dashboard',   icon: LayoutDashboard, view: 'dashboard' as ViewMode, color: 'cyan' },
  { id: 'main',      label: 'Chat',         icon: MessageSquare,   view: 'main'      as ViewMode, color: 'purple' },
  { id: 'heartbeat', label: 'Heartbeat',    icon: Heart,           view: 'heartbeat' as ViewMode, color: 'pink' },
  { id: 'zen',       label: 'Zen Voice',    icon: Brain,           view: 'zen'       as ViewMode, color: 'blue' },
  { id: 'logs',      label: 'Logs',         icon: Terminal,        view: 'logs'      as ViewMode, color: 'green' },
  { id: 'config',    label: 'Config',       icon: Settings,        view: 'config'    as ViewMode, color: 'amber' },
]

const secondaryNav = [
  { id: 'memory',   label: 'Memory Vault',   icon: Database,  view: 'memory' as ViewMode,   color: 'violet' },
  { id: 'diary',    label: "Krystal's Diary", icon: Book,     view: 'diary' as ViewMode,    color: 'rose' },
  { id: 'security', label: 'Security & Guard', icon: Shield,   view: 'security' as ViewMode,  color: 'emerald' },
  { id: 'plugins',  label: 'Plugins Lab',      icon: Blocks,   view: 'plugins' as ViewMode,   color: 'orange' },
  { id: 'trading',  label: 'Trading Hub',     icon: TrendingUp, view: 'trading' as ViewMode,  color: 'emerald' },
  { id: 'api-keys', label: 'API Keys',       icon: Key,      view: 'api' as ViewMode,      color: 'blue' },
]

const colorMap: Record<string, string> = {
  cyan:    'rgba(6,182,212,0.8)',
  purple:  'rgba(139,92,246,0.8)',
  pink:    'rgba(236,72,153,0.8)',
  blue:    'rgba(59,130,246,0.8)',
  green:   'rgba(16,185,129,0.8)',
  amber:   'rgba(245,158,11,0.8)',
  violet:  'rgba(167,139,250,0.8)',
  rose:    'rgba(251,113,133,0.8)',
  emerald: 'rgba(16,185,129,0.8)',
  orange:  'rgba(251,146,60,0.8)',
}

const sidebarVariants = {
  hidden: { x: -280 },
  visible: {
    x: 0,
    transition: { type: 'spring', stiffness: 300, damping: 30 }
  }
}

const itemVariants = {
  hidden: { x: -20, opacity: 0 },
  visible: (i: number) => ({
    x: 0, opacity: 1,
    transition: { delay: i * 0.06, duration: 0.4, ease: [0.4, 0, 0.2, 1] }
  })
}

export default function Sidebar({ currentView, onViewChange }: SidebarProps) {
  return (
    <motion.aside
      variants={sidebarVariants}
      initial="hidden"
      animate="visible"
      className="relative w-64 flex flex-col overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #05080f 0%, #030609 100%)',
        borderRight: '1px solid rgba(255,255,255,0.055)',
      }}
    >
      {/* Ambient purple glow top-left */}
      <div
        className="absolute -top-20 -left-20 w-56 h-56 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse, rgba(139,92,246,0.12) 0%, transparent 70%)',
          filter: 'blur(30px)',
        }}
      />

      {/* Logo */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="flex items-center gap-3 px-6 py-5"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}
      >
        <div className="relative">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 rounded-xl"
            style={{
              background: 'conic-gradient(from 0deg, rgba(139,92,246,0.6), rgba(6,182,212,0.6), rgba(139,92,246,0.6))',
              filter: 'blur(4px)',
            }}
          />
          <div
            className="relative w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #4c1d95, #1e3a5f)' }}
          >
            <Zap className="w-5 h-5 text-white" />
          </div>
        </div>

        <div>
          <h1
            className="text-base font-bold tracking-widest uppercase leading-none"
            style={{
              fontFamily: 'Orbitron, monospace',
              background: 'linear-gradient(135deg, #a78bfa 0%, #22d3ee 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Krystal
          </h1>
          <p className="text-[9px] tracking-[0.3em] uppercase text-white/30 mt-0.5">AI Interface v1.0</p>
        </div>
      </motion.div>

      {/* Primary Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto scrollbar-none">
        <p className="text-[9px] tracking-[0.3em] uppercase text-white/20 px-3 mb-3">Navigation</p>
        <div className="space-y-1">
          {primaryNav.map((item, i) => {
            const Icon = item.icon
            const isActive = currentView === item.view
            const accentColor = colorMap[item.color]

            return (
              <motion.button
                key={item.id}
                custom={i}
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                whileHover={{ x: 3, transition: { duration: 0.15 } }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onViewChange(item.view)}
                className="relative w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-colors duration-200 group"
                style={
                  isActive
                    ? {
                        background: `linear-gradient(135deg, ${accentColor}20 0%, rgba(255,255,255,0.02) 100%)`,
                        border: `1px solid ${accentColor}35`,
                        boxShadow: `0 4px 20px ${accentColor}15, inset 0 1px 0 rgba(255,255,255,0.07)`,
                      }
                    : { border: '1px solid transparent' }
                }
              >
                {/* Active left bar */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                    style={{ background: accentColor, boxShadow: `0 0 8px ${accentColor}` }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}

                <Icon
                  className="w-4 h-4 flex-shrink-0 transition-all duration-200"
                  style={{ color: isActive ? accentColor : 'rgba(255,255,255,0.35)' }}
                />
                <span
                  className="text-sm font-medium transition-colors duration-200"
                  style={{
                    color: isActive ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.4)',
                    fontFamily: 'Syne, sans-serif',
                  }}
                >
                  {item.label}
                </span>

                {/* Hover glow dot */}
                {!isActive && (
                  <motion.div
                    className="absolute right-3 w-1 h-1 rounded-full opacity-0 group-hover:opacity-60"
                    style={{ background: accentColor }}
                    transition={{ duration: 0.2 }}
                  />
                )}
              </motion.button>
            )
          })}
        </div>

        {/* Divider */}
        <div className="my-5 mx-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }} />

        <p className="text-[9px] tracking-[0.3em] uppercase text-white/20 px-3 mb-3">Advanced</p>
        <div className="space-y-1">
          {secondaryNav.map((item, i) => {
            const Icon = item.icon
            const isActive = currentView === item.view
            const accentColor = colorMap[item.color]

            return (
              <motion.button
                key={item.id}
                custom={primaryNav.length + i}
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                whileHover={{ x: 3, transition: { duration: 0.15 } }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onViewChange(item.view)}
                className="relative w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-colors duration-200 group"
                style={
                  isActive
                    ? {
                        background: `linear-gradient(135deg, ${accentColor}20 0%, rgba(255,255,255,0.02) 100%)`,
                        border: `1px solid ${accentColor}35`,
                        boxShadow: `0 4px 20px ${accentColor}15, inset 0 1px 0 rgba(255,255,255,0.07)`,
                      }
                    : { border: '1px solid transparent' }
                }
              >
                {/* Active left bar */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                    style={{ background: accentColor, boxShadow: `0 0 8px ${accentColor}` }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}

                <Icon
                  className="w-4 h-4 flex-shrink-0 transition-all duration-200"
                  style={{ color: isActive ? accentColor : 'rgba(255,255,255,0.35)' }}
                />
                <span
                  className="text-sm font-medium transition-colors duration-200"
                  style={{
                    color: isActive ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.4)',
                    fontFamily: 'Syne, sans-serif',
                  }}
                >
                  {item.label}
                </span>

                {/* Hover glow dot */}
                {!isActive && (
                  <motion.div
                    className="absolute right-3 w-1 h-1 rounded-full opacity-0 group-hover:opacity-60"
                    style={{ background: accentColor }}
                    transition={{ duration: 0.2 }}
                  />
                )}
              </motion.button>
            )
          })}
        </div>
      </nav>

      {/* Footer status */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="px-4 py-4"
        style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}
      >
        <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
          style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.12)' }}
        >
          <motion.div
            className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0"
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{ boxShadow: '0 0 8px rgba(16,185,129,0.8)' }}
          />
          <span
            className="text-[10px] font-medium text-emerald-400/90 tracking-wider"
            style={{ fontFamily: 'JetBrains Mono, monospace' }}
          >
            SYSTEM ONLINE
          </span>
        </div>
      </motion.div>
    </motion.aside>
  )
}