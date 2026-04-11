import React, { useEffect, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { VRMLoaderPlugin } from '@pixiv/three-vrm';

export function VRMModel({ url, talkingAmplitude }: { url: string; talkingAmplitude: number }) {
  const [vrm, setVrm] = useState<any>(null);

  useEffect(() => {
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));
    
    loader.load(url, (gltf) => {
      const loadedVrm = gltf.userData.vrm;
      // Rotate model to face camera if needed: loadedVrm.scene.rotation.y = Math.PI;
      setVrm(loadedVrm);
    });
  }, [url]);

  useFrame((state, delta) => {
    if (vrm) {
      vrm.update(delta); // Updates physics
      
      // Basic Lip Sync Logic (will map to actual audio later)
      if (talkingAmplitude > 0.1) {
        vrm.expressionManager.setValue('aa', Math.min(talkingAmplitude * 2, 1.0));
      } else {
        vrm.expressionManager.setValue('aa', 0);
      }
    }
  });

  return vrm ? <primitive object={vrm.scene} /> : null;
}
