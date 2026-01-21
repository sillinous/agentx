'use client';

import { Suspense, useState, useRef, useCallback, createElement, useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Stage, useGLTF, Html, useProgress, useAnimations } from '@react-three/drei';
import * as THREE from 'three';
import type { OrbitControls as OrbitControlsType } from 'three-stdlib';

// Environment presets available in drei
const ENVIRONMENTS = [
  { name: 'City', value: 'city' },
  { name: 'Studio', value: 'studio' },
  { name: 'Sunset', value: 'sunset' },
  { name: 'Dawn', value: 'dawn' },
  { name: 'Night', value: 'night' },
  { name: 'Warehouse', value: 'warehouse' },
  { name: 'Forest', value: 'forest' },
  { name: 'Apartment', value: 'apartment' },
  { name: 'Park', value: 'park' },
  { name: 'Lobby', value: 'lobby' },
] as const;

type EnvironmentPreset = typeof ENVIRONMENTS[number]['value'];

// Animation state passed up from Model component
interface AnimationState {
  names: string[];
  isPlaying: boolean;
  currentAnimation: string | null;
  duration: number;
  currentTime: number;
  play: (name?: string) => void;
  pause: () => void;
  stop: () => void;
  setTime: (time: number) => void;
  setSpeed: (speed: number) => void;
}

// Model info for the info panel
interface ModelInfo {
  vertices: number;
  triangles: number;
  materials: number;
  bounds: { x: number; y: number; z: number };
}

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

