import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Shield, Lock, Eye, FileText, Terminal, Globe,
  Cpu, HardDrive, AlertTriangle, CheckCircle, XCircle,
  Power, Settings, User, Key
} from 'lucide-react'

interface Permission {
  id: string
  name: string
  description: string
  enabled: boolean
  icon: any
  category: 'system' | 'network' | 'privacy' | 'execution'
  risk: 'low' | 'medium' | 'high' | 'critical'
}

const INITIAL_PERMISSIONS: Permission[] = [
  {
    id: 'os_control',
    name: 'OS Control',
    description: 'Launch applications, control media, execute system commands',
    enabled: true,
    icon: Terminal,
    category: 'execution',
    risk: 'high',
  },
  {
    id: 'file_system',
    name: 'File System Access',
    description: 'Read, write, and modify files on the local system',
    enabled: false,
    icon: FileText,
    category: 'system',
    risk: 'critical',
  },
  {
    id: 'web_browser',
    name: 'Web Browser Control',
    description: 'Open URLs, search the web, access online services',
    enabled: true,
    icon: Globe,
    category: 'network',
    risk: 'medium',
  },
  {
    id: 'webcam_access',
    name: 'Webcam & Vision',
    description: 'Capture images from camera for visual analysis',
    enabled: false,
    icon: Eye,
    category: 'privacy',
    risk: 'high',
  },
  {
    id: 'microphone',
    name: 'Microphone Access',
    description: 'Listen to audio input for voice commands',
    enabled: true,
    icon: Cpu,
    category: 'privacy',
    risk: 'high',
  },
  {
    id: 'screen_capture',
    name: 'Screen Capture',
    description: 'Take screenshots of the desktop',
    enabled: false,
    icon: HardDrive,
    category: 'privacy',
    risk: 'critical',
  },
  {
    id: 'api_keys',
    name: 'API Key Management',
    description: 'Access and manage external API credentials',
    enabled: true,
    icon: Key,
    category: 'system',
    risk: 'critical',
  },
  {
    id: 'user_data',
    name: 'Personal Data Access',
    description: 'Access contacts, calendar, and personal files',
    enabled: false,
    icon: User,
    category: 'privacy',
    risk: 'critical',
  },
]

const riskColors: Record<string, { bg: string; border: string; text: string }> = {
  low: { bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)', text: '#34d399' },
  medium: { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)', text: '#fbbf24' },
  high: { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)', text: '#f87171' },
  critical: { bg: 'rgba(220,38,38,0.15)', border: 'rgba(220,38,38,0.4)', text: '#ef4444' },
}

