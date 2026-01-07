'use client';

import { Layout } from 'lucide-react';

interface LiveCanvasProps {
  showOverlay?: boolean;
}

export function LiveCanvas({ showOverlay = false }: LiveCanvasProps) {
  return (
    <div className="col-span-8 bg-black/40 border border-white/10 rounded-2xl relative overflow-hidden flex flex-col">
      {/* Canvas Header */}
      <div className="h-10 border-b border-white/5 bg-white/5 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
          <div className="w-2 h-2 rounded-full bg-amber-500/50"></div>
          <div className="w-2 h-2 rounded-full bg-emerald-500/50"></div>
        </div>
        <div className="text-xs text-slate-500 font-mono">
          LIVE PREVIEW: production-v2.4
        </div>
      </div>

      {/* Canvas Body */}
      <div className="flex-1 p-8 overflow-y-auto">
        <PreviewContent />
      </div>

      {/* System Ready Overlay */}
      {showOverlay && <SystemReadyOverlay />}
    </div>
  );
}

// Preview Content - mock generated site preview
function PreviewContent() {
  return (
    <div className="max-w-2xl mx-auto bg-white text-slate-900 rounded-lg shadow-2xl overflow-hidden min-h-[500px]">
      <div className="h-48 bg-slate-900 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-600 to-blue-900 opacity-80"></div>
        <h1 className="text-3xl font-bold text-white relative z-10">
          Master Your Craft
        </h1>
      </div>
      <div className="p-8 space-y-4">
        <div className="h-4 w-3/4 bg-slate-200 rounded"></div>
        <div className="h-4 w-full bg-slate-200 rounded"></div>
        <div className="h-4 w-5/6 bg-slate-200 rounded"></div>
        <div className="mt-8 flex gap-4">
          <div className="h-10 w-32 bg-slate-900 rounded"></div>
          <div className="h-10 w-32 border border-slate-300 rounded"></div>
        </div>
      </div>
    </div>
  );
}

// System Ready Overlay
function SystemReadyOverlay() {
  return (
    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center text-center p-6">
      <div className="w-24 h-24 mb-6 rounded-full border border-cyan-500/30 flex items-center justify-center relative">
        <div className="absolute inset-0 bg-cyan-500/10 blur-xl rounded-full animate-pulse"></div>
        <Layout className="w-10 h-10 text-cyan-400" />
      </div>
      <h2 className="text-2xl font-light text-white mb-2">System Ready</h2>
      <p className="text-slate-400 max-w-md">
        The canvas is blank. Ask the Architect to build a landing page, or the
        Sentry to analyze your data.
      </p>
    </div>
  );
}

export default LiveCanvas;
