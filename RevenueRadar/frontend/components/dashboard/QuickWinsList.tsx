'use client';

import { Card, CardTitle } from '@/components/ui/Card';
import { Badge, TierBadge } from '@/components/ui/Badge';
import { formatCurrency } from '@/lib/utils';
import { Clock, DollarSign, TrendingUp, Target } from 'lucide-react';

// Project-level quick win from the API
interface ProjectQuickWin {
  id: string;
  name: string;
  description?: string;
  tier: string;
  status: string;
  overall_score: number;
  revenue_potential_min: number;
  revenue_potential_max: number;
  total_effort_hours: number;
  total_revenue_impact: number;
  roi: number;
  action_count: number;
  pending_actions: number;
  completed_actions: number;
  progress: string;
}

interface QuickWinsListProps {
  opportunities: ProjectQuickWin[];
  loading?: boolean;
}

export function QuickWinsList({ opportunities = [], loading }: QuickWinsListProps) {
  if (loading || !opportunities || opportunities.length === 0) {
    return (
      <Card>
        <CardTitle>Quick Wins</CardTitle>
        <div className="animate-pulse space-y-3 mt-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded" />
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <CardTitle>Quick Wins (Top ROI)</CardTitle>
        <Badge variant="info">{opportunities.length} projects</Badge>
      </div>

      <div className="space-y-3">
        {opportunities.slice(0, 5).map((project, index) => (
          <a
            key={project.id || index}
            href={`/projects/${project.id}`}
            className="block p-3 border border-gray-100 rounded-lg hover:bg-gray-50 hover:border-gray-200 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="w-4 h-4 text-blue-500" />
                  <span className="font-medium text-gray-900">{project.name}</span>
                  <TierBadge tier={project.tier as 'tier1' | 'tier2' | 'tier3'} />
                </div>

                <p className="text-sm text-gray-500 mb-2 line-clamp-1">
                  {project.description || 'No description'}
                </p>

                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {project.total_effort_hours}h effort
                  </span>
                  <span className="flex items-center gap-1 text-green-600">
                    <DollarSign className="w-3 h-3" />
                    {formatCurrency(project.revenue_potential_min)}-{formatCurrency(project.revenue_potential_max)}/mo
                  </span>
                  <span className="flex items-center gap-1 text-blue-600 font-medium">
                    <TrendingUp className="w-3 h-3" />
                    ${Math.round(project.roi)}/hr ROI
                  </span>
                </div>
              </div>

              <div className="text-right ml-4">
                <div className="text-2xl font-bold text-gray-900">{project.overall_score}</div>
                <div className="text-xs text-gray-500">score</div>
              </div>
            </div>
          </a>
        ))}
      </div>

      {opportunities.length > 5 && (
        <div className="mt-4 pt-4 border-t border-gray-100 text-center">
          <a href="/quickwins" className="text-sm text-blue-600 hover:text-blue-700">
            View all {opportunities.length} projects →
          </a>
        </div>
      )}
    </Card>
  );
}
