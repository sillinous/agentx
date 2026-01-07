'use client';

import { ArrowRight } from 'lucide-react';

// Agent configuration
export const AGENTS = {
  scribe: { name: 'Scribe', description: 'Content generation', color: 'cyan' },
  architect: { name: 'Architect', description: 'UI components', color: 'purple' },
  sentry: { name: 'Sentry', description: 'Analytics', color: 'amber' },
} as const;

export type AgentKey = keyof typeof AGENTS;

// Chat Message
export interface Message {
  sender: 'user' | 'system';
  text: string;
}

interface ChatMessageProps {
  sender: 'user' | 'system';
  text: string;
}

export function ChatMessage({ sender, text }: ChatMessageProps) {
  return (
    <div className={`flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] p-3 rounded-xl text-sm leading-relaxed whitespace-pre-wrap ${
          sender === 'user'
            ? 'bg-cyan-600 text-white rounded-br-none'
            : 'bg-slate-800 text-slate-200 rounded-bl-none border border-white/5'
        }`}
      >
        {text}
      </div>
    </div>
  );
}

// Loading Indicator
export function ChatLoading() {
  return (
    <div className="flex justify-start">
      <div className="bg-slate-800 p-3 rounded-xl rounded-bl-none border border-white/5 flex gap-2">
        <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></span>
        <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce [animation-delay:100ms]"></span>
        <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce [animation-delay:200ms]"></span>
      </div>
    </div>
  );
}

// Chat History
interface ChatHistoryProps {
  messages: Message[];
  isLoading?: boolean;
}

export function ChatHistory({ messages, isLoading = false }: ChatHistoryProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-700">
      {messages.map((msg, idx) => (
        <ChatMessage key={idx} sender={msg.sender} text={msg.text} />
      ))}
      {isLoading && <ChatLoading />}
    </div>
  );
}

// Agent Selector
interface AgentSelectorProps {
  selectedAgent: AgentKey;
  onSelectAgent: (agent: AgentKey) => void;
}

export function AgentSelector({ selectedAgent, onSelectAgent }: AgentSelectorProps) {
  const colorClasses = {
    cyan: {
      selected: 'bg-cyan-600 text-white border-cyan-500',
      default: 'border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10',
    },
    purple: {
      selected: 'bg-purple-600 text-white border-purple-500',
      default: 'border-purple-500/30 text-purple-400 hover:bg-purple-500/10',
    },
    amber: {
      selected: 'bg-amber-600 text-white border-amber-500',
      default: 'border-amber-500/30 text-amber-400 hover:bg-amber-500/10',
    },
  };

  return (
    <div className="flex gap-2">
      {(Object.keys(AGENTS) as AgentKey[]).map((agentKey) => {
        const agent = AGENTS[agentKey];
        const isSelected = selectedAgent === agentKey;
        const colors = colorClasses[agent.color];

        return (
          <button
            key={agentKey}
            type="button"
            onClick={() => onSelectAgent(agentKey)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
              isSelected ? colors.selected : colors.default
            }`}
          >
            {agent.name}
          </button>
        );
      })}
    </div>
  );
}

// Chat Input
interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  placeholder = 'Type a message...',
  disabled = false,
}: ChatInputProps) {
  return (
    <form onSubmit={onSubmit} className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full bg-slate-800 text-white placeholder-slate-500 rounded-xl py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 border border-white/5 transition-all disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="absolute right-2 top-2 p-1.5 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-white transition-colors disabled:opacity-50 disabled:hover:bg-cyan-600"
      >
        <ArrowRight className="w-4 h-4" />
      </button>
    </form>
  );
}

// Chat Panel - combines history, selector, and input
interface ChatPanelProps {
  messages: Message[];
  isLoading: boolean;
  selectedAgent: AgentKey;
  onSelectAgent: (agent: AgentKey) => void;
  inputValue: string;
  onInputChange: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}

export function ChatPanel({
  messages,
  isLoading,
  selectedAgent,
  onSelectAgent,
  inputValue,
  onInputChange,
  onSubmit,
}: ChatPanelProps) {
  return (
    <div className="col-span-4 flex flex-col h-full bg-slate-900/80 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-sm">
      <ChatHistory messages={messages} isLoading={isLoading} />

      <div className="p-4 border-t border-white/10 bg-slate-900 space-y-3">
        <AgentSelector selectedAgent={selectedAgent} onSelectAgent={onSelectAgent} />
        <ChatInput
          value={inputValue}
          onChange={onInputChange}
          onSubmit={onSubmit}
          placeholder={`Ask ${AGENTS[selectedAgent].name} anything...`}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}

export default ChatPanel;
