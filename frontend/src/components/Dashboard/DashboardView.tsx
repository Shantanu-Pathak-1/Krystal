import { useState, useEffect } from 'react'
import { Database, Activity, Clock, Server, Cpu, HardDrive, Wifi, Shield, Users, Brain, Zap } from 'lucide-react'

interface SystemStatus {
  db_connected: boolean
  pinecone_active: boolean
  uptime: string
  total_memories: number
  active_sessions: number
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_status: boolean
}

export default function DashboardView() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    db_connected: false,
    pinecone_active: false,
    uptime: '00:00:00',
    total_memories: 0,
    active_sessions: 0,
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    network_status: false,
  })

  useEffect(() => {
    // Fetch real system status from backend
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/stats')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        setSystemStatus(data)
      } catch (error) {
        console.error('Failed to fetch system status:', error)
        // Set fallback values on error
        setSystemStatus({
          db_connected: false,
          pinecone_active: false,
          uptime: '00:00:00',
          total_memories: 0,
          active_sessions: 0,
          cpu_usage: 0,
          memory_usage: 0,
          disk_usage: 0,
          network_status: false,
        })
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const StatCard = ({ icon: Icon, title, value, subtitle, color }: {
    icon: any
    title: string
    value: string | number
    subtitle?: string
    color: string
  }) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="text-2xl font-bold text-white">{value}</div>
      </div>
      <div className="text-sm text-gray-400">{title}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  )

  const ProgressCard = ({ icon: Icon, title, value, color }: {
    icon: any
    title: string
    value: number
    color: string
  }) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center space-x-3 mb-4">
        <Icon className="w-5 h-5 text-gray-400" />
        <span className="text-gray-400">{title}</span>
      </div>
      <div className="text-2xl font-bold text-white mb-2">{value.toFixed(1)}%</div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-colors ${color}`}
          style={{ width: `${value}%` }}
        ></div>
      </div>
    </div>
  )

  const StatusCard = ({ icon: Icon, title, status, subtitle }: {
    icon: any
    title: string
    status: boolean
    subtitle: string
  }) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Icon className={`w-5 h-5 ${status ? 'text-green-400' : 'text-red-400'}`} />
          <div>
            <div className="text-white font-medium">{title}</div>
            <div className="text-sm text-gray-400">{subtitle}</div>
          </div>
        </div>
        <div className={`w-3 h-3 rounded-full ${status ? 'bg-green-400' : 'bg-red-400'} ${status ? 'animate-pulse' : ''}`}></div>
      </div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">AI Control Center</h1>
        <p className="text-gray-400">System overview and performance metrics</p>
      </div>

      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          icon={Database}
          title="Vector Memories"
          value={systemStatus.total_memories}
          subtitle="Stored embeddings"
          color="bg-blue-500"
        />
        <StatCard
          icon={Users}
          title="Active Sessions"
          value={systemStatus.active_sessions}
          subtitle="Current users"
          color="bg-green-500"
        />
        <StatCard
          icon={Clock}
          title="System Uptime"
          value={systemStatus.uptime}
          subtitle="Since last restart"
          color="bg-purple-500"
        />
        <StatCard
          icon={Zap}
          title="API Requests"
          value="1,247"
          subtitle="Last 24 hours"
          color="bg-yellow-500"
        />
      </div>

      {/* System Performance */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white mb-4">System Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ProgressCard
            icon={Cpu}
            title="CPU Usage"
            value={systemStatus.cpu_usage}
            color={systemStatus.cpu_usage < 50 ? 'bg-green-400' : systemStatus.cpu_usage < 80 ? 'bg-yellow-400' : 'bg-red-400'}
          />
          <ProgressCard
            icon={Activity}
            title="Memory Usage"
            value={systemStatus.memory_usage}
            color={systemStatus.memory_usage < 50 ? 'bg-green-400' : systemStatus.memory_usage < 80 ? 'bg-yellow-400' : 'bg-red-400'}
          />
          <ProgressCard
            icon={HardDrive}
            title="Disk Usage"
            value={systemStatus.disk_usage}
            color={systemStatus.disk_usage < 50 ? 'bg-green-400' : systemStatus.disk_usage < 80 ? 'bg-yellow-400' : 'bg-red-400'}
          />
        </div>
      </div>

      {/* Service Status */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white mb-4">Service Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatusCard
            icon={Database}
            title="MongoDB"
            status={systemStatus.db_connected}
            subtitle="Chat history storage"
          />
          <StatusCard
            icon={Brain}
            title="Pinecone"
            status={systemStatus.pinecone_active}
            subtitle="Vector database"
          />
          <StatusCard
            icon={Server}
            title="Krystal Engine"
            status={true}
            subtitle="Core AI engine"
          />
          <StatusCard
            icon={Wifi}
            title="Network"
            status={systemStatus.network_status}
            subtitle="Internet connectivity"
          />
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <button className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:bg-gray-700 transition-colors text-left">
            <Shield className="w-6 h-6 text-blue-400 mb-2" />
            <div className="text-white font-medium">Security Scan</div>
            <div className="text-sm text-gray-400">Run system security check</div>
          </button>
          <button className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:bg-gray-700 transition-colors text-left">
            <Database className="w-6 h-6 text-green-400 mb-2" />
            <div className="text-white font-medium">Backup Data</div>
            <div className="text-sm text-gray-400">Export chat history</div>
          </button>
          <button className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:bg-gray-700 transition-colors text-left">
            <Brain className="w-6 h-6 text-purple-400 mb-2" />
            <div className="text-white font-medium">Clear Memory</div>
            <div className="text-sm text-gray-400">Reset vector store</div>
          </button>
          <button className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:bg-gray-700 transition-colors text-left">
            <Activity className="w-6 h-6 text-yellow-400 mb-2" />
            <div className="text-white font-medium">System Health</div>
            <div className="text-sm text-gray-400">Run diagnostics</div>
          </button>
        </div>
      </div>
    </div>
  )
}
