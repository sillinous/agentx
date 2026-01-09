import { Link } from 'react-router-dom';
import { Card, Badge, LoadingScreen, StatusBadge } from '../components/ui';
import { useStatistics, useEvents, useHealth } from '../api/hooks';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useStatistics();
  const { data: eventsData, isLoading: eventsLoading } = useEvents({ limit: 10 });
  const { data: health } = useHealth();

  if (statsLoading) {
    return <LoadingScreen message="Loading dashboard..." />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Agent operations overview and recent activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Agents</p>
              <p className="text-3xl font-bold text-gray-900">{stats?.total_agents || 0}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Capabilities</p>
              <p className="text-3xl font-bold text-gray-900">
                {stats?.capabilities_count || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">⚡</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Production</p>
              <p className="text-3xl font-bold text-gray-900">
                {stats?.by_status?.production || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🚀</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">System Status</p>
              <p className="text-xl font-bold text-gray-900 capitalize mt-1">
                {health?.status || 'Unknown'}
              </p>
            </div>
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">💚</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Distribution Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* By Domain */}
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">By Domain</h3>
          <div className="space-y-3">
            {stats?.by_domain &&
              Object.entries(stats.by_domain).map(([domain, count]) => (
                <div key={domain} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{domain}</span>
                  <Badge variant={domain === 'system' ? 'purple' : domain === 'business' ? 'info' : 'default'}>
                    {count}
                  </Badge>
                </div>
              ))}
          </div>
        </Card>

        {/* By Type */}
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">By Type</h3>
          <div className="space-y-3">
            {stats?.by_type &&
              Object.entries(stats.by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{type}</span>
                  <Badge>{count}</Badge>
                </div>
              ))}
          </div>
        </Card>

        {/* By Status */}
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">By Status</h3>
          <div className="space-y-3">
            {stats?.by_status &&
              Object.entries(stats.by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{status}</span>
                  <StatusBadge status={status} />
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
          </div>
        </Card>
      </div>

      {/* Quick Links and Recent Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Links */}
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <Link
              to="/agents"
              className="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <div className="text-2xl mb-2">🤖</div>
              <div className="font-medium text-gray-900">Browse Agents</div>
              <div className="text-sm text-gray-500">Discover and test agents</div>
            </Link>
            <Link
              to="/workflows"
              className="p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <div className="text-2xl mb-2">🔄</div>
              <div className="font-medium text-gray-900">Run Workflows</div>
              <div className="text-sm text-gray-500">Execute multi-agent flows</div>
            </Link>
            <Link
              to="/evaluations"
              className="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <div className="text-2xl mb-2">⭐</div>
              <div className="font-medium text-gray-900">Evaluations</div>
              <div className="text-sm text-gray-500">View your feedback</div>
            </Link>
            <a
              href="/api/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="text-2xl mb-2">📚</div>
              <div className="font-medium text-gray-900">API Docs</div>
              <div className="text-sm text-gray-500">Swagger documentation</div>
            </a>
          </div>
        </Card>

        {/* Recent Events */}
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">Recent Events</h3>
          {eventsLoading ? (
            <LoadingScreen message="Loading events..." />
          ) : eventsData?.events && eventsData.events.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-auto">
              {eventsData.events.map((event) => (
                <div
                  key={event.id}
                  className="flex items-start gap-3 p-2 bg-gray-50 rounded"
                >
                  <div className="flex-shrink-0">
                    <Badge variant="info">{event.type}</Badge>
                  </div>
                  <div className="flex-grow min-w-0">
                    <p className="text-sm text-gray-700 truncate">{event.source}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No recent events</p>
          )}
        </Card>
      </div>
    </div>
  );
}
