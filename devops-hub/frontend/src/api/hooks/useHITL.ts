import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';

export interface HITLRequest {
  id: string;
  request_type: string;
  title: string;
  description: string;
  agent_id: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in_review' | 'fulfilled' | 'rejected' | 'cancelled';
  workflow_id?: string;
  context: Record<string, unknown>;
  required_fields: Record<string, string>;
  response_data?: Record<string, unknown>;
  created_at: string;
  fulfilled_at?: string;
  fulfilled_by?: string;
  notes?: string;
}

export interface CreateHITLRequestPayload {
  agent_id: string;
  request_type: string;
  title: string;
  description: string;
  required_fields?: Record<string, string>;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  workflow_id?: string;
  context?: Record<string, unknown>;
}

export interface FulfillHITLRequestPayload {
  fulfilled_by: string;
  response_data: Record<string, unknown>;
  notes?: string;
}

export interface RejectHITLRequestPayload {
  rejected_by: string;
  reason: string;
}

export interface HITLStatistics {
  total_requests: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  by_type: Record<string, number>;
  average_response_time_hours: number;
  pending_requests: number;
}

export function useHITLRequests(
  status?: string,
  priority?: string,
  agentId?: string,
  limit = 50,
  offset = 0
) {
  return useQuery({
    queryKey: ['hitl-requests', status, priority, agentId, limit, offset],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (priority) params.append('priority', priority);
      if (agentId) params.append('agent_id', agentId);
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());

      const response = await apiClient.get<HITLRequest[]>(`/hitl/requests?${params}`);
      return response.data;
    },
  });
}

export function useHITLRequest(requestId: string) {
  return useQuery({
    queryKey: ['hitl-request', requestId],
    queryFn: async () => {
      const response = await apiClient.get<HITLRequest>(`/hitl/requests/${requestId}`);
      return response.data;
    },
    enabled: !!requestId,
  });
}

export function useCreateHITLRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateHITLRequestPayload) => {
      const response = await apiClient.post<HITLRequest>('/hitl/requests', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hitl-requests'] });
      queryClient.invalidateQueries({ queryKey: ['hitl-statistics'] });
    },
  });
}

export function useFulfillHITLRequest(requestId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: FulfillHITLRequestPayload) => {
      const response = await apiClient.post<HITLRequest>(
        `/hitl/requests/${requestId}/fulfill`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hitl-requests'] });
      queryClient.invalidateQueries({ queryKey: ['hitl-request', requestId] });
      queryClient.invalidateQueries({ queryKey: ['hitl-statistics'] });
    },
  });
}

export function useRejectHITLRequest(requestId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: RejectHITLRequestPayload) => {
      const response = await apiClient.post<HITLRequest>(
        `/hitl/requests/${requestId}/reject`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hitl-requests'] });
      queryClient.invalidateQueries({ queryKey: ['hitl-request', requestId] });
      queryClient.invalidateQueries({ queryKey: ['hitl-statistics'] });
    },
  });
}

export function useHITLStatistics() {
  return useQuery({
    queryKey: ['hitl-statistics'],
    queryFn: async () => {
      const response = await apiClient.get<HITLStatistics>('/hitl/statistics');
      return response.data;
    },
  });
}
