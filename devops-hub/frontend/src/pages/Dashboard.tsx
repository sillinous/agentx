import { Link } from 'react-router-dom';
import { Card, Badge, Skeleton, SkeletonCard, StatusBadge } from '../components/ui';
import { useStatistics, useEvents, useHealth } from '../api/hooks';
import { useEffect, useState } from 'react';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useStatistics();
  const { data: eventsData, isLoading: eventsLoading } = useEvents({ limit: 10 });
  const { data: health } = useHealth();

  // Real-time pulse for system status - must be before any conditional returns
  const [showPulse, setShowPulse] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setShowPulse(prev => !prev);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  if (statsLoading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Agent operations overview and recent activity
          </p>
        </div>
        
        {/* Stats Grid Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <div className="flex items-center justify-between">
                <div className="space-y-2 flex-1">
                  <Skeleton width="60%" height={16} />
                  <Skeleton width="40%" height={32} />
                </div>
                <Skeleton variant="circular" width={48} height={48} />
              </div>
            </Card>
          ))}
        </div>

        {/* Distribution Cards Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Agent operations overview and recent activity
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'} ${showPulse ? 'animate-pulse' : ''}`} />
          <span className="text-gray-600 dark:text-gray-300">Live</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card hover animate>
          <Link to="/agents" className="block">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Total Agents</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats?.total_agents || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/50 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🤖</span>
              </div>
            </div>
          </Link>
        </Card>

        <Card hover animate>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Capabilities</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {stats?.capabilities_count || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/50 rounded-lg flex items-center justify-center">
              <span className="text-2xl">⚡</span>
            </div>
          </div>
        </Card>

        <Card hover animate>
          <Link to="/agents?status=production" className="block">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Production</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {stats?.by_status?.production || 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/50 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🚀</span>
              </div>
            </div>
          </Link>
        </Card>

        <Card hover animate>
          <Link to="/health" className="block">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">System Status</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white capitalize mt-1">
                  {health?.status || 'Unknown'}
                </p>
              </div>
              <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/50 rounded-lg flex items-center justify-center">
                <span className="text-2xl">💚</span>
              </div>
            </div>
          </Link>
        </Card>
      </div>

      {/* Distribution Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* By Domain */}
        <Card animate>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">By Domain</h3>
          <div className="space-y-3">
            {stats?.by_domain &&
              Object.entries(stats.by_domain).map(([domain, count]) => (
                <div key={domain} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{domain}</span>
                  <Badge variant={domain === 'system' ? 'purple' : domain === 'business' ? 'info' : 'default'}>
                    {count}
                  </Badge>
                </div>
              ))}
          </div>
        </Card>

        {/* By Type */}
        <Card animate>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">By Type</h3>
          <div className="space-y-3">
            {stats?.by_type &&
              Object.entries(stats.by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{type}</span>
                  <Badge>{count}</Badge>
                </div>
              ))}
          </div>
        </Card>

        {/* By Status */}
        <Card animate>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">By Status</h3>
          <div className="space-y-3">
            {stats?.by_status &&
              Object.entries(stats.by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{status}</span>
                  <StatusBadge status={status} />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{count}</span>
                </div>
              ))}
          </div>
        </Card>
      </div>

      {/* Quick Links and Recent Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Links */}
        <Card animate>
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <Link
              to="/agents"
              className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors group"
            >
              <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">🤖</div>
              <div className="font-medium text-gray-900 dark:text-white">Browse Agents</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Discover and test agents</div>
            </Link>
            <Link
              to="/workflows"
              className="p-4 bg-purple-50 dark:bg-purple-900/30 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors group"
            >
              <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">🔄</div>
              <div className="font-medium text-gray-900 dark:text-white">Run Workflows</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Execute multi-agent flows</div>
            </Link>
            <Link
              to="/human-actions"
              className="p-4 bg-green-50 dark:bg-green-900/30 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 transition-colors group"
            >
              <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">👤</div>
              <div className="font-medium text-gray-900 dark:text-white">Human Actions</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Pending HITL requests</div>
            </Link>
            <Link
              to="/workflows/builder"
              className="p-4 bg-amber-50 dark:bg-amber-900/30 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/50 transition-colors group"
            >
              <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">🛠️</div>
              <div className="font-medium text-gray-900 dark:text-white">Build Workflow</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Create custom workflows</div>
            </Link>
          </div>
        </Card>

        {/* Recent Events */}
        <Card animate>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Events</h3>
            <Link to="/health" className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
              View all
            </Link>
          </div>
          {eventsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-start gap-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
                  <Skeleton width={60} height={24} className="rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton width="70%" height={14} />
                    <Skeleton width="40%" height={12} />
                  </div>
                </div>
              ))}
            </div>
          ) : eventsData?.events && eventsData.events.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-auto">
              {eventsData.events.map((event, index) => (
                <div
                  key={event.id}
                  className="flex items-start gap-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded animate-fade-in-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex-shrink-0">
                    <Badge variant="info">{event.type}</Badge>
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className="text-sm text-gray-700 dark:text-gray-300 truncate">{event.source}</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-2">📭</div>
              <p className="text-gray-400 dark:text-gray-500">No recent events</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
