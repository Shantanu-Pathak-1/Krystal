import { Component, ErrorInfo, ReactNode } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.warn('[ErrorBoundary] Caught error:', error.message, info.componentStack)
  }

  reset = () => this.setState({ hasError: false, error: null })

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center justify-center h-full gap-6 p-8"
          style={{
            background: 'radial-gradient(ellipse at center, rgba(239,68,68,0.06) 0%, transparent 70%)',
          }}
        >
          {/* Icon */}
          <motion.div
            animate={{ rotate: [0, -3, 3, -3, 0] }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="p-5 rounded-2xl"
            style={{
              background: 'rgba(239,68,68,0.08)',
              border: '1px solid rgba(239,68,68,0.2)',
            }}
          >
            <AlertTriangle className="w-10 h-10 text-red-400" />
          </motion.div>

          {/* Text */}
          <div className="text-center max-w-sm">
            <h3
              className="text-lg font-bold text-white/80 mb-2"
              style={{ fontFamily: 'Orbitron, monospace' }}
            >
              3D Render Failed
            </h3>
            <p className="text-sm text-white/35 font-mono leading-relaxed">
              The neural avatar module encountered an error. This is usually caused
              by a missing VRM model file or a WebGL context issue.
            </p>
            {this.state.error && (
              <p
                className="mt-3 text-[11px] px-3 py-2 rounded-lg text-red-400/60 font-mono"
                style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.12)' }}
              >
                {this.state.error.message}
              </p>
            )}
          </div>

          {/* Retry */}
          <motion.button
            whileHover={{ scale: 1.04, y: -2 }}
            whileTap={{ scale: 0.96 }}
            onClick={this.reset}
            className="flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all"
            style={{
              background: 'rgba(139,92,246,0.12)',
              border: '1px solid rgba(139,92,246,0.3)',
              color: '#a78bfa',
            }}
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </motion.button>
        </motion.div>
      )
    }

    return this.props.children
  }
}