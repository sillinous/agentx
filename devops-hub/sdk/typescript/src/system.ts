/**
 * DevOps Hub SDK - System API
 */

import type { HttpClient } from './client';
import type { HealthResponse, StatisticsResponse, Event } from './types';

export class SystemApi {
  constructor(private client: HttpClient) {}

  /**
   * Get system health status
   */
  async health(): Promise<HealthResponse> {
    const { data } = await this.client.get<HealthResponse>('/api/health');
    return data;
  }

  /**
   * Get detailed health status
   */
  async healthDetailed(): Promise<Record<string, unknown>> {
    const { data } = await this.client.get<Record<string, unknown>>('/api/health/detailed');
    return data;
  }

  /**
   * Get system statistics
   */
  async statistics(): Promise<StatisticsResponse> {
    const { data } = await this.client.get<StatisticsResponse>('/api/statistics');
    return data;
  }

  /**
   * Get system metrics (Prometheus format)
   */
  async metrics(): Promise<string> {
    const { data } = await this.client.get<string>('/api/metrics');
    return data;
  }

  /**
   * Emit an event
   * @param event - Event data
   */
  async emitEvent(event: Omit<Event, 'id' | 'timestamp'>): Promise<Event> {
    const { data } = await this.client.post<Event>('/api/events', event);
    return data;
  }

  /**
   * Get recent events
   * @param limit - Maximum number of events to return
   * @param eventType - Optional event type filter
   */
  async getEvents(limit?: number, eventType?: string): Promise<Event[]> {
    const { data } = await this.client.get<Event[]>('/api/events', { limit, type: eventType });
    return data;
  }

  /**
   * Get API version information
   */
  async version(): Promise<{ version: string; api_version: string }> {
    const { data } = await this.client.get<{ version: string; api_version: string }>('/api/version');
    return data;
  }
}
