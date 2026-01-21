import { useState } from 'react';
import { Card, Button, Input, Select, TextArea, Badge } from '../ui';
import type { AgentDomain, AgentType } from '../../types';

interface AgentCapabilityInput {
  id: string;
  name: string;
  description: string;
  parameters: string;
}

interface AgentBuilderProps {
  onSave?: (agent: AgentDefinition) => void;
  onCancel?: () => void;
}

interface AgentDefinition {
  name: string;
  description: string;
  domain: AgentDomain;
  type: AgentType;
  capabilities: AgentCapabilityInput[];
  protocols: string[];
}

const DOMAIN_OPTIONS = [
  { value: 'system', label: 'System - Core infrastructure' },
  { value: 'business', label: 'Business - Domain operations' },
  { value: 'utility', label: 'Utility - General purpose' },
];

const TYPE_OPTIONS = [
  { value: 'supervisor', label: 'Supervisor - Orchestrates other agents' },
  { value: 'coordinator', label: 'Coordinator - Routes and manages tasks' },
  { value: 'worker', label: 'Worker - Executes specific tasks' },
  { value: 'analyst', label: 'Analyst - Analyzes data and provides insights' },
];

const PROTOCOL_OPTIONS = [
  { value: 'a2a', label: 'A2A - Agent to Agent' },
  { value: 'acp', label: 'ACP - Agent Communication Protocol' },
  { value: 'anp', label: 'ANP - Agent Network Protocol' },
  { value: 'mcp', label: 'MCP - Model Context Protocol' },
];

const generateId = () => `cap_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;

export default function AgentBuilder({ onSave, onCancel }: AgentBuilderProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState<AgentDomain>('utility');
  const [type, setType] = useState<AgentType>('worker');
  const [protocols, setProtocols] = useState<string[]>(['a2a', 'acp']);
  const [capabilities, setCapabilities] = useState<AgentCapabilityInput[]>([
    { id: generateId(), name: '', description: '', parameters: '{}' },
  ]);
  const [activeSection, setActiveSection] = useState<'basic' | 'capabilities' | 'preview'>('basic');

  const addCapability = () => {
    setCapabilities((prev) => [
      ...prev,
      { id: generateId(), name: '', description: '', parameters: '{}' },
    ]);
  };

  const updateCapability = (id: string, field: keyof AgentCapabilityInput, value: string) => {
    setCapabilities((prev) =>
      prev.map((cap) => (cap.id === id ? { ...cap, [field]: value } : cap))
    );
  };

  const removeCapability = (id: string) => {
    setCapabilities((prev) => prev.filter((cap) => cap.id !== id));
  };

  const toggleProtocol = (protocol: string) => {
    setProtocols((prev) =>
      prev.includes(protocol) ? prev.filter((p) => p !== protocol) : [...prev, protocol]
    );
  };

  const handleSave = () => {
    if (!name.trim() || !description.trim() || capabilities.length === 0) {
      alert('Please fill in all required fields');
      return;
    }
    onSave?.({
      name,
      description,
      domain,
      type,
      capabilities,
      protocols,
    });
  };

  const isValid =
    name.trim() &&
    description.trim() &&
    capabilities.length > 0 &&
    capabilities.every((c) => c.name.trim());

  return (
    <div className="space-y-6">
      {/* Section Tabs */}
      <div className="flex border-b border-gray-200">
        {(['basic', 'capabilities', 'preview'] as const).map((section) => (
          <button
            key={section}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px capitalize ${
              activeSection === section
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveSection(section)}
          >
            {section === 'basic' ? 'Basic Info' : section}
          </button>
        ))}
      </div>

      {/* Basic Info Section */}
      {activeSection === 'basic' && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Information</h3>
          <div className="space-y-4">
            <Input
              label="Agent Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Custom Agent"
              required
            />
            <TextArea
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this agent does..."
              rows={3}
              required
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Domain"
                options={DOMAIN_OPTIONS}
                value={domain}
                onChange={(e) => setDomain(e.target.value as AgentDomain)}
              />
              <Select
                label="Type"
                options={TYPE_OPTIONS}
                value={type}
                onChange={(e) => setType(e.target.value as AgentType)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Protocols</label>
              <div className="flex flex-wrap gap-2">
                {PROTOCOL_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggleProtocol(opt.value)}
                    className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                      protocols.includes(opt.value)
                        ? 'bg-blue-100 border-blue-300 text-blue-700'
                        : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Capabilities Section */}
      {activeSection === 'capabilities' && (
        <div className="space-y-4">
          {capabilities.map((cap, index) => (
            <Card key={cap.id}>
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium text-gray-900">Capability {index + 1}</h4>
                {capabilities.length > 1 && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => removeCapability(cap.id)}
                  >
                    Remove
                  </Button>
                )}
              </div>
              <div className="space-y-3">
                <Input
                  label="Name"
                  value={cap.name}
                  onChange={(e) => updateCapability(cap.id, 'name', e.target.value)}
                  placeholder="process_data"
                />
                <Input
                  label="Description"
                  value={cap.description}
                  onChange={(e) => updateCapability(cap.id, 'description', e.target.value)}
                  placeholder="Processes input data and returns results"
                />
                <TextArea
                  label="Parameters (JSON Schema)"
                  value={cap.parameters}
                  onChange={(e) => updateCapability(cap.id, 'parameters', e.target.value)}
                  placeholder='{"input": {"type": "string"}}'
                  rows={3}
                />
              </div>
            </Card>
          ))}
          <Button variant="secondary" onClick={addCapability} className="w-full">
            + Add Capability
          </Button>
        </div>
      )}

      {/* Preview Section */}
      {activeSection === 'preview' && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Preview</h3>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center text-3xl">
                🤖
              </div>
              <div>
                <h4 className="text-xl font-bold text-gray-900">{name || 'Untitled Agent'}</h4>
                <p className="text-gray-500 mt-1">{description || 'No description'}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="purple">{domain}</Badge>
              <Badge variant="info">{type}</Badge>
              {protocols.map((p) => (
                <Badge key={p} variant="default">
                  {p.toUpperCase()}
                </Badge>
              ))}
            </div>
            <div>
              <h5 className="font-medium text-gray-700 mb-2">
                Capabilities ({capabilities.length})
              </h5>
              <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                {capabilities.map((cap) => (
                  <div key={cap.id} className="flex items-center gap-2">
                    <span className="text-green-500">⚡</span>
                    <span className="font-mono text-sm">{cap.name || 'unnamed'}</span>
                    {cap.description && (
                      <span className="text-gray-400 text-sm">- {cap.description}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-3">
        {onCancel && (
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button onClick={handleSave} disabled={!isValid}>
          Create Agent
        </Button>
      </div>
    </div>
  );
}
