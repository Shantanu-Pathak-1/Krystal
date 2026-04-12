 import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, Database, HardDrive, Zap, Globe, Server, Cloud, TrendingUp, Flame } from 'lucide-react'

interface ProviderStats {
  today: number
  total: number
  limit: number
  percent: number
  last_reset: string
}

interface StorageStats {
  mongodb: {
    size_mb: number
    docs: number
    last_updated: string
  }
  pinecone: {
    vectors: number
    fullness: number
    last_updated: string
  }
}

interface UsageData {
  providers: Record<string, ProviderStats>
  storage: StorageStats
  last_updated: string
}

export default function ApiDashboardView() {
  const [stats, setStats] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/resources/stats');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        console.log("Fetched Stats:", data);
        console.log("Providers:", data.providers);
        console.log("Storage:", data.storage);
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoading(false)
      }
    };

    fetchStats();
  }, [])

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      groq: '#10b981',
      sambanova: '#f59e0b',
      together: '#8b5cf6',
      openrouter: '#06b6d4',
      fireworks: '#ef4444',
      gemini: '#f59e0b',
      huggingface: '#f97316',
      ollama: '#8b5cf6'
    }
    return colors[provider] || '#6b7280'
  }

  const getProviderIcon = (provider: string) => {
    const icons: Record<string, JSX.Element> = {
      groq: <Zap className="w-5 h-5" />,
      sambanova: <Server className="w-5 h-5" />,
      together: <Globe className="w-5 h-5" />,
      openrouter: <Activity className="w-5 h-5" />,
      fireworks: <Flame className="w-5 h-5" />,
      gemini: <Cloud className="w-5 h-5" />,
      huggingface: <TrendingUp className="w-5 h-5" />,
      ollama: <Database className="w-5 h-5" />
    }
    return icons[provider] || <Activity className="w-5 h-5" />
  }

  const formatProviderName = (provider: string) => {
    return provider.charAt(0).toUpperCase() + provider.slice(1)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl font-semibold text-red-400 mb-2">Failed to load usage data</p>
          <p className="text-sm text-gray-400">Please check your API connection</p>
        </div>
      </div>
    )
  }

  console.log("Rendering stats:", stats);
  console.log("Providers keys:", stats.providers ? Object.keys(stats.providers) : "No providers");

  return (
    <div className="h-full w-full overflow-y-auto p-6 pb-32">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">API & Resource Dashboard</h1>
        <p className="text-gray-400">Monitor your AI provider usage and storage statistics</p>
      </motion.div>

      {/* Provider Usage Cards */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8"
      >
        {Object.entries(stats?.providers || {}).map(([provider, providerStats], index) => (
          <motion.div
            key={provider}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            className="relative group"
            style={{
              background: 'rgba(6,9,20,0.8)',
              backdropFilter: 'blur(20px)',
              border: `1px solid ${getProviderColor(provider)}30`,
              borderRadius: '16px',
              padding: '20px'
            }}
          >
            {/* Glowing border effect */}
            <div 
              className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              style={{
                background: `linear-gradient(135deg, ${getProviderColor(provider)}20, transparent)`,
                border: `1px solid ${getProviderColor(provider)}40`,
                borderRadius: '16px',
                padding: '2px'
              }}
            />
            
            <div className="relative z-10">
              {/* Provider Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div 
                    className="p-2 rounded-lg"
                    style={{ backgroundColor: `${getProviderColor(provider)}20` }}
                  >
                    {getProviderIcon(provider)}
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{formatProviderName(provider)}</h3>
                    <p className="text-xs text-gray-400">AI Provider</p>
                  </div>
                </div>
              </div>

              {/* Usage Stats */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">Today's Requests</span>
                    <span className="text-sm font-semibold text-white">{providerStats?.today || 0}</span>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">Total Requests</span>
                    <span className="text-sm font-semibold text-white">{providerStats?.total || 0}</span>
                  </div>
                </div>

                {/* Daily Limit Progress Bar */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-400">Daily Limit</span>
                    <span className="text-xs text-gray-300">
                      {providerStats?.today || 0}/{providerStats?.limit || 0}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: getProviderColor(provider) }}
                      initial={{ width: 0 }}
                      animate={{ width: `${providerStats?.percent || 0}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                    />
                  </div>
                  <div className="text-xs text-gray-400 mt-1 text-right">
                    {providerStats?.percent?.toFixed(1) || 0}% used
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Storage Cards */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* MongoDB Storage Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
          className="relative group"
          style={{
            background: 'rgba(6,9,20,0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(34,197,94,0.3)',
            borderRadius: '16px',
            padding: '24px'
          }}
        >
          {/* Glowing border effect */}
          <div 
            className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{
              background: 'linear-gradient(135deg, rgba(34,197,94,0.2), transparent)',
              border: '1px solid rgba(34,197,94,0.4)',
              borderRadius: '16px',
              padding: '2px'
            }}
          />
          
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-4">
              <div 
                className="p-3 rounded-xl"
                style={{ backgroundColor: 'rgba(34,197,94,0.2)' }}
              >
                <Database className="w-6 h-6" style={{ color: '#22c55e' }} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">MongoDB</h3>
                <p className="text-sm text-gray-400">Chat History Database</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Database Size</span>
                <span className="text-lg font-semibold text-white">
                  {stats?.storage?.mongodb?.size_mb?.toFixed(2) || 0} MB
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Document Count</span>
                <span className="text-lg font-semibold text-white">
                  {stats?.storage?.mongodb?.docs?.toLocaleString() || 0}
                </span>
              </div>

              <div className="text-xs text-gray-500">
                Last updated: {stats?.storage?.mongodb?.last_updated ? new Date(stats.storage.mongodb.last_updated).toLocaleString() : 'N/A'}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Pinecone Storage Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.5 }}
          className="relative group"
          style={{
            background: 'rgba(6,9,20,0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(139,92,246,0.3)',
            borderRadius: '16px',
            padding: '24px'
          }}
        >
          {/* Glowing border effect */}
          <div 
            className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{
              background: 'linear-gradient(135deg, rgba(139,92,246,0.2), transparent)',
              border: '1px solid rgba(139,92,246,0.4)',
              borderRadius: '16px',
              padding: '2px'
            }}
          />
          
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-4">
              <div 
                className="p-3 rounded-xl"
                style={{ backgroundColor: 'rgba(139,92,246,0.2)' }}
              >
                <HardDrive className="w-6 h-6" style={{ color: '#8b5cf6' }} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Pinecone</h3>
                <p className="text-sm text-gray-400">Vector Memory Store</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Vector Count</span>
                <span className="text-lg font-semibold text-white">
                  {stats?.storage?.pinecone?.vectors?.toLocaleString() || 0}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Index Fullness</span>
                <span className="text-lg font-semibold text-white">
                  {stats?.storage?.pinecone?.fullness?.toFixed(1) || 0}%
                </span>
              </div>

              {/* Index Fullness Progress Bar */}
              <div>
                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: '#8b5cf6' }}
                    initial={{ width: 0 }}
                    animate={{ width: `${stats?.storage?.pinecone?.fullness || 0}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                  />
                </div>
              </div>

              <div className="text-xs text-gray-500">
                Last updated: {stats?.storage?.pinecone?.last_updated ? new Date(stats.storage.pinecone.last_updated).toLocaleString() : 'N/A'}
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Last Updated */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.8 }}
      >
        <div className="text-center text-sm text-gray-500 mt-8">
          Last updated: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'N/A'}
        </div>
      </motion.div>
    </div>
  )
}
