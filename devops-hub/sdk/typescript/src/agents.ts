/**
 * DevOps Hub SDK - Agents API
 */

import type { HttpClient } from './client';
import type {
  AgentSummary,
  AgentDetail,
  DiscoverFilters,
  DiscoverResponse,
  ExecutionRequest,
  ExecutionResponse,
  ValidationResponse,
} from './types';

export class AgentsApi {
  constructor(private client: HttpClient) {}

  /**
   * List all agents
   * @param status - Optional status filter
   */
  async list(status?: string): Promise<AgentSummary[]> {
    const { data } = await this.client.get<AgentSummary[]>('/api/agents', { status });
    return data;
  }

  /**
   * Discover agents with filters
   * @param filters - Discovery filters
   */
  async discover(filters: DiscoverFilters = {}): Promise<DiscoverResponse> {
    const { data } = await this.client.get<DiscoverResponse>('/api/agents/discover', filters);
    return data;
  }

  /**
   * Get agent details
   * @param agentId - Agent ID
   */
  async get(agentId: string): Promise<AgentDetail> {
    const { data } = await this.client.get<AgentDetail>(`/api/agents/${agentId}`);
    return data;
  }

  /**
   * Get agent capabilities
   * @param agentId - Agent ID
   */
  async getCapabilities(agentId: string): Promise<{ agent_id: string; capabilities: string[] }> {
    const { data } = await this.client.get<{ agent_id: string; capabilities: string[] }>(
      `/api/agents/${agentId}/capabilities`
    );
    return data;
  }

  /**
   * Execute an agent capability
   * @param agentId - Agent ID
   * @param request - Execution request
   */
  async execute(agentId: string, request: ExecutionRequest): Promise<ExecutionResponse> {
    const { data } = await this.client.post<ExecutionResponse>(
      `/api/agents/${agentId}/execute`,
      request
    );
    return data;
  }

  /**
   * Validate an agent
   * @param agentId - Agent ID
   */
  async validate(agentId: string): Promise<ValidationResponse> {
    const { data } = await this.client.post<ValidationResponse>(`/api/agents/${agentId}/validate`);
    return data;
  }

  /**
   * Get all domains
   */
  async getDomains(): Promise<string[]> {
    const { data } = await this.client.get<{ domains: string[] }>('/api/domains');
    return data.domains;
  }

  /**
   * Get all capabilities
   */
  async getAllCapabilities(): Promise<string[]> {
    const { data } = await this.client.get<{ capabilities: string[] }>('/api/capabilities');
    return data.capabilities;
  }
}
