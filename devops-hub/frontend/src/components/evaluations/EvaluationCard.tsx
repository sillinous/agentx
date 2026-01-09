import { Link } from 'react-router-dom';
import { Card, Badge, Button } from '../ui';
import Rating from '../ui/Rating';
import type { Evaluation } from '../../types';

interface EvaluationCardProps {
  evaluation: Evaluation;
  onDelete?: (id: string) => void;
}

export default function EvaluationCard({ evaluation, onDelete }: EvaluationCardProps) {
  const targetLink =
    evaluation.targetType === 'agent'
      ? `/agents/${evaluation.targetId}`
      : `/workflows/${evaluation.targetId}`;

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div className="flex-grow">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant={evaluation.targetType === 'agent' ? 'info' : 'purple'}>
              {evaluation.targetType}
            </Badge>
            <Link
              to={targetLink}
              className="font-medium text-gray-900 hover:text-blue-600"
            >
              {evaluation.targetName}
            </Link>
          </div>

          <div className="flex items-center gap-3 mb-2">
            <Rating value={evaluation.rating} readonly size="sm" />
            <span className="text-sm text-gray-500">
              {new Date(evaluation.createdAt).toLocaleDateString()}
            </span>
          </div>

          {evaluation.feedback && (
            <p className="text-sm text-gray-600 mt-2">{evaluation.feedback}</p>
          )}
        </div>

        {onDelete && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(evaluation.id)}
            className="text-gray-400 hover:text-red-500"
          >
            ✕
          </Button>
        )}
      </div>
    </Card>
  );
}
