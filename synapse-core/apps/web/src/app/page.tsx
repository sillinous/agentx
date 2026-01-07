"use client";

import React, { useState } from 'react';
import {
  NavBar,
  ControlDashboard,
  ChatPanel,
  LiveCanvas,
  AGENTS,
  type AgentKey,
  type Message,
  type KPIData,
  type ActivityItem,
} from '@/components';

// --- THEME CONFIGURATION (The "Dark Glass" Brand) ---
// Background: #0a0e17 (Approximated as slate-950)
// Primary: #00f0ff (Approximated as cyan-400)
// Surface: #161b22 (Approximated as slate-900/50)

const SynapseInterface = () => {
  // --- STATE MANAGEMENT ---
  const [mode, setMode] = useState<'control' | 'command'>('control');
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<Message[]>([
    { sender: 'system', text: 'Genesis Complete. Agents are online. Waiting for command...' }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentKey>('scribe');
  const [threadId] = useState(() => `thread-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`);

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
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    const agentInfo = AGENTS[selectedAgent];
    setChatHistory(prev => [...prev, { sender: 'user', text: userMessage }]);
    setChatInput('');
    setIsProcessing(true);

    try {
      const response = await fetch('/api/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent: selectedAgent,
          thread_id: threadId,
          prompt: userMessage,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get agent response');
      }

      const data = await response.json();

      // Format the response based on type
      let responseText: string;
      if (typeof data.response === 'object') {
        if (data.response.type === 'text') {
          responseText = data.response.content;
        } else if (data.response.type === 'component') {
          responseText = `Component generated:\n\`\`\`tsx\n${data.response.code}\n\`\`\`\n\n${data.response.description || ''}`;
        } else if (data.response.type === 'analytics_report') {
          responseText = `Analytics Report:\n${data.response.insights}\n\nRecommendations: ${data.response.recommendations}`;
        } else {
          responseText = JSON.stringify(data.response, null, 2);
        }
      } else {
        responseText = data.response || 'No response from agent.';
      }

      setChatHistory(prev => [...prev, {
        sender: 'system',
        text: `[${agentInfo.name}] ${responseText}`
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
      <NavBar mode={mode} setMode={setMode} isProcessing={isProcessing} />

      {/* --- MAIN CONTENT AREA --- */}
      <main className="p-6 h-[calc(100vh-64px)] overflow-hidden">
        {/* === MODE B: CONTROL DASHBOARD === */}
        {mode === 'control' && (
          <ControlDashboard kpiData={kpiData} activityFeed={activityFeed} />
        )}

        {/* === MODE A: COMMAND INTERFACE === */}
        {mode === 'command' && (
          <div className="h-full grid grid-cols-12 gap-6 animate-in zoom-in-95 duration-500">
            {/* Left Col: The Conversation */}
            <ChatPanel
              messages={chatHistory}
              isLoading={isProcessing}
              selectedAgent={selectedAgent}
              onSelectAgent={setSelectedAgent}
              inputValue={chatInput}
              onInputChange={setChatInput}
              onSubmit={handleCommandSubmit}
            />

            {/* Right Col: The Live Canvas */}
            <LiveCanvas showOverlay={chatHistory.length === 1} />
          </div>
        )}
      </main>
    </div>
  );
};

export default SynapseInterface;
