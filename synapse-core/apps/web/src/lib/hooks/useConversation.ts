'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { synapseAPI } from '../api/client';
import type { AgentType, ChatMessage, ConversationSummary } from '../api/types';

interface Message {
  sender: 'user' | 'system';
  text: string;
}

interface UseConversationOptions {
  agent: AgentType;
  threadId?: string;
  autoSave?: boolean;
  onError?: (error: Error) => void;
}

interface UseConversationReturn {
  messages: Message[];
  isLoading: boolean;
  isSaving: boolean;
  error: Error | null;
  threadId: string;
  conversationList: ConversationSummary[];
  sendMessage: (prompt: string) => Promise<void>;
  loadConversation: (threadId: string) => Promise<void>;
  refreshConversationList: () => Promise<void>;
  clearMessages: () => void;
  setAgent: (agent: AgentType) => void;
  startNewConversation: () => void;
}

// Generate a unique thread ID
function generateThreadId(): string {
  return `thread-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useConversation({
  agent: initialAgent,
  threadId: initialThreadId,
  autoSave = true,
  onError,
}: UseConversationOptions): UseConversationReturn {
  const [agent, setAgentState] = useState<AgentType>(initialAgent);
  const [threadId, setThreadId] = useState<string>(initialThreadId || generateThreadId());
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'system', text: 'Genesis Complete. Agents are online. Waiting for command...' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [conversationList, setConversationList] = useState<ConversationSummary[]>([]);

  // Track if we've made changes that need saving
  const hasUnsavedChanges = useRef(false);

  // Format agent response for display
  const formatResponse = (data: { response: unknown }): string => {
    const response = data.response;
    if (typeof response === 'object' && response !== null) {
      const typed = response as { type?: string; content?: string; code?: string; description?: string; insights?: string; recommendations?: string };
      if (typed.type === 'text') {
        return typed.content || '';
      } else if (typed.type === 'component') {
        return `Component generated:\n\`\`\`tsx\n${typed.code}\n\`\`\`\n\n${typed.description || ''}`;
      } else if (typed.type === 'analytics_report') {
        return `Analytics Report:\n${typed.insights}\n\nRecommendations: ${typed.recommendations}`;
      }
      return JSON.stringify(response, null, 2);
    }
    return String(response) || 'No response from agent.';
  };

  // Save conversation to backend
  const saveConversation = useCallback(async () => {
    if (!autoSave || messages.length <= 1) return;

    setIsSaving(true);
    try {
      await synapseAPI.saveConversation(threadId, agent, messages);
      hasUnsavedChanges.current = false;
    } catch (err) {
      console.error('Failed to save conversation:', err);
      // Don't throw - saving is best effort
    } finally {
      setIsSaving(false);
    }
  }, [threadId, agent, messages, autoSave]);

  // Send a message to the agent
  const sendMessage = useCallback(async (prompt: string) => {
    if (!prompt.trim()) return;

    const userMessage: Message = { sender: 'user', text: prompt };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    hasUnsavedChanges.current = true;

    try {
      const data = await synapseAPI.invokeAgent({
        agent,
        thread_id: threadId,
        prompt,
      });

      const responseText = formatResponse(data);
      const agentNames: Record<AgentType, string> = {
        scribe: 'Scribe',
        architect: 'Architect',
        sentry: 'Sentry',
      };

      const systemMessage: Message = {
        sender: 'system',
        text: `[${agentNames[agent]}] ${responseText}`,
      };

      setMessages(prev => [...prev, systemMessage]);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onError?.(error);

      setMessages(prev => [...prev, {
        sender: 'system',
        text: `Error: ${error.message}`,
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [agent, threadId, onError]);

  // Load a specific conversation
  const loadConversation = useCallback(async (loadThreadId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const conversation = await synapseAPI.getConversation(loadThreadId);
      if (conversation) {
        setThreadId(loadThreadId);
        setAgentState(conversation.agent_type);
        setMessages(conversation.messages.map(m => ({
          sender: m.sender,
          text: m.text,
        })));
        hasUnsavedChanges.current = false;
      } else {
        throw new Error('Conversation not found');
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to load conversation');
      setError(error);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [onError]);

  // Refresh the conversation list
  const refreshConversationList = useCallback(async () => {
    try {
      const response = await synapseAPI.listConversations(undefined, 50);
      setConversationList(response.conversations);
    } catch (err) {
      console.error('Failed to load conversation list:', err);
    }
  }, []);

  // Clear messages and start fresh
  const clearMessages = useCallback(() => {
    setMessages([
      { sender: 'system', text: 'Genesis Complete. Agents are online. Waiting for command...' }
    ]);
    hasUnsavedChanges.current = false;
  }, []);

  // Start a new conversation
  const startNewConversation = useCallback(() => {
    // Save current conversation if needed
    if (hasUnsavedChanges.current) {
      saveConversation();
    }

    setThreadId(generateThreadId());
    clearMessages();
  }, [clearMessages, saveConversation]);

  // Change the active agent
  const setAgent = useCallback((newAgent: AgentType) => {
    setAgentState(newAgent);
  }, []);

  // Auto-save when messages change (debounced)
  useEffect(() => {
    if (!autoSave || !hasUnsavedChanges.current) return;

    const timer = setTimeout(() => {
      saveConversation();
    }, 2000); // Save 2 seconds after last change

    return () => clearTimeout(timer);
  }, [messages, autoSave, saveConversation]);

  // Load conversation list on mount
  useEffect(() => {
    refreshConversationList();
  }, [refreshConversationList]);

  return {
    messages,
    isLoading,
    isSaving,
    error,
    threadId,
    conversationList,
    sendMessage,
    loadConversation,
    refreshConversationList,
    clearMessages,
    setAgent,
    startNewConversation,
  };
}

export default useConversation;
