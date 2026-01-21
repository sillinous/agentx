/**
 * DevOps Hub SDK - Type Definitions
 */

// Agent Types
export type AgentStatus = 'draft' | 'staging' | 'production' | 'deprecated' | 'retired';
export type AgentDomain = 'system' | 'business' | 'utility';
export type AgentType = 'supervisor' | 'coordinator' | 'worker' | 'analyst';

export interface AgentSummary {
  id: string;
  name: string;
  version: string;
  status: AgentStatus;
  domain: AgentDomain;
  type: AgentType;
  description: string;
  capabilities: string[];
}

export interface PerformanceMetrics {
  max_concurrent_requests: number;
  average_latency_ms: number;
  uptime_percent: number;
}

export interface AgentDetail extends AgentSummary {
  protocols: string[];
  implementations: Record<string, string>;
  documentation: string;
  performance: PerformanceMetrics;
}

export interface DiscoverFilters {
  domain?: string;
  capability?: string;
  status?: string;
  agent_type?: string;
}

export interface DiscoverResponse {
  agents: AgentSummary[];
  total: number;
  filters_applied: {
    domain: string | null;
    capability: string | null;
    status: string | null;
    agent_type: string | null;
  };
}

// Execution Types
export interface ExecutionRequest {
  capability: string;
  input_data: Record<string, unknown>;
  timeout_seconds?: number;
}

export interface ExecutionResponse {
  agent_id: string;
  status: 'success' | 'error';
  output: Record<string, unknown> | null;
  error: string | null;
  execution_time_ms: number;
  timestamp: string;
}

// Validation Types
export interface ValidationIssue {
  principle: string;
  severity: string;
  message: string;
  suggestion: string;
}

export interface ValidationResponse {
  is_valid: boolean;
  agent_id: string;
  score: number;
  error_count: number;
  warning_count: number;
  issues: ValidationIssue[];
}

// Workflow Types
export type StepType = 'agent' | 'parallel' | 'conditional' | 'transform' | 'wait';
export type WorkflowStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export interface WorkflowStep {
  name: string;
  type: StepType;
  agent_id: string | null;
  capability: string | null;
}

export interface WorkflowSummary {
  id: string;
  name: string;
  description: string;
  version: string;
  steps_count: number;
}

export interface WorkflowDetail {
  id: string;
  name: string;
  description: string;
  version: string;
  steps: WorkflowStep[];
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: WorkflowStatus;
  current_step: number;
  context: Record<string, unknown>;
  results: Record<string, unknown>;
  errors: Array<Record<string, unknown>>;
  started_at: string | null;
  completed_at: string | null;
}

export interface CreateWorkflowRequest {
  name: string;
  description: string;
  steps: WorkflowStep[];
}

export interface StartWorkflowRequest {
  initial_context?: Record<string, unknown>;
}

// System Types
export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export interface StatisticsResponse {
  total_agents: number;
  by_status: Record<string, number>;
  by_domain: Record<string, number>;
  by_type: Record<string, number>;
  capabilities_count: number;
  apqc_processes_count: number;
}

// Event Types
export interface Event {
  id: string;
  type: string;
  source: string;
  data: Record<string, unknown>;
  timestamp: string;
  correlation_id: string | null;
  metadata: Record<string, unknown>;
}

// SDK Configuration
export interface SDKConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

// API Response wrapper
export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

// Error types
export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: Record<string, unknown>;
}
