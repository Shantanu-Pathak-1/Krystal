import { useState, useEffect, useRef } from 'react'
import { Activity, Cpu, HardDrive, Wifi, Clock, AlertCircle } from 'lucide-react'

interface LogEntry {
  id: string
  timestamp: Date
  level: 'info' | 'warning' | 'error' | 'success'
  source: string
  message: string
}

interface SystemMetrics {
  cpu: number
  memory: number
  disk: number
  network: boolean
  uptime: string
}

export default function HeartbeatMonitor() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 0,
    memory: 0,
    disk: 0,
    network: true,
    uptime: '00:00:00',
  })
  const [isConnected] = useState(true)
  const logsEndRef = useRef<HTMLDivElement>(null)

  // Simulate real-time log updates
  useEffect(() => {
    const generateLog = (): LogEntry => {
      const sources = ['Heartbeat', 'System', 'Security', 'API', 'Database', 'Memory']
      const levels: LogEntry['level'][] = ['info', 'warning', 'error', 'success']
      const messages = [
        'System check completed successfully',
        'Monitoring active processes',
        'Resource usage within normal parameters',
        'Scheduled task completed',
        'Security scan initiated',
        'Database connection established',
        'Memory optimization performed',
        'Background service running',
        'Cache cleanup completed',
        'Health check passed',
      ]

      const level = levels[Math.floor(Math.random() * levels.length)]
      
      return {
        id: Date.now().toString(),
        timestamp: new Date(),
        level,
        source: sources[Math.floor(Math.random() * sources.length)],
        message: messages[Math.floor(Math.random() * messages.length)],
      }
    }

    const interval = setInterval(() => {
      const newLog = generateLog()
      setLogs(prev => [...prev.slice(-99), newLog]) // Keep last 100 logs
    }, 2000 + Math.random() * 3000) // Random interval between 2-5 seconds

    return () => clearInterval(interval)
  }, [])

  // Simulate metrics updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        cpu: Math.max(0, Math.min(100, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(0, Math.min(100, prev.memory + (Math.random() - 0.5) * 5)),
        disk: Math.max(0, Math.min(100, prev.disk + (Math.random() - 0.5) * 2)),
        network: Math.random() > 0.1,
        uptime: formatUptime(Date.now() - 1000 * 60 * 30), // Start from 30 minutes ago
      }))
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const formatUptime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    return `${String(hours).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
  }

  const getLevelColor = (level: LogEntry['level']): string => {
    switch (level) {
      case 'info':
        return 'text-blue-400'
      case 'warning':
        return 'text-yellow-400'
      case 'error':
        return 'text-red-400'
      case 'success':
        return 'text-green-400'
      default:
        return 'text-gray-400'
    }
  }

  const getLevelBg = (level: LogEntry['level']): string => {
    switch (level) {
      case 'info':
        return 'bg-blue-500/20'
      case 'warning':
        return 'bg-yellow-500/20'
      case 'error':
        return 'bg-red-500/20'
      case 'success':
        return 'bg-green-500/20'
      default:
        return 'bg-gray-500/20'
    }
  }

  const getMetricColor = (value: number): string => {
    if (value < 50) return 'text-green-400'
    if (value < 80) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="flex h-full bg-krystal-dark">
      {/* Metrics Panel */}
      <div className="w-80 bg-krystal-darker border-r border-gray-800 p-6">
        <div className="flex items-center space-x-2 mb-6">
          <Activity className={`w-5 h-5 ${isConnected ? 'text-green-400' : 'text-red-400'}`} />
          <h2 className="text-lg font-semibold text-white">System Monitor</h2>
        </div>

        {/* Connection Status */}
        <div className="mb-6 p-4 bg-gray-800 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Status</span>
            <span className={`text-sm font-medium ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              {isConnected ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>

        {/* System Metrics */}
        <div className="space-y-4">
          <div className="p-4 bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400">CPU</span>
              </div>
              <span className={`text-sm font-medium ${getMetricColor(metrics.cpu)}`}>
                {metrics.cpu.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-colors ${
                  metrics.cpu < 50 ? 'bg-green-400' : metrics.cpu < 80 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                style={{ width: `${metrics.cpu}%` }}
              ></div>
            </div>
          </div>

          <div className="p-4 bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400">Memory</span>
              </div>
              <span className={`text-sm font-medium ${getMetricColor(metrics.memory)}`}>
                {metrics.memory.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-colors ${
                  metrics.memory < 50 ? 'bg-green-400' : metrics.memory < 80 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                style={{ width: `${metrics.memory}%` }}
              ></div>
            </div>
          </div>

          <div className="p-4 bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <HardDrive className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400">Disk</span>
              </div>
              <span className={`text-sm font-medium ${getMetricColor(metrics.disk)}`}>
                {metrics.disk.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-colors ${
                  metrics.disk < 50 ? 'bg-green-400' : metrics.disk < 80 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                style={{ width: `${metrics.disk}%` }}
              ></div>
            </div>
          </div>

          <div className="p-4 bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Wifi className={`w-4 h-4 ${metrics.network ? 'text-green-400' : 'text-red-400'}`} />
                <span className="text-gray-400">Network</span>
              </div>
              <span className={`text-sm font-medium ${metrics.network ? 'text-green-400' : 'text-red-400'}`}>
                {metrics.network ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          <div className="p-4 bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400">Uptime</span>
              </div>
              <span className="text-sm font-medium text-gray-300">{metrics.uptime}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Logs Panel */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">System Logs</h3>
          <p className="text-sm text-gray-400">Real-time system monitoring output</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 font-mono text-sm scrollbar-thin">
          {logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <AlertCircle className="w-8 h-8 mx-auto mb-2" />
                <p>Waiting for system logs...</p>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className={`flex items-start space-x-3 p-2 rounded ${getLevelBg(log.level)}`}
                >
                  <span className="text-gray-500 text-xs">
                    {log.timestamp.toLocaleTimeString()}
                  </span>
                  <span className={`text-xs font-medium ${getLevelColor(log.level)}`}>
                    [{log.level.toUpperCase()}]
                  </span>
                  <span className="text-gray-400 text-xs">
                    {log.source}:
                  </span>
                  <span className="text-gray-300 flex-1">
                    {log.message}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
