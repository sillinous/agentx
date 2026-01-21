import { useMemo } from 'react';
import type { WorkflowStep, StepType } from '../../types';

interface StepWithId extends WorkflowStep {
  id: string;
}

interface WorkflowVisualizerProps {
  steps: StepWithId[];
  currentStep?: number;
  executionStatus?: 'pending' | 'running' | 'completed' | 'failed';
}

const STEP_ICONS: Record<StepType, string> = {
  agent: '🤖',
  parallel: '⚡',
  conditional: '🔀',
  transform: '🔄',
  wait: '⏱️',
};

const STEP_COLORS: Record<StepType, { bg: string; border: string; text: string }> = {
  agent: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
  parallel: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
  conditional: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700' },
  transform: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  wait: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700' },
};

export default function WorkflowVisualizer({
  steps,
  currentStep,
  executionStatus,
}: WorkflowVisualizerProps) {
  const nodes = useMemo(() => {
    return steps.map((step, index) => {
      const colors = STEP_COLORS[step.type] || STEP_COLORS.agent;
      const isActive = currentStep === index;
      const isCompleted = currentStep !== undefined && index < currentStep;
      const isFailed = executionStatus === 'failed' && currentStep === index;

      return {
        ...step,
        index,
        colors,
        isActive,
        isCompleted,
        isFailed,
        icon: STEP_ICONS[step.type] || '📦',
      };
    });
  }, [steps, currentStep, executionStatus]);

  if (steps.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
        <div className="text-center">
          <div className="text-4xl mb-2">🔧</div>
          <p className="text-gray-500">Add steps to see the workflow visualization</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 rounded-lg p-6 overflow-x-auto">
      <div className="flex items-center justify-center min-w-max">
        {/* Start Node */}
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-green-100 border-2 border-green-300 flex items-center justify-center">
            <span className="text-xl">▶️</span>
          </div>
          <span className="text-xs text-gray-500 mt-1">Start</span>
        </div>

        {/* Steps */}
        {nodes.map((node, index) => (
          <div key={node.id} className="flex items-center">
            {/* Connector */}
            <div className="flex items-center">
              <div
                className={`w-12 h-1 ${
                  node.isCompleted ? 'bg-green-400' : node.isActive ? 'bg-blue-400' : 'bg-gray-300'
                }`}
              />
              <div
                className={`w-3 h-3 rotate-45 -ml-1.5 ${
                  node.isCompleted ? 'bg-green-400' : node.isActive ? 'bg-blue-400' : 'bg-gray-300'
                }`}
              />
            </div>

            {/* Step Node */}
            <div className="flex flex-col items-center mx-2">
              <div
                className={`
                  relative w-32 p-3 rounded-lg border-2 transition-all
                  ${node.colors.bg} ${node.colors.border}
                  ${node.isActive ? 'ring-2 ring-blue-400 ring-offset-2' : ''}
                  ${node.isCompleted ? 'ring-2 ring-green-400 ring-offset-2' : ''}
                  ${node.isFailed ? 'ring-2 ring-red-400 ring-offset-2' : ''}
                `}
              >
                {/* Status indicator */}
                {(node.isActive || node.isCompleted || node.isFailed) && (
                  <div className="absolute -top-2 -right-2">
                    {node.isActive && (
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 text-white text-xs animate-pulse">
                        ⏳
                      </span>
                    )}
                    {node.isCompleted && (
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-500 text-white text-xs">
                        ✓
                      </span>
                    )}
                    {node.isFailed && (
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-white text-xs">
                        ✕
                      </span>
                    )}
                  </div>
                )}

                <div className="text-center">
                  <span className="text-xl">{node.icon}</span>
                  <p className={`text-xs font-medium ${node.colors.text} mt-1 truncate`}>
                    {node.name || `Step ${index + 1}`}
                  </p>
                  <p className="text-xs text-gray-400 capitalize">{node.type}</p>
                </div>
              </div>

              {/* Step number */}
              <span className="text-xs text-gray-400 mt-1">#{index + 1}</span>
            </div>
          </div>
        ))}

        {/* End connector */}
        <div className="flex items-center">
          <div
            className={`w-12 h-1 ${
              executionStatus === 'completed' ? 'bg-green-400' : 'bg-gray-300'
            }`}
          />
          <div
            className={`w-3 h-3 rotate-45 -ml-1.5 ${
              executionStatus === 'completed' ? 'bg-green-400' : 'bg-gray-300'
            }`}
          />
        </div>

        {/* End Node */}
        <div className="flex flex-col items-center">
          <div
            className={`w-12 h-12 rounded-full flex items-center justify-center border-2 ${
              executionStatus === 'completed'
                ? 'bg-green-100 border-green-300'
                : executionStatus === 'failed'
                ? 'bg-red-100 border-red-300'
                : 'bg-gray-100 border-gray-300'
            }`}
          >
            <span className="text-xl">
              {executionStatus === 'completed' ? '✅' : executionStatus === 'failed' ? '❌' : '🏁'}
            </span>
          </div>
          <span className="text-xs text-gray-500 mt-1">End</span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-4 mt-6 pt-4 border-t border-gray-200">
        {Object.entries(STEP_COLORS).map(([type, colors]) => (
          <div key={type} className="flex items-center gap-1">
            <span className="text-sm">{STEP_ICONS[type as StepType]}</span>
            <span className={`text-xs ${colors.text} capitalize`}>{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
