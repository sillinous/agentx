import { useState, useMemo } from 'react';
import { Card, Select, Button } from '../components/ui';
import { EvaluationCard } from '../components/evaluations';
import { useEvaluations } from '../api/hooks';

export default function Evaluations() {
  const { evaluations, deleteEvaluation, exportToCsv } = useEvaluations();
  const [typeFilter, setTypeFilter] = useState<'' | 'agent' | 'workflow'>('');
  const [ratingFilter, setRatingFilter] = useState('');

  const filteredEvaluations = useMemo(() => {
    return evaluations.filter((e) => {
      if (typeFilter && e.targetType !== typeFilter) return false;
      if (ratingFilter && e.rating !== parseInt(ratingFilter)) return false;
      return true;
    });
  }, [evaluations, typeFilter, ratingFilter]);

  const stats = useMemo(() => {
    const agentEvals = evaluations.filter((e) => e.targetType === 'agent');
    const workflowEvals = evaluations.filter((e) => e.targetType === 'workflow');
    const avgRating =
      evaluations.length > 0
        ? evaluations.reduce((sum, e) => sum + e.rating, 0) / evaluations.length
        : 0;

    return {
      total: evaluations.length,
      agents: agentEvals.length,
      workflows: workflowEvals.length,
      avgRating: avgRating.toFixed(1),
    };
  }, [evaluations]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Evaluations</h1>
          <p className="text-gray-500 mt-1">Your feedback and ratings history</p>
        </div>
        <Button onClick={exportToCsv} disabled={evaluations.length === 0}>
          Export CSV
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-sm text-gray-500">Total Evaluations</p>
          <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Agent Reviews</p>
          <p className="text-3xl font-bold text-blue-600">{stats.agents}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Workflow Reviews</p>
          <p className="text-3xl font-bold text-purple-600">{stats.workflows}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Average Rating</p>
          <div className="flex items-center gap-2">
            <p className="text-3xl font-bold text-yellow-500">{stats.avgRating}</p>
            <span className="text-yellow-400 text-2xl">★</span>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex gap-4">
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as '' | 'agent' | 'workflow')}
            options={[
              { value: '', label: 'All Types' },
              { value: 'agent', label: 'Agents' },
              { value: 'workflow', label: 'Workflows' },
            ]}
          />
          <Select
            value={ratingFilter}
            onChange={(e) => setRatingFilter(e.target.value)}
            options={[
              { value: '', label: 'All Ratings' },
              { value: '5', label: '5 Stars' },
              { value: '4', label: '4 Stars' },
              { value: '3', label: '3 Stars' },
              { value: '2', label: '2 Stars' },
              { value: '1', label: '1 Star' },
            ]}
          />
        </div>
      </Card>

      {/* Evaluations List */}
      {filteredEvaluations.length > 0 ? (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            Showing {filteredEvaluations.length} evaluation
            {filteredEvaluations.length !== 1 && 's'}
          </p>
          {filteredEvaluations.map((evaluation) => (
            <EvaluationCard
              key={evaluation.id}
              evaluation={evaluation}
              onDelete={deleteEvaluation}
            />
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⭐</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {evaluations.length === 0 ? 'No evaluations yet' : 'No matching evaluations'}
            </h3>
            <p className="text-gray-500">
              {evaluations.length === 0
                ? 'Execute agents or workflows and rate your experience'
                : 'Try adjusting your filters'}
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
