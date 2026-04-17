import { useState, useEffect } from 'react'
import Layout from './components/Layout/Layout'
import MainChat from './components/MainChat/MainChat'
import HeartbeatMonitor from './components/HeartbeatMonitor/HeartbeatMonitor'
import ZenVoiceMode from './components/ZenVoiceMode/ZenVoiceMode'
import DashboardView from './components/Dashboard/DashboardView'
import LogsView from './components/Logs/LogsView'
import ConfigView from './components/Config/ConfigView'
import MemoryVaultView from './components/MemoryVault/MemoryVaultView'
import DiaryView from './components/Diary/DiaryView'
import QuickChatView from './components/QuickChat/QuickChatView'
import ApiDashboardView from './views/ApiDashboardView'
import TradingView from './views/TradingView'
import { AutonomyProvider } from './context/AutonomyContext'
import { PerformanceProvider } from './context/PerformanceContext'
import { ThemeProvider } from './context/ThemeContext'

type ViewMode = 'main' | 'heartbeat' | 'zen' | 'dashboard' | 'logs' | 'config' | 'memory' | 'diary' | 'api' | 'trading'
type AutonomyMode = 'safe' | 'agentic' | 'god'

export default function App() {
  const [currentView, setCurrentView] = useState<ViewMode>(() => {
    // Check if this is a fresh boot or refresh
    const isFreshBoot = !sessionStorage.getItem('krystal_app_initialized')

    if (isFreshBoot) {
      // Fresh boot - start with dashboard
      sessionStorage.setItem('krystal_app_initialized', 'true')
      return 'dashboard'
    } else {
      // Refresh - restore last view from localStorage
      const savedView = localStorage.getItem('krystal_last_view')
      return (savedView as ViewMode) || 'dashboard'
    }
  })
  const [autonomyMode, setAutonomyMode] = useState<AutonomyMode>('agentic')
  const [isQuickView, setIsQuickView] = useState(false)

  // Save current view to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('krystal_last_view', currentView)
  }, [currentView])

  useEffect(() => {
    // Basic manual routing for Electron dual-window setup
    if (window.location.pathname === '/quick') {
      setIsQuickView(true)
    }

    // Voice Status Polling for Auto-Popup logic
    let lastStatus = 'passive';
    const pollVoiceStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/system/voice-status');
        const data = await response.json();
        const currentStatus = data.voice_status;

        if (lastStatus === 'passive' && currentStatus === 'active') {
          // @ts-ignore - Electron IPC
          if (window.require) {
            const electron = window.require('electron');
            electron.ipcRenderer.send('wake-word-detected');
          }
        }
        lastStatus = currentStatus;
      } catch (error) {
        // Silently handle polling errors
      }
    };

    const intervalId = setInterval(pollVoiceStatus, 2000);
    return () => clearInterval(intervalId);
  }, [])

  if (isQuickView) {
    return (
      <ThemeProvider>
        <PerformanceProvider>
          <QuickChatView />
        </PerformanceProvider>
      </ThemeProvider>
    )
  }

  // Strict conditional rendering - only one view visible at a time
  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardView key="dashboard" />
      case 'main':
        return <MainChat key="main" />
      case 'heartbeat':
        return <HeartbeatMonitor key="heartbeat" />
      case 'zen':
        return <ZenVoiceMode key="zen" />
      case 'logs':
        return <LogsView key="logs" />
      case 'config':
        return <ConfigView key="config" />
      case 'memory':
        return <MemoryVaultView key="memory" />
      case 'diary':
        return <DiaryView key="diary" />
      case 'api':
        return <ApiDashboardView key="api" />
      case 'trading':
        return <TradingView key="trading" />
      default:
        return <DashboardView key="dashboard" />
    }
  }

  return (
    <ThemeProvider>
      <PerformanceProvider>
        <AutonomyProvider autonomyMode={autonomyMode} setAutonomyMode={setAutonomyMode}>
          <Layout
            currentView={currentView}
            setCurrentView={setCurrentView}
            autonomyMode={autonomyMode}
            setAutonomyMode={setAutonomyMode}
          >
            {renderCurrentView()}
          </Layout>
        </AutonomyProvider>
      </PerformanceProvider>
    </ThemeProvider>
  )
}
