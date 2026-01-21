'use client';

import { useEffect, useState } from 'react';
import { Card, CardTitle } from '@/components/ui/Card';
import { Badge, PriorityBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { getPipeline, updateOpportunityStatus } from '@/lib/api';
import { formatCurrency, getCategoryIcon } from '@/lib/utils';
import type { Opportunity } from '@/lib/types';
import { Clock, DollarSign, ArrowRight, RefreshCw } from 'lucide-react';

const COLUMNS = [
  { key: 'pending', label: 'Pending', color: 'bg-gray-100' },
  { key: 'in_progress', label: 'In Progress', color: 'bg-blue-100' },
  { key: 'completed', label: 'Completed', color: 'bg-green-100' },
  { key: 'blocked', label: 'Blocked', color: 'bg-red-100' },
];

export default function PipelinePage() {
  const [pipeline, setPipeline] = useState<Record<string, Opportunity[]>>({
    pending: [],
    in_progress: [],
    completed: [],
    blocked: [],
  });
  const [loading, setLoading] = useState(true);

  const fetchPipeline = async () => {
    setLoading(true);
    try {
      const data = await getPipeline();
      setPipeline(data.pipeline);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPipeline();
  }, []);

  const handleMoveNext = async (opp: Opportunity) => {
    const statusOrder = ['pending', 'in_progress', 'completed'];
    const currentIndex = statusOrder.indexOf(opp.status);
    if (currentIndex < statusOrder.length - 1) {
      const nextStatus = statusOrder[currentIndex + 1];
      await updateOpportunityStatus(opp.id, nextStatus);
      await fetchPipeline();
    }
  };

  const totalValue = Object.values(pipeline)
    .flat()
    .reduce((sum, opp) => sum + opp.revenue_impact, 0);

  const completedValue = pipeline.completed?.reduce((sum, opp) => sum + opp.revenue_impact, 0) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Opportunity Pipeline</h1>
          <p className="text-gray-500 mt-1">
            Track and manage monetization opportunities
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Pipeline Value</p>
            <p className="text-xl font-bold text-green-600">{formatCurrency(totalValue)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Completed</p>
            <p className="text-xl font-bold text-blue-600">{formatCurrency(completedValue)}</p>
          </div>
          <Button onClick={fetchPipeline} variant="outline" disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Pipeline Board */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {COLUMNS.map((column) => {
          const items = pipeline[column.key] || [];
          const columnValue = items.reduce((sum, opp) => sum + opp.revenue_impact, 0);

          return (
            <div key={column.key} className="flex flex-col">
              {/* Column Header */}
              <div className={`${column.color} rounded-t-lg p-3`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">{column.label}</span>
                  <Badge variant="default">{items.length}</Badge>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {formatCurrency(columnValue)} potential
                </p>
              </div>

              {/* Column Content */}
              <div className="flex-1 bg-gray-50 rounded-b-lg p-2 min-h-[400px] space-y-2">
                {loading ? (
                  <div className="animate-pulse space-y-2">
                    {[1, 2].map((i) => (
                      <div key={i} className="h-24 bg-gray-200 rounded" />
                    ))}
                  </div>
                ) : items.length === 0 ? (
                  <p className="text-center text-gray-400 text-sm py-8">No items</p>
                ) : (
                  items.map((opp) => (
                    <Card key={opp.id} padding="sm" className="cursor-pointer hover:shadow-md">
                      <div className="flex items-start gap-2 mb-2">
                        <span className="text-lg">{getCategoryIcon(opp.category)}</span>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 text-sm truncate">
                            {opp.title}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {opp.project_name}
                          </p>
                        </div>
                        <PriorityBadge priority={opp.priority} />
                      </div>

                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {opp.effort_hours}h
                        </span>
                        <span className="flex items-center gap-1 text-green-600">
                          <DollarSign className="w-3 h-3" />
                          {formatCurrency(opp.revenue_impact)}
                        </span>
                      </div>

                      {column.key !== 'completed' && column.key !== 'blocked' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="w-full mt-2 text-xs"
                          onClick={() => handleMoveNext(opp)}
                        >
                          Move to {column.key === 'pending' ? 'In Progress' : 'Completed'}
                          <ArrowRight className="w-3 h-3 ml-1" />
                        </Button>
                      )}
                    </Card>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
