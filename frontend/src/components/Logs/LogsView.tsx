import { useState, useEffect, useRef } from 'react'
import { Terminal, Download, Filter, Search, RefreshCw, AlertCircle, Info, CheckCircle, XCircle } from 'lucide-react'

interface LogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'success' | 'debug'
  source: string
  message: string
  metadata?: Record<string, any>
}

export default function LogsView() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([])
  const [selectedLevel, setSelectedLevel] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const fetchLogs = async () => {
      setIsLoading(true)
      try {
        const response = await fetch('http://localhost:8000/api/logs')
        const data = await response.json()
        setLogs(data.logs || [])
      } catch (error) {
        console.error('Failed to fetch logs:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchLogs()
    const interval = setInterval(fetchLogs, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    let filtered = logs

    // Filter by level
    if (selectedLevel !== 'all') {
      filtered = filtered.filter(log => log.level === selectedLevel)
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.source.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    setFilteredLogs(filtered)
  }, [logs, selectedLevel, searchTerm])

  useEffect(() => {
    if (autoScroll) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [filteredLogs, autoScroll])

  const getLevelIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'info':
        return <Info className="w-4 h-4 text-blue-400" />
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-400" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-400" />
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'debug':
        return <Terminal className="w-4 h-4 text-gray-400" />
      default:
        return <Info className="w-4 h-4 text-gray-400" />
    }
  }

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'info':
        return 'text-blue-400'
      case 'warning':
        return 'text-yellow-400'
      case 'error':
        return 'text-red-400'
      case 'success':
        return 'text-green-400'
      case 'debug':
        return 'text-gray-400'
      default:
        return 'text-gray-400'
    }
  }

  const getLevelBg = (level: LogEntry['level']) => {
    switch (level) {
      case 'info':
        return 'bg-blue-500/20'
      case 'warning':
        return 'bg-yellow-500/20'
      case 'error':
        return 'bg-red-500/20'
      case 'success':
        return 'bg-green-500/20'
      case 'debug':
        return 'bg-gray-500/20'
      default:
        return 'bg-gray-500/20'
    }
  }

  const exportLogs = () => {
    const logData = filteredLogs.map(log => 
      `${log.timestamp} [${log.level.toUpperCase()}] ${log.source}: ${log.message}`
    ).join('\n')
    
    const blob = new Blob([logData], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `krystal-logs-${new Date().toISOString()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const clearLogs = () => {
    setLogs([])
    setFilteredLogs([])
  }

  const refreshLogs = () => {
    // Logs are auto-refreshed every 5 seconds
    // This button is now just a placeholder for manual refresh if needed
    window.location.reload()
  }

  return (
    <div className="flex h-full bg-krystal-dark">
      {/* Main Logs Panel */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-800 p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Terminal className="w-6 h-6 text-gray-400" />
              <h1 className="text-xl font-semibold text-white">System Logs</h1>
              <span className="text-sm text-gray-400">({filteredLogs.length} entries)</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  autoScroll ? 'bg-krystal-purple text-white' : 'bg-gray-800 text-gray-400'
                }`}
              >
                Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
              </button>
              <button
                onClick={refreshLogs}
                className="p-2 bg-gray-800 text-gray-400 rounded hover:bg-gray-700 transition-colors"
                title="Refresh logs"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button
                onClick={exportLogs}
                className="p-2 bg-gray-800 text-gray-400 rounded hover:bg-gray-700 transition-colors"
                title="Export logs"
              >
                <Download className="w-4 h-4" />
              </button>
              <button
                onClick={clearLogs}
                className="p-2 bg-gray-800 text-gray-400 rounded hover:bg-gray-700 transition-colors"
                title="Clear logs"
              >
                <XCircle className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search logs..."
                className="w-full pl-10 pr-3 py-2 bg-gray-800 text-white rounded border border-gray-700 focus:border-krystal-purple focus:outline-none"
              />
            </div>

            {/* Level Filter */}
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="px-3 py-2 bg-gray-800 text-white rounded border border-gray-700 focus:border-krystal-purple focus:outline-none"
              >
                <option value="all">All Levels</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
                <option value="success">Success</option>
                <option value="debug">Debug</option>
              </select>
            </div>
          </div>
        </div>

        {/* Logs Display */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto p-4 font-mono text-sm scrollbar-thin">
            {isLoading ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin" />
                  <p>Loading logs...</p>
                </div>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Terminal className="w-8 h-8 mx-auto mb-2" />
                  <p>No logs found</p>
                  <p className="text-sm">Try adjusting your filters</p>
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredLogs.map((log) => (
                  <div
                    key={log.id}
                    className={`flex items-start space-x-3 p-2 rounded ${getLevelBg(log.level)} hover:bg-opacity-30 transition-colors`}
                  >
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      {getLevelIcon(log.level)}
                      <span className="text-gray-500 text-xs">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs font-medium ${getLevelColor(log.level)}`}>
                          [{log.level.toUpperCase()}]
                        </span>
                        <span className="text-gray-400 text-xs">
                          {log.source}
                        </span>
                      </div>
                      <div className="text-gray-300 break-words">
                        {log.message}
                      </div>
                      {log.metadata && (
                        <div className="text-xs text-gray-500 mt-1">
                          {Object.entries(log.metadata).map(([key, value]) => (
                            <span key={key} className="mr-3">
                              {key}: {JSON.stringify(value)}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Side Panel - Log Statistics */}
      <div className="w-64 bg-krystal-darker border-l border-gray-800 p-4">
        <h3 className="text-lg font-semibold text-white mb-4">Log Statistics</h3>
        
        <div className="space-y-4">
          <div>
            <div className="text-sm text-gray-400 mb-2">Total Logs</div>
            <div className="text-2xl font-bold text-white">{logs.length}</div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-400">Info</span>
              <span className="text-sm text-white">
                {logs.filter(l => l.level === 'info').length}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-yellow-400">Warning</span>
              <span className="text-sm text-white">
                {logs.filter(l => l.level === 'warning').length}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-red-400">Error</span>
              <span className="text-sm text-white">
                {logs.filter(l => l.level === 'error').length}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-green-400">Success</span>
              <span className="text-sm text-white">
                {logs.filter(l => l.level === 'success').length}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Debug</span>
              <span className="text-sm text-white">
                {logs.filter(l => l.level === 'debug').length}
              </span>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-4">
            <div className="text-sm text-gray-400 mb-2">Sources</div>
            <div className="space-y-1">
              {Array.from(new Set(logs.map(l => l.source))).map(source => (
                <div key={source} className="flex items-center justify-between">
                  <span className="text-xs text-gray-300">{source}</span>
                  <span className="text-xs text-white">
                    {logs.filter(l => l.source === source).length}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
