/**
 * ZenVoiceMode.tsx — Fixed camera + larger model + better layout
 */

import { useState, useEffect, useRef, useCallback, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Volume2, VolumeX, Sparkles } from 'lucide-react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei'
import { ErrorBoundary } from '../ErrorBoundary/ErrorBoundary'
import { TTSPlayer } from '../../utils/audioProcessor'
import SafeVRMModel from './SafeVRMModel'

const VRM_URL = '/models/shanvika_personal_dress_1.vrm'

type Status = 'idle' | 'listening' | 'processing' | 'speaking' | 'error'

/* ── Waveform bars ─────────────────────────────────────────────────────── */
function AudioVisualizer({ amplitude, active }: { amplitude: number; active: boolean }) {
  const BAR_COUNT = 32
  return (
    <div className="flex items-end justify-center gap-[2px]" style={{ height: 48 }}>
      {Array.from({ length: BAR_COUNT }).map((_, i) => {
        const center = BAR_COUNT / 2
        const distFromCenter = Math.abs(i - center) / center
        const baseH = active ? (1 - distFromCenter * 0.6) * amplitude * 44 : 3
        const jitter = active ? Math.random() * 5 : 0
        const finalH = Math.max(3, baseH + jitter)
        return (
          <motion.div
            key={i}
            animate={{ height: finalH, opacity: active ? 0.7 + (1 - distFromCenter) * 0.3 : 0.2 }}
            transition={{ duration: 0.07, ease: 'linear' }}
            style={{
              width: 3,
              borderRadius: 2,
              background: active ? `linear-gradient(to top, #8b5cf6, #22d3ee)` : 'rgba(255,255,255,0.1)',
              boxShadow: active && finalH > 18 ? '0 0 6px rgba(139,92,246,0.5)' : 'none',
            }}
          />
        )
      })}
    </div>
  )
}

/* ── Status badge ──────────────────────────────────────────────────────── */
const STATUS_META: Record<Status, { label: string; color: string; pulse: boolean }> = {
  idle:       { label: 'STANDBY',    color: 'rgba(255,255,255,0.25)', pulse: false },
  listening:  { label: 'LISTENING',  color: '#ef4444',                pulse: true  },
  processing: { label: 'THINKING',   color: '#f59e0b',                pulse: true  },
  speaking:   { label: 'SPEAKING',   color: '#10b981',                pulse: true  },
  error:      { label: 'ERROR',      color: '#ef4444',                pulse: false },
}

function StatusBadge({ status }: { status: Status }) {
  const meta = STATUS_META[status]
  return (
    <div
      className="flex items-center gap-2 px-4 py-2 rounded-full"
      style={{ background: `${meta.color}15`, border: `1px solid ${meta.color}40` }}
    >
      <motion.div
        className="w-2 h-2 rounded-full"
        animate={meta.pulse ? { opacity: [1, 0.2, 1] } : { opacity: 1 }}
        transition={{ duration: 1.2, repeat: Infinity }}
        style={{ background: meta.color, boxShadow: `0 0 8px ${meta.color}` }}
      />
      <span
        className="text-xs font-bold tracking-[0.3em]"
        style={{ color: meta.color, fontFamily: 'JetBrains Mono, monospace' }}
      >
        {meta.label}
      </span>
    </div>
  )
}

/* ── Studio Lights ─────────────────────────────────────────────────────── */
function StudioLights() {
  return (
    <>
      <ambientLight intensity={0.55} color="#1a1535" />
      {/* Key light — left front, warm purple */}
      <spotLight
        position={[-2.5, 4, 3.5]}
        intensity={3.5}
        angle={0.38}
        penumbra={0.9}
        color="#b07ef8"
        castShadow
      />
      {/* Fill light — right, cool cyan */}
      <spotLight
        position={[3, 3.5, 2.5]}
        intensity={1.8}
        angle={0.5}
        penumbra={1}
        color="#06b6d4"
      />
      {/* Rim / hair light — behind top */}
      <spotLight
        position={[0, 5, -3]}
        intensity={2.2}
        angle={0.4}
        penumbra={0.8}
        color="#e0aaff"
      />
      {/* Ground bounce */}
      <directionalLight position={[0, -1, 2]} intensity={0.3} color="#4c1d95" />
      <hemisphereLight args={['#1a0a3e', '#000010', 0.4]} />
    </>
  )
}

