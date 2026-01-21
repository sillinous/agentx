'use client';

import { Card, CardTitle } from '@/components/ui/Card';
import { formatCurrency } from '@/lib/utils';
import type { Overview } from '@/lib/types';

interface TierChartProps {
  overview: Overview | null;
}

export function TierChart({ overview }: TierChartProps) {
  if (!overview) return null;

  const tiers = [
    {
      key: 'tier1',
      label: 'Tier 1',
      sublabel: 'Immediate Revenue',
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-700',
    },
    {
      key: 'tier2',
      label: 'Tier 2',
      sublabel: 'High Priority',
      color: 'bg-yellow-500',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-700',
    },
    {
      key: 'tier3',
      label: 'Tier 3',
      sublabel: 'Scalable',
      color: 'bg-gray-500',
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-700',
    },
  ];

  const totalProjects = overview.total_projects || 1;

  return (
    <Card>
      <CardTitle className="mb-4">Portfolio Distribution</CardTitle>

      <div className="space-y-4">
        {tiers.map((tier) => {
          const summary = overview.tier_summary[tier.key];
          const count = summary?.count || 0;
          const percentage = Math.round((count / totalProjects) * 100);
          const revenue = summary?.revenue_max || 0;

          return (
            <div key={tier.key} className={`p-3 rounded-lg ${tier.bgColor}`}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className={`font-medium ${tier.textColor}`}>{tier.label}</span>
                  <span className="text-xs text-gray-500 ml-2">{tier.sublabel}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">{count} projects</span>
              </div>

              <div className="w-full bg-white rounded-full h-2 mb-2">
                <div
                  className={`${tier.color} h-2 rounded-full transition-all duration-500`}
                  style={{ width: `${percentage}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">{percentage}% of portfolio</span>
                <span className={tier.textColor}>Up to {formatCurrency(revenue)}/mo</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Total Potential</span>
          <span className="text-lg font-bold text-green-600">
            {formatCurrency(overview.revenue_potential.max)}/mo
          </span>
        </div>
      </div>
    </Card>
  );
}
