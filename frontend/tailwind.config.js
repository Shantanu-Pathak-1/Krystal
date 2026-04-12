/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base surfaces — true blacks
        'void': '#000000',
        'void-1': '#050810',
        'void-2': '#080d1a',
        'void-3': '#0d1225',
        'void-4': '#111827',
        // Legacy aliases kept for compatibility
        'krystal-dark': '#080d1a',
        'krystal-darker': '#050810',
        'krystal-blue': '#1e40af',
        'krystal-cyan': '#06b6d4',
        'krystal-purple': '#8b5cf6',
        // Neon accent palette
        'neon': {
          purple:  '#8b5cf6',
          'purple-bright': '#a78bfa',
          'purple-dim':    '#6d28d9',
          cyan:    '#06b6d4',
          'cyan-bright':   '#22d3ee',
          'cyan-dim':      '#0891b2',
          pink:    '#ec4899',
          green:   '#10b981',
          amber:   '#f59e0b',
          red:     '#ef4444',
        },
        // Glass surfaces
        'glass': {
          DEFAULT: 'rgba(255,255,255,0.04)',
          border:  'rgba(255,255,255,0.08)',
          hover:   'rgba(255,255,255,0.07)',
          active:  'rgba(139,92,246,0.15)',
        },
      },
      fontFamily: {
        // Display / headings — futuristic geometric
        display: ['Orbitron', 'monospace'],
        // Body — clean variable
        sans: ['Syne', 'system-ui', 'sans-serif'],
        // Data / code / metrics
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        // Micro-grid overlay (applied as pseudo-element in CSS)
        'grid-pattern': `
          linear-gradient(rgba(139,92,246,0.04) 1px, transparent 1px),
          linear-gradient(90deg, rgba(139,92,246,0.04) 1px, transparent 1px)
        `,
        // Radial glow effects
        'glow-purple': 'radial-gradient(ellipse at center, rgba(139,92,246,0.25) 0%, transparent 70%)',
        'glow-cyan':   'radial-gradient(ellipse at center, rgba(6,182,212,0.20) 0%, transparent 70%)',
        'glow-zen':    'radial-gradient(ellipse at 50% 60%, rgba(6,182,212,0.18) 0%, rgba(139,92,246,0.12) 40%, transparent 70%)',
        // Gradient mesh background
        'mesh-dark': `
          radial-gradient(at 20% 20%, rgba(139,92,246,0.15) 0px, transparent 50%),
          radial-gradient(at 80% 80%, rgba(6,182,212,0.10) 0px, transparent 50%),
          radial-gradient(at 50% 50%, rgba(8,13,26,1) 0px, transparent 100%)
        `,
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
      boxShadow: {
        // Neon glow shadows
        'neon-purple':  '0 0 20px rgba(139,92,246,0.5), 0 0 60px rgba(139,92,246,0.15)',
        'neon-purple-sm': '0 0 10px rgba(139,92,246,0.4)',
        'neon-cyan':    '0 0 20px rgba(6,182,212,0.5), 0 0 60px rgba(6,182,212,0.15)',
        'neon-cyan-sm': '0 0 10px rgba(6,182,212,0.4)',
        'neon-pink':    '0 0 20px rgba(236,72,153,0.5)',
        'neon-green':   '0 0 20px rgba(16,185,129,0.5)',
        'neon-red':     '0 0 20px rgba(239,68,68,0.5)',
        // Glass card shadows
        'glass':        '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)',
        'glass-hover':  '0 16px 48px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.10)',
        'glass-active': '0 8px 32px rgba(139,92,246,0.25), inset 0 1px 0 rgba(139,92,246,0.2)',
        // Inner glows
        'inner-purple': 'inset 0 0 30px rgba(139,92,246,0.1)',
        'inner-cyan':   'inset 0 0 30px rgba(6,182,212,0.1)',
      },
      keyframes: {
        // Breathing pulse for status indicators
        'glow-pulse': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 8px rgba(139,92,246,0.6)' },
          '50%':       { opacity: '0.7', boxShadow: '0 0 20px rgba(139,92,246,0.9)' },
        },
        'glow-pulse-cyan': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 8px rgba(6,182,212,0.6)' },
          '50%':       { opacity: '0.7', boxShadow: '0 0 20px rgba(6,182,212,0.9)' },
        },
        // Scan line sweep
        'scan': {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        // Floating animation for avatar/elements
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
        // Data stream scrolling
        'data-stream': {
          '0%':   { transform: 'translateY(0)', opacity: '1' },
          '100%': { transform: 'translateY(-100%)', opacity: '0' },
        },
        // Shimmer effect for loading states
        'shimmer': {
          '0%':   { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        // Border rotate for active cards
        'border-spin': {
          '0%':   { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        // Waveform bar animation
        'wave-bar': {
          '0%, 100%': { transform: 'scaleY(0.1)' },
          '50%':       { transform: 'scaleY(1)' },
        },
        // Flicker for neon text
        'flicker': {
          '0%, 95%, 100%': { opacity: '1' },
          '96%':            { opacity: '0.8' },
          '97%':            { opacity: '1' },
          '98%':            { opacity: '0.6' },
          '99%':            { opacity: '1' },
        },
      },
      animation: {
        'glow-pulse':      'glow-pulse 2s ease-in-out infinite',
        'glow-pulse-cyan': 'glow-pulse-cyan 2s ease-in-out infinite',
        'scan':            'scan 4s linear infinite',
        'float':           'float 3s ease-in-out infinite',
        'shimmer':         'shimmer 2s linear infinite',
        'border-spin':     'border-spin 4s linear infinite',
        'flicker':         'flicker 4s linear infinite',
        'wave-bar-1':      'wave-bar 0.8s ease-in-out infinite',
        'wave-bar-2':      'wave-bar 0.8s ease-in-out 0.1s infinite',
        'wave-bar-3':      'wave-bar 0.8s ease-in-out 0.2s infinite',
        'wave-bar-4':      'wave-bar 0.8s ease-in-out 0.3s infinite',
        'wave-bar-5':      'wave-bar 0.8s ease-in-out 0.4s infinite',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'sharp':  'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      backdropBlur: {
        'xs': '2px',
        '4xl': '72px',
      },
    },
  },
  plugins: [],
}