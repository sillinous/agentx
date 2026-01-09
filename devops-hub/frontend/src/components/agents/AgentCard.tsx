import { Link } from 'react-router-dom';
import { Card, Badge, StatusBadge, DomainBadge, TypeBadge } from '../ui';
import { RatingDisplay } from '../ui/Rating';
import { useEvaluations } from '../../api/hooks';
import type { AgentSummary } from '../../types';

interface AgentCardProps {
  agent: AgentSummary;
}

export default function AgentCard({ agent }: AgentCardProps) {
  const { getEvaluationsForTarget, getAverageRating } = useEvaluations();
  const evaluations = getEvaluationsForTarget('agent', agent.id);
  const avgRating = getAverageRating('agent', agent.id);

  return (
    <Link to={`/agents/${agent.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <div className="flex flex-col h-full">
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-semibold text-gray-900 truncate">{agent.name}</h3>
            <StatusBadge status={agent.status} />
          </div>

          <div className="flex gap-2 mb-3">
            <DomainBadge domain={agent.domain} />
            <TypeBadge type={agent.type} />
          </div>

          <p className="text-sm text-gray-600 mb-3 line-clamp-2 flex-grow">
            {agent.description}
          </p>

          <div className="flex flex-wrap gap-1 mb-3">
            {agent.capabilities.slice(0, 3).map((cap) => (
              <Badge key={cap} variant="default">
                {cap}
              </Badge>
            ))}
            {agent.capabilities.length > 3 && (
              <Badge variant="default">+{agent.capabilities.length - 3}</Badge>
            )}
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-gray-100">
            <span className="text-xs text-gray-400">v{agent.version}</span>
            <RatingDisplay value={avgRating} count={evaluations.length} />
          </div>
        </div>
      </Card>
    </Link>
  );
}
