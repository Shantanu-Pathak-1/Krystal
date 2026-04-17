import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type PerformanceMode = 'eco' | 'balanced' | 'overdrive' | 'auto';

interface PerformanceContextType {
  mode: PerformanceMode;
  setMode: (mode: PerformanceMode) => void;
  pollingInterval: number;
  enableAnimations: boolean;
  actualMode: 'eco' | 'balanced' | 'overdrive'; // The resolved mode when in 'auto'
}

const PerformanceContext = createContext<PerformanceContextType | undefined>(undefined);

export const PerformanceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<PerformanceMode>('balanced');
  const [actualMode, setActualMode] = useState<'eco' | 'balanced' | 'overdrive'>('balanced');

  const getPollingInterval = () => {
    const targetMode = mode === 'auto' ? actualMode : mode;
    switch (targetMode) {
      case 'eco': return 60000;
      case 'balanced': return 30000;
      case 'overdrive': return 1000;
      default: return 30000;
    }
  };

  const enableAnimations = (mode === 'auto' ? actualMode : mode) !== 'eco';

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (mode === 'auto') {
      const monitorSystem = async () => {
        try {
          const res = await fetch('http://localhost:8000/api/dashboard/stats');
          const stats = await res.json();
          
          // Logic: High CPU/RAM (>80%) -> Eco
          // Low Load (<30%) -> Overdrive
          // Otherwise -> Balanced
          if (stats.cpu_usage > 80 || stats.memory_usage > 80) {
            setActualMode('eco');
          } else if (stats.cpu_usage < 30 && stats.memory_usage < 50) {
            setActualMode('overdrive');
          } else {
            setActualMode('balanced');
          }
        } catch (e) {
          console.error('Performance Monitor failed:', e);
        }
      };

      monitorSystem();
      intervalId = setInterval(monitorSystem, 10000); // Check every 10s
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [mode]);

  useEffect(() => {
    // Notify Electron and Backend of mode change
    const updateSystemMode = async () => {
      const targetMode = mode === 'auto' ? actualMode : mode;
      try {
        // Notify Backend
        await fetch('http://localhost:8000/api/system/mode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: targetMode }),
        });

        // Notify Electron via IPC if available
        if (window.require) {
          const { ipcRenderer } = window.require('electron');
          ipcRenderer.send('change-performance-mode', targetMode);
        }
      } catch (error) {
        console.error('Failed to sync performance mode:', error);
      }
    };

    updateSystemMode();
  }, [mode, actualMode]);

  return (
    <PerformanceContext.Provider value={{ 
      mode, 
      setMode, 
      pollingInterval: getPollingInterval(), 
      enableAnimations,
      actualMode 
    }}>
      {children}
    </PerformanceContext.Provider>
  );
};

export const usePerformance = () => {
  const context = useContext(PerformanceContext);
  if (context === undefined) {
    throw new Error('usePerformance must be used within a PerformanceProvider');
  }
  return context;
};