// 3D Model component that loads GLTF/GLB files with animation support
function AnimatedModel({
  url,
  onAnimationStateChange,
  onModelInfoChange,
  playbackSpeed = 1
}: {
  url: string;
  onAnimationStateChange?: (state: AnimationState) => void;
  onModelInfoChange?: (info: ModelInfo) => void;
  playbackSpeed?: number;
}) {
  const { scene, animations } = useGLTF(url);
  const clonedScene = scene.clone(true);
  const { actions, names, mixer } = useAnimations(animations, clonedScene);

  const [currentAnimation, setCurrentAnimation] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Calculate model info
  useEffect(() => {
    if (onModelInfoChange) {
      let vertices = 0;
      let triangles = 0;
      const materialsSet = new Set<string>();

      clonedScene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
          const geometry = object.geometry;
          vertices += geometry.attributes.position?.count || 0;
          if (geometry.index) {
            triangles += geometry.index.count / 3;
          } else {
            triangles += vertices / 3;
          }
          if (object.material) {
            if (Array.isArray(object.material)) {
              object.material.forEach(m => materialsSet.add(m.name || m.uuid));
            } else {
              materialsSet.add(object.material.name || object.material.uuid);
            }
          }
        }
      });

      const box = new THREE.Box3().setFromObject(clonedScene);
      const size = box.getSize(new THREE.Vector3());

      onModelInfoChange({
        vertices,
        triangles: Math.floor(triangles),
        materials: materialsSet.size,
        bounds: { x: size.x, y: size.y, z: size.z }
      });
    }
  }, [clonedScene, onModelInfoChange]);

  // Update animation time periodically
  useEffect(() => {
    if (!mixer || !isPlaying) return;

    const interval = setInterval(() => {
      if (currentAnimation && actions[currentAnimation]) {
        setCurrentTime(actions[currentAnimation]!.time);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [mixer, isPlaying, currentAnimation, actions]);

  // Apply playback speed
  useEffect(() => {
    if (mixer) {
      // eslint-disable-next-line react-hooks/immutability
      mixer.timeScale = playbackSpeed;
    }
  }, [mixer, playbackSpeed]);

  // Expose animation controls
  useEffect(() => {
    if (onAnimationStateChange) {
      const play = (name?: string) => {
        const animName = name || names[0];
        if (animName && actions[animName]) {
          // Stop all other animations
          Object.values(actions).forEach(action => action?.stop());
          actions[animName]!.reset().play();
          setCurrentAnimation(animName);
          setIsPlaying(true);
          setDuration(actions[animName]!.getClip().duration);
        }
      };

      const pause = () => {
        if (currentAnimation && actions[currentAnimation]) {
          actions[currentAnimation]!.paused = true;
          setIsPlaying(false);
        }
      };

      const stop = () => {
        Object.values(actions).forEach(action => action?.stop());
        setIsPlaying(false);
        setCurrentTime(0);
        setCurrentAnimation(null);
      };

      const setTime = (time: number) => {
        if (currentAnimation && actions[currentAnimation]) {
          actions[currentAnimation]!.time = time;
          setCurrentTime(time);
        }
      };

      const setSpeed = (speed: number) => {
        if (mixer) {
          mixer.timeScale = speed;
        }
      };

      onAnimationStateChange({
        names,
        isPlaying,
        currentAnimation,
        duration,
        currentTime,
        play,
        pause,
        stop,
        setTime,
        setSpeed
      });
    }
  }, [names, isPlaying, currentAnimation, duration, currentTime, actions, mixer, onAnimationStateChange]);

  return createElement('group', null,
    createElement('primitive', { object: clonedScene })
  );
}

// Screenshot helper component that accesses the Three.js context
function ScreenshotHelper({ onCapture }: { onCapture: (dataUrl: string) => void }) {
  const { gl, scene, camera } = useThree();

  useEffect(() => {
    const handleCapture = () => {
      gl.render(scene, camera);
      const dataUrl = gl.domElement.toDataURL('image/png');
      onCapture(dataUrl);
    };

    // Expose capture function globally for the component to call
    (window as unknown as { __captureScreenshot?: () => void }).__captureScreenshot = handleCapture;

    return () => {
      delete (window as unknown as { __captureScreenshot?: () => void }).__captureScreenshot;
    };
  }, [gl, scene, camera, onCapture]);

  return null;
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

// Model Info Panel Component
function ModelInfoPanel({ info, isVisible, onToggle }: {
  info: ModelInfo | null;
  isVisible: boolean;
  onToggle: () => void;
}) {
  if (!info) return null;

  return (
    <div className="absolute bottom-4 right-4 z-10">
      <button
        onClick={onToggle}
        className="bg-white/90 backdrop-blur-sm rounded-lg shadow-lg px-3 py-2 text-sm text-gray-700 hover:bg-white transition-colors flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {isVisible ? 'Hide Info' : 'Show Info'}
      </button>
      {isVisible && (
        <div className="mt-2 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 text-sm">
          <h4 className="font-medium text-gray-800 mb-2">Model Statistics</h4>
          <div className="space-y-1 text-gray-600">
            <div className="flex justify-between gap-4">
              <span>Vertices:</span>
              <span className="font-mono">{info.vertices.toLocaleString()}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Triangles:</span>
              <span className="font-mono">{info.triangles.toLocaleString()}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Materials:</span>
              <span className="font-mono">{info.materials}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Size:</span>
              <span className="font-mono text-xs">
                {info.bounds.x.toFixed(2)} × {info.bounds.y.toFixed(2)} × {info.bounds.z.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Animation Controls Panel
function AnimationControls({
  animationState,
  playbackSpeed,
  onSpeedChange,
  loop,
  onLoopChange
}: {
  animationState: AnimationState | null;
  playbackSpeed: number;
  onSpeedChange: (speed: number) => void;
  loop: boolean;
  onLoopChange: (loop: boolean) => void;
}) {
  if (!animationState || animationState.names.length === 0) return null;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="absolute bottom-16 left-4 right-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3">
      <div className="flex items-center gap-3">
        {/* Play/Pause Button */}
        <button
          onClick={() => animationState.isPlaying ? animationState.pause() : animationState.play(animationState.currentAnimation || undefined)}
          className="w-10 h-10 flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 rounded-full text-white transition-colors"
        >
          {animationState.isPlaying ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Stop Button */}
        <button
          onClick={() => animationState.stop()}
          className="w-8 h-8 flex items-center justify-center bg-gray-200 hover:bg-gray-300 rounded text-gray-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 6h12v12H6z" />
          </svg>
        </button>

        {/* Timeline */}
        <div className="flex-1 flex items-center gap-2">
          <span className="text-xs text-gray-500 w-10">{formatTime(animationState.currentTime)}</span>
          <input
            type="range"
            min={0}
            max={animationState.duration || 1}
            step={0.01}
            value={animationState.currentTime}
            onChange={(e) => animationState.setTime(parseFloat(e.target.value))}
            className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <span className="text-xs text-gray-500 w-10">{formatTime(animationState.duration)}</span>
        </div>

        {/* Animation Selector (if multiple) */}
        {animationState.names.length > 1 && (
          <select
            value={animationState.currentAnimation || ''}
            onChange={(e) => animationState.play(e.target.value)}
            className="px-2 py-1 text-sm border border-gray-300 rounded bg-white"
          >
            {animationState.names.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        )}

        {/* Speed Control */}
        <select
          value={playbackSpeed}
          onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
          className="px-2 py-1 text-sm border border-gray-300 rounded bg-white"
        >
          <option value={0.25}>0.25x</option>
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>

        {/* Loop Toggle */}
        <label className="flex items-center gap-1 cursor-pointer">
          <input
            type="checkbox"
            checked={loop}
            onChange={(e) => onLoopChange(e.target.checked)}
            className="w-4 h-4 text-indigo-600 rounded"
          />
          <span className="text-xs text-gray-600">Loop</span>
        </label>
      </div>
    </div>
  );
}

interface ModelViewerProps {
  url: string;
  className?: string;
  showControls?: boolean;
  initialEnvironment?: EnvironmentPreset;
  showAnimationControls?: boolean;
}

export function ModelViewer({
  url,
  className = '',
  showControls = true,
  initialEnvironment = 'city',
  showAnimationControls = true
}: ModelViewerProps) {
  const [autoRotate, setAutoRotate] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [environment, setEnvironment] = useState<EnvironmentPreset>(initialEnvironment);
  const [showEnvironmentPicker, setShowEnvironmentPicker] = useState(false);
  const [animationState, setAnimationState] = useState<AnimationState | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [showModelInfo, setShowModelInfo] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [loop, setLoop] = useState(true);
  const controlsRef = useRef<OrbitControlsType>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Reset camera to initial position
  const handleResetView = useCallback(() => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  }, []);

  // Zoom in/out functions
  const handleZoomIn = useCallback(() => {
    if (controlsRef.current) {
      const camera = controlsRef.current.object as THREE.PerspectiveCamera;
      camera.position.multiplyScalar(0.8);
      controlsRef.current.update();
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (controlsRef.current) {
      const camera = controlsRef.current.object as THREE.PerspectiveCamera;
      camera.position.multiplyScalar(1.25);
      controlsRef.current.update();
    }
  }, []);

  // Toggle fullscreen
  const handleFullscreenToggle = useCallback(() => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch((err) => {
        console.error('Fullscreen error:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      }).catch((err) => {
        console.error('Exit fullscreen error:', err);
      });
    }
  }, []);

  // Screenshot capture
  const handleScreenshot = useCallback(() => {
    const captureFunc = (window as unknown as { __captureScreenshot?: () => void }).__captureScreenshot;
    if (captureFunc) {
      captureFunc();
    }
  }, []);

  const handleScreenshotCapture = useCallback((dataUrl: string) => {
    const link = document.createElement('a');
    link.download = `model-screenshot-${Date.now()}.png`;
    link.href = dataUrl;
    link.click();
  }, []);

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

  const hasAnimations = animationState && animationState.names.length > 0;

  return (
    <div
      ref={containerRef}
      className={`relative ${className} ${isFullscreen ? 'bg-gray-900' : ''}`}
    >
      {/* Main Controls Panel */}
      {showControls && (
        <div className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 space-y-3">
          {/* Auto-rotate Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRotate}
              onChange={(e) => setAutoRotate(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">Auto-rotate</span>
          </label>

          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700">Zoom:</span>
            <button
              onClick={handleZoomIn}
              className="w-8 h-8 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
              title="Zoom In"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m6-6H6" />
              </svg>
            </button>
            <button
              onClick={handleZoomOut}
              className="w-8 h-8 flex items-center justify-center bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
              title="Zoom Out"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" />
              </svg>
            </button>
          </div>

          {/* Reset View */}
          <button
            onClick={handleResetView}
            className="w-full px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors flex items-center justify-center gap-2"
            title="Reset View"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Reset View
          </button>

          {/* Screenshot Button */}
          <button
            onClick={handleScreenshot}
            className="w-full px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors flex items-center justify-center gap-2"
            title="Take Screenshot"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Screenshot
          </button>

          {/* Environment Picker */}
          <div className="relative">
            <button
              onClick={() => setShowEnvironmentPicker(!showEnvironmentPicker)}
              className="w-full px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors flex items-center justify-between gap-2"
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Environment
              </span>
              <svg className={`w-4 h-4 transition-transform ${showEnvironmentPicker ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showEnvironmentPicker && (
              <div className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-48 overflow-y-auto">
                {ENVIRONMENTS.map((env) => (
                  <button
                    key={env.value}
                    onClick={() => {
                      setEnvironment(env.value);
                      setShowEnvironmentPicker(false);
                    }}
                    className={`w-full px-3 py-1.5 text-sm text-left hover:bg-gray-100 ${
                      environment === env.value ? 'bg-indigo-50 text-indigo-600' : 'text-gray-700'
                    }`}
                  >
                    {env.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Fullscreen Toggle */}
          <button
            onClick={handleFullscreenToggle}
            className="w-full px-3 py-1.5 text-sm bg-indigo-100 hover:bg-indigo-200 rounded text-indigo-700 transition-colors flex items-center justify-center gap-2"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Exit Fullscreen
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
                Fullscreen
              </>
            )}
          </button>
        </div>
      )}

      {/* Help Text */}
      <div className="absolute bottom-4 left-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-2">
        <p className="text-xs text-gray-500">
          Drag to rotate | Scroll to zoom | Shift+drag to pan
        </p>
      </div>

      {/* Model Info Panel */}
      <ModelInfoPanel
        info={modelInfo}
        isVisible={showModelInfo}
        onToggle={() => setShowModelInfo(!showModelInfo)}
      />

      {/* Animation Controls */}
      {showAnimationControls && hasAnimations && (
        <AnimationControls
          animationState={animationState}
          playbackSpeed={playbackSpeed}
          onSpeedChange={setPlaybackSpeed}
          loop={loop}
          onLoopChange={setLoop}
        />
      )}

      {/* 3D Canvas */}
      <Canvas
        shadows
        dpr={[1, 2]}
        camera={{ position: [0, 0, 5], fov: 50 }}
        className="rounded-lg"
        gl={{ preserveDrawingBuffer: true }}
        onError={(e) => {
          console.error('Canvas error:', e);
          setError('WebGL not supported or model failed to render');
        }}
      >
        <ScreenshotHelper onCapture={handleScreenshotCapture} />
        <Suspense fallback={<Loader />}>
          <Stage
            environment={environment}
            intensity={0.6}
            adjustCamera={true}
            shadows={{ type: 'accumulative', color: '#d9afd9', opacity: 0.8 }}
          >
            <AnimatedModel
              url={url}
              onAnimationStateChange={setAnimationState}
              onModelInfoChange={setModelInfo}
              playbackSpeed={playbackSpeed}
            />
          </Stage>
          <OrbitControls
            ref={controlsRef}
            autoRotate={autoRotate}
            autoRotateSpeed={2}
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minPolarAngle={0}
            maxPolarAngle={Math.PI}
            minDistance={1}
            maxDistance={20}
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
