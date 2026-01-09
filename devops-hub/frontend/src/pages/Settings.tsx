import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button, Card, Input } from '../components/ui';

export default function Settings() {
  const { apiKey, login, logout } = useAuth();
  const [newApiKey, setNewApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const maskedKey = apiKey ? `${apiKey.slice(0, 8)}${'*'.repeat(24)}${apiKey.slice(-4)}` : '';

  const handleUpdateKey = () => {
    if (!newApiKey.trim()) {
      setMessage({ type: 'error', text: 'Please enter a valid API key' });
      return;
    }
    login(newApiKey.trim());
    setNewApiKey('');
    setMessage({ type: 'success', text: 'API key updated successfully' });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleGenerateKey = () => {
    // Generate a random API key (in production, this would call the backend)
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const generatedKey = Array.from({ length: 32 }, () =>
      chars.charAt(Math.floor(Math.random() * chars.length))
    ).join('');
    login(generatedKey);
    setMessage({ type: 'success', text: 'New API key generated and saved' });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleClearKey = () => {
    logout();
    setMessage({ type: 'success', text: 'API key cleared' });
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your API key and system preferences</p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* API Key Management */}
      <Card padding="lg">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">API Key Management</h2>

        {apiKey ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Current API Key</label>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-gray-100 rounded-md text-sm font-mono text-gray-800">
                  {showKey ? apiKey : maskedKey}
                </code>
                <Button variant="ghost" size="sm" onClick={() => setShowKey(!showKey)}>
                  {showKey ? 'Hide' : 'Show'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(apiKey);
                    setMessage({ type: 'success', text: 'API key copied to clipboard' });
                    setTimeout(() => setMessage(null), 2000);
                  }}
                >
                  Copy
                </Button>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Update API Key</label>
              <div className="flex gap-2">
                <Input
                  type="password"
                  value={newApiKey}
                  onChange={(e) => setNewApiKey(e.target.value)}
                  placeholder="Enter new API key"
                  className="flex-1"
                />
                <Button onClick={handleUpdateKey}>Update</Button>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4 flex gap-3">
              <Button variant="secondary" onClick={handleGenerateKey}>
                Generate New Key
              </Button>
              <Button variant="danger" onClick={handleClearKey}>
                Clear Key
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-gray-600">No API key configured. Enter a key or generate a new one.</p>
            <div className="flex gap-2">
              <Input
                type="password"
                value={newApiKey}
                onChange={(e) => setNewApiKey(e.target.value)}
                placeholder="Enter API key"
                className="flex-1"
              />
              <Button onClick={handleUpdateKey}>Save</Button>
            </div>
            <Button variant="secondary" onClick={handleGenerateKey}>
              Generate New Key
            </Button>
          </div>
        )}
      </Card>

      {/* System Preferences */}
      <Card padding="lg">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Preferences</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-gray-900">API Base URL</p>
              <p className="text-sm text-gray-500">Configure the backend API endpoint</p>
            </div>
            <code className="px-3 py-1 bg-gray-100 rounded text-sm">/api</code>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-gray-200">
            <div>
              <p className="font-medium text-gray-900">Cache Duration</p>
              <p className="text-sm text-gray-500">How long to cache API responses</p>
            </div>
            <code className="px-3 py-1 bg-gray-100 rounded text-sm">30 seconds</code>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-gray-200">
            <div>
              <p className="font-medium text-gray-900">Request Timeout</p>
              <p className="text-sm text-gray-500">Maximum wait time for API requests</p>
            </div>
            <code className="px-3 py-1 bg-gray-100 rounded text-sm">30 seconds</code>
          </div>
        </div>
      </Card>

      {/* Danger Zone */}
      <Card padding="lg" className="border-red-200">
        <h2 className="text-lg font-semibold text-red-600 mb-4">Danger Zone</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-900">Clear All Data</p>
            <p className="text-sm text-gray-500">Remove all stored settings and preferences</p>
          </div>
          <Button
            variant="danger"
            onClick={() => {
              localStorage.clear();
              window.location.reload();
            }}
          >
            Clear All Data
          </Button>
        </div>
      </Card>
    </div>
  );
}
