'use client';

import { Cpu, Bell, Zap } from 'lucide-react';

interface NavBarProps {
  mode: 'control' | 'command';
  setMode: (mode: 'control' | 'command') => void;
  isProcessing?: boolean;
}

export function NavBar({ mode, setMode, isProcessing = false }: NavBarProps) {
  return (
    <nav className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      {/* Logo Area */}
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${isProcessing ? 'animate-pulse bg-cyan-500/20' : 'bg-slate-800'}`}>
          <Cpu className="w-6 h-6 text-cyan-400" />
        </div>
        <span className="font-bold text-xl tracking-wider font-mono">SYNAPSE</span>
      </div>

      {/* Mode Toggle */}
      <ModeToggle mode={mode} setMode={setMode} />

      {/* User Profile */}
      <div className="flex items-center gap-4">
        <Bell className="w-5 h-5 text-slate-400 hover:text-white cursor-pointer" />
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 border border-white/20"></div>
      </div>
    </nav>
  );
}

interface ModeToggleProps {
  mode: 'control' | 'command';
  setMode: (mode: 'control' | 'command') => void;
}

export function ModeToggle({ mode, setMode }: ModeToggleProps) {
  return (
    <div className="relative bg-slate-900 rounded-full p-1 flex border border-white/10">
      <button
        onClick={() => setMode('control')}
        className={`px-6 py-1.5 rounded-full text-sm font-medium transition-all duration-300 ${
          mode === 'control'
            ? 'bg-slate-700 text-white shadow-lg'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        Control
      </button>
      <button
        onClick={() => setMode('command')}
        className={`px-6 py-1.5 rounded-full text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
          mode === 'command'
            ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/20'
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <Zap className="w-3 h-3" /> Command
      </button>
    </div>
  );
}

export default NavBar;
