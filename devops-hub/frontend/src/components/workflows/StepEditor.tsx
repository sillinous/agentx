import { useEffect } from 'react';
import { Card, Input, Select, TextArea, Button } from '../ui';
import { useAgents, useAgentCapabilities } from '../../api/hooks';
import type { WorkflowStep, StepType } from '../../types';

interface StepEditorProps {
  step: WorkflowStep & { id: string };
  index: number;
  totalSteps: number;
  onChange: (step: WorkflowStep & { id: string }) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDelete: () => void;
}

const STEP_TYPES: { value: StepType; label: string }[] = [
  { value: 'agent', label: 'Agent Execution' },
  { value: 'parallel', label: 'Parallel Execution' },
  { value: 'conditional', label: 'Conditional' },
  { value: 'transform', label: 'Transform Data' },
  { value: 'wait', label: 'Wait' },
];

export default function StepEditor({
  step,
  index,
  totalSteps,
  onChange,
  onMoveUp,
  onMoveDown,
  onDelete,
}: StepEditorProps) {
  const { data: agents, isLoading: agentsLoading } = useAgents('production');
  const { data: capabilitiesData, isLoading: capabilitiesLoading } = useAgentCapabilities(
    step.agent_id || ''
  );

  // Reset capability when agent changes and current capability is no longer valid
  useEffect(() => {
    if (step.agent_id && capabilitiesData) {
      const capabilities = capabilitiesData.capabilities || [];
      if (step.capability && !capabilities.includes(step.capability)) {
        onChange({ ...step, capability: null });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- onChange and step are intentionally excluded to prevent infinite loops
  }, [step.agent_id, step.capability, capabilitiesData]);

  const agentOptions = agents?.map((agent) => ({
    value: agent.id,
    label: `${agent.name} (${agent.type})`,
  })) || [];

  const capabilityOptions = (capabilitiesData?.capabilities || []).map((cap) => ({
    value: cap,
    label: cap,
  }));

  return (
    <Card className="relative">
      {/* Step header with ordering controls */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
            {index + 1}
          </span>
          <span className="text-sm font-medium text-gray-700">Step {index + 1}</span>
        </div>

        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onMoveUp}
            disabled={index === 0}
            title="Move up"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onMoveDown}
            disabled={index === totalSteps - 1}
            title="Move down"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </Button>
          <Button
            type="button"
            variant="danger"
            size="sm"
            onClick={onDelete}
            title="Delete step"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </Button>
        </div>
      </div>

      {/* Step configuration */}
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Step Name"
            value={step.name}
            onChange={(e) => onChange({ ...step, name: e.target.value })}
            placeholder="Enter step name..."
          />
          <Select
            label="Step Type"
            options={STEP_TYPES}
            value={step.type}
            onChange={(e) => onChange({ ...step, type: e.target.value as StepType })}
          />
        </div>

        {step.type === 'agent' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Agent"
              options={agentOptions}
              value={step.agent_id || ''}
              onChange={(e) => onChange({ ...step, agent_id: e.target.value || null, capability: null })}
              placeholder="Select an agent..."
              disabled={agentsLoading}
            />
            <Select
              label="Capability"
              options={capabilityOptions}
              value={step.capability || ''}
              onChange={(e) => onChange({ ...step, capability: e.target.value || null })}
              placeholder={step.agent_id ? 'Select a capability...' : 'Select an agent first'}
              disabled={!step.agent_id || capabilitiesLoading}
            />
          </div>
        )}

        {(step.type === 'transform' || step.type === 'conditional') && (
          <TextArea
            label="Configuration (JSON)"
            value={JSON.stringify((step as unknown as { config?: unknown }).config || {}, null, 2)}
            onChange={(e) => {
              try {
                const config = JSON.parse(e.target.value);
                onChange({ ...step, config } as WorkflowStep & { id: string });
              } catch {
                // Invalid JSON, ignore
              }
            }}
            placeholder='{"expression": "..."}'
            rows={3}
          />
        )}

        {step.type === 'wait' && (
          <Input
            label="Wait Duration (seconds)"
            type="number"
            min={1}
            value={(step as unknown as { duration_seconds?: number }).duration_seconds || 5}
            onChange={(e) => onChange({ ...step, duration_seconds: parseInt(e.target.value, 10) || 5 } as WorkflowStep & { id: string })}
          />
        )}
      </div>
    </Card>
  );
}
