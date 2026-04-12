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
  // Direct state update - no React Router navigation
  const handleViewChange = (view: ViewMode) => {
    setCurrentView(view)
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
        <div className="flex-1 h-screen overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  )
}
