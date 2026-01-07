"use client";

import React, { useState } from 'react';
import {
  NavBar,
  ControlDashboard,
  ChatPanel,
  LiveCanvas,
  ConversationSidebar,
  AGENTS,
  type AgentKey,
  type KPIData,
  type ActivityItem,
} from '@/components';
import { useConversation } from '@/lib/hooks/useConversation';

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

  // --- MOCK DATA FOR DASHBOARD ---
  const kpiData: KPIData[] = [
    { title: 'Total Revenue', value: '$12,450', trend: '+12%', color: 'text-emerald-400' },
    { title: 'Active Members', value: '1,240', trend: '+5%', color: 'text-cyan-400' },
    { title: 'Churn Rate', value: '2.1%', trend: '-0.4%', color: 'text-emerald-400' },
  ];

  const activityFeed: ActivityItem[] = [
    { agent: 'Sentry', action: 'Detected high bounce rate on /pricing', time: '2m ago', type: 'alert' },
    { agent: 'Scribe', action: 'Drafted "Welcome Back" email sequence', time: '15m ago', type: 'success' },
    { agent: 'Architect', action: 'Deployed v2.4 of Landing Page', time: '1h ago', type: 'info' },
  ];

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
