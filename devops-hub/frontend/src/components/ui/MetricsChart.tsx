import { useMemo } from 'react';

interface DataPoint {
  label: string;
  value: number;
  color?: string;
}

interface MetricsChartProps {
  data: DataPoint[];
  type?: 'bar' | 'donut' | 'progress';
  title?: string;
  showLabels?: boolean;
  showValues?: boolean;
  height?: number;
}

const DEFAULT_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green
  '#8B5CF6', // purple
  '#F59E0B', // amber
  '#EF4444', // red
  '#06B6D4', // cyan
  '#EC4899', // pink
];

export default function MetricsChart({
  data,
  type = 'bar',
  title,
  showLabels = true,
  showValues = true,
  height = 200,
}: MetricsChartProps) {
  const processedData = useMemo(() => {
    return data.map((item, index) => ({
      ...item,
      color: item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
    }));
  }, [data]);

  const total = useMemo(() => processedData.reduce((sum, item) => sum + item.value, 0), [processedData]);
  const maxValue = useMemo(() => Math.max(...processedData.map((d) => d.value), 1), [processedData]);

  if (type === 'bar') {
    return (
      <div className="w-full">
        {title && <h4 className="text-sm font-medium text-gray-700 mb-3">{title}</h4>}
        <div className="space-y-3" style={{ minHeight: height }}>
          {processedData.map((item, index) => (
            <div key={index}>
              <div className="flex items-center justify-between text-sm mb-1">
                {showLabels && <span className="text-gray-600">{item.label}</span>}
                {showValues && <span className="font-medium text-gray-900">{item.value}</span>}
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${(item.value / maxValue) * 100}%`,
                    backgroundColor: item.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (type === 'donut') {
    const size = Math.min(height, 200);
    const strokeWidth = 24;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;

    // Pre-compute segment offsets using reduce to avoid mutation during render
    const segmentsWithOffsets = processedData.reduce<Array<{
      item: typeof processedData[0];
      index: number;
      dashLength: number;
      offset: number;
    }>>((acc, item, index) => {
      const percentage = total > 0 ? item.value / total : 0;
      const dashLength = percentage * circumference;
      const offset = acc.length > 0 ? acc[acc.length - 1].offset + acc[acc.length - 1].dashLength : 0;
      acc.push({ item, index, dashLength, offset });
      return acc;
    }, []);

    return (
      <div className="w-full">
        {title && <h4 className="text-sm font-medium text-gray-700 mb-3">{title}</h4>}
        <div className="flex items-center gap-6">
          <div className="relative" style={{ width: size, height: size }}>
            <svg width={size} height={size} className="transform -rotate-90">
              {/* Background circle */}
              <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke="#E5E7EB"
                strokeWidth={strokeWidth}
              />
              {/* Data segments */}
              {segmentsWithOffsets.map(({ item, index, dashLength, offset }) => (
                <circle
                  key={index}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="none"
                  stroke={item.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${dashLength} ${circumference - dashLength}`}
                  strokeDashoffset={-offset}
                  className="transition-all duration-500"
                />
              ))}
            </svg>
            {/* Center text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-gray-900">{total}</span>
              <span className="text-xs text-gray-500">Total</span>
            </div>
          </div>
          {/* Legend */}
          {showLabels && (
            <div className="flex-1 space-y-2">
              {processedData.map((item, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-gray-600 flex-1">{item.label}</span>
                  {showValues && (
                    <span className="text-sm font-medium text-gray-900">{item.value}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (type === 'progress') {
    return (
      <div className="w-full">
        {title && <h4 className="text-sm font-medium text-gray-700 mb-3">{title}</h4>}
        <div className="space-y-4" style={{ minHeight: height }}>
          {processedData.map((item, index) => {
            const percentage = Math.min(100, Math.max(0, item.value));
            return (
              <div key={index}>
                <div className="flex items-center justify-between text-sm mb-1">
                  {showLabels && <span className="text-gray-600">{item.label}</span>}
                  {showValues && (
                    <span className="font-medium text-gray-900">{percentage}%</span>
                  )}
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: item.color,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return null;
}
