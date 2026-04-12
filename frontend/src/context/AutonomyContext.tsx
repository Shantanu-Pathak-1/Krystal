import { createContext, useContext, ReactNode } from 'react'
import { AutonomyMode } from '../types'

interface AutonomyContextType {
  autonomyMode: AutonomyMode
  setAutonomyMode: (mode: AutonomyMode) => void
}

const AutonomyContext = createContext<AutonomyContextType | undefined>(undefined)

export function AutonomyProvider({
  children,
  autonomyMode,
  setAutonomyMode,
}: {
  children: ReactNode
  autonomyMode: AutonomyMode
  setAutonomyMode: (mode: AutonomyMode) => void
}) {
  return (
    <AutonomyContext.Provider value={{ autonomyMode, setAutonomyMode }}>
      {children}
    </AutonomyContext.Provider>
  )
}

export function useAutonomy() {
  const context = useContext(AutonomyContext)
  if (context === undefined) {
    throw new Error('useAutonomy must be used within an AutonomyProvider')
  }
  return context
}
