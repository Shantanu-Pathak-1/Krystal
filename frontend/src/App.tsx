import { useState } from 'react'
import Layout from './components/Layout/Layout'
import MainChat from './components/MainChat/MainChat'
import HeartbeatMonitor from './components/HeartbeatMonitor/HeartbeatMonitor'
import ZenVoiceMode from './components/ZenVoiceMode/ZenVoiceMode'
import DashboardView from './components/Dashboard/DashboardView'
import LogsView from './components/Logs/LogsView'
import ConfigView from './components/Config/ConfigView'
import MemoryVaultView from './components/MemoryVault/MemoryVaultView'
import DiaryView from './components/Diary/DiaryView'
import SecurityView from './components/Security/SecurityView'
import PluginsLabView from './components/PluginsLab/PluginsLabView'
import ApiDashboardView from './components/ApiDashboard/ApiDashboardView'
import { AutonomyProvider } from './context/AutonomyContext'

type ViewMode = 'main' | 'heartbeat' | 'zen' | 'dashboard' | 'logs' | 'config' | 'memory' | 'diary' | 'security' | 'plugins' | 'api'
type AutonomyMode = 'safe' | 'agentic' | 'god'

export default function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('dashboard')
  const [autonomyMode, setAutonomyMode] = useState<AutonomyMode>('agentic')

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
      case 'security':
        return <SecurityView key="security" />
      case 'plugins':
        return <PluginsLabView key="plugins" />
      case 'api':
        return <ApiDashboardView key="api" />
      default:
        return <DashboardView key="dashboard" />
    }
  }

  return (
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
  )
}
