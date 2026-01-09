import { useQuery, useMutation } from '@tanstack/react-query';
import client from '../client';
import type { WorkflowSummary, WorkflowDetail, WorkflowExecution } from '../../types';

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const { data } = await client.get<{ workflows: WorkflowSummary[] }>('/workflows');
      return data.workflows;
    },
  });
}

export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: async () => {
      const { data } = await client.get<WorkflowDetail>(`/workflows/${workflowId}`);
      return data;
    },
    enabled: !!workflowId,
  });
}

export function useExecuteWorkflow() {
  return useMutation({
    mutationFn: async ({
      workflowId,
      inputData,
    }: {
      workflowId: string;
      inputData: Record<string, unknown>;
    }) => {
      const { data } = await client.post<WorkflowExecution>(
        `/workflows/${workflowId}/execute`,
        inputData
      );
      return data;
    },
  });
}

export function useWorkflowExecutions(workflowId?: string, status?: string) {
  return useQuery({
    queryKey: ['workflow-executions', workflowId, status],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (workflowId) params.workflow_id = workflowId;
      if (status) params.status = status;
      const { data } = await client.get<{ executions: WorkflowExecution[] }>(
        '/workflow-executions',
        { params }
      );
      return data.executions;
    },
  });
}

export function useWorkflowExecution(executionId: string) {
  return useQuery({
    queryKey: ['workflow-execution', executionId],
    queryFn: async () => {
      const { data } = await client.get<WorkflowExecution>(
        `/workflow-executions/${executionId}`
      );
      return data;
    },
    enabled: !!executionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'running' || data.status === 'pending')) {
        return 2000;
      }
      return false;
    },
  });
}
