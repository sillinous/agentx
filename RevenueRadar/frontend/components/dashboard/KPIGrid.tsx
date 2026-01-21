'use client';

import { Card } from '@/components/ui/Card';
import { formatCurrency, formatNumber } from '@/lib/utils';
import type { Overview } from '@/lib/types';
import {
  TrendingUp,
  Package,
  DollarSign,
  Zap,
  Target,
  BarChart3,
} from 'lucide-react';

interface KPIGridProps {
  overview: Overview | null;
  loading?: boolean;
}

export function KPIGrid({ overview, loading }: KPIGridProps) {
  if (loading || !overview) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-20 bg-gray-200 rounded" />
          </Card>
        ))}
      </div>
    );
  }

  const kpis = [
    {
      title: 'Total Projects',
      value: formatNumber(overview.total_projects),
      icon: Package,
      color: 'bg-blue-100 text-blue-600',
      subtext: `${overview.by_tier.tier1 || 0} Tier 1`,
    },
    {
      title: 'Revenue Potential',
      value: formatCurrency(overview.revenue_potential.max),
      icon: DollarSign,
      color: 'bg-green-100 text-green-600',
      subtext: `Min: ${formatCurrency(overview.revenue_potential.min)}/mo`,
    },
    {
      title: 'Avg Overall Score',
      value: `${overview.avg_scores.overall}`,
      icon: Target,
      color: 'bg-purple-100 text-purple-600',
      subtext: `Revenue: ${overview.avg_scores.revenue}`,
    },
    {
      title: 'Ready to Launch',
      value: formatNumber(overview.by_status.ready || 0),
      icon: Zap,
      color: 'bg-yellow-100 text-yellow-600',
      subtext: `${overview.by_status.development || 0} in development`,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi) => (
        <Card key={kpi.title}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">{kpi.title}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{kpi.value}</p>
              <p className="text-xs text-gray-400 mt-1">{kpi.subtext}</p>
            </div>
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${kpi.color}`}>
              <kpi.icon className="w-6 h-6" />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
