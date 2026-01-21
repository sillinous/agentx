/**
 * DevOps Hub TypeScript SDK
 *
 * A comprehensive SDK for interacting with the DevOps Hub API.
 *
 * @example
 * ```typescript
 * import { DevOpsHub } from '@devops-hub/sdk';
 *
 * const hub = new DevOpsHub({
 *   baseUrl: 'http://localhost:8100',
 *   apiKey: 'your-api-key',
 * });
 *
 * // List agents
 * const agents = await hub.agents.list();
 *
 * // Execute an agent capability
 * const result = await hub.agents.execute('analytics-agent', {
 *   capability: 'calculate_stats',
 *   input_data: { data: [1, 2, 3, 4, 5] },
 * });
 *
 * // Start a workflow
 * const execution = await hub.workflows.start('my-workflow', {
 *   initial_context: { key: 'value' },
 * });
 * ```
 */

import { HttpClient, DevOpsHubError } from './client';
import { AgentsApi } from './agents';
import { WorkflowsApi } from './workflows';
import { SystemApi } from './system';
import type { SDKConfig } from './types';

export class DevOpsHub {
  private client: HttpClient;

  /** Agents API - manage and execute agents */
  public readonly agents: AgentsApi;

  /** Workflows API - create and run workflows */
  public readonly workflows: WorkflowsApi;

  /** System API - health, metrics, and events */
  public readonly system: SystemApi;

  /**
   * Create a new DevOps Hub SDK instance
   * @param config - SDK configuration
   */
  constructor(config: SDKConfig) {
    this.client = new HttpClient(config);
    this.agents = new AgentsApi(this.client);
    this.workflows = new WorkflowsApi(this.client);
    this.system = new SystemApi(this.client);
  }

  /**
   * Set the API key for authentication
   * @param apiKey - API key
   */
  setApiKey(apiKey: string): void {
    this.client.setApiKey(apiKey);
  }

  /**
   * Clear the API key
   */
  clearApiKey(): void {
    this.client.clearApiKey();
  }
}

// Export types
export type {
  SDKConfig,
  ApiResponse,
  ApiError,
  AgentStatus,
  AgentDomain,
  AgentType,
  AgentSummary,
  AgentDetail,
  PerformanceMetrics,
  DiscoverFilters,
  DiscoverResponse,
  ExecutionRequest,
  ExecutionResponse,
  ValidationIssue,
  ValidationResponse,
  StepType,
  WorkflowStatus,
  WorkflowStep,
  WorkflowSummary,
  WorkflowDetail,
  WorkflowExecution,
  CreateWorkflowRequest,
  StartWorkflowRequest,
  HealthResponse,
  StatisticsResponse,
  Event,
} from './types';

// Export client utilities
export { DevOpsHubError, HttpClient } from './client';

// Export API classes for advanced usage
export { AgentsApi } from './agents';
export { WorkflowsApi } from './workflows';
export { SystemApi } from './system';

// Default export
export default DevOpsHub;
