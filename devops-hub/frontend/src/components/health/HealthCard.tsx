import { Card } from '../ui';

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

interface HealthCardProps {
  serviceName: string;
  status: HealthStatus;
  latencyMs?: number;
  lastCheck?: string;
  details?: string;
  className?: string;
}

const statusConfig: Record<HealthStatus, { color: string; bgColor: string; label: string }> = {
  healthy: {
    color: 'bg-green-500',
    bgColor: 'bg-green-50',
    label: 'Healthy',
  },
  degraded: {
    color: 'bg-yellow-500',
    bgColor: 'bg-yellow-50',
    label: 'Degraded',
  },
  unhealthy: {
    color: 'bg-red-500',
    bgColor: 'bg-red-50',
    label: 'Unhealthy',
  },
  unknown: {
    color: 'bg-gray-400',
    bgColor: 'bg-gray-50',
    label: 'Unknown',
  },
};

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) {
    return `${diffSec}s ago`;
  }
  if (diffSec < 3600) {
    return `${Math.floor(diffSec / 60)}m ago`;
  }
  return date.toLocaleTimeString();
}

function getLatencyColor(latencyMs: number): string {
  if (latencyMs < 100) return 'text-green-600';
  if (latencyMs < 500) return 'text-yellow-600';
  return 'text-red-600';
}

export default function HealthCard({
  serviceName,
  status,
  latencyMs,
  lastCheck,
  details,
  className = '',
}: HealthCardProps) {
  const config = statusConfig[status];

  return (
    <Card className={`${config.bgColor} ${className}`} padding="sm">
      <div className="flex items-start gap-3">
        {/* Status Indicator */}
        <div className="flex-shrink-0 mt-1">
          <div className={`w-3 h-3 rounded-full ${config.color}`}>
            <div
              className={`w-3 h-3 rounded-full ${config.color} ${
                status === 'healthy' ? 'animate-pulse' : ''
              }`}
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-grow min-w-0">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-gray-900 truncate">{serviceName}</h4>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                status === 'healthy'
                  ? 'bg-green-100 text-green-800'
                  : status === 'degraded'
                  ? 'bg-yellow-100 text-yellow-800'
                  : status === 'unhealthy'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {config.label}
            </span>
          </div>

          <div className="mt-2 flex items-center gap-4 text-sm">
            {latencyMs !== undefined && (
              <div className="flex items-center gap-1">
                <span className="text-gray-500">Latency:</span>
                <span className={`font-medium ${getLatencyColor(latencyMs)}`}>
                  {latencyMs}ms
                </span>
              </div>
            )}
            {lastCheck && (
              <div className="flex items-center gap-1">
                <span className="text-gray-500">Checked:</span>
                <span className="text-gray-700">{formatTimestamp(lastCheck)}</span>
              </div>
            )}
          </div>

          {details && (
            <p className="mt-1 text-xs text-gray-500 truncate">{details}</p>
          )}
        </div>
      </div>
    </Card>
  );
}

// Compact version for grid display
interface HealthIndicatorProps {
  name: string;
  status: HealthStatus;
  onClick?: () => void;
}

export function HealthIndicator({ name, status, onClick }: HealthIndicatorProps) {
  const config = statusConfig[status];

  return (
    <button
      onClick={onClick}
      className={`p-3 rounded-lg border ${config.bgColor} hover:shadow-sm transition-shadow text-left w-full`}
    >
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${config.color}`} />
        <span className="text-sm font-medium text-gray-900 truncate">{name}</span>
      </div>
    </button>
  );
}
