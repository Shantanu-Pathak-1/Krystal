import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Activity, Shield, Check, X, RefreshCw, Sliders, Zap, Globe, Cpu } from 'lucide-react'
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets'
import { CandlestickData } from 'lightweight-charts'

interface MarketData {
  symbol: string
  bid: number
  ask: number
  change: number
  changePercent: number
}

interface AgentAnalysis {
  agent: string
  signal: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  reasoning: string
  timestamp: string
}

interface TradingStatus {
  markets: MarketData[]
  analyses: AgentAnalysis[]
  capital: number
  dailyLoss: number
  dailyProfit: number
  targetProfit: number
  riskLimit: number
  systemShutdown: boolean
  shutdownReason: string
  data_source: { [key: string]: string }
  indicators?: {
    rsi: number
    ema_20: number
    ema_50: number
    sma_50: number
    macd: number
    macd_signal: number
    current_price: number
  }
  pendingTrade: {
    symbol: string
    action: 'BUY' | 'SELL'
    amount: number
    price: number
  } | null
  positionSize?: {
    symbol: string
    risk_percentage: number
    risk_amount: number
    current_price: number
    stop_loss_pips: number
    position_size: number
    position_value: number
  }
  agentPerformance?: {
    agent: string
    totalRecommendations: number
    correctPredictions: number
    accuracyScore: number
    lastUpdated: string
  }[]
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: 'spring', stiffness: 300, damping: 30 }
  }
}

const marketSymbols = {
  'Forex': ['EUR/USD', 'GBP/USD', 'USD/JPY'],
  'Stocks': ['RELIANCE', 'TCS', 'AAPL', 'TSLA'],
  'Nifty 50': ['NIFTY 50'],
  'Crypto': ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD']
}

