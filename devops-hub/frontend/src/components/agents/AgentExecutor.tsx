import { useState } from 'react';
import { Card, Button, Select, TextArea, Spinner, StatusBadge, useToast } from '../ui';
import { useExecuteAgent } from '../../api/hooks';
import type { ExecutionResponse } from '../../types';

interface AgentExecutorProps {
  agentId: string;
  capabilities: string[];
  onExecutionComplete?: (response: ExecutionResponse) => void;
}

export default function AgentExecutor({
  agentId,
  capabilities,
  onExecutionComplete,
}: AgentExecutorProps) {
  const [selectedCapability, setSelectedCapability] = useState('');
  const [inputJson, setInputJson] = useState('{}');
  const [jsonError, setJsonError] = useState('');
  const [result, setResult] = useState<ExecutionResponse | null>(null);
  const toast = useToast();

  const { mutate: executeAgent, isPending } = useExecuteAgent();

  const handleExecute = () => {
    setJsonError('');
    let inputData: Record<string, unknown>;
    try {
      inputData = JSON.parse(inputJson);
    } catch {
      setJsonError('Invalid JSON format');
      return;
    }

    executeAgent(
      {
        agentId,
        request: {
          capability: selectedCapability,
          input_data: inputData,
        },
      },
      {
        onSuccess: (response) => {
          setResult(response);
          onExecutionComplete?.(response);
          if (response.status === 'success') {
            toast.showToast(
              'success',
              'Agent executed successfully',
              `Completed in ${response.execution_time_ms.toFixed(0)}ms`
            );
          } else {
            toast.showToast(
              'error',
              'Agent execution failed',
              response.error || 'Unknown error'
            );
          }
        },
        onError: (error) => {
          const errorMessage = error instanceof Error ? error.message : 'Execution failed';
          setResult({
            agent_id: agentId,
            status: 'error',
            output: null,
            error: errorMessage,
            execution_time_ms: 0,
            timestamp: new Date().toISOString(),
          });
          toast.showToast('error', 'Execution failed', errorMessage);
        },
      }
    );
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Execute Agent</h3>

      <div className="space-y-4">
        <Select
          label="Capability"
          value={selectedCapability}
          onChange={(e) => setSelectedCapability(e.target.value)}
          options={capabilities.map((c) => ({ value: c, label: c }))}
          placeholder="Select a capability..."
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Input Data (JSON)
          </label>
          <TextArea
            value={inputJson}
            onChange={(e) => setInputJson(e.target.value)}
            placeholder='{"key": "value"}'
            className="font-mono text-sm"
            rows={4}
          />
          {jsonError && <p className="text-sm text-red-600 mt-1">{jsonError}</p>}
        </div>

        <Button
          onClick={handleExecute}
          disabled={!selectedCapability || isPending}
          className="w-full"
        >
          {isPending ? (
            <>
              <Spinner size="sm" className="mr-2" /> Executing...
            </>
          ) : (
            'Execute'
          )}
        </Button>

        {result && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-sm">Result</span>
              <div className="flex items-center gap-2">
                <StatusBadge status={result.status} />
                <span className="text-xs text-gray-500">
                  {result.execution_time_ms.toFixed(0)}ms
                </span>
              </div>
            </div>
            {result.error ? (
              <p className="text-sm text-red-600">{result.error}</p>
            ) : (
              <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-48">
                {JSON.stringify(result.output, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
