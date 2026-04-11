import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import MainChat from './components/MainChat/MainChat'
import HeartbeatMonitor from './components/HeartbeatMonitor/HeartbeatMonitor'
import ZenVoiceMode from './components/ZenVoiceMode/ZenVoiceMode'
import DashboardView from './components/Dashboard/DashboardView'
import LogsView from './components/Logs/LogsView'
import ConfigView from './components/Config/ConfigView'

type ViewMode = 'main' | 'heartbeat' | 'zen' | 'dashboard' | 'logs' | 'config'
type AutonomyMode = 'safe' | 'agentic' | 'god'

export default function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('main')
  const [autonomyMode, setAutonomyMode] = useState<AutonomyMode>('agentic')

  return (
    <Layout
      currentView={currentView}
      setCurrentView={setCurrentView}
      autonomyMode={autonomyMode}
      setAutonomyMode={setAutonomyMode}
    >
      <Routes>
        <Route path="/" element={<DashboardView />} />
        <Route path="/dashboard" element={<DashboardView />} />
        <Route path="/chat" element={<MainChat />} />
        <Route path="/heartbeat" element={<HeartbeatMonitor />} />
        <Route path="/zen" element={<ZenVoiceMode />} />
        <Route path="/logs" element={<LogsView />} />
        <Route path="/config" element={<ConfigView />} />
      </Routes>
    </Layout>
  )
}