/* ── Avatar loading fallback (renders inside Canvas) ───────────────────── */
function AvatarLoadingMesh() {
  return (
    <group>
      <mesh position={[0, 0.9, 0]}>
        <capsuleGeometry args={[0.2, 1.0, 8, 16]} />
        <meshStandardMaterial color="#8b5cf6" wireframe opacity={0.4} transparent />
      </mesh>
      <mesh position={[0, 1.65, 0]}>
        <sphereGeometry args={[0.23, 16, 16]} />
        <meshStandardMaterial color="#22d3ee" wireframe opacity={0.4} transparent />
      </mesh>
      <mesh position={[0, 1.0, 0]}>
        <sphereGeometry args={[0.1, 8, 8]} />
        <meshStandardMaterial color="#a78bfa" emissive="#a78bfa" emissiveIntensity={4} />
      </mesh>
    </group>
  )
}

/* ── Canvas loading overlay ──────────────────────────────────────────────── */
function CanvasLoadingOverlay() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10">
      <div className="relative">
        <motion.div
          className="w-20 h-20 rounded-full"
          style={{ border: '2px solid transparent', borderTopColor: '#8b5cf6', borderRightColor: 'rgba(139,92,246,0.3)' }}
          animate={{ rotate: 360 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          className="absolute inset-2 rounded-full"
          style={{ border: '2px solid transparent', borderTopColor: '#22d3ee', borderLeftColor: 'rgba(34,211,238,0.3)' }}
          animate={{ rotate: -360 }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            className="w-2 h-2 rounded-full bg-purple-400"
            animate={{ scale: [1, 1.6, 1], opacity: [1, 0.4, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
        </div>
      </div>
      <motion.p
        animate={{ opacity: [0, 1, 0.6, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
        className="mt-5 text-xs tracking-[0.25em] uppercase font-mono"
        style={{ color: 'rgba(167,139,250,0.6)' }}
      >
        Loading Neural Avatar…
      </motion.p>
      <motion.div
        className="mt-4 h-px w-32"
        style={{ background: 'linear-gradient(90deg, transparent, #8b5cf6, transparent)' }}
        animate={{ scaleX: [0, 1, 0], opacity: [0, 1, 0] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
      />
    </div>
  )
}

/* ── 3D Scene ───────────────────────────────────────────────────────────── */
function ThreeDScene({ talkingAmplitude, emotionState }: { talkingAmplitude: number; emotionState: string }) {
  return (
    <Canvas
      shadows
      camera={{
        // Camera at mid-height, pulled back enough to see full body
        position: [0, 1.0, 3.2],
        fov: 58,
        near: 0.05,
        far: 100,
      }}
      style={{ width: '100%', height: '100%', background: 'transparent' }}
      gl={{ alpha: true, antialias: true }}
    >
      <StudioLights />

      {/* scale=1.7 — full body fits, slightly above center */}
      <group position={[0, -0.1, 0]} scale={[1.7, 1.7, 1.7]}>
        <Suspense fallback={<AvatarLoadingMesh />}>
          <SafeVRMModel
            url={VRM_URL}
            talkingAmplitude={talkingAmplitude}
            emotionState={emotionState}
          />
        </Suspense>
      </group>

      <ContactShadows
        position={[0, -0.1, 0]}
        opacity={0.5}
        scale={5}
        blur={2}
        far={3}
        color="#3b0764"
      />
      <Environment preset="night" />

      {/* Camera FULLY LOCKED -- no accidental drag/zoom/pan */}
      <OrbitControls
        enabled={false}
        enableRotate={false}
        enableZoom={false}
        enablePan={false}
      />
    </Canvas>
  )
}

/* ── Canvas Fallback ────────────────────────────────────────────────────── */
function CanvasFallback() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center">
      <div className="relative w-48 h-64">
        <motion.div
          className="absolute inset-0 rounded-t-[50%] rounded-b-[20%]"
          style={{
            background: 'linear-gradient(180deg, rgba(139,92,246,0.08) 0%, rgba(6,182,212,0.05) 100%)',
            border: '1px solid rgba(139,92,246,0.2)',
          }}
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        />
        {Array.from({ length: 8 }).map((_, i) => (
          <motion.div
            key={i}
            className="absolute left-0 right-0 h-px"
            style={{ top: `${12 + i * 11}%`, background: `rgba(139,92,246,${0.04 + i * 0.01})` }}
            animate={{ opacity: [0.3, 0.8, 0.3], scaleX: [0.7, 1, 0.7] }}
            transition={{ duration: 2.5, delay: i * 0.3, repeat: Infinity }}
          />
        ))}
        <motion.div
          className="absolute inset-x-0 h-8"
          style={{ background: 'linear-gradient(180deg, transparent, rgba(139,92,246,0.12), transparent)' }}
          animate={{ top: ['0%', '90%', '0%'] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
      <p className="mt-4 text-xs text-white/30 font-mono tracking-widest">
        3D renderer offline — place VRM at /public/models/
      </p>
    </div>
  )
}

/* ── Main component ────────────────────────────────────────────────────── */
export default function ZenVoiceMode() {
  const [status, setStatus] = useState<Status>('idle')
  const [userSpeech, setUserSpeech] = useState('')
  const [krystalResponse, setKrystalResponse] = useState('')
  const [talkingAmplitude, setTalkingAmplitude] = useState(0)
  const [muted, setMuted] = useState(false)
  const [canvasReady, setCanvasReady] = useState(false)
  const [emotionState, setEmotionState] = useState('idle')

  const ttsPlayer = useRef(new TTSPlayer())

  useEffect(() => {
    const t = setTimeout(() => setCanvasReady(true), 100)
    return () => clearTimeout(t)
  }, [])

  useEffect(() => () => { ttsPlayer.current?.stop() }, [])

  // Sync emotion to status
  useEffect(() => {
    if (status === 'listening') setEmotionState('listening')
    else if (status === 'processing') setEmotionState('thinking')
    else if (status === 'speaking') setEmotionState('speaking')
    else setEmotionState('idle')
  }, [status])

  const speakResponse = useCallback(async (text: string) => {
    if (muted) { setStatus('idle'); return }
    setStatus('speaking')
    try {
      await ttsPlayer.current.playTextWithLipSync(text, (amp) => setTalkingAmplitude(amp))
    } catch {
      simulateSpeech(text)
    } finally {
      setStatus('idle')
      setTalkingAmplitude(0)
    }
  }, [muted])

  const simulateSpeech = useCallback((text: string) => {
    const words = text.split(' ')
    let i = 0
    const next = () => {
      if (i >= words.length) { setTalkingAmplitude(0); setStatus('idle'); return }
      const wordLen = words[i].length
      const iv = setInterval(() => setTalkingAmplitude(0.3 + Math.random() * 0.7), 50)
      setTimeout(() => { clearInterval(iv); setTalkingAmplitude(0); i++; setTimeout(next, 150) }, wordLen * 120)
    }
    setStatus('speaking')
    next()
  }, [])

  const toggle = useCallback(async () => {
    if (status === 'listening') {
      setStatus('processing')
      await new Promise(r => setTimeout(r, 1800))
      const response = "I'm fully online and ready. My neural systems are synchronized. How can I assist you today?"
      setKrystalResponse(response)
      await speakResponse(response)
    } else if (status === 'idle' || status === 'error') {
      setStatus('listening')
      setUserSpeech('')
      setKrystalResponse('')
      setTimeout(() => setUserSpeech('Hey Krystal, are you there?'), 2500)
    }
  }, [status, speakResponse])

  const isInteractable = status === 'idle' || status === 'listening' || status === 'error'
  const waveActive = status === 'listening' || status === 'speaking'

  return (
    <div
      className="relative flex h-full overflow-hidden"
      style={{ background: 'radial-gradient(ellipse at 50% 35%, #0e0824 0%, #030510 55%, #000005 100%)' }}
    >
      {/* Ambient glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px]"
          style={{ background: 'radial-gradient(ellipse, rgba(139,92,246,0.07) 0%, transparent 65%)', filter: 'blur(70px)' }}
        />
        <div
          className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px]"
          style={{ background: 'radial-gradient(ellipse, rgba(6,182,212,0.09) 0%, transparent 70%)', filter: 'blur(55px)' }}
        />
        {/* Floor glow */}
        <div
          className="absolute bottom-0 left-1/4 right-1/4 h-24"
          style={{ background: 'radial-gradient(ellipse, rgba(139,92,246,0.12) 0%, transparent 80%)', filter: 'blur(30px)' }}
        />
      </div>

      {/* ── 3D Canvas ────────────────────────────────────────────────────── */}
      <div className="flex-1 relative" style={{ minHeight: 0 }}>
        <AnimatePresence>
          {!canvasReady && <CanvasLoadingOverlay />}
        </AnimatePresence>

        <ErrorBoundary fallback={<CanvasFallback />}>
          <ThreeDScene talkingAmplitude={talkingAmplitude} emotionState={emotionState} />
        </ErrorBoundary>

        {/* ── Bottom HUD — raised higher so it doesn't clip model ── */}
        <div className="absolute bottom-0 left-0 right-0 pb-6 flex flex-col items-center gap-4">

          {/* Transcript bubbles */}
          <AnimatePresence>
            {userSpeech && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="px-4 py-2 rounded-xl max-w-xs text-center"
                style={{ background: 'rgba(139,92,246,0.12)', border: '1px solid rgba(139,92,246,0.25)', backdropFilter: 'blur(12px)' }}
              >
                <p className="text-xs text-purple-300/80 font-mono">"{userSpeech}"</p>
              </motion.div>
            )}
            {krystalResponse && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="px-4 py-2 rounded-xl max-w-sm text-center"
                style={{ background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)', backdropFilter: 'blur(12px)' }}
              >
                <p className="text-xs text-cyan-300/70 font-mono">"{krystalResponse}"</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Waveform */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="w-72 px-4 py-3 rounded-2xl"
            style={{
              background: 'rgba(4,5,18,0.75)',
              border: '1px solid rgba(255,255,255,0.07)',
              backdropFilter: 'blur(18px)',
            }}
          >
            <AudioVisualizer amplitude={talkingAmplitude} active={waveActive} />
          </motion.div>

          {/* Control bar */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex items-center gap-4"
          >
            <StatusBadge status={status} />

            {/* Mic button */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.93 }}
              onClick={toggle}
              disabled={!isInteractable}
              className="relative w-16 h-16 rounded-full flex items-center justify-center"
              style={{
                background: status === 'listening'
                  ? 'linear-gradient(135deg, #dc2626, #991b1b)'
                  : 'linear-gradient(135deg, rgba(139,92,246,0.9), rgba(109,40,217,0.9))',
                border: `2px solid ${status === 'listening' ? 'rgba(239,68,68,0.5)' : 'rgba(139,92,246,0.5)'}`,
                boxShadow: status === 'listening'
                  ? '0 0 30px rgba(239,68,68,0.5), 0 0 60px rgba(239,68,68,0.2)'
                  : '0 0 30px rgba(139,92,246,0.5), 0 0 60px rgba(139,92,246,0.2)',
                opacity: isInteractable ? 1 : 0.5,
              }}
            >
              {status === 'listening' && (
                <motion.div
                  className="absolute inset-0 rounded-full"
                  style={{ border: '2px solid rgba(239,68,68,0.4)' }}
                  animate={{ scale: [1, 1.5, 1.5], opacity: [0.8, 0, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
              {status === 'processing' && (
                <motion.div
                  className="absolute inset-0 rounded-full"
                  style={{ border: '2px solid rgba(245,158,11,0.5)' }}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                />
              )}
              {status === 'listening'
                ? <MicOff className="w-6 h-6 text-white" />
                : <Mic className="w-6 h-6 text-white" />
              }
            </motion.button>

            {/* Mute */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setMuted(m => !m)}
              className="w-10 h-10 rounded-full flex items-center justify-center"
              style={{
                background: muted ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.05)',
                border: `1px solid ${muted ? 'rgba(239,68,68,0.35)' : 'rgba(255,255,255,0.1)'}`,
                backdropFilter: 'blur(10px)',
              }}
            >
              {muted ? <VolumeX className="w-4 h-4 text-red-400" /> : <Volume2 className="w-4 h-4 text-white/50" />}
            </motion.button>
          </motion.div>
        </div>
      </div>

      {/* ── Side info panel ──────────────────────────────────────────────── */}
      <motion.aside
        initial={{ x: 320, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 260, damping: 28 }}
        className="w-72 flex flex-col p-5 gap-4 overflow-y-auto"
        style={{
          background: 'rgba(3,5,15,0.88)',
          backdropFilter: 'blur(20px)',
          borderLeft: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div className="flex items-center gap-2 pt-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <h3
            className="text-[11px] font-bold tracking-[0.35em] uppercase text-white/30"
            style={{ fontFamily: 'Orbitron, monospace' }}
          >
            Zen Mode
          </h3>
        </div>

        {([
          ['Voice Input',  status === 'listening',         '#ef4444'],
          ['Processing',   status === 'processing',        '#f59e0b'],
          ['Lip Sync',     talkingAmplitude > 0.05,       '#8b5cf6'],
          ['TTS Output',   status === 'speaking',          '#10b981'],
        ] as const).map(([label, active, color]) => (
          <div
            key={label}
            className="flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300"
            style={{
              background: active ? `${color}10` : 'rgba(255,255,255,0.025)',
              border: `1px solid ${active ? `${color}25` : 'rgba(255,255,255,0.05)'}`,
            }}
          >
            <span className="text-xs font-semibold text-white/50">{label}</span>
            <motion.div
              className="w-2 h-2 rounded-full"
              animate={active ? { opacity: [1, 0.2, 1] } : { opacity: 0.2 }}
              transition={{ duration: 1.2, repeat: Infinity }}
              style={{
                background: active ? color : 'rgba(255,255,255,0.2)',
                boxShadow: active ? `0 0 8px ${color}` : 'none',
              }}
            />
          </div>
        ))}

        {/* Amplitude meter */}
        <div
          className="px-4 py-4 rounded-xl"
          style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}
        >
          <p className="text-[10px] text-white/25 tracking-widest uppercase font-mono mb-3">Amplitude</p>
          <div className="flex items-end justify-center gap-0.5" style={{ height: 40 }}>
            {Array.from({ length: 16 }).map((_, i) => (
              <motion.div
                key={i}
                animate={{
                  height: talkingAmplitude > 0.05 ? `${Math.random() * talkingAmplitude * 100}%` : '6%',
                }}
                transition={{ duration: 0.06 }}
                className="flex-1 rounded-sm"
                style={{
                  background: talkingAmplitude > 0.05
                    ? 'linear-gradient(to top, #8b5cf6, #22d3ee)'
                    : 'rgba(255,255,255,0.06)',
                }}
              />
            ))}
          </div>
        </div>

        {/* Emotion state */}
        <div
          className="px-4 py-3 rounded-xl"
          style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}
        >
          <p className="text-[10px] text-white/25 tracking-widest uppercase font-mono mb-2">Emotion State</p>
          <div className="flex items-center gap-2">
            <motion.div
              className="w-2 h-2 rounded-full"
              animate={{ scale: [1, 1.3, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                background: emotionState === 'speaking' ? '#10b981' :
                  emotionState === 'listening' ? '#ef4444' :
                  emotionState === 'thinking' ? '#f59e0b' : '#8b5cf6',
              }}
            />
            <span className="text-sm font-mono text-white/60 capitalize">{emotionState}</span>
          </div>
        </div>

        {/* Voice commands */}
        <div className="mt-1">
          <p className="text-[10px] text-white/25 tracking-widest uppercase font-mono mb-3">Voice Commands</p>
          <div className="space-y-2">
            {[
              ['"Hey Krystal"', 'Wake word'],
              ['"Stop"',        'End response'],
              ['"Repeat"',      'Say again'],
              ['"Clear"',       'Reset context'],
            ].map(([cmd, desc]) => (
              <div key={cmd} className="flex items-center justify-between">
                <span
                  className="text-[11px] font-mono px-2 py-1 rounded-md"
                  style={{ background: 'rgba(139,92,246,0.1)', color: '#a78bfa' }}
                >
                  {cmd}
                </span>
                <span className="text-[10px] text-white/25">{desc}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-auto pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <p className="text-[10px] text-white/20 tracking-widest uppercase font-mono mb-2">3D Controls</p>
          <div className="space-y-1.5 text-[10px] text-white/25 font-mono">
            <p>Drag → Rotate camera</p>
            <p>Scroll → Zoom in/out</p>
            <p>Right-drag → Pan view</p>
          </div>
        </div>
      </motion.aside>
    </div>
  )
}