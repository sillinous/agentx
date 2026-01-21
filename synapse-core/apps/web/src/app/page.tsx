"use client";

import React, { useState, useEffect, useCallback } from 'react';
import {
  NavBar,
  ControlDashboard,
  ChatPanel,
  LiveCanvas,
  ConversationSidebar,
  type AgentKey,
  type KPIData,
  type ActivityItem,
} from '@/components';
import { useConversation } from '@/lib/hooks/useConversation';
import { synapseAPI } from '@/lib/api';

// --- THEME CONFIGURATION (The "Dark Glass" Brand) ---
// Background: #0a0e17 (Approximated as slate-950)
// Primary: #00f0ff (Approximated as cyan-400)
// Surface: #161b22 (Approximated as slate-900/50)

const SynapseInterface = () => {
  // --- STATE MANAGEMENT ---
  const [mode, setMode] = useState<'control' | 'command'>('control');
  const [chatInput, setChatInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<AgentKey>('scribe');
  const [showSidebar, setShowSidebar] = useState(false);

  // Use the conversation hook for persistent conversations
  const {
    messages,
    isLoading,
    isSaving,
    threadId,
    conversationList,
    sendMessage,
    loadConversation,
    startNewConversation,
    setAgent,
  } = useConversation({
    agent: selectedAgent,
    autoSave: true,
    onError: (error) => console.error('Conversation error:', error),
  });

  // --- DASHBOARD DATA STATE ---
  const [kpiData, setKpiData] = useState<KPIData[]>([
    { title: 'Agent Conversations', value: '...', trend: 'Loading', color: 'text-cyan-400' },
    { title: 'Content Generated', value: '...', trend: 'Loading', color: 'text-emerald-400' },
    { title: 'Active Agents', value: '3', trend: 'Operational', color: 'text-amber-400' },
  ]);

  const [activityFeed, setActivityFeed] = useState<ActivityItem[]>([
    { agent: 'SYSTEM', action: 'Loading activity feed...', time: 'Now', type: 'info' },
  ]);

  // Fetch dashboard metrics
  const fetchDashboardMetrics = useCallback(async () => {
    try {
      const metrics = await synapseAPI.getDashboardMetrics();
      setKpiData(metrics.kpis);
      setActivityFeed(metrics.activity_feed);
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      // Keep showing loading state or set error state
    }
  }, []);

  // Fetch dashboard data on mount and when mode changes to control
  useEffect(() => {
    if (mode === 'control') {
      fetchDashboardMetrics();
      // Refresh every 30 seconds when on dashboard
      const interval = setInterval(fetchDashboardMetrics, 30000);
      return () => clearInterval(interval);
    }
  }, [mode, fetchDashboardMetrics]);

  // --- HANDLERS ---
  const handleCommandSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!chatInput.trim() || isLoading) return;

    const message = chatInput;
    setChatInput('');
    await sendMessage(message);
  };

  const handleAgentSelect = (agent: AgentKey) => {
    setSelectedAgent(agent);
    setAgent(agent);
  };

  const handleSelectConversation = async (conversationThreadId: string) => {
    await loadConversation(conversationThreadId);
    setShowSidebar(false);
  };

  const handleNewConversation = () => {
    startNewConversation();
    setShowSidebar(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30">
      {/* --- TOP NAVIGATION BAR --- */}
      <NavBar mode={mode} setMode={setMode} isProcessing={isLoading} />

      {/* --- MAIN CONTENT AREA --- */}
      <main className="p-6 h-[calc(100vh-64px)] overflow-hidden">
        {/* === MODE B: CONTROL DASHBOARD === */}
        {mode === 'control' && (
          <ControlDashboard kpiData={kpiData} activityFeed={activityFeed} />
        )}

        {/* === MODE A: COMMAND INTERFACE === */}
        {mode === 'command' && (
          <div className="h-full flex gap-6 animate-in zoom-in-95 duration-500">
            {/* Conversation Sidebar (collapsible) */}
            {showSidebar && (
              <ConversationSidebar
                conversations={conversationList}
                activeThreadId={threadId}
                onSelectConversation={handleSelectConversation}
                onNewConversation={handleNewConversation}
              />
            )}

            {/* Main Command Interface */}
            <div className={`flex-1 grid ${showSidebar ? 'grid-cols-12' : 'grid-cols-12'} gap-6`}>
              {/* Left Col: The Conversation */}
              <div className="col-span-4 flex flex-col h-full">
                {/* Sidebar Toggle & Status */}
                <div className="flex items-center justify-between mb-3">
                  <button
                    onClick={() => setShowSidebar(!showSidebar)}
                    className="text-xs text-slate-400 hover:text-white transition-colors"
                  >
                    {showSidebar ? 'Hide History' : 'Show History'}
                  </button>
                  {isSaving && (
                    <span className="text-xs text-slate-500">Saving...</span>
                  )}
                </div>

                <ChatPanel
                  messages={messages}
                  isLoading={isLoading}
                  selectedAgent={selectedAgent}
                  onSelectAgent={handleAgentSelect}
                  inputValue={chatInput}
                  onInputChange={setChatInput}
                  onSubmit={handleCommandSubmit}
                />
              </div>

              {/* Right Col: The Live Canvas */}
              <div className="col-span-8">
                <LiveCanvas showOverlay={messages.length === 1} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default SynapseInterface;
