import { useQuery, useMutation } from '@tanstack/react-query';
import client from '../client';
import type {
  AgentSummary,
  AgentDetail,
  DiscoverResponse,
  ExecutionRequest,
  ExecutionResponse,
  ValidationResponse,
} from '../../types';

interface DiscoverFilters {
  domain?: string;
  capability?: string;
  status?: string;
  agent_type?: string;
}

export function useAgents(status?: string) {
  return useQuery({
    queryKey: ['agents', status],
    queryFn: async () => {
      const params = status ? { status } : {};
      const { data } = await client.get<AgentSummary[]>('/agents', { params });
      return data;
    },
  });
}

export function useDiscoverAgents(filters: DiscoverFilters) {
  return useQuery({
    queryKey: ['agents', 'discover', filters],
    queryFn: async () => {
      const { data } = await client.get<DiscoverResponse>('/agents/discover', {
        params: filters,
      });
      return data;
    },
  });
}

export function useAgent(agentId: string) {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: async () => {
      const { data } = await client.get<AgentDetail>(`/agents/${agentId}`);
      return data;
    },
    enabled: !!agentId,
  });
}

export function useAgentCapabilities(agentId: string) {
  return useQuery({
    queryKey: ['agent', agentId, 'capabilities'],
    queryFn: async () => {
      const { data } = await client.get<{ agent_id: string; capabilities: string[] }>(
        `/agents/${agentId}/capabilities`
      );
      return data;
    },
    enabled: !!agentId,
  });
}

export function useExecuteAgent() {
  return useMutation({
    mutationFn: async ({
      agentId,
      request,
    }: {
      agentId: string;
      request: ExecutionRequest;
    }) => {
      const { data } = await client.post<ExecutionResponse>(
        `/agents/${agentId}/execute`,
        request
      );
      return data;
    },
  });
}

export function useValidateAgent() {
  return useMutation({
    mutationFn: async (agentId: string) => {
      const { data } = await client.post<ValidationResponse>(
        `/agents/${agentId}/validate`
      );
      return data;
    },
  });
}

export function useDomains() {
  return useQuery({
    queryKey: ['domains'],
    queryFn: async () => {
      const { data } = await client.get<{ domains: string[] }>('/domains');
      return data.domains;
    },
  });
}

export function useCapabilities() {
  return useQuery({
    queryKey: ['capabilities'],
    queryFn: async () => {
      const { data } = await client.get<{ capabilities: string[] }>('/capabilities');
      return data.capabilities;
    },
  });
}
