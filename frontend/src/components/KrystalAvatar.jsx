import { useEffect, useRef } from 'react'
import { useFrame, useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { VRM, VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm'

function KrystalAvatar({ vrmUrl = '/models/krystal.vrm', onLoad = () => {} }) {
  const vrmRef = useRef(null)
  const mixerRef = useRef(null)

  // Load VRM
  const gltf = useLoader(GLTFLoader, vrmUrl, (loader) => {
    loader.register((parser) => new VRMLoaderPlugin(parser))
  })

  useEffect(() => {
    if (gltf) {
      VRMUtils.removeUnnecessaryJoints(gltf.scene)
      const vrm = gltf.userData.vrm
      vrmRef.current = vrm
      VRMUtils.rotateVRM(vrm)
      onLoad(vrm)
      
      // Setup animation mixer
      mixerRef.current = new THREE.AnimationMixer(vrm.scene)
    }
  }, [gltf, onLoad])

  useFrame((state, delta) => {
    if (mixerRef.current) {
      mixerRef.current.update(delta)
    }
  })

  return (
    <primitive 
      object={gltf?.scene} 
      scale={2.5}
      position={[0, -1.2, 0]}
    />
  )
}

// Default export
export default KrystalAvatar

// Named export for ZenVoiceMode (YEH LINE ADD KARI HAI)
export const VRMModel = KrystalAvatar