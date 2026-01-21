# DevOps Hub TypeScript SDK

Official TypeScript SDK for the DevOps Hub API.

## Installation

```bash
npm install @devops-hub/sdk
# or
yarn add @devops-hub/sdk
# or
pnpm add @devops-hub/sdk
```

## Quick Start

```typescript
import { DevOpsHub } from '@devops-hub/sdk';

const hub = new DevOpsHub({
  baseUrl: 'http://localhost:8100',
  apiKey: 'your-api-key',
});

// List all agents
const agents = await hub.agents.list();
console.log(agents);

// Execute an agent
const result = await hub.agents.execute('analytics-agent', {
  capability: 'calculate_stats',
  input_data: { data: [1, 2, 3, 4, 5] },
});
console.log(result.output);
```

## Configuration

```typescript
interface SDKConfig {
  baseUrl: string;      // Required: API base URL
  apiKey?: string;      // Optional: API key for authentication
  timeout?: number;     // Optional: Request timeout in ms (default: 30000)
  headers?: Record<string, string>; // Optional: Custom headers
}
```

## API Reference

### Agents API

```typescript
// List all agents
const agents = await hub.agents.list();
const productionAgents = await hub.agents.list('production');

// Discover agents with filters
const discovered = await hub.agents.discover({
  domain: 'business',
  capability: 'data-analysis',
  status: 'production',
});

// Get agent details
const agent = await hub.agents.get('analytics-agent');

// Get agent capabilities
const caps = await hub.agents.getCapabilities('analytics-agent');

// Execute an agent capability
const result = await hub.agents.execute('analytics-agent', {
  capability: 'calculate_stats',
  input_data: { data: [1, 2, 3, 4, 5] },
  timeout_seconds: 30,
});

// Validate an agent
const validation = await hub.agents.validate('analytics-agent');

// Get all domains and capabilities
const domains = await hub.agents.getDomains();
const capabilities = await hub.agents.getAllCapabilities();
```

### Workflows API

```typescript
// List all workflows
const workflows = await hub.workflows.list();

// Get workflow details
const workflow = await hub.workflows.get('my-workflow');

// Create a workflow
const newWorkflow = await hub.workflows.create({
  name: 'Data Pipeline',
  description: 'Process and analyze data',
  steps: [
    { name: 'Extract', type: 'agent', agent_id: 'data-processor', capability: 'extract' },
    { name: 'Transform', type: 'agent', agent_id: 'data-processor', capability: 'transform' },
    { name: 'Analyze', type: 'agent', agent_id: 'analytics-agent', capability: 'calculate_stats' },
  ],
});

// Start a workflow
const execution = await hub.workflows.start('my-workflow', {
  initial_context: { source: 'api' },
});

// Get execution status
const status = await hub.workflows.getExecution(execution.id);

// List executions
const executions = await hub.workflows.listExecutions();
const pendingExecutions = await hub.workflows.listExecutions(undefined, 'pending');

// Control execution
await hub.workflows.pauseExecution(execution.id);
await hub.workflows.resumeExecution(execution.id);
await hub.workflows.cancelExecution(execution.id);
```

### System API

```typescript
// Health check
const health = await hub.system.health();
const detailed = await hub.system.healthDetailed();

// Statistics
const stats = await hub.system.statistics();

// Events
const events = await hub.system.getEvents(100, 'agent.executed');
await hub.system.emitEvent({
  type: 'custom.event',
  source: 'my-app',
  data: { key: 'value' },
  correlation_id: null,
  metadata: {},
});

// Version info
const version = await hub.system.version();
```

## Error Handling

```typescript
import { DevOpsHub, DevOpsHubError } from '@devops-hub/sdk';

try {
  const result = await hub.agents.execute('invalid-agent', {
    capability: 'test',
    input_data: {},
  });
} catch (error) {
  if (error instanceof DevOpsHubError) {
    console.error('API Error:', error.message);
    console.error('Status:', error.status);
    console.error('Code:', error.code);
    console.error('Details:', error.details);
  } else {
    throw error;
  }
}
```

## TypeScript Support

Full TypeScript support with exported types:

```typescript
import type {
  AgentSummary,
  AgentDetail,
  ExecutionRequest,
  ExecutionResponse,
  WorkflowExecution,
  HealthResponse,
} from '@devops-hub/sdk';
```

## Browser & Node.js Support

The SDK uses the Fetch API and works in:
- Node.js 18+
- Modern browsers
- Edge runtime
- Deno

## License

MIT
