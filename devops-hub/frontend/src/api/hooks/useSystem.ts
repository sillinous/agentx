import { useQuery } from '@tanstack/react-query';
import client from '../client';
import type { HealthResponse, StatisticsResponse, Event } from '../../types';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await client.get<HealthResponse>('/health');
      return data;
    },
    refetchInterval: 30000,
  });
}

export function useStatistics() {
  return useQuery({
    queryKey: ['statistics'],
    queryFn: async () => {
      const { data } = await client.get<StatisticsResponse>('/statistics');
      return data;
    },
  });
}

interface EventsParams {
  event_type?: string;
  source?: string;
  limit?: number;
}

export function useEvents(params: EventsParams = {}) {
  return useQuery({
    queryKey: ['events', params],
    queryFn: async () => {
      const { data } = await client.get<{ events: Event[]; total: number }>('/events', {
        params: { limit: 10, ...params },
      });
      return data;
    },
    refetchInterval: 10000,
  });
}
