'use client';

import { MessageSquare, Plus, Clock, Loader2 } from 'lucide-react';
import type { ConversationSummary } from '@/lib/api/types';

interface ConversationSidebarProps {
  conversations: ConversationSummary[];
  activeThreadId?: string;
  isLoading?: boolean;
  onSelectConversation: (threadId: string) => void;
  onNewConversation: () => void;
}

export function ConversationSidebar({
  conversations,
  activeThreadId,
  isLoading = false,
  onSelectConversation,
  onNewConversation,
}: ConversationSidebarProps) {
  const agentColors: Record<string, string> = {
    scribe: 'text-cyan-400',
    architect: 'text-purple-400',
    sentry: 'text-amber-400',
  };

  return (
    <div className="w-64 bg-slate-900/50 border-r border-white/10 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Conversation
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            No conversations yet
          </div>
        ) : (
          conversations.map((conv) => (
            <ConversationItem
              key={conv.thread_id}
              conversation={conv}
              isActive={conv.thread_id === activeThreadId}
              agentColor={agentColors[conv.agent_type] || 'text-slate-400'}
              onClick={() => onSelectConversation(conv.thread_id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  agentColor: string;
  onClick: () => void;
}

function ConversationItem({
  conversation,
  isActive,
  agentColor,
  onClick,
}: ConversationItemProps) {
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg transition-all ${
        isActive
          ? 'bg-white/10 border border-cyan-500/30'
          : 'hover:bg-white/5 border border-transparent'
      }`}
    >
      <div className="flex items-start gap-2">
        <MessageSquare className={`w-4 h-4 mt-0.5 ${agentColor}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className={`text-xs font-medium uppercase ${agentColor}`}>
              {conversation.agent_type}
            </span>
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTime(conversation.updated_at)}
            </span>
          </div>
          <p className="text-sm text-slate-300 truncate">
            {conversation.last_message || 'No messages'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {conversation.message_count} message{conversation.message_count !== 1 ? 's' : ''}
          </p>
        </div>
      </div>
    </button>
  );
}

export default ConversationSidebar;
