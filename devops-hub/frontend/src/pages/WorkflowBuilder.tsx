import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Input, TextArea } from '../components/ui';
import StepEditor from '../components/workflows/StepEditor';
import WorkflowVisualizer from '../components/workflows/WorkflowVisualizer';
import type { WorkflowStep } from '../types';

interface StepWithId extends WorkflowStep {
  id: string;
}

const generateId = () => `step_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

const createEmptyStep = (): StepWithId => ({
  id: generateId(),
  name: '',
  type: 'agent',
  agent_id: null,
  capability: null,
});

export default function WorkflowBuilder() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [steps, setSteps] = useState<StepWithId[]>([createEmptyStep()]);
  const [activeTab, setActiveTab] = useState<'editor' | 'visualizer'>('editor');
  const [isSaving, setIsSaving] = useState(false);

  const addStep = useCallback(() => {
    setSteps((prev) => [...prev, createEmptyStep()]);
  }, []);

  const updateStep = useCallback((index: number, step: StepWithId) => {
    setSteps((prev) => prev.map((s, i) => (i === index ? step : s)));
  }, []);

  const deleteStep = useCallback((index: number) => {
    setSteps((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const moveStep = useCallback((index: number, direction: 'up' | 'down') => {
    setSteps((prev) => {
      const newSteps = [...prev];
      const targetIndex = direction === 'up' ? index - 1 : index + 1;
      if (targetIndex < 0 || targetIndex >= newSteps.length) return prev;
      [newSteps[index], newSteps[targetIndex]] = [newSteps[targetIndex], newSteps[index]];
      return newSteps;
    });
  }, []);

  const handleSave = async () => {
    if (!name.trim()) {
      alert('Please enter a workflow name');
      return;
    }
    if (steps.length === 0) {
      alert('Please add at least one step');
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch('/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description,
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          steps: steps.map(({ id: _id, ...step }) => step),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        navigate(`/workflows/${data.id}`);
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to save workflow');
      }
    } catch {
      alert('Network error. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const isValid = name.trim() && steps.length > 0 && steps.every((s) => s.name.trim());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workflow Builder</h1>
          <p className="text-gray-500 mt-1">Create multi-agent workflows visually</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={() => navigate('/workflows')}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!isValid || isSaving}>
            {isSaving ? 'Saving...' : 'Save Workflow'}
          </Button>
        </div>
      </div>

      {/* Workflow Details */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Workflow Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Workflow Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter workflow name..."
            required
          />
          <div className="md:col-span-2">
            <TextArea
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this workflow does..."
              rows={2}
            />
          </div>
        </div>
      </Card>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200">
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            activeTab === 'editor'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveTab('editor')}
        >
          Step Editor
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            activeTab === 'visualizer'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveTab('visualizer')}
        >
          Visual Flow
        </button>
      </div>

      {/* Content based on tab */}
      {activeTab === 'editor' ? (
        <div className="space-y-4">
          {steps.map((step, index) => (
            <StepEditor
              key={step.id}
              step={step}
              index={index}
              totalSteps={steps.length}
              onChange={(updated) => updateStep(index, updated)}
              onMoveUp={() => moveStep(index, 'up')}
              onMoveDown={() => moveStep(index, 'down')}
              onDelete={() => deleteStep(index)}
            />
          ))}

          <Button variant="secondary" onClick={addStep} className="w-full">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Step
          </Button>
        </div>
      ) : (
        <WorkflowVisualizer steps={steps} />
      )}
    </div>
  );
}
