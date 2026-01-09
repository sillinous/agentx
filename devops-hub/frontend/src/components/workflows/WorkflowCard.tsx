import { Link } from 'react-router-dom';
import { Card, Badge } from '../ui';
import { RatingDisplay } from '../ui/Rating';
import { useEvaluations } from '../../api/hooks';
import type { WorkflowSummary } from '../../types';

interface WorkflowCardProps {
  workflow: WorkflowSummary;
}

export default function WorkflowCard({ workflow }: WorkflowCardProps) {
  const { getEvaluationsForTarget, getAverageRating } = useEvaluations();
  const evaluations = getEvaluationsForTarget('workflow', workflow.id);
  const avgRating = getAverageRating('workflow', workflow.id);

  return (
    <Link to={`/workflows/${workflow.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <div className="flex flex-col h-full">
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-semibold text-gray-900">{workflow.name}</h3>
            <Badge variant="info">{workflow.steps_count} steps</Badge>
          </div>

          <p className="text-sm text-gray-600 mb-4 flex-grow line-clamp-3">
            {workflow.description}
          </p>

          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <span className="text-xs text-gray-400">v{workflow.version}</span>
            <RatingDisplay value={avgRating} count={evaluations.length} />
          </div>
        </div>
      </Card>
    </Link>
  );
}
