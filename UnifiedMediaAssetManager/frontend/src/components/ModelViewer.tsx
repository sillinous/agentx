'use client';

import { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, useGLTF, Html, useProgress } from '@react-three/drei';

// Loading component shown while model loads
function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <div className="flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
        <p className="mt-4 text-sm text-gray-600">{progress.toFixed(0)}% loaded</p>
      </div>
    </Html>
  );
}

// 3D Model component that loads GLTF/GLB files
function Model({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} />;
}

// Error boundary fallback
function ErrorFallback({ error }: { error: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full bg-gray-100 rounded-lg p-8">
      <svg className="w-16 h-16 text-red-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <p className="text-red-600 font-medium">Failed to load 3D model</p>
      <p className="text-gray-500 text-sm mt-2">{error}</p>
    </div>
  );
}

interface ModelViewerProps {
  url: string;
  className?: string;
  showControls?: boolean;
}

export function ModelViewer({ url, className = '', showControls = true }: ModelViewerProps) {
  const [autoRotate, setAutoRotate] = useState(true);
  const [error, setError] = useState<string | null>(null);

  if (error) {
    return <ErrorFallback error={error} />;
  }

  if (!url) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`}>
        <p className="text-gray-500">No model URL provided</p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Controls Panel */}
      {showControls && (
        <div className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRotate}
              onChange={(e) => setAutoRotate(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">Auto-rotate</span>
          </label>
        </div>
      )}

      {/* Help Text */}
      <div className="absolute bottom-4 left-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-2">
        <p className="text-xs text-gray-500">
          Drag to rotate | Scroll to zoom | Shift+drag to pan
        </p>
      </div>

      {/* 3D Canvas */}
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [0, 0, 5], fov: 50 }}
        className="rounded-lg"
        onError={(e) => {
          console.error('Canvas error:', e);
          setError('WebGL not supported or model failed to render');
        }}
      >
        <Suspense fallback={<Loader />}>
          <Stage
            environment="city"
            intensity={0.6}
            adjustCamera={true}
            shadows={{ type: 'accumulative', color: '#d9afd9', opacity: 0.8 }}
          >
            <Model url={url} />
          </Stage>
          <OrbitControls
            autoRotate={autoRotate}
            autoRotateSpeed={2}
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minPolarAngle={0}
            maxPolarAngle={Math.PI}
          />
        </Suspense>
      </Canvas>
    </div>
  );
}

// Preload hook for performance optimization
export function preloadModel(url: string) {
  useGLTF.preload(url);
}

export default ModelViewer;
