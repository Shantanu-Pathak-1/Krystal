import { useState } from 'react'
import { ChevronDown, RefreshCw, Camera, Shield, Mic } from 'lucide-react'
import { ViewMode, AutonomyMode } from '../../types'

interface TopNavigationProps {
  currentView: ViewMode
  onViewChange: (view: ViewMode) => void
  autonomyMode: AutonomyMode
  setAutonomyMode: (mode: AutonomyMode) => void
}

export default function TopNavigation({
  currentView,
  onViewChange,
  autonomyMode,
  setAutonomyMode,
}: TopNavigationProps) {
  const [viewDropdownOpen, setViewDropdownOpen] = useState(false)
  const [autonomyDropdownOpen, setAutonomyDropdownOpen] = useState(false)

  const viewOptions = [
    { value: 'main', label: 'Main Chat' },
    { value: 'heartbeat', label: 'Heartbeat Monitor' },
    { value: 'zen', label: 'Zen Voice Mode' },
  ]

  const autonomyOptions = [
    { value: 'safe', label: 'Safe Mode', description: 'Chat only' },
    { value: 'agentic', label: 'Agentic', description: 'Default tool use' },
    { value: 'god', label: 'God Mode', description: 'Full OS Trinetra access' },
  ]

  const getAutonomyColor = (mode: AutonomyMode) => {
    switch (mode) {
      case 'safe':
        return 'text-green-400 border-green-400'
      case 'agentic':
        return 'text-yellow-400 border-yellow-400'
      case 'god':
        return 'text-red-400 border-red-400'
    }
  }

  return (
    <div className="h-16 bg-krystal-dark border-b border-gray-800 flex items-center justify-between px-6">
      {/* Left Side - View Dropdown */}
      <div className="flex items-center space-x-4">
        <div className="relative">
          <button
            onClick={() => setViewDropdownOpen(!viewDropdownOpen)}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <span className="text-white">
              {viewOptions.find(opt => opt.value === currentView)?.label}
            </span>
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </button>

          {viewDropdownOpen && (
            <div className="absolute top-full left-0 mt-2 w-48 bg-krystal-dark border border-gray-800 rounded-lg shadow-lg z-10">
              {viewOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => {
                    onViewChange(option.value as ViewMode)
                    setViewDropdownOpen(false)
                  }}
                  className={`w-full text-left px-4 py-2 hover:bg-gray-800 transition-colors ${
                    currentView === option.value ? 'bg-krystal-purple text-white' : 'text-gray-300'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Side - Autonomy Dropdown and Action Icons */}
      <div className="flex items-center space-x-4">
        {/* Autonomy Dropdown */}
        <div className="relative">
          <button
            onClick={() => setAutonomyDropdownOpen(!autonomyDropdownOpen)}
            className={`flex items-center space-x-2 px-4 py-2 border rounded-lg transition-colors ${getAutonomyColor(autonomyMode)}`}
          >
            <span>
              {autonomyOptions.find(opt => opt.value === autonomyMode)?.label}
            </span>
            <ChevronDown className="w-4 h-4" />
          </button>

          {autonomyDropdownOpen && (
            <div className="absolute top-full right-0 mt-2 w-56 bg-krystal-dark border border-gray-800 rounded-lg shadow-lg z-10">
              {autonomyOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => {
                    setAutonomyMode(option.value as AutonomyMode)
                    setAutonomyDropdownOpen(false)
                  }}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-800 transition-colors ${
                    autonomyMode === option.value ? 'bg-krystal-purple text-white' : 'text-gray-300'
                  }`}
                >
                  <div className="font-medium">{option.label}</div>
                  <div className="text-xs text-gray-400">{option.description}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Action Icons */}
        <div className="flex items-center space-x-2">
          <button
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            title="Clear Context"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          
          <button
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            title="Webcam"
          >
            <Camera className="w-5 h-5" />
          </button>
          
          <button
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            title="Security Status"
          >
            <Shield className="w-5 h-5" />
          </button>

          {currentView === 'main' && (
            <button
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              title="Voice Input"
            >
              <Mic className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
