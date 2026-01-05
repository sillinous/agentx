"use client"; // This directive makes the component a Client Component

import React, { useState, useEffect } from 'react';
import {
  Activity,
  MessageSquare,
  Cpu,
  Layout,
  Users,
  DollarSign,
  Send,
  Zap,
  Menu,
  Bell,
  Search,
  ArrowRight
} from 'lucide-react';

// --- THEME CONFIGURATION (The "Dark Glass" Brand) ---
// Background: #0a0e17 (Approximated as slate-950)
// Primary: #00f0ff (Approximated as cyan-400)
// Surface: #161b22 (Approximated as slate-900/50)

const SynapseInterface = () => {
  // --- STATE MANAGEMENT ---
  const [mode, setMode] = useState('control'); // 'control' or 'command'
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { sender: 'system', text: 'Genesis Complete. Agents are online. Waiting for command...' }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);

  // --- MOCK DATA FOR DASHBOARD ---
  const kpiData = [
    { title: 'Total Revenue', value: '$12,450', trend: '+12%', color: 'text-emerald-400' },
    { title: 'Active Members', value: '1,240', trend: '+5%', color: 'text-cyan-400' },
    { title: 'Churn Rate', value: '2.1%', trend: '-0.4%', color: 'text-emerald-400' },
  ];

  const activityFeed = [
    { agent: 'Sentry', action: 'Detected high bounce rate on /pricing', time: '2m ago', type: 'alert' },
    { agent: 'Scribe', action: 'Drafted "Welcome Back" email sequence', time: '15m ago', type: 'success' },
    { agent: 'Architect', action: 'Deployed v2.4 of Landing Page', time: '1h ago', type: 'info' },
  ];

  // --- HANDLERS ---
  const handleCommandSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    const newHistory = [...chatHistory, { sender: 'user', text: userMessage }];
    setChatHistory(newHistory);
    setChatInput('');
    setIsProcessing(true);

    try {
      // For now, use a mock user_id and a fixed thread_id
      const mockUserId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"; // This should eventually come from user session
      const threadId = "synapse-default-thread"; // This could be dynamic per conversation

      const response = await fetch('/api/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent: 'scribe', // Assuming we are invoking the scribe agent for now
          thread_id: threadId,
          user_id: mockUserId,
          prompt: userMessage,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get agent response');
      }

      const data = await response.json();
      setChatHistory(prev => [...prev, {
        sender: 'system',
        text: data.response || 'No response from agent.'
      }]);

    } catch (error) {
      console.error("Error invoking agent:", error);
      setChatHistory(prev => [...prev, {
        sender: 'system',
        text: `Error: ${error instanceof Error ? error.message : 'Could not connect to agent.'}`
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30">

      {/* --- TOP NAVIGATION BAR --- */}
      <nav className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">

        {/* Logo Area */}
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isProcessing ? 'animate-pulse bg-cyan-500/20' : 'bg-slate-800'}`}>
            <Cpu className="w-6 h-6 text-cyan-400" />
          </div>
          <span className="font-bold text-xl tracking-wider font-mono">SYNAPSE</span>
        </div>

        {/* THE TOGGLE (Control vs Command) */}
        <div className="relative bg-slate-900 rounded-full p-1 flex border border-white/10">
          <button
            onClick={() => setMode('control')}
            className={`px-6 py-1.5 rounded-full text-sm font-medium transition-all duration-300 ${mode === 'control' ? 'bg-slate-700 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
          >
            Control
          </button>
          <button
            onClick={() => setMode('command')}
            className={`px-6 py-1.5 rounded-full text-sm font-medium transition-all duration-300 flex items-center gap-2 ${mode === 'command' ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/20' : 'text-slate-400 hover:text-white'}`}
          >
            <Zap className="w-3 h-3" /> Command
          </button>
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-4">
          <Bell className="w-5 h-5 text-slate-400 hover:text-white cursor-pointer" />
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 border border-white/20"></div>
        </div>
      </nav>


      {/* --- MAIN CONTENT AREA --- */}
      <main className="p-6 h-[calc(100vh-64px)] overflow-hidden">

        {/* === MODE B: CONTROL DASHBOARD === */}
        {mode === 'control' && (
          <div className="max-w-7xl mx-auto h-full grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* KPI Row */}
            <div className="col-span-12 grid grid-cols-3 gap-6">
              {kpiData.map((kpi, idx) => (
                <div key={idx} className="bg-slate-900/50 border border-white/5 p-6 rounded-2xl hover:border-cyan-500/30 transition-colors group">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-slate-400 text-sm font-medium">{kpi.title}</h3>
                    <div className={`text-xs px-2 py-1 rounded bg-white/5 ${kpi.color}`}>{kpi.trend}</div>
                  </div>
                  <div className="text-3xl font-bold text-white group-hover:text-cyan-50 group-hover:drop-shadow-[0_0_10px_rgba(0,240,255,0.3)] transition-all">
                    {kpi.value}
                  </div>
                </div>
              ))}
            </div>

            {/* Main Chart Area (Mockup) */}
            <div className="col-span-8 bg-slate-900/50 border border-white/5 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 blur-3xl rounded-full pointer-events-none"></div>
              <h3 className="text-lg font-medium mb-6 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" /> Revenue Velocity
              </h3>
              <div className="h-64 flex items-end justify-between gap-2 opacity-80">
                {[40, 60, 45, 70, 85, 60, 75, 50, 65, 90, 80, 95].map((h, i) => (
                  <div key={i} style={{ height: `${h}%` }} className="w-full bg-slate-700 rounded-t-sm hover:bg-cyan-500 transition-colors"></div>
                ))}
              </div>
            </div>

            {/* Agent Activity Feed */}
            <div className="col-span-4 bg-slate-900/50 border border-white/5 rounded-2xl p-6 flex flex-col">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-amber-400" /> Agent Feed
              </h3>
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {activityFeed.map((item, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-white/5 border border-white/5 text-sm">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-mono text-xs text-cyan-400 uppercase tracking-wider">{item.agent}</span>
                      <span className="text-xs text-slate-500">{item.time}</span>
                    </div>
                    <p className="text-slate-300">{item.action}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}


        {/* === MODE A: COMMAND INTERFACE === */}
        {mode === 'command' && (
          <div className="h-full grid grid-cols-12 gap-6 animate-in zoom-in-95 duration-500">

            {/* Left Col: The Conversation */}
            <div className="col-span-4 flex flex-col h-full bg-slate-900/80 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-sm">

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700">
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] p-3 rounded-xl text-sm leading-relaxed ${
                      msg.sender === 'user'
                        ? 'bg-cyan-600 text-white rounded-br-none'
                        : 'bg-slate-800 text-slate-200 rounded-bl-none border border-white/5'
                    }`}>
                      {msg.text}
                    </div>
                  </div>
                ))}
                {isProcessing && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800 p-3 rounded-xl rounded-bl-none border border-white/5 flex gap-2">
                      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></span>
                      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce delay-100"></span>
                      <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce delay-200"></span>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="p-4 border-t border-white/10 bg-slate-900">
                <form onSubmit={handleCommandSubmit} className="relative">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Command the swarm..."
                    className="w-full bg-slate-800 text-white placeholder-slate-500 rounded-xl py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 border border-white/5 transition-all"
                  />
                  <button type="submit" className="absolute right-2 top-2 p-1.5 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white transition-colors">
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>

            {/* Right Col: The Live Canvas */}
            <div className="col-span-8 bg-black/40 border border-white/10 rounded-2xl relative overflow-hidden flex flex-col">

              {/* Canvas Header */}
              <div className="h-10 border-b border-white/5 bg-white/5 flex items-center justify-between px-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                  <div className="w-2 h-2 rounded-full bg-amber-500/50"></div>
                  <div className="w-2 h-2 rounded-full bg-emerald-500/50"></div>
                </div>
                <div className="text-xs text-slate-500 font-mono">LIVE PREVIEW: production-v2.4</div>
              </div>

              {/* Canvas Body (Simulation of a generated site) */}
              <div className="flex-1 p-8 overflow-y-auto">
                {/* Simulated Generated Content */}
                <div className="max-w-2xl mx-auto bg-white text-slate-900 rounded-lg shadow-2xl overflow-hidden min-h-[500px]">
                   <div className="h-48 bg-slate-900 flex items-center justify-center relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-cyan-600 to-blue-900 opacity-80"></div>
                      <h1 className="text-3xl font-bold text-white relative z-10">Master Your Craft</h1>
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
              </div>

              {/* Canvas Overlay (The 'System Dreaming' effect) */}
              {chatHistory.length === 1 && (
                <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center text-center p-6">
                  <div className="w-24 h-24 mb-6 rounded-full border border-cyan-500/30 flex items-center justify-center relative">
                     <div className="absolute inset-0 bg-cyan-500/10 blur-xl rounded-full animate-pulse"></div>
                     <Layout className="w-10 h-10 text-cyan-400" />
                  </div>
                  <h2 className="2xl font-light text-white mb-2">System Ready</h2>
                  <p className="text-slate-400 max-w-md">The canvas is blank. Ask the Architect to build a landing page, or the Sentry to analyze your data.</p>
                </div>
              )}

            </div>
          </div>
        )}

      </main>
    </div>
  );
};

export default SynapseInterface;