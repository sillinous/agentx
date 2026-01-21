import type {
  AgentType,
  AgentInvokeRequest,
  AgentResponse,
  Conversation,
  ConversationListResponse,
  ContentListResponse,
  ContentSearchResponse,
  HealthStatus,
  APIError,
  StreamEvent,
  DashboardMetrics,
} from './types';

// API base URL - uses Next.js API routes as proxy
const API_BASE = '/api';

// Generic fetch wrapper with error handling
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error: APIError = await response.json().catch(() => ({
      error: 'Request failed',
      status_code: response.status,
    }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// Synapse API client
export const synapseAPI = {
  // Health check
  async health(): Promise<HealthStatus> {
    return fetchAPI<HealthStatus>('/health');
  },

  // Invoke an agent
  async invokeAgent(request: AgentInvokeRequest): Promise<AgentResponse> {
    return fetchAPI<AgentResponse>('/agent', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Invoke an agent with streaming response
  async invokeAgentStream(
    request: Omit<AgentInvokeRequest, 'stream'>,
    onEvent: (event: StreamEvent) => void
  ): Promise<void> {
    const url = `${API_BASE}/agent`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...request, stream: true }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Stream failed' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6)) as StreamEvent;
              onEvent(event);
            } catch {
              // Skip malformed events
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  // Get a specific conversation
  async getConversation(threadId: string): Promise<Conversation | null> {
    try {
      return await fetchAPI<Conversation>(`/conversations/${threadId}`);
    } catch {
      return null;
    }
  },

  // List conversations
  async listConversations(
    agentType?: AgentType,
    limit: number = 20
  ): Promise<ConversationListResponse> {
    const params = new URLSearchParams();
    if (agentType) params.set('agent_type', agentType);
    params.set('limit', limit.toString());

    return fetchAPI<ConversationListResponse>(`/conversations?${params}`);
  },

  // Save conversation
  async saveConversation(
    threadId: string,
    agentType: AgentType,
    messages: Array<{ sender: 'user' | 'system'; text: string }>
  ): Promise<{ success: boolean }> {
    return fetchAPI<{ success: boolean }>(`/conversations/${threadId}`, {
      method: 'PUT',
      body: JSON.stringify({ agent_type: agentType, messages }),
    });
  },

  // List generated content
  async listContent(
    contentType?: string,
    limit: number = 20
  ): Promise<ContentListResponse> {
    const params = new URLSearchParams();
    if (contentType) params.set('content_type', contentType);
    params.set('limit', limit.toString());

    return fetchAPI<ContentListResponse>(`/content?${params}`);
  },

  // Search content semantically
  async searchContent(
    query: string,
    contentType?: string,
    limit: number = 5
  ): Promise<ContentSearchResponse> {
    return fetchAPI<ContentSearchResponse>('/content/search', {
      method: 'POST',
      body: JSON.stringify({ query, content_type: contentType, limit }),
    });
  },

  // Get dashboard metrics
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return fetchAPI<DashboardMetrics>('/dashboard/metrics');
  },
};

export default synapseAPI;
