/**
 * SafeVRMModel.tsx — Clean stable animations only.
 * No gesture system. No body sway. Subtle breathing + blink + lipsync only.
 */

import { useEffect, useRef, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface SafeVRMModelProps {
  url: string
  talkingAmplitude: number
  emotionState?: string
  onLoaded?: () => void
  onError?: (err: Error) => void
}

export default function SafeVRMModel({
  url,
  talkingAmplitude,
  emotionState = 'idle',
  onLoaded,
  onError,
}: SafeVRMModelProps) {
  const vrmRef    = useRef<any>(null)
  const [vrmScene, setVrmScene] = useState<THREE.Object3D | null>(null)
  const [loadError, setLoadError] = useState(false)

  const clockRef     = useRef(new THREE.Clock())
  const blinkTimer   = useRef(0)
  const nextBlink    = useRef(2.5 + Math.random() * 3)
  const blinkElapsed = useRef(0)
  const isBlinking   = useRef(false)
  const lookCur      = useRef(new THREE.Vector2(0, 0))
  const lookTgt      = useRef(new THREE.Vector2(0, 0))

  useEffect(() => {
    const schedule = () => {
      const id = setTimeout(() => {
        lookTgt.current.set(
          (Math.random() - 0.5) * 0.14,
          (Math.random() - 0.5) * 0.07,
        )
        schedule()
      }, 4000 + Math.random() * 4000)
      return id
    }
    const id = schedule()
    return () => clearTimeout(id)
  }, [])

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const { GLTFLoader }                = await import('three/examples/jsm/loaders/GLTFLoader')
        const { VRMLoaderPlugin, VRMUtils } = await import('@pixiv/three-vrm')
        const loader = new (GLTFLoader as any)()
        loader.register((parser: any) => new (VRMLoaderPlugin as any)(parser))
        loader.load(
          url,
          (gltf: any) => {
            if (cancelled) return
            const vrm = gltf.userData.vrm
            if (!vrm) { setLoadError(true); onError?.(new Error('No VRM data')); return }
            try { (VRMUtils as any).removeUnnecessaryJoints(gltf.scene) } catch {}
            try { (VRMUtils as any).rotateVRM0(vrm) } catch {
              try { vrm.scene.rotation.y = Math.PI } catch {}
            }
            // Force upright — remove any X/Z tilt baked in
            try { vrm.scene.rotation.x = 0; vrm.scene.rotation.z = 0 } catch {}
            vrmRef.current = vrm
            setVrmScene(vrm.scene)
            onLoaded?.()
          },
          undefined,
          (err: any) => {
            if (cancelled) return
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

  const getBone = (h: any, name: string): any => {
    try { return h?.getRawBoneNode?.(name) ?? h?.getBoneNode?.(name) ?? null } catch { return null }
  }

  useFrame((_, delta) => {
    const vrm = vrmRef.current
    if (!vrm) return
    try { vrm.update(delta) } catch {}

    const t       = clockRef.current.getElapsedTime()
    const h       = vrm?.humanoid
    const exprMgr = vrm?.expressionManager

    if (h) {
      try {
        /* breathing */
        const breathe = Math.sin(t * 1.1) * 0.007
        const spine = getBone(h, 'spine')
        if (spine) { spine.rotation.x = breathe; spine.rotation.z = 0 }
        const chest = getBone(h, 'chest')
        if (chest) { chest.rotation.x = breathe * 0.4; chest.rotation.z = 0 }
        const hips = getBone(h, 'hips')
        if (hips) { hips.rotation.x = 0; hips.rotation.z = 0; hips.position.y = Math.sin(t * 1.1) * 0.002 }

        /* look drift */
        lookCur.current.x += (lookTgt.current.x - lookCur.current.x) * delta * 1.0
        lookCur.current.y += (lookTgt.current.y - lookCur.current.y) * delta * 1.0

        const neck = getBone(h, 'neck')
        if (neck) {
          neck.rotation.y = lookCur.current.x * 0.45 + Math.sin(t * 0.16) * 0.01
          neck.rotation.x = lookCur.current.y * 0.28
          neck.rotation.z = 0
        }
        const head = getBone(h, 'head')
        if (head) {
          if (talkingAmplitude > 0.1) {
            head.rotation.x = Math.sin(t * 4.5) * talkingAmplitude * 0.025
            head.rotation.y = lookCur.current.x * 0.5
            head.rotation.z = 0
          } else {
            head.rotation.x = lookCur.current.y * 0.35 + Math.sin(t * 0.12) * 0.006
            head.rotation.y = lookCur.current.x * 0.55 + Math.sin(t * 0.2) * 0.014
            head.rotation.z = 0
          }
        }

        /* arms — natural straight hang, NO swinging */
        const lua = getBone(h, 'leftUpperArm')
        if (lua)  { lua.rotation.x = 0.05;  lua.rotation.z =  1.0; lua.rotation.y = 0 }
        const rua = getBone(h, 'rightUpperArm')
        if (rua)  { rua.rotation.x = 0.05;  rua.rotation.z = -1.0; rua.rotation.y = 0 }
        const lla = getBone(h, 'leftLowerArm')
        if (lla)  { lla.rotation.x = 0.03;  lla.rotation.z = 0;    lla.rotation.y = 0 }
        const rla = getBone(h, 'rightLowerArm')
        if (rla)  { rla.rotation.x = 0.03;  rla.rotation.z = 0;    rla.rotation.y = 0 }

        /* legs — dead straight */
        for (const name of ['leftUpperLeg','rightUpperLeg','leftLowerLeg','rightLowerLeg']) {
          const b = getBone(h, name)
          if (b) { b.rotation.x = 0; b.rotation.z = 0; b.rotation.y = 0 }
        }
      } catch {}
    }

    /* lip sync */
    if (exprMgr) {
      try {
        if (talkingAmplitude > 0.08) {
          exprMgr.setValue('aa', Math.min(talkingAmplitude * 1.3, 0.85))
        } else {
          const cur = exprMgr.getValue?.('aa') ?? 0
          exprMgr.setValue('aa', Math.max(0, cur * 0.55))
        }
      } catch {}

      /* blink */
      try {
        blinkTimer.current += delta
        if (blinkTimer.current >= nextBlink.current) {
          blinkTimer.current = 0; nextBlink.current = 3 + Math.random() * 4
          isBlinking.current = true; blinkElapsed.current = 0
        }
        if (isBlinking.current) {
          blinkElapsed.current += delta
          const p = Math.min(blinkElapsed.current / 0.12, 1)
          const v = p < 0.5 ? p * 2 : (1 - p) * 2
          try { exprMgr.setValue('blink', v) } catch {
            try { exprMgr.setValue('blinkLeft', v) } catch {}
            try { exprMgr.setValue('blinkRight', v) } catch {}
          }
          if (p >= 1) {
            isBlinking.current = false
            try { exprMgr.setValue('blink', 0) } catch {
              try { exprMgr.setValue('blinkLeft', 0) } catch {}
              try { exprMgr.setValue('blinkRight', 0) } catch {}
            }
          }
        }
      } catch {}
    }
  })

  if (!vrmScene) {
    return (
      <group>
        <mesh position={[0, 0.85, 0]}>
          <cylinderGeometry args={[0.18, 0.22, 1.1, 16]} />
          <meshStandardMaterial color="#8b5cf6" wireframe />
        </mesh>
        <mesh position={[0, 1.55, 0]}>
          <sphereGeometry args={[0.22, 16, 16]} />
          <meshStandardMaterial color="#22d3ee" wireframe />
        </mesh>
        <mesh position={[0, 0.9, 0]}>
          <sphereGeometry args={[0.1, 8, 8]} />
          <meshStandardMaterial
            color={loadError ? '#ef4444' : '#a78bfa'}
            emissive={loadError ? '#ef4444' : '#a78bfa'}
            emissiveIntensity={3}
          />
        </mesh>
      </group>
    )
  }

  return <primitive object={vrmScene} />
}