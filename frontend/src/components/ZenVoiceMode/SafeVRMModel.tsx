/**
 * SafeVRMModel.tsx
 *
 * Root fix: VRM scene stored in state → rendered via <primitive object={vrm.scene} />
 * This avoids the groupRef re-render bug where the scene was added to a stale ref.
 */

import { useEffect, useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface SafeVRMModelProps {
  url: string
  talkingAmplitude: number
  onLoaded?: () => void
  onError?: (err: Error) => void
}

export default function SafeVRMModel({
  url,
  talkingAmplitude,
  onLoaded,
  onError,
}: SafeVRMModelProps) {
  const vrmRef = useRef<any>(null)
  const [vrmScene, setVrmScene] = useState<THREE.Object3D | null>(null)
  const [loadError, setLoadError] = useState(false)
  const clockRef = useRef(new THREE.Clock())
  const blinkTimerRef = useRef(0)
  const nextBlinkRef = useRef(2 + Math.random() * 3)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const { GLTFLoader } = await import('three/examples/jsm/loaders/GLTFLoader')
        const { VRMLoaderPlugin, VRMUtils } = await import('@pixiv/three-vrm')

        const loader = new (GLTFLoader as any)()
        loader.register((parser: any) => new (VRMLoaderPlugin as any)(parser))

        loader.load(
          url,
          (gltf: any) => {
            if (cancelled) return
            const vrm = gltf.userData.vrm
            if (!vrm) {
              setLoadError(true)
              onError?.(new Error('No VRM data in file'))
              return
            }
            // Face camera
            try { (VRMUtils as any).removeUnnecessaryJoints(gltf.scene) } catch {}
            try { (VRMUtils as any).rotateVRM0(vrm) } catch {
              try { vrm.scene.rotation.y = Math.PI } catch {}
            }

            vrmRef.current = vrm
            setVrmScene(vrm.scene)   // ← store scene in state, primitive renders it
            onLoaded?.()
          },
          undefined,
          (err: any) => {
            if (cancelled) return
            console.warn('[SafeVRMModel]', err)
            setLoadError(true)
            onError?.(new Error(String(err?.message ?? 'Load failed')))
          }
        )
      } catch (err: any) {
        if (cancelled) return
        setLoadError(true)
        onError?.(err instanceof Error ? err : new Error(String(err)))
      }
    }

    load()
    return () => { cancelled = true }
  }, [url])

  // Animation loop
  useFrame((_, delta) => {
    if (!vrmRef.current) return

    try { vrmRef.current.update(delta) } catch {}

    const t = clockRef.current.getElapsedTime()
    const humanoid = vrmRef.current?.humanoid
    const expressionManager = vrmRef.current?.expressionManager

    const getBone = (name: string) => {
      try {
        return humanoid?.getRawBoneNode?.(name) ?? humanoid?.getBoneNode?.(name) ?? null
      } catch { return null }
    }

    // ── Idle breathing + body sway ────────────────────────────────────
    if (humanoid) {
      try {
        const breathe = Math.sin(t * 1.15) * 0.013

        const spine = getBone('spine')
        if (spine) spine.rotation.x = breathe

        const chest = getBone('chest')
        if (chest) {
          chest.rotation.x = breathe * 0.5
          chest.rotation.z = Math.sin(t * 0.38) * 0.004
        }

        const hips = getBone('hips')
        if (hips) {
          hips.rotation.z = Math.sin(t * 0.45) * 0.005
          hips.position.y = Math.sin(t * 1.15) * 0.003
        }

        const neck = getBone('neck')
        if (neck) neck.rotation.y = Math.sin(t * 0.25) * 0.02

        const head = getBone('head')
        if (head) {
          if (talkingAmplitude > 0.1) {
            head.rotation.x = Math.sin(t * 7) * talkingAmplitude * 0.05
            head.rotation.y = Math.sin(t * 2.5) * 0.035
          } else {
            head.rotation.y = Math.sin(t * 0.28) * 0.055
            head.rotation.x = Math.sin(t * 0.18) * 0.018
          }
        }

        const leftUpperArm = getBone('leftUpperArm')
        if (leftUpperArm) {
          leftUpperArm.rotation.z = 1.05 + Math.sin(t * 0.75) * 0.022
          leftUpperArm.rotation.x = Math.sin(t * 0.5) * 0.018
        }

        const rightUpperArm = getBone('rightUpperArm')
        if (rightUpperArm) {
          rightUpperArm.rotation.z = -(1.05 + Math.sin(t * 0.75 + Math.PI) * 0.022)
          rightUpperArm.rotation.x = Math.sin(t * 0.5 + 0.6) * 0.018
        }
      } catch {}
    }

    // ── Lip sync ─────────────────────────────────────────────────────
    if (expressionManager) {
      try {
        if (talkingAmplitude > 0.08) {
          expressionManager.setValue('aa', Math.min(talkingAmplitude * 1.7, 1.0))
        } else {
          const cur = expressionManager.getValue?.('aa') ?? 0
          expressionManager.setValue('aa', Math.max(0, cur * 0.7))
        }
      } catch {}

      // ── Auto blink ───────────────────────────────────────────────
      try {
        blinkTimerRef.current += delta
        if (blinkTimerRef.current >= nextBlinkRef.current) {
          blinkTimerRef.current = 0
          nextBlinkRef.current = 2.5 + Math.random() * 4
          ;(vrmRef.current as any).__blinkElapsed = 0
          ;(vrmRef.current as any).__blinking = true
        }
        if ((vrmRef.current as any).__blinking) {
          const BLINK_DUR = 0.14
          ;(vrmRef.current as any).__blinkElapsed += delta
          const p = Math.min((vrmRef.current as any).__blinkElapsed / BLINK_DUR, 1)
          const v = p < 0.5 ? p * 2 : (1 - p) * 2
          try { expressionManager.setValue('blink', v) } catch {
            try { expressionManager.setValue('blinkLeft', v) } catch {}
            try { expressionManager.setValue('blinkRight', v) } catch {}
          }
          if (p >= 1) {
            ;(vrmRef.current as any).__blinking = false
            try { expressionManager.setValue('blink', 0) } catch {
              try { expressionManager.setValue('blinkLeft', 0) } catch {}
              try { expressionManager.setValue('blinkRight', 0) } catch {}
            }
          }
        }
      } catch {}
    }
  })

  // ── Placeholder (loading or error) ───────────────────────────────
  if (!vrmScene) {
    return (
      <group>
        {/* Body */}
        <mesh position={[0, 0.8, 0]}>
          <cylinderGeometry args={[0.18, 0.22, 1.1, 16]} />
          <meshStandardMaterial color="#8b5cf6" wireframe />
        </mesh>
        {/* Head */}
        <mesh position={[0, 1.55, 0]}>
          <sphereGeometry args={[0.22, 16, 16]} />
          <meshStandardMaterial color="#22d3ee" wireframe />
        </mesh>
        {/* Glowing core */}
        <mesh position={[0, 0.9, 0]}>
          <sphereGeometry args={[0.12, 8, 8]} />
          <meshStandardMaterial
            color={loadError ? '#ef4444' : '#a78bfa'}
            emissive={loadError ? '#ef4444' : '#a78bfa'}
            emissiveIntensity={3}
          />
        </mesh>
      </group>
    )
  }

  // ── Actual VRM model ─────────────────────────────────────────────
  return <primitive object={vrmScene} />
}