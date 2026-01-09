import { useState, useEffect } from 'react';
import { Card, Button, TextArea, Spinner, StatusBadge } from '../ui';
import { useExecuteWorkflow, useWorkflowExecution } from '../../api/hooks';
import type { WorkflowExecution, WorkflowStep } from '../../types';

interface WorkflowExecutorProps {
  workflowId: string;
  steps: WorkflowStep[];
  onExecutionComplete?: (execution: WorkflowExecution) => void;
}

export default function WorkflowExecutor({
  workflowId,
  steps,
  onExecutionComplete,
}: WorkflowExecutorProps) {
  const [inputJson, setInputJson] = useState('{}');
  const [jsonError, setJsonError] = useState('');
  const [executionId, setExecutionId] = useState<string | null>(null);

  const { mutate: executeWorkflow, isPending: isStarting } = useExecuteWorkflow();
  const { data: execution } = useWorkflowExecution(executionId || '');

  useEffect(() => {
    if (execution && (execution.status === 'completed' || execution.status === 'failed')) {
      onExecutionComplete?.(execution);
    }
  }, [execution, onExecutionComplete]);

  const handleExecute = () => {
    setJsonError('');
    let inputData: Record<string, unknown>;
    try {
      inputData = JSON.parse(inputJson);
    } catch {
      setJsonError('Invalid JSON format');
      return;
    }

    executeWorkflow(
      { workflowId, inputData },
      {
        onSuccess: (result) => {
          setExecutionId(result.id);
        },
        onError: (error) => {
          setJsonError(error instanceof Error ? error.message : 'Execution failed');
        },
      }
    );
  };

  const isRunning = execution?.status === 'running' || execution?.status === 'pending';

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Execute Workflow</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Input Data (JSON)
          </label>
          <TextArea
            value={inputJson}
            onChange={(e) => setInputJson(e.target.value)}
            placeholder='{"market": "technology", "region": "global"}'
            className="font-mono text-sm"
            rows={4}
            disabled={isRunning}
          />
          {jsonError && <p className="text-sm text-red-600 mt-1">{jsonError}</p>}
        </div>

        <Button
          onClick={handleExecute}
          disabled={isStarting || isRunning}
          className="w-full"
        >
          {isStarting || isRunning ? (
            <>
              <Spinner size="sm" className="mr-2" />{' '}
              {isStarting ? 'Starting...' : 'Running...'}
            </>
          ) : (
            'Execute Workflow'
          )}
        </Button>

        {execution && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-3">
              <span className="font-medium text-sm">Execution Progress</span>
              <StatusBadge status={execution.status} />
            </div>

            {/* Step Progress */}
            <div className="space-y-2 mb-4">
              {steps.map((step, index) => {
                const isCompleted = index < execution.current_step;
                const isCurrent = index === execution.current_step && isRunning;
                const isPending = index > execution.current_step;

                return (
                  <div
                    key={step.name}
                    className={`flex items-center gap-3 p-2 rounded ${
                      isCompleted
                        ? 'bg-green-50'
                        : isCurrent
                        ? 'bg-blue-50'
                        : 'bg-gray-50'
                    }`}
                  >
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isCurrent
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-300 text-gray-600'
                      }`}
                    >
                      {isCompleted ? '✓' : isCurrent ? <Spinner size="sm" /> : index + 1}
                    </div>
                    <div className="flex-grow">
                      <span
                        className={`text-sm ${
                          isPending ? 'text-gray-400' : 'text-gray-700'
                        }`}
                      >
                        {step.name}
                      </span>
                      {step.agent_id && (
                        <span className="text-xs text-gray-400 ml-2">
                          ({step.agent_id})
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Results */}
            {(execution.status === 'completed' || execution.status === 'failed') && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium block mb-2">Results</span>
                {execution.errors.length > 0 ? (
                  <div className="text-sm text-red-600">
                    {execution.errors.map((err, i) => (
                      <p key={i}>{JSON.stringify(err)}</p>
                    ))}
                  </div>
                ) : (
                  <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-48">
                    {JSON.stringify(execution.results, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
