import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Badge, LoadingScreen, StatusBadge } from '../components/ui';
import { WorkflowExecutor } from '../components/workflows';
import { RatingForm } from '../components/evaluations';
import { useWorkflow, useWorkflowExecutions, useEvaluations } from '../api/hooks';
import type { WorkflowExecution } from '../types';

export default function WorkflowDetail() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const { data: workflow, isLoading } = useWorkflow(workflowId || '');
  const { data: executions } = useWorkflowExecutions(workflowId);
  const { getEvaluationsForTarget } = useEvaluations();

  const [lastExecution, setLastExecution] = useState<WorkflowExecution | null>(null);
  const [showRatingForm, setShowRatingForm] = useState(false);

  const evaluations = getEvaluationsForTarget('workflow', workflowId || '');

  if (isLoading) {
    return <LoadingScreen message="Loading workflow details..." />;
  }

  if (!workflow) {
    return (
      <Card>
        <div className="text-center py-12">
          <div className="text-4xl mb-4">🔄</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Workflow not found</h3>
          <Link to="/workflows" className="text-blue-600 hover:underline">
            Back to workflows
          </Link>
        </div>
      </Card>
    );
  }

  const handleExecutionComplete = (execution: WorkflowExecution) => {
    setLastExecution(execution);
    if (execution.status === 'completed') {
      setShowRatingForm(true);
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/workflows" className="hover:text-gray-700">
          Workflows
        </Link>
        <span>/</span>
        <span className="text-gray-900">{workflow.name}</span>
      </div>

      {/* Header */}
      <Card>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{workflow.name}</h1>
              <Badge variant="info">{workflow.steps.length} steps</Badge>
            </div>
            <p className="text-gray-600 max-w-2xl">{workflow.description}</p>
            <p className="text-sm text-gray-400 mt-2">Version {workflow.version}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Steps */}
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">Workflow Steps</h3>
            <div className="space-y-3">
              {workflow.steps.map((step, index) => (
                <div
                  key={step.name}
                  className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium text-blue-700">
                    {index + 1}
                  </div>
                  <div className="flex-grow">
                    <p className="font-medium text-gray-900">{step.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="default">{step.type}</Badge>
                      {step.agent_id && (
                        <Link
                          to={`/agents/${step.agent_id}`}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          {step.agent_id}
                        </Link>
                      )}
                      {step.capability && (
                        <Badge variant="info">{step.capability}</Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Execution History */}
          {executions && executions.length > 0 && (
            <Card>
              <h3 className="font-semibold text-gray-900 mb-4">Recent Executions</h3>
              <div className="space-y-2">
                {executions.slice(0, 5).map((execution) => (
                  <div
                    key={execution.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded"
                  >
                    <div>
                      <p className="text-sm font-mono text-gray-600">
                        {execution.id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-gray-400">
                        {execution.started_at
                          ? new Date(execution.started_at).toLocaleString()
                          : 'Not started'}
                      </p>
                    </div>
                    <StatusBadge status={execution.status} />
                  </div>
                ))}
              </div>
            </Card>
          )}

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
          <WorkflowExecutor
            workflowId={workflow.id}
            steps={workflow.steps}
            onExecutionComplete={handleExecutionComplete}
          />

          {/* Rating Form */}
          {(showRatingForm || lastExecution) && (
            <RatingForm
              targetType="workflow"
              targetId={workflow.id}
              targetName={workflow.name}
              executionId={lastExecution?.id}
              onSubmit={() => setShowRatingForm(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