/* ── Glass Card ────────────────────────────────────────────────────────── */
function GlassCard({
  children,
  accent = '#10b981',
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
  risk,
}: {
  enabled: boolean
  onChange: () => void
  risk: string
}) {
  const colors = riskColors[risk]

  return (
    <motion.button
      whileTap={{ scale: 0.95 }}
      onClick={onChange}
      className="relative w-12 h-6 rounded-full transition-colors duration-300"
      style={{
        background: enabled ? colors.bg : 'rgba(255,255,255,0.1)',
        border: `1px solid ${enabled ? colors.border : 'rgba(255,255,255,0.1)'}`,
      }}
    >
      <motion.div
        animate={{ x: enabled ? 24 : 2 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        className="absolute top-1 w-4 h-4 rounded-full"
        style={{
          background: enabled ? colors.text : 'rgba(255,255,255,0.4)',
          boxShadow: enabled ? `0 0 10px ${colors.text}` : 'none',
        }}
      />
    </motion.button>
  )
}

/* ── Permission Card ─────────────────────────────────────────────────────── */
function PermissionCard({
  permission,
  onToggle,
  index,
}: {
  permission: Permission
  onToggle: () => void
  index: number
}) {
  const Icon = permission.icon
  const risk = riskColors[permission.risk]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
      className="relative p-4 rounded-xl group"
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: `1px solid ${permission.enabled ? risk.border : 'rgba(255,255,255,0.06)'}`,
      }}
    >
      <div className="flex items-start gap-4">
        <div
          className="p-2.5 rounded-xl flex-shrink-0"
          style={{
            background: permission.enabled ? risk.bg : 'rgba(255,255,255,0.05)',
            border: `1px solid ${permission.enabled ? risk.border : 'rgba(255,255,255,0.08)'}`,
          }}
        >
          <Icon className="w-5 h-5" style={{ color: permission.enabled ? risk.text : 'rgba(255,255,255,0.4)' }} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-semibold text-white/80">{permission.name}</h3>
            <Toggle enabled={permission.enabled} onChange={onToggle} risk={permission.risk} />
          </div>
          <p className="text-xs text-white/40 mb-2">{permission.description}</p>
          
          <div className="flex items-center gap-2">
            <span
              className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{
                background: risk.bg,
                color: risk.text,
                border: `1px solid ${risk.border}`,
              }}
            >
              {permission.risk.toUpperCase()} RISK
            </span>
            <span className="text-[10px] text-white/30 uppercase">
              {permission.category}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function SecurityView() {
  const [permissions, setPermissions] = useState<Permission[]>(INITIAL_PERMISSIONS)
  const [activeTab, setActiveTab] = useState<string>('all')

  const togglePermission = (id: string) => {
    setPermissions(prev =>
      prev.map(p => (p.id === id ? { ...p, enabled: !p.enabled } : p))
    )
  }

  const filteredPermissions = activeTab === 'all'
    ? permissions
    : permissions.filter(p => p.category === activeTab)

  const enabledCount = permissions.filter(p => p.enabled).length
  const criticalEnabled = permissions.filter(p => p.enabled && p.risk === 'critical').length

  const tabs = [
    { id: 'all', label: 'All', icon: Settings },
    { id: 'system', label: 'System', icon: Terminal },
    { id: 'network', label: 'Network', icon: Globe },
    { id: 'privacy', label: 'Privacy', icon: Eye },
    { id: 'execution', label: 'Execution', icon: Power },
  ]

  return (
    <div className="h-full overflow-y-auto p-6 scrollbar-none">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-2">
          <div
            className="p-2 rounded-xl"
            style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }}
          >
            <Shield className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h1
              className="text-xl font-bold tracking-wider uppercase"
              style={{ fontFamily: 'Orbitron, monospace', color: 'rgba(255,255,255,0.9)' }}
            >
              Security & Guard
            </h1>
            <p className="text-xs text-white/40 font-mono">Permission Control Center</p>
          </div>
        </div>
      </motion.div>

      {/* Status Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <GlassCard accent="#10b981" delay={0.1}>
          <div className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              <span className="text-xs text-white/50 uppercase tracking-wider">Enabled</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: '#34d399', fontFamily: 'JetBrains Mono' }}>
              {enabledCount}
            </p>
            <p className="text-[10px] text-white/30 mt-1">of {permissions.length} permissions</p>
          </div>
        </GlassCard>

        <GlassCard accent="#ef4444" delay={0.2}>
          <div className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <span className="text-xs text-white/50 uppercase tracking-wider">Critical</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: '#f87171', fontFamily: 'JetBrains Mono' }}>
              {criticalEnabled}
            </p>
            <p className="text-[10px] text-white/30 mt-1">high-risk permissions active</p>
          </div>
        </GlassCard>

        <GlassCard accent="#8b5cf6" delay={0.3}>
          <div className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Lock className="w-5 h-5 text-violet-400" />
              <span className="text-xs text-white/50 uppercase tracking-wider">Security Level</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: '#a78bfa', fontFamily: 'JetBrains Mono' }}>
              {criticalEnabled > 2 ? 'LOW' : criticalEnabled > 0 ? 'MEDIUM' : 'HIGH'}
            </p>
            <p className="text-[10px] text-white/30 mt-1">
              {criticalEnabled > 2 ? 'Multiple critical permissions enabled' : 'System well protected'}
            </p>
          </div>
        </GlassCard>
      </div>

      {/* Tabs */}
      <GlassCard accent="#10b981" delay={0.4}>
        <div className="p-2 flex flex-wrap gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <motion.button
                key={tab.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActiveTab(tab.id)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all duration-200"
                style={{
                  background: isActive ? 'rgba(16,185,129,0.15)' : 'transparent',
                  border: `1px solid ${isActive ? 'rgba(16,185,129,0.3)' : 'transparent'}`,
                  color: isActive ? '#34d399' : 'rgba(255,255,255,0.5)',
                }}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </motion.button>
            )
          })}
        </div>
      </GlassCard>

      {/* Permissions Grid */}
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
        {filteredPermissions.map((permission, idx) => (
          <PermissionCard
            key={permission.id}
            permission={permission}
            onToggle={() => togglePermission(permission.id)}
            index={idx}
          />
        ))}
      </div>

      {filteredPermissions.length === 0 && (
        <div className="text-center py-12">
          <XCircle className="w-12 h-12 text-white/10 mx-auto mb-3" />
          <p className="text-sm text-white/40">No permissions in this category</p>
        </div>
      )}

      {/* Footer Warning */}
      {criticalEnabled > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-6 p-4 rounded-xl"
          style={{
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.2)',
          }}
        >
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-300">Security Notice</p>
              <p className="text-xs text-red-200/60 mt-1">
                You have {criticalEnabled} critical-risk permission(s) enabled. 
                These grant Krystal significant control over your system. 
                Ensure you trust the AI's decision-making before enabling these features.
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
