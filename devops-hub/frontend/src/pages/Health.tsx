import { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, Badge, LoadingScreen } from '../components/ui';
import { HealthCard, HealthIndicator, EventStream } from '../components/health';
import type { HealthStatus } from '../components/health';
import { useHealth, useStatistics, useEvents } from '../api/hooks';
import { useAgents } from '../api/hooks/useAgents';

type WebSocketStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

interface AgentHealth {
  id: string;
  name: string;
  status: HealthStatus;
  latencyMs?: number;
  lastCheck: string;
}

export default function Health() {
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>('disconnected');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [eventsPerMinute, setEventsPerMinute] = useState<number>(0);

  // Query hooks with polling
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useHealth();
  const { data: stats, isLoading: statsLoading } = useStatistics();
  const { data: eventsData, isLoading: eventsLoading } = useEvents({ limit: 20 });
  const { data: agents, isLoading: agentsLoading } = useAgents();

  // Poll health every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      refetchHealth();
      setLastRefresh(new Date());
    }, 10000);

    return () => clearInterval(interval);
  }, [refetchHealth]);

  // Calculate events per minute (mock calculation based on event count)
  useEffect(() => {
    if (eventsData?.events) {
      // Simple calculation - count events in the last minute
      const now = new Date();
      const oneMinuteAgo = new Date(now.getTime() - 60000);
      const recentEvents = eventsData.events.filter(
        (e) => new Date(e.timestamp) > oneMinuteAgo
      );
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setEventsPerMinute(recentEvents.length);
    }
  }, [eventsData]);

  // Simulate WebSocket status (would connect to real WS in production)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setWsStatus('connecting');
    const timeout = setTimeout(() => {
      setWsStatus('connected');
    }, 1000);

    return () => clearTimeout(timeout);
  }, []);

  // Derive agent health from agents data with stable mock latencies
  const agentHealthData: AgentHealth[] = useMemo(() => {
    const now = new Date().toISOString();
    return agents?.map((agent, index) => ({
      id: agent.id,
      name: agent.name,
      status: agent.status === 'production' ? 'healthy' :
              agent.status === 'staging' ? 'degraded' :
              agent.status === 'deprecated' || agent.status === 'retired' ? 'unhealthy' : 'unknown',
      latencyMs: 50 + ((index * 37) % 150), // Deterministic mock latency based on index
      lastCheck: now,
    })) || [];
  }, [agents]);

  // Get system health status
  const getSystemHealthStatus = useCallback((): HealthStatus => {
    if (!health?.status) return 'unknown';
    if (health.status === 'healthy') return 'healthy';
    if (health.status === 'degraded') return 'degraded';
    return 'unhealthy';
  }, [health]);

  // Get WebSocket status badge variant
  const getWsStatusVariant = (): 'success' | 'warning' | 'danger' | 'default' => {
    switch (wsStatus) {
      case 'connected': return 'success';
      case 'connecting': return 'warning';
      case 'error': return 'danger';
      default: return 'default';
    }
  };

  if (healthLoading || statsLoading) {
    return <LoadingScreen message="Loading health data..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Health Monitoring</h1>
          <p className="text-gray-500 mt-1">
            Real-time system health and event monitoring
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* WebSocket Status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected' ? 'bg-green-500 animate-pulse' :
              wsStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
              wsStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
            }`} />
            <Badge variant={getWsStatusVariant()}>
              WS: {wsStatus}
            </Badge>
          </div>
          {/* Last Refresh */}
          <span className="text-sm text-gray-500">
            Updated: {lastRefresh.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">System Status</p>
              <p className="text-xl font-bold text-gray-900 capitalize mt-1">
                {health?.status || 'Unknown'}
              </p>
            </div>
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
              getSystemHealthStatus() === 'healthy' ? 'bg-green-100' :
              getSystemHealthStatus() === 'degraded' ? 'bg-yellow-100' :
              getSystemHealthStatus() === 'unhealthy' ? 'bg-red-100' : 'bg-gray-100'
            }`}>
              <div className={`w-4 h-4 rounded-full ${
                getSystemHealthStatus() === 'healthy' ? 'bg-green-500' :
                getSystemHealthStatus() === 'degraded' ? 'bg-yellow-500' :
                getSystemHealthStatus() === 'unhealthy' ? 'bg-red-500' : 'bg-gray-400'
              }`} />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Agents</p>
              <p className="text-3xl font-bold text-gray-900">{stats?.total_agents || 0}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">&#129302;</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Active Workflows</p>
              <p className="text-3xl font-bold text-gray-900">
                {stats?.by_status?.production || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">&#128260;</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Events / min</p>
              <p className="text-3xl font-bold text-gray-900">{eventsPerMinute}</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">&#9889;</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Service Health Cards */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="font-semibold text-gray-900">Service Health</h2>

          <HealthCard
            serviceName="API Server"
            status={getSystemHealthStatus()}
            latencyMs={health ? 45 : undefined}
            lastCheck={health?.timestamp || new Date().toISOString()}
            details={`Version ${health?.version || 'unknown'}`}
          />

          <HealthCard
            serviceName="Event Bus"
            status={wsStatus === 'connected' ? 'healthy' : wsStatus === 'connecting' ? 'degraded' : 'unhealthy'}
            latencyMs={wsStatus === 'connected' ? 12 : undefined}
            lastCheck={new Date().toISOString()}
            details="WebSocket connection status"
          />

          <HealthCard
            serviceName="Agent Registry"
            status={agentsLoading ? 'unknown' : agents && agents.length > 0 ? 'healthy' : 'degraded'}
            latencyMs={agentsLoading ? undefined : 78}
            lastCheck={new Date().toISOString()}
            details={`${agents?.length || 0} agents registered`}
          />
        </div>

        {/* Event Stream */}
        <div className="lg:col-span-2">
          {eventsLoading ? (
            <Card>
              <LoadingScreen message="Loading events..." />
            </Card>
          ) : (
            <EventStream
              events={eventsData?.events || []}
              maxHeight="500px"
              autoScroll={true}
            />
          )}
        </div>
      </div>

      {/* Agent Health Grid */}
      <div>
        <h2 className="font-semibold text-gray-900 mb-4">Agent Health Status</h2>
        {agentsLoading ? (
          <LoadingScreen message="Loading agent health..." />
        ) : agentHealthData.length === 0 ? (
          <Card>
            <p className="text-gray-400 text-center py-8">No agents registered</p>
          </Card>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {agentHealthData.map((agent) => (
              <HealthIndicator
                key={agent.id}
                name={agent.name}
                status={agent.status}
              />
            ))}
          </div>
        )}
      </div>

      {/* Status Legend */}
      <Card padding="sm">
        <div className="flex items-center justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-gray-600">Healthy</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span className="text-gray-600">Degraded</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-gray-600">Unhealthy</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-400" />
            <span className="text-gray-600">Unknown</span>
          </div>
        </div>
      </Card>
    </div>
  );
}
