/**
 * DevOps Hub SDK - Workflows API
 */

import type { HttpClient } from './client';
import type {
  WorkflowSummary,
  WorkflowDetail,
  WorkflowExecution,
  CreateWorkflowRequest,
  StartWorkflowRequest,
} from './types';

export class WorkflowsApi {
  constructor(private client: HttpClient) {}

  /**
   * List all workflows
   */
  async list(): Promise<WorkflowSummary[]> {
    const { data } = await this.client.get<WorkflowSummary[]>('/api/workflows');
    return data;
  }

  /**
   * Get workflow details
   * @param workflowId - Workflow ID
   */
  async get(workflowId: string): Promise<WorkflowDetail> {
    const { data } = await this.client.get<WorkflowDetail>(`/api/workflows/${workflowId}`);
    return data;
  }

  /**
   * Create a new workflow
   * @param workflow - Workflow definition
   */
  async create(workflow: CreateWorkflowRequest): Promise<WorkflowDetail> {
    const { data } = await this.client.post<WorkflowDetail>('/api/workflows', workflow);
    return data;
  }

  /**
   * Update a workflow
   * @param workflowId - Workflow ID
   * @param workflow - Updated workflow definition
   */
  async update(workflowId: string, workflow: Partial<CreateWorkflowRequest>): Promise<WorkflowDetail> {
    const { data } = await this.client.put<WorkflowDetail>(`/api/workflows/${workflowId}`, workflow);
    return data;
  }

  /**
   * Delete a workflow
   * @param workflowId - Workflow ID
   */
  async delete(workflowId: string): Promise<{ deleted: boolean }> {
    const { data } = await this.client.delete<{ deleted: boolean }>(`/api/workflows/${workflowId}`);
    return data;
  }

  /**
   * Start a workflow execution
   * @param workflowId - Workflow ID
   * @param request - Start request with initial context
   */
  async start(workflowId: string, request: StartWorkflowRequest = {}): Promise<WorkflowExecution> {
    const { data } = await this.client.post<WorkflowExecution>(
      `/api/workflows/${workflowId}/start`,
      request
    );
    return data;
  }

  /**
   * Get workflow execution status
   * @param executionId - Execution ID
   */
  async getExecution(executionId: string): Promise<WorkflowExecution> {
    const { data } = await this.client.get<WorkflowExecution>(`/api/executions/${executionId}`);
    return data;
  }

  /**
   * List all executions
   * @param workflowId - Optional workflow ID filter
   * @param status - Optional status filter
   */
  async listExecutions(workflowId?: string, status?: string): Promise<WorkflowExecution[]> {
    const { data } = await this.client.get<WorkflowExecution[]>('/api/executions', {
      workflow_id: workflowId,
      status,
    });
    return data;
  }

  /**
   * Pause a workflow execution
   * @param executionId - Execution ID
   */
  async pauseExecution(executionId: string): Promise<WorkflowExecution> {
    const { data } = await this.client.post<WorkflowExecution>(`/api/executions/${executionId}/pause`);
    return data;
  }

  /**
   * Resume a paused workflow execution
   * @param executionId - Execution ID
   */
  async resumeExecution(executionId: string): Promise<WorkflowExecution> {
    const { data } = await this.client.post<WorkflowExecution>(`/api/executions/${executionId}/resume`);
    return data;
  }

  /**
   * Cancel a workflow execution
   * @param executionId - Execution ID
   */
  async cancelExecution(executionId: string): Promise<WorkflowExecution> {
    const { data } = await this.client.post<WorkflowExecution>(`/api/executions/${executionId}/cancel`);
    return data;
  }
}
