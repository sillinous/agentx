import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Input, Select, Badge, Spinner } from '../components/ui';
import client from '../api/client';

interface Integration {
  id: string;
  name: string;
  type: string;
  config: Record<string, unknown>;
  is_active: boolean;
  has_credentials: boolean;
  last_used_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

const INTEGRATION_TYPES = [
  { value: 'slack', label: 'Slack', icon: '💬', description: 'Send notifications to Slack channels' },
  { value: 'email', label: 'Email (SMTP)', icon: '📧', description: 'Send email notifications' },
  { value: 'teams', label: 'Microsoft Teams', icon: '👥', description: 'Send notifications to Teams' },
  { value: 'discord', label: 'Discord', icon: '🎮', description: 'Send notifications to Discord' },
  { value: 'webhook', label: 'Webhook', icon: '🔗', description: 'Send to custom webhook URL' },
  { value: 'openai', label: 'OpenAI', icon: '🤖', description: 'OpenAI API for content generation' },
  { value: 'anthropic', label: 'Anthropic', icon: '🧠', description: 'Claude API for AI features' },
];

export default function Integrations() {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [credentialInput, setCredentialInput] = useState<{ id: string; type: string; value: string } | null>(null);

  // Form state
  const [newIntegration, setNewIntegration] = useState({
    name: '',
    type: 'slack',
    config: {} as Record<string, string>,
  });

  // Fetch integrations
  const { data: integrations, isLoading } = useQuery({
    queryKey: ['integrations'],
    queryFn: async () => {
      const { data } = await client.get<Integration[]>('/integrations');
      return data;
    },
  });

  // Create integration
  const createMutation = useMutation({
    mutationFn: async (data: typeof newIntegration) => {
      const { data: result } = await client.post('/integrations', data);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      setShowAddForm(false);
      setNewIntegration({ name: '', type: 'slack', config: {} });
    },
  });

  // Delete integration
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await client.delete(`/integrations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  // Store credential
  const storeCred = useMutation({
    mutationFn: async ({ id, credType, value }: { id: string; credType: string; value: string }) => {
      await client.post(`/integrations/${id}/credentials`, {
        credential_type: credType,
        value,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
      setCredentialInput(null);
    },
  });

  // Test integration
  const testMutation = useMutation({
    mutationFn: async (id: string) => {
      const { data } = await client.post<{ success: boolean; error?: string }>(`/integrations/${id}/test`);
      return data;
    },
    onSuccess: (data) => {
      if (data.success) {
        alert('Test successful!');
      } else {
        alert(`Test failed: ${data.error}`);
      }
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  const getCredentialType = (integrationType: string) => {
    switch (integrationType) {
      case 'slack':
      case 'teams':
      case 'discord':
      case 'webhook':
        return 'webhook_url';
      case 'openai':
      case 'anthropic':
        return 'api_key';
      case 'email':
        return 'smtp_config';
      default:
        return 'api_key';
    }
  };

  const getCredentialLabel = (integrationType: string) => {
    switch (integrationType) {
      case 'slack':
        return 'Slack Webhook URL';
      case 'teams':
        return 'Teams Webhook URL';
      case 'discord':
        return 'Discord Webhook URL';
      case 'webhook':
        return 'Webhook URL';
      case 'openai':
        return 'OpenAI API Key';
      case 'anthropic':
        return 'Anthropic API Key';
      case 'email':
        return 'SMTP Password';
      default:
        return 'API Key';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Integrations</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Connect external services for notifications and AI capabilities
          </p>
        </div>
        <Button onClick={() => setShowAddForm(true)}>
          + Add Integration
        </Button>
      </div>

      {/* Add Integration Form */}
      {showAddForm && (
        <Card>
          <h2 className="text-lg font-semibold mb-4">Add New Integration</h2>
          <div className="space-y-4">
            <Input
              label="Integration Name"
              value={newIntegration.name}
              onChange={(e) => setNewIntegration({ ...newIntegration, name: e.target.value })}
              placeholder="My Slack Workspace"
            />
            <Select
              label="Integration Type"
              value={newIntegration.type}
              onChange={(e) => setNewIntegration({ ...newIntegration, type: e.target.value })}
              options={INTEGRATION_TYPES.map(t => ({ value: t.value, label: `${t.icon} ${t.label}` }))}
            />

            {/* Type-specific config */}
            {newIntegration.type === 'slack' && (
              <Input
                label="Default Channel"
                value={newIntegration.config.default_channel || ''}
                onChange={(e) => setNewIntegration({
                  ...newIntegration,
                  config: { ...newIntegration.config, default_channel: e.target.value }
                })}
                placeholder="#general"
              />
            )}

            {newIntegration.type === 'email' && (
              <>
                <Input
                  label="SMTP Host"
                  value={newIntegration.config.smtp_host || ''}
                  onChange={(e) => setNewIntegration({
                    ...newIntegration,
                    config: { ...newIntegration.config, smtp_host: e.target.value }
                  })}
                  placeholder="smtp.gmail.com"
                />
                <Input
                  label="SMTP Port"
                  type="number"
                  value={newIntegration.config.smtp_port || '587'}
                  onChange={(e) => setNewIntegration({
                    ...newIntegration,
                    config: { ...newIntegration.config, smtp_port: e.target.value }
                  })}
                />
                <Input
                  label="From Address"
                  value={newIntegration.config.from_address || ''}
                  onChange={(e) => setNewIntegration({
                    ...newIntegration,
                    config: { ...newIntegration.config, from_address: e.target.value }
                  })}
                  placeholder="notifications@example.com"
                />
              </>
            )}

            <div className="flex gap-2">
              <Button
                onClick={() => createMutation.mutate(newIntegration)}
                disabled={!newIntegration.name || createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating...' : 'Create Integration'}
              </Button>
              <Button variant="secondary" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Integration List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {integrations?.map((integration) => {
          const typeInfo = INTEGRATION_TYPES.find(t => t.value === integration.type);
          return (
            <Card key={integration.id} className="relative">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{typeInfo?.icon || '🔌'}</div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {integration.name}
                    </h3>
                    <p className="text-sm text-gray-500">{typeInfo?.label || integration.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={integration.is_active ? 'success' : 'default'}>
                    {integration.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  {integration.has_credentials && (
                    <Badge variant="info">Configured</Badge>
                  )}
                </div>
              </div>

              {/* Status */}
              {integration.last_error && (
                <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-600 dark:text-red-400">
                  Last error: {integration.last_error}
                </div>
              )}
              {integration.last_used_at && !integration.last_error && (
                <p className="mt-2 text-xs text-gray-400">
                  Last used: {new Date(integration.last_used_at).toLocaleString()}
                </p>
              )}

              {/* Credential Input */}
              {credentialInput?.id === integration.id ? (
                <div className="mt-4 space-y-2">
                  <Input
                    label={getCredentialLabel(integration.type)}
                    type="password"
                    value={credentialInput.value}
                    onChange={(e) => setCredentialInput({ ...credentialInput, value: e.target.value })}
                    placeholder={integration.type.includes('webhook') ? 'https://...' : 'sk-...'}
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => storeCred.mutate({
                        id: integration.id,
                        credType: getCredentialType(integration.type),
                        value: credentialInput.value,
                      })}
                      disabled={!credentialInput.value || storeCred.isPending}
                    >
                      {storeCred.isPending ? 'Saving...' : 'Save Credential'}
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => setCredentialInput(null)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="mt-4 flex gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setCredentialInput({
                      id: integration.id,
                      type: getCredentialType(integration.type),
                      value: '',
                    })}
                  >
                    {integration.has_credentials ? 'Update Credential' : 'Add Credential'}
                  </Button>
                  {integration.has_credentials && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => testMutation.mutate(integration.id)}
                      disabled={testMutation.isPending}
                    >
                      {testMutation.isPending ? 'Testing...' : 'Test'}
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => {
                      if (confirm('Delete this integration?')) {
                        deleteMutation.mutate(integration.id);
                      }
                    }}
                  >
                    Delete
                  </Button>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Empty State */}
      {(!integrations || integrations.length === 0) && !showAddForm && (
        <Card className="text-center py-12">
          <div className="text-5xl mb-4">🔌</div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">No Integrations</h3>
          <p className="text-gray-500 mt-1 mb-4">
            Connect external services to enable notifications and AI capabilities
          </p>
          <Button onClick={() => setShowAddForm(true)}>
            Add Your First Integration
          </Button>
        </Card>
      )}

      {/* Help Section */}
      <Card>
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3">How to Configure</h3>
        <div className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
          <p><strong>Slack:</strong> Create an <a href="https://api.slack.com/messaging/webhooks" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Incoming Webhook</a> in your Slack workspace and paste the URL.</p>
          <p><strong>Teams:</strong> Add an <a href="https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Incoming Webhook</a> connector to your Teams channel.</p>
          <p><strong>Discord:</strong> Create a <a href="https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Webhook</a> in your Discord server settings.</p>
          <p><strong>OpenAI/Anthropic:</strong> Get your API key from the provider's developer console.</p>
        </div>
      </Card>
    </div>
  );
}