export default function TradingView() {
  const [status, setStatus] = useState<TradingStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [isLive, setIsLive] = useState(false)
  const [currency, setCurrency] = useState<'USD' | 'INR'>('USD')
  const [refreshing, setRefreshing] = useState(false)
  const [selectedSymbol, setSelectedSymbol] = useState('EUR/USD')
  const [selectedMarket, setSelectedMarket] = useState<'Forex' | 'Stocks' | 'Nifty 50' | 'Crypto'>('Forex')
  const [chartData, setChartData] = useState<CandlestickData[]>([])
  const [riskPercentage, setRiskPercentage] = useState(1.0)
  const [groqTypewriter, setGroqTypewriter] = useState('')
  const [geminiTypewriter, setGeminiTypewriter] = useState('')
  const [systemLocked, setSystemLocked] = useState(false)
  const [riskSettings, setRiskSettings] = useState({
    dailyLossLimit: 5000,
    targetProfitGoal: 10000,
    autoSell: false,
    stopLoss: false
  })
  const [agentStatus, setAgentStatus] = useState({
    groq_enabled: true,
    gemini_enabled: true
  })

  const USD_TO_INR = 83

  const formatCurrency = (value: number) => {
    if (currency === 'INR') {
      return `₹${(value * USD_TO_INR).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
    return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  // Helper to map UI symbols to TradingView symbols
  const getTVSymbol = (symbol: string) => {
    const mappings: { [key: string]: string } = {
      'EUR/USD': 'FX:EURUSD',
      'GBP/USD': 'FX:GBPUSD',
      'USD/JPY': 'FX:USDJPY',
      'AAPL': 'NASDAQ:AAPL',
      'GOOGL': 'NASDAQ:GOOGL',
      'TSLA': 'NASDAQ:TSLA',
      'MSFT': 'NASDAQ:MSFT',
      'RELIANCE': 'BSE:RELIANCE',
      'TCS': 'BSE:TCS',
      'HDFCBANK': 'BSE:HDFCBANK',
      'INFY': 'BSE:INFY',
      'NIFTY 50': 'BSE:NIFTY',
      'BTC/USD': 'BINANCE:BTCUSDT',
      'ETH/USD': 'BINANCE:ETHUSDT',
      'SOL/USD': 'BINANCE:SOLUSDT',
      'XRP/USD': 'BINANCE:XRPUSDT'
    }
    return mappings[symbol] || symbol
  }

  const fetchOHLCData = useCallback(async () => {
    // We'll use the AdvancedRealTimeChart widget instead of manual OHLC for now
    // as per user request to fix the blank chart.
  }, [selectedSymbol])

  const fetchStatus = useCallback(async () => {
    try {
      const mode = isLive ? 'live' : 'simulated'
      const response = await fetch(`http://localhost:8000/api/trading/status?mode=${mode}&symbol=${selectedSymbol}`)
      if (!response.ok) {
        console.error('Trading status API returned error:', response.status)
        setLoading(false)
        setRefreshing(false)
        return
      }
      const data = await response.json()
      setStatus(data)
      setLoading(false)
      setRefreshing(false)
      
      // Trigger typewriter effect for reasoning
      const groqAnalysis = data.analyses?.find((a: AgentAnalysis) => a.agent === 'groq')
      const geminiAnalysis = data.analyses?.find((a: AgentAnalysis) => a.agent === 'gemini')
      
      if (groqAnalysis?.reasoning && groqAnalysis.reasoning !== groqTypewriter) {
        typewriterEffect(groqAnalysis.reasoning, setGroqTypewriter)
      }
      if (geminiAnalysis?.reasoning && geminiAnalysis.reasoning !== geminiTypewriter) {
        typewriterEffect(geminiAnalysis.reasoning, setGeminiTypewriter)
      }
    } catch (error) {
      console.error('Failed to fetch trading status:', error)
      setLoading(false)
      setRefreshing(false)
    }
  }, [isLive, selectedSymbol])

  const typewriterEffect = (text: string, setter: (val: string) => void) => {
    let index = 0
    setter('')
    const interval = setInterval(() => {
      if (index < text.length) {
        setter(text.slice(0, index + 1))
        index++
      } else {
        clearInterval(interval)
      }
    }, 20)
    return () => clearInterval(interval)
  }

  useEffect(() => {
    fetchStatus()
    const statusInterval = setInterval(fetchStatus, 3000)
    return () => clearInterval(statusInterval)
  }, [fetchStatus])

  useEffect(() => {
    fetchOHLCData()
  }, [selectedSymbol, fetchOHLCData])

  useEffect(() => {
    if (status?.pendingTrade) {
      // Calculate position size based on risk percentage
      fetch(`http://localhost:8000/api/trading/position-size?symbol=${status.pendingTrade.symbol}&risk_percentage=${riskPercentage}`)
        .then(res => res.json())
        .then(data => {
          setStatus(prev => prev ? { ...prev, positionSize: data } : null)
        })
        .catch(err => console.error('Failed to calculate position size:', err))
    }
  }, [status?.pendingTrade, riskPercentage])

  // Check if risk limit exceeded
  useEffect(() => {
    if (status?.dailyLoss && status.dailyLoss >= riskSettings.dailyLossLimit) {
      setSystemLocked(true)
    }
  }, [status?.dailyLoss, riskSettings.dailyLossLimit])
  
  // Handle system shutdown from backend
  useEffect(() => {
    if (status?.systemShutdown) {
      setSystemLocked(true)
    }
  }, [status?.systemShutdown])
  
  // Send risk settings to backend when changed
  useEffect(() => {
    const updateRiskSettings = async () => {
      try {
        await fetch('http://localhost:8000/api/trading/risk-settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            daily_loss_limit: riskSettings.dailyLossLimit,
            target_profit: riskSettings.targetProfitGoal
          })
        })
      } catch (err) {
        console.error('Failed to update risk settings:', err)
      }
    }
    updateRiskSettings()
  }, [riskSettings.dailyLossLimit, riskSettings.targetProfitGoal])
  
  // Fetch AI agent status
  useEffect(() => {
    const fetchAgentStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/trading/agent-status')
        const data = await response.json()
        if (data.success) {
          setAgentStatus(data.status)
        }
      } catch (err) {
        console.error('Failed to fetch agent status:', err)
      }
    }
    fetchAgentStatus()
  }, [])

  const handleRefresh = () => {
    setRefreshing(true)
    fetchStatus()
  }

  const handleTradeDecision = async (approved: boolean) => {
    if (!status?.pendingTrade) return

    try {
      const response = await fetch('http://localhost:8000/api/trading/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: status.pendingTrade.symbol,
          action: status.pendingTrade.action,
          amount: status.pendingTrade.amount,
          approved
        })
      })
      const data = await response.json()
      fetchStatus()
    } catch (error) {
      console.error('Failed to execute trade:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 rounded-full"
          style={{
            background: 'conic-gradient(from 0deg, #10b981, #06b6d4, #10b981)',
            filter: 'blur(2px)'
          }}
        />
      </div>
    )
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="h-full overflow-y-auto p-4 space-y-4"
      style={{
        background: 'linear-gradient(180deg, #05080f 0%, #030609 100%)'
      }}
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Orbitron, monospace' }}>
            Trading Hub
          </h1>
          <div className="flex items-center gap-3 mt-1">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md">
              <Globe className="w-3 h-3 text-cyan-400" />
              <span className="text-[10px] text-white/60 font-medium uppercase tracking-wider">Mode:</span>
              <button 
                onClick={() => setIsLive(!isLive)}
                className={`flex items-center gap-1 px-1.5 py-0.5 rounded transition-all ${isLive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-yellow-500/20 text-yellow-400'}`}
              >
                <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${isLive ? 'bg-emerald-400' : 'bg-yellow-400'}`} />
                <span className="text-[10px] font-bold uppercase tracking-tighter">
                  {isLive ? 'LIVE MARKET (FCS)' : 'SIMULATED DATA'}
                </span>
              </button>
            </div>
            {/* Currency Toggle */}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md">
              <span className="text-[10px] text-white/60 font-medium uppercase tracking-wider">Currency:</span>
              <div className="flex bg-black/40 rounded-md p-0.5">
                {(['USD', 'INR'] as const).map((curr) => (
                  <button
                    key={curr}
                    onClick={() => setCurrency(curr)}
                    className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                      currency === curr 
                        ? 'bg-cyan-500/30 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.2)]' 
                        : 'text-white/40 hover:text-white/60'
                    }`}
                  >
                    {curr}
                  </button>
                ))}
              </div>
            </div>
            <p className="text-white/30 text-[10px] uppercase tracking-widest font-mono">v2.0 Real-Time Engine</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRefresh}
            className="p-2.5 rounded-xl transition-all hover:shadow-[0_0_15px_rgba(16,185,129,0.3)]"
            style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.2)'
            }}
          >
            <RefreshCw className={`w-4 h-4 text-emerald-400 ${refreshing ? 'animate-spin' : ''}`} />
          </motion.button>
        </div>
      </motion.div>

      {/* Market Switcher */}
      <motion.div variants={itemVariants} className="flex gap-2">
        {(['Forex', 'Stocks', 'Nifty 50', 'Crypto'] as const).map((market) => (
          <motion.button
            key={market}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              setSelectedMarket(market)
              setSelectedSymbol(marketSymbols[market][0])
            }}
            className={`flex-1 py-2 px-4 rounded-lg text-xs font-semibold transition-all ${
              selectedMarket === market
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-white/5 text-white/60 border border-white/10'
            }`}
          >
            {market}
          </motion.button>
        ))}
      </motion.div>

      {/* Capital Overview with Risk Slider */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-4 gap-3"
      >
        <div
          className="p-3 rounded-lg"
          style={{
            background: 'rgba(16, 185, 129, 0.05)',
            border: '1px solid rgba(16, 185, 129, 0.15)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <p className="text-white/40 text-[10px] uppercase tracking-wider mb-1">Capital</p>
          <p className="text-lg font-bold text-emerald-400">
            {formatCurrency(status?.capital || 0)}
          </p>
        </div>
        <div
          className="p-3 rounded-lg"
          style={{
            background: 'rgba(6, 182, 212, 0.05)',
            border: '1px solid rgba(6, 182, 212, 0.15)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <p className="text-white/40 text-[10px] uppercase tracking-wider mb-1">Daily Loss</p>
          <p className="text-lg font-bold text-cyan-400">
            {formatCurrency(status?.dailyLoss || 0)}
          </p>
        </div>
        <div
          className="p-3 rounded-lg"
          style={{
            background: 'rgba(239, 68, 68, 0.05)',
            border: '1px solid rgba(239, 68, 68, 0.15)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <p className="text-white/40 text-[10px] uppercase tracking-wider mb-1">Target Profit</p>
          <p className="text-lg font-bold text-red-400">
            {formatCurrency(riskSettings.targetProfitGoal)}
          </p>
        </div>
        <div
          className="p-3 rounded-lg"
          style={{
            background: 'rgba(168, 85, 247, 0.05)',
            border: '1px solid rgba(168, 85, 247, 0.15)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <p className="text-white/40 text-[10px] uppercase tracking-wider mb-1">Trade Risk</p>
          <div className="flex items-center gap-2">
            <Sliders className="w-3 h-3 text-purple-400" />
            <p className="text-lg font-bold text-purple-400">
              {riskPercentage}%
            </p>
          </div>
          <input
            type="range"
            min="0.5"
            max="5"
            step="0.5"
            value={riskPercentage}
            onChange={(e) => setRiskPercentage(parseFloat(e.target.value))}
            className="w-full mt-2 accent-purple-500"
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              height: '3px',
              borderRadius: '2px'
            }}
          />
        </div>
      </motion.div>

      {/* AI Agent Controls */}
      <motion.div
        variants={itemVariants}
        className="p-4 rounded-lg"
        style={{
          background: 'rgba(16, 185, 129, 0.03)',
          border: '1px solid rgba(16, 185, 129, 0.1)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white/90">AI Agent Controls</h2>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center justify-between p-3 rounded-lg" style={{ background: 'rgba(139, 92, 246, 0.05)', border: '1px solid rgba(139, 92, 246, 0.15)' }}>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-400" />
              <span className="text-white/70 text-xs font-semibold">Groq (Technical)</span>
            </div>
            <button
              onClick={() => {
                const newState = !agentStatus.groq_enabled
                setAgentStatus(prev => ({ ...prev, groq_enabled: newState }))
                fetch('http://localhost:8000/api/trading/toggle-groq', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ enabled: newState })
                })
              }}
              className={`w-8 h-4 rounded-full transition-all ${agentStatus.groq_enabled ? 'bg-emerald-500' : 'bg-white/20'}`}
            >
              <div className={`w-3 h-3 rounded-full bg-white transition-all ${agentStatus.groq_enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg" style={{ background: 'rgba(6, 182, 212, 0.05)', border: '1px solid rgba(6, 182, 212, 0.15)' }}>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400" />
              <span className="text-white/70 text-xs font-semibold">Gemini (Sentiment)</span>
            </div>
            <button
              onClick={() => {
                const newState = !agentStatus.gemini_enabled
                setAgentStatus(prev => ({ ...prev, gemini_enabled: newState }))
                fetch('http://localhost:8000/api/trading/toggle-gemini', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ enabled: newState })
                })
              }}
              className={`w-8 h-4 rounded-full transition-all ${agentStatus.gemini_enabled ? 'bg-emerald-500' : 'bg-white/20'}`}
            >
              <div className={`w-3 h-3 rounded-full bg-white transition-all ${agentStatus.gemini_enabled ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Risk Settings Panel */}
      <motion.div
        variants={itemVariants}
        className="p-4 rounded-lg"
        style={{
          background: 'rgba(239, 68, 68, 0.03)',
          border: '1px solid rgba(239, 68, 68, 0.1)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-red-400" />
          <h2 className="text-sm font-semibold text-white/90">Risk Settings</h2>
        </div>
        <div className="grid grid-cols-4 gap-3">
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Daily Loss Limit ($)</label>
            <input
              type="number"
              value={riskSettings.dailyLossLimit}
              onChange={(e) => setRiskSettings(prev => ({ ...prev, dailyLossLimit: parseFloat(e.target.value) || 0 }))}
              className="w-full px-2 py-1 rounded bg-white/5 border border-white/10 text-white text-xs"
            />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Target Profit ($)</label>
            <input
              type="number"
              value={riskSettings.targetProfitGoal}
              onChange={(e) => setRiskSettings(prev => ({ ...prev, targetProfitGoal: parseFloat(e.target.value) || 0 }))}
              className="w-full px-2 py-1 rounded bg-white/5 border border-white/10 text-white text-xs"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[10px] text-white/40">Auto-Sell</label>
            <button
              onClick={() => setRiskSettings(prev => ({ ...prev, autoSell: !prev.autoSell }))}
              className={`w-8 h-4 rounded-full transition-all ${riskSettings.autoSell ? 'bg-emerald-500' : 'bg-white/20'}`}
            >
              <div className={`w-3 h-3 rounded-full bg-white transition-all ${riskSettings.autoSell ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[10px] text-white/40">Stop-Loss</label>
            <button
              onClick={() => setRiskSettings(prev => ({ ...prev, stopLoss: !prev.stopLoss }))}
              className={`w-8 h-4 rounded-full transition-all ${riskSettings.stopLoss ? 'bg-emerald-500' : 'bg-white/20'}`}
            >
              <div className={`w-3 h-3 rounded-full bg-white transition-all ${riskSettings.stopLoss ? 'translate-x-4' : 'translate-x-0.5'}`} />
            </button>
          </div>
        </div>
      </motion.div>

      {/* Live Market Watch with Chart */}
      <motion.div
        variants={itemVariants}
        className="p-4 rounded-xl"
        style={{
          background: 'rgba(16, 185, 129, 0.03)',
          border: '1px solid rgba(16, 185, 129, 0.1)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-white/90">Live Market Watch</h2>
              {status?.data_source && status.data_source[selectedSymbol] === 'live' ? (
                <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[10px] text-emerald-400 font-semibold uppercase tracking-tight">LIVE MARKET (FCS)</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-yellow-500/10 border border-yellow-500/30">
                  <div className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
                  <span className="text-[10px] text-yellow-400 font-semibold uppercase tracking-tight">SIMULATED DATA</span>
                </div>
              )}
            </div>
            {/* Asset Status Row */}
            {status?.markets?.find(m => m.symbol === selectedSymbol) && (
              <div className="flex items-center gap-6 px-4 py-1.5 rounded-xl bg-black/40 border border-white/5 backdrop-blur-md">
                <div className="flex flex-col">
                  <span className="text-[9px] text-white/30 uppercase font-bold tracking-widest">Price</span>
                  <span className="text-sm font-mono font-bold text-cyan-400">
                    {status.markets.find(m => m.symbol === selectedSymbol)?.bid.toFixed(5)}
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-white/30 uppercase font-bold tracking-widest">Change</span>
                  <span className={`text-sm font-mono font-bold ${
                    (status.markets.find(m => m.symbol === selectedSymbol)?.change || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}>
                    {(status.markets.find(m => m.symbol === selectedSymbol)?.change || 0) >= 0 ? '+' : ''}
                    {status.markets.find(m => m.symbol === selectedSymbol)?.change.toFixed(2)}%
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-white/30 uppercase font-bold tracking-widest">Volume</span>
                  <span className="text-sm font-mono font-bold text-white/80">
                    {(Math.random() * 1000000).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            {marketSymbols[selectedMarket].map((symbol) => (
              <motion.button
                key={symbol}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedSymbol(symbol)}
                className={`px-2 py-1 rounded-md text-[10px] font-semibold transition-all ${
                  selectedSymbol === symbol
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-white/5 text-white/60 border border-white/10'
                }`}
              >
                {symbol}
              </motion.button>
            ))}
          </div>
        </div>
        
        {/* Technical Indicators Row */}
        {status?.indicators && (
          <div className="flex gap-4 mb-4">
            {[
              { label: 'RSI (14)', value: status.indicators.rsi.toFixed(1), color: status.indicators.rsi > 70 ? 'text-red-400' : status.indicators.rsi < 30 ? 'text-emerald-400' : 'text-cyan-400' },
              { label: 'EMA (20)', value: status.indicators.ema_20.toFixed(5), color: 'text-purple-400' },
              { label: 'EMA (50)', value: status.indicators.ema_50.toFixed(5), color: 'text-blue-400' },
              { label: 'MACD', value: status.indicators.macd.toFixed(5), color: 'text-amber-400' },
              { label: 'Signal', value: status.indicators.macd_signal.toFixed(5), color: 'text-rose-400' }
            ].map((ind, i) => (
              <div key={i} className="flex-1 p-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md">
                <span className="text-[9px] text-white/30 uppercase font-bold tracking-widest block mb-0.5">{ind.label}</span>
                <span className={`text-xs font-mono font-bold ${ind.color}`}>{ind.value}</span>
              </div>
            ))}
          </div>
        )}

        {/* Chart */}
        <div className="h-[450px] mb-4 overflow-hidden rounded-xl border border-white/10 bg-black/40">
          <AdvancedRealTimeChart 
            symbol={getTVSymbol(selectedSymbol)}
            theme="dark"
            autosize
            interval="D"
            timezone="Etc/UTC"
            style="1"
            locale="en"
            toolbar_bg="#f1f3f6"
            enable_publishing={false}
            hide_side_toolbar={false}
            allow_symbol_change={true}
            container_id="tradingview_widget"
          />
        </div>
        
        {/* Market Data Cards */}
        <div className="space-y-2">
          {status?.markets?.map((market) => (
            <motion.div
              key={market.symbol}
              whileHover={{ x: 4 }}
              className={`flex items-center justify-between p-3 rounded-md transition-all ${
                selectedSymbol === market.symbol
                  ? 'bg-emerald-500/10 border border-emerald-500/30'
                  : 'bg-white/5 border border-white/10'
              }`}
            >
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-md flex items-center justify-center font-bold text-white text-xs"
                  style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)' }}
                >
                  {market.symbol.substring(0, 3)}
                </div>
                <div>
                  <p className="font-semibold text-white text-sm">{market.symbol}</p>
                  <p className="text-white/40 text-xs">
                    Bid: {market.bid.toFixed(5)} | Ask: {market.ask.toFixed(5)}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-semibold text-sm ${market.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {market.change >= 0 ? '+' : ''}{market.change.toFixed(2)}%
                </p>
                <p className="text-white/40 text-xs">
                  {market.change >= 0 ? '+' : ''}{market.changePercent.toFixed(3)}%
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* AI Performance Stats */}
      <motion.div
        variants={itemVariants}
        className="p-4 rounded-lg"
        style={{
          background: 'rgba(16, 185, 129, 0.03)',
          border: '1px solid rgba(16, 185, 129, 0.1)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white/90">AI Performance Stats</h2>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {status?.agentPerformance?.map((perf) => (
            <div
              key={perf.agent}
              className="p-3 rounded-lg"
              style={{
                background: perf.agent === 'groq' ? 'rgba(139, 92, 246, 0.05)' : 'rgba(6, 182, 212, 0.05)',
                border: perf.agent === 'groq' ? '1px solid rgba(139, 92, 246, 0.15)' : '1px solid rgba(6, 182, 212, 0.15)'
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-white/70 text-xs font-semibold capitalize">{perf.agent}</span>
                <span className={`text-lg font-bold ${perf.accuracyScore >= 70 ? 'text-emerald-400' : perf.accuracyScore >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {perf.accuracyScore}%
                </span>
              </div>
              <div className="flex justify-between text-[10px] text-white/50">
                <span>{perf.correctPredictions}/{perf.totalRecommendations} correct</span>
                <span>Rec: {perf.totalRecommendations}</span>
              </div>
              <div className="mt-2 h-1 rounded-full bg-white/10 overflow-hidden">
                <div
                  className={`h-full transition-all ${perf.accuracyScore >= 70 ? 'bg-emerald-500' : perf.accuracyScore >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${perf.accuracyScore}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* AI Workflow Explanation */}
      <motion.div
        variants={itemVariants}
        className="p-4 rounded-lg"
        style={{
          background: 'rgba(16, 185, 129, 0.03)',
          border: '1px solid rgba(16, 185, 129, 0.1)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white/90">How AI Works</h2>
        </div>
        <div className="space-y-2 text-xs text-white/60">
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 rounded-full bg-purple-500/20 flex items-center justify-center text-[10px] font-bold text-purple-400 flex-shrink-0 mt-0.5">1</div>
            <p><span className="text-purple-300 font-semibold">Groq Technical Analyst</span> analyzes RSI, MACD indicators to detect overbought/oversold conditions</p>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 rounded-full bg-cyan-500/20 flex items-center justify-center text-[10px] font-bold text-cyan-400 flex-shrink-0 mt-0.5">2</div>
            <p><span className="text-cyan-300 font-semibold">Gemini Sentiment Analyst</span> analyzes news flow and market sentiment via web search</p>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center text-[10px] font-bold text-emerald-400 flex-shrink-0 mt-0.5">3</div>
            <p><span className="text-emerald-300 font-semibold">Iron Guard Risk Manager</span> validates trades against risk limits (1% max per trade, $5K daily loss limit)</p>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 rounded-full bg-yellow-500/20 flex items-center justify-center text-[10px] font-bold text-yellow-400 flex-shrink-0 mt-0.5">4</div>
            <p><span className="text-yellow-300 font-semibold">Human Approval</span> - You review and approve/reject the trade before execution</p>
          </div>
        </div>
      </motion.div>

      {/* Agent Analysis */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-2 gap-3"
      >
        {/* Groq Technical Analyst */}
        <div
          className="p-4 rounded-lg"
          style={{
            background: 'rgba(139, 92, 246, 0.03)',
            border: '1px solid rgba(139, 92, 246, 0.1)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-white/90">Groq Technical</h2>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-white/60 text-xs">Signal</span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  (status?.analyses?.find(a => a.agent === 'groq')?.signal || 'HOLD') === 'BUY'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : (status?.analyses?.find(a => a.agent === 'groq')?.signal || 'HOLD') === 'SELL'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-gray-500/20 text-gray-400'
                }`}
              >
                {status?.analyses?.find(a => a.agent === 'groq')?.signal || 'HOLD'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-white/60 text-xs">Confidence</span>
              <span className="text-white/90 font-semibold text-sm">
                {status?.analyses?.find(a => a.agent === 'groq')?.confidence || 0}%
              </span>
            </div>
            <div className="mt-2 p-2 rounded-md bg-black/30 border border-white/10">
              <p className="text-[10px] text-white/50 mb-1 font-mono">// GROQ_ANALYSIS</p>
              <p className="text-xs text-emerald-300/90 font-mono leading-relaxed">
                {groqTypewriter || status?.analyses?.find(a => a.agent === 'groq')?.reasoning || `Analyzing technical indicators for ${selectedSymbol}... Detecting support/resistance zones and RSI divergence.`}
                <span className="inline-block w-1.5 h-3 ml-1 bg-emerald-400 animate-pulse" />
              </p>
            </div>
          </div>
        </div>

        {/* Gemini Sentiment Analyst */}
        <div
          className="p-4 rounded-lg"
          style={{
            background: 'rgba(6, 182, 212, 0.03)',
            border: '1px solid rgba(6, 182, 212, 0.1)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold text-white/90">Gemini Sentiment</h2>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-white/60 text-xs">Signal</span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  (status?.analyses?.find(a => a.agent === 'gemini')?.signal || 'HOLD') === 'BUY'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : (status?.analyses?.find(a => a.agent === 'gemini')?.signal || 'HOLD') === 'SELL'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-gray-500/20 text-gray-400'
                }`}
              >
                {status?.analyses?.find(a => a.agent === 'gemini')?.signal || 'HOLD'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-white/60 text-xs">Confidence</span>
              <span className="text-white/90 font-semibold text-sm">
                {status?.analyses?.find(a => a.agent === 'gemini')?.confidence || 0}%
              </span>
            </div>
            <div className="mt-2 p-2 rounded-md bg-black/30 border border-white/10">
              <p className="text-[10px] text-white/50 mb-1 font-mono">// GEMINI_SENTIMENT</p>
              <p className="text-xs text-cyan-300/90 font-mono leading-relaxed">
                {geminiTypewriter || status?.analyses?.find(a => a.agent === 'gemini')?.reasoning || `Parsing global news sentiment for ${selectedSymbol}. Monitoring institutional order flow and macro-economic catalysts.`}
                <span className="inline-block w-1.5 h-3 ml-1 bg-cyan-400 animate-pulse" />
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* AI Trade Proposal Action Block */}
      <motion.div
        variants={itemVariants}
        className="p-4 rounded-lg"
        style={{
          background: 'rgba(16, 185, 129, 0.05)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
        }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white tracking-wide" style={{ fontFamily: 'Syne, sans-serif' }}>AI Trade Proposal</h2>
          </div>
          <div className="px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30">
            <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest">Autonomous Consensus</span>
          </div>
        </div>

        {status?.pendingTrade ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest mb-2">Strategy Details</p>
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <span className="text-white/60 text-xs">Signal</span>
                    <span className={`text-sm font-bold ${status.pendingTrade.action === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {status.pendingTrade.action} {selectedSymbol}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white/60 text-xs">Entry Price</span>
                    <span className="text-sm font-mono text-white/90">{status.pendingTrade.price.toFixed(5)}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-white/60">Position Size</span>
                    <span className="text-white/90 font-mono">{formatCurrency(status.positionSize?.position_size || 0)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest mb-2">Risk Management</p>
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <span className="text-white/60 text-xs">Stop Loss (SL)</span>
                    <span className="text-sm font-mono text-red-400/80">{(status.pendingTrade.price * (status.pendingTrade.action === 'BUY' ? 0.985 : 1.015)).toFixed(5)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-white/60 text-xs">Take Profit (TP)</span>
                    <span className="text-sm font-mono text-emerald-400/80">{(status.pendingTrade.price * (status.pendingTrade.action === 'BUY' ? 1.04 : 0.96)).toFixed(5)}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-white/60">Risk/Reward</span>
                    <span className="text-cyan-400 font-mono">1:2.6</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="md:col-span-2 flex gap-3 mt-2">
              <motion.button
                whileHover={{ scale: 1.02, boxShadow: '0 0 20px rgba(16,185,129,0.2)' }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleTradeDecision(true)}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all"
                style={{
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)'
                }}
              >
                <Check className="w-4 h-4" />
                Approve Trade
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleTradeDecision(false)}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all"
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#f87171'
                }}
              >
                <X className="w-4 h-4" />
                Reject Trade
              </motion.button>
            </div>
          </div>
        ) : (
          <div className="py-8 flex flex-col items-center justify-center text-center">
            <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
              <Activity className="w-6 h-6 text-white/20 animate-pulse" />
            </div>
            <p className="text-white/40 text-sm font-medium">Scanning Market for High-Probability Setups...</p>
            <p className="text-white/20 text-[10px] mt-1 font-mono uppercase tracking-widest">Waiting for Groq & Gemini Consensus</p>
          </div>
        )}
      </motion.div>

      {/* System Locked Overlay */}
      {systemLocked && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 flex items-center justify-center z-50"
          style={{
            background: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <div
            className="p-8 rounded-2xl text-center"
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '2px solid rgba(239, 68, 68, 0.3)',
              backdropFilter: 'blur(20px)'
            }}
          >
            <Shield className="w-16 h-16 text-red-500 mx-auto mb-4 animate-pulse" />
            <h2 className="text-2xl font-bold text-red-400 mb-2" style={{ fontFamily: 'Orbitron, monospace' }}>
              SYSTEM LOCKED
            </h2>
            <p className="text-white/70 text-sm">{status?.shutdownReason || 'Risk Limit Exceeded'}</p>
            <p className="text-white/50 text-xs mt-2">
              Daily Loss: ${status?.dailyLoss?.toLocaleString()} / Limit: ${riskSettings.dailyLossLimit.toLocaleString()}
            </p>
            <button
              onClick={() => setSystemLocked(false)}
              className="mt-6 px-6 py-2 rounded-lg bg-white/10 text-white text-sm hover:bg-white/20 transition-all"
            >
              Acknowledge & Reset
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
