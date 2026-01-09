import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Card,
  Badge,
  Button,
  LoadingScreen,
  StatusBadge,
  DomainBadge,
  TypeBadge,
} from '../components/ui';
import { AgentExecutor } from '../components/agents';
import { RatingForm } from '../components/evaluations';
import { useAgent, useValidateAgent, useEvaluations } from '../api/hooks';
import type { ExecutionResponse, ValidationResponse } from '../types';

export default function AgentDetail() {
  const { agentId } = useParams<{ agentId: string }>();
  const { data: agent, isLoading } = useAgent(agentId || '');
  const { mutate: validateAgent, isPending: isValidating } = useValidateAgent();
  const { getEvaluationsForTarget } = useEvaluations();

  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [lastExecution, setLastExecution] = useState<ExecutionResponse | null>(null);
  const [showRatingForm, setShowRatingForm] = useState(false);

  const evaluations = getEvaluationsForTarget('agent', agentId || '');

  if (isLoading) {
    return <LoadingScreen message="Loading agent details..." />;
  }

  if (!agent) {
    return (
      <Card>
        <div className="text-center py-12">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Agent not found</h3>
          <Link to="/agents" className="text-blue-600 hover:underline">
            Back to agents
          </Link>
        </div>
      </Card>
    );
  }

  const handleValidate = () => {
    validateAgent(agent.id, {
      onSuccess: setValidation,
    });
  };

  const handleExecutionComplete = (response: ExecutionResponse) => {
    setLastExecution(response);
    if (response.status === 'success') {
      setShowRatingForm(true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/agents" className="hover:text-gray-700">
          Agents
        </Link>
        <span>/</span>
        <span className="text-gray-900">{agent.name}</span>
      </div>

      {/* Header */}
      <Card>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
              <StatusBadge status={agent.status} />
            </div>
            <div className="flex gap-2 mb-4">
              <DomainBadge domain={agent.domain} />
              <TypeBadge type={agent.type} />
              <Badge>{`v${agent.version}`}</Badge>
            </div>
            <p className="text-gray-600 max-w-2xl">{agent.description}</p>
          </div>
          <Button variant="secondary" onClick={handleValidate} disabled={isValidating}>
            {isValidating ? 'Validating...' : 'Validate'}
          </Button>
        </div>
      </Card>

      {/* Validation Result */}
      {validation && (
        <Card className={validation.is_valid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Validation Result</h3>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">
                {validation.score.toFixed(1)}
              </span>
              <Badge variant={validation.is_valid ? 'success' : 'danger'}>
                {validation.is_valid ? 'Valid' : 'Invalid'}
              </Badge>
            </div>
          </div>
          {validation.issues.length > 0 && (
            <div className="space-y-2">
              {validation.issues.map((issue, i) => (
                <div
                  key={i}
                  className={`p-2 rounded text-sm ${
                    issue.severity === 'error' ? 'bg-red-100' : 'bg-yellow-100'
                  }`}
                >
                  <span className="font-medium">[{issue.principle}]</span> {issue.message}
                  {issue.suggestion && (
                    <p className="text-gray-600 mt-1">💡 {issue.suggestion}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Capabilities */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">Capabilities</h3>
            <div className="flex flex-wrap gap-2">
              {agent.capabilities.map((cap) => (
                <Badge key={cap} variant="info">
                  {cap}
                </Badge>
              ))}
            </div>
          </Card>

          {/* Protocols */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">Protocols</h3>
            <div className="flex flex-wrap gap-2">
              {agent.protocols.map((protocol) => (
                <Badge key={protocol} variant="purple">
                  {protocol}
                </Badge>
              ))}
            </div>
          </Card>

          {/* Performance */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">Performance Metrics</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-2xl font-bold text-gray-900">
                  {agent.performance.max_concurrent_requests}
                </p>
                <p className="text-xs text-gray-500">Max Concurrent</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-2xl font-bold text-gray-900">
                  {agent.performance.average_latency_ms}ms
                </p>
                <p className="text-xs text-gray-500">Avg Latency</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-2xl font-bold text-gray-900">
                  {agent.performance.uptime_percent}%
                </p>
                <p className="text-xs text-gray-500">Uptime</p>
              </div>
            </div>
          </Card>

          {/* User Evaluations */}
          {evaluations.length > 0 && (
            <Card>
              <h3 className="font-semibold text-gray-900 mb-4">
                User Evaluations ({evaluations.length})
              </h3>
              <div className="space-y-3">
                {evaluations.slice(0, 3).map((evaluation) => (
                  <div key={evaluation.id} className="p-3 bg-gray-50 rounded">
                    <div className="flex items-center gap-2 mb-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <span
                          key={star}
                          className={
                            star <= evaluation.rating ? 'text-yellow-400' : 'text-gray-300'
                          }
                        >
                          ★
                        </span>
                      ))}
                      <span className="text-xs text-gray-400">
                        {new Date(evaluation.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                    {evaluation.feedback && (
                      <p className="text-sm text-gray-600">{evaluation.feedback}</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Executor */}
          <AgentExecutor
            agentId={agent.id}
            capabilities={agent.capabilities}
            onExecutionComplete={handleExecutionComplete}
          />

          {/* Rating Form */}
          {(showRatingForm || lastExecution) && (
            <RatingForm
              targetType="agent"
              targetId={agent.id}
              targetName={agent.name}
              executionId={lastExecution?.timestamp}
              onSubmit={() => setShowRatingForm(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
