'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardTitle } from '@/components/ui/Card';
import { Badge, PriorityBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { getQuickWins, updateOpportunityStatus } from '@/lib/api';
import { formatCurrency, getCategoryIcon } from '@/lib/utils';
import type { Opportunity } from '@/lib/types';
import { Clock, DollarSign, TrendingUp, ArrowUpRight, Check, RefreshCw } from 'lucide-react';

export default function QuickWinsPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await getQuickWins(50);
      setOpportunities(data.quick_wins);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStart = async (opp: Opportunity) => {
    await updateOpportunityStatus(opp.id, 'in_progress');
    await fetchData();
  };

  const handleComplete = async (opp: Opportunity) => {
    await updateOpportunityStatus(opp.id, 'completed');
    await fetchData();
  };

  const totalValue = opportunities.reduce((sum, opp) => sum + opp.revenue_impact, 0);
  const totalHours = opportunities.reduce((sum, opp) => sum + opp.effort_hours, 0);
  const avgROI = totalHours > 0 ? Math.round(totalValue / totalHours) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quick Wins</h1>
          <p className="text-gray-500 mt-1">
            Opportunities sorted by ROI (Revenue / Effort)
          </p>
        </div>
        <Button onClick={fetchData} variant="outline" disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-sm text-gray-500">Total Opportunities</p>
          <p className="text-2xl font-bold text-gray-900">{opportunities.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Total Revenue Impact</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalValue)}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Total Effort</p>
          <p className="text-2xl font-bold text-blue-600">{totalHours} hours</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Average ROI</p>
          <p className="text-2xl font-bold text-purple-600">${avgROI}/hour</p>
        </Card>
      </div>

      {/* Opportunities List */}
      <Card>
        <CardTitle className="mb-4">All Quick Wins</CardTitle>

        {loading ? (
          <div className="animate-pulse space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-20 bg-gray-100 rounded" />
            ))}
          </div>
        ) : opportunities.length === 0 ? (
          <p className="text-center text-gray-500 py-8">
            No opportunities found. Try scanning your repositories first.
          </p>
        ) : (
          <div className="space-y-3">
            {opportunities.map((opp, index) => {
              const roi = opp.effort_hours > 0
                ? Math.round(opp.revenue_impact / opp.effort_hours)
                : 0;

              return (
                <div
                  key={opp.id || index}
                  className={`p-4 border rounded-lg transition-colors ${
                    opp.status === 'completed'
                      ? 'bg-green-50 border-green-200'
                      : opp.status === 'in_progress'
                      ? 'bg-blue-50 border-blue-200'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-gray-400 font-mono text-sm">#{index + 1}</span>
                        <span className="text-xl">{getCategoryIcon(opp.category)}</span>
                        <span
                          className={`font-semibold text-lg ${
                            opp.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'
                          }`}
                        >
                          {opp.title}
                        </span>
                        <PriorityBadge priority={opp.priority} />
                        {opp.status !== 'pending' && (
                          <Badge
                            variant={opp.status === 'completed' ? 'success' : 'info'}
                          >
                            {opp.status.replace('_', ' ')}
                          </Badge>
                        )}
                      </div>

                      <p className="text-sm text-gray-500 mb-2">{opp.description}</p>

                      <div className="flex items-center gap-2">
                        <Link
                          href={`/projects/${opp.project_id}`}
                          className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                        >
                          {opp.project_name}
                          <ArrowUpRight className="w-3 h-3" />
                        </Link>
                      </div>

                      <div className="flex items-center gap-6 mt-3 text-sm">
                        <span className="flex items-center gap-1 text-gray-500">
                          <Clock className="w-4 h-4" />
                          {opp.effort_hours} hours
                        </span>
                        <span className="flex items-center gap-1 text-green-600 font-medium">
                          <DollarSign className="w-4 h-4" />
                          {formatCurrency(opp.revenue_impact)} impact
                        </span>
                        <span className="flex items-center gap-1 text-purple-600 font-medium">
                          <TrendingUp className="w-4 h-4" />
                          ${roi}/hr ROI
                        </span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      {opp.status === 'pending' && (
                        <Button size="sm" variant="outline" onClick={() => handleStart(opp)}>
                          Start
                        </Button>
                      )}
                      {opp.status === 'in_progress' && (
                        <Button size="sm" variant="primary" onClick={() => handleComplete(opp)}>
                          <Check className="w-4 h-4 mr-1" />
                          Complete
                        </Button>
                      )}
                      {opp.status === 'completed' && (
                        <Badge variant="success" size="md">
                          <Check className="w-4 h-4 mr-1" />
                          Done
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
}
