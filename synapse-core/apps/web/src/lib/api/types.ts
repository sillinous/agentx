// Agent types
export type AgentType = 'scribe' | 'architect' | 'sentry';

// Request/Response types
export interface AgentInvokeRequest {
  agent: AgentType;
  thread_id: string;
  prompt: string;
  user_id?: string;
  stream?: boolean;
}

// Streaming event types
export type StreamEvent =
  | { type: 'start'; agent: AgentType }
  | { type: 'chunk'; content: string }
  | { type: 'done'; thread_id: string }
  | { type: 'error'; message: string };

export interface AgentResponse {
  agent: AgentType;
  thread_id: string;
  response: AgentResponseContent;
  metadata?: Record<string, unknown>;
}

export type AgentResponseContent =
  | TextResponse
  | ComponentResponse
  | AnalyticsResponse
  | string;

export interface TextResponse {
  type: 'text';
  content: string;
}

export interface ComponentResponse {
  type: 'component';
  code: string;
  description?: string;
}

export interface AnalyticsResponse {
  type: 'analytics_report';
  insights: string;
  recommendations: string;
}

// Chat message types
export interface ChatMessage {
  sender: 'user' | 'system';
  text: string;
  timestamp?: string;
}

// Conversation types
export interface Conversation {
  id: string;
  thread_id: string;
  user_id: string;
  agent_type: AgentType;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  conversations: ConversationSummary[];
  total: number;
}

export interface ConversationSummary {
  thread_id: string;
  agent_type: AgentType;
  message_count: number;
  last_message?: string;
  created_at: string;
  updated_at: string;
}

// Content types
export interface GeneratedContent {
  id: string;
  user_id: string;
  content_type: string;
  content: string;
  agent_type?: AgentType;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface ContentListResponse {
  content: GeneratedContent[];
  total: number;
}

export interface ContentSearchResponse {
  results: GeneratedContent[];
  query: string;
}

// Health check
export interface HealthStatus {
  status: string;
  version?: string;
  agents?: {
    scribe: boolean;
    architect: boolean;
    sentry: boolean;
  };
}

// Error types
export interface APIError {
  error: string;
  detail?: string;
  status_code?: number;
}

// Dashboard types
export interface DashboardKPI {
  title: string;
  value: string;
  trend: string;
  color: string;
}

export interface DashboardActivity {
  agent: string;
  action: string;
  time: string;
  type: 'alert' | 'success' | 'info';
}

export interface DashboardMetrics {
  kpis: DashboardKPI[];
  activity_feed: DashboardActivity[];
  revenue_data: number[];
  timestamp: string;
}
