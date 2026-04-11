import { useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopNavigation from './TopNavigation'
import { ViewMode, AutonomyMode } from '../../types'

interface LayoutProps {
  children: React.ReactNode
  currentView: ViewMode
  setCurrentView: (view: ViewMode) => void
  autonomyMode: AutonomyMode
  setAutonomyMode: (mode: AutonomyMode) => void
}

export default function Layout({
  children,
  currentView,
  setCurrentView,
  autonomyMode,
  setAutonomyMode,
}: LayoutProps) {
  const navigate = useNavigate()

  const handleViewChange = (view: ViewMode) => {
    setCurrentView(view)
    switch (view) {
      case 'dashboard':
        navigate('/dashboard')
        break
      case 'main':
        navigate('/chat')
        break
      case 'heartbeat':
        navigate('/heartbeat')
        break
      case 'zen':
        navigate('/zen')
        break
      case 'logs':
        navigate('/logs')
        break
      case 'config':
        navigate('/config')
        break
    }
  }

  return (
    <div className="flex h-screen bg-krystal-darker">
      {/* Sidebar */}
      <Sidebar currentView={currentView} onViewChange={handleViewChange} />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Navigation */}
        <TopNavigation
          currentView={currentView}
          onViewChange={handleViewChange}
          autonomyMode={autonomyMode}
          setAutonomyMode={setAutonomyMode}
        />
        
        {/* Dynamic Content Area */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  )
}
