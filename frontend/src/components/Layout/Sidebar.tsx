import { MessageSquare, Brain, Heart, Shield, Database, Book, Users, LayoutDashboard, Terminal, Settings } from 'lucide-react'
import { ViewMode } from '../../types'

interface SidebarProps {
  currentView: ViewMode
  onViewChange: (view: ViewMode) => void
}

export default function Sidebar({ currentView, onViewChange }: SidebarProps) {
  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      view: 'dashboard' as ViewMode,
    },
    {
      id: 'main',
      label: 'Chat',
      icon: MessageSquare,
      view: 'main' as ViewMode,
    },
    {
      id: 'heartbeat',
      label: 'Heartbeat',
      icon: Heart,
      view: 'heartbeat' as ViewMode,
    },
    {
      id: 'zen',
      label: 'Zen Voice',
      icon: Brain,
      view: 'zen' as ViewMode,
    },
    {
      id: 'logs',
      label: 'Logs',
      icon: Terminal,
      view: 'logs' as ViewMode,
    },
    {
      id: 'config',
      label: 'Config',
      icon: Settings,
      view: 'config' as ViewMode,
    },
  ]

  const secondaryItems = [
    { id: 'memory', label: 'Memory Vault', icon: Database },
    { id: 'diary', label: "Krystal's Diary", icon: Book },
    { id: 'social', label: 'Social & Guard', icon: Users },
    { id: 'security', label: 'Security', icon: Shield },
  ]

  return (
    <div className="w-64 bg-krystal-dark border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-krystal-purple rounded-lg flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">Krystal AI</h1>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.view
            
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.view)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-krystal-purple text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            )
          })}
        </div>

        {/* Divider */}
        <div className="my-6 border-t border-gray-800"></div>

        {/* Secondary Navigation */}
        <div className="space-y-2">
          {secondaryItems.map((item) => {
            const Icon = item.icon
            
            return (
              <button
                key={item.id}
                className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            )
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-500">
          <div className="flex items-center justify-between">
            <span>Status</span>
            <span className="text-green-400">Online</span>
          </div>
        </div>
      </div>
    </div>
  )
}
