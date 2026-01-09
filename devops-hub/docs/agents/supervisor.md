# Supervisor Agent

**Agent ID:** `supervisor-agent`
**Version:** 1.0.0
**Type:** Supervisor
**Domain:** System
**Status:** Production

## Overview

The Supervisor Agent is the central orchestrator of the DevOps Hub agent ecosystem. It oversees the entire agent network, coordinates complex multi-agent workflows, manages agent lifecycles, and ensures smooth operation across all system components.

As the primary control plane for the ecosystem, the Supervisor Agent maintains awareness of all registered agents, their health status, and current workloads. It serves as the entry point for workflow execution and provides high-level monitoring capabilities.

## Capabilities

### 1. Orchestration
**Name:** `orchestration`

Execute multi-agent workflows with dependency management. The Supervisor creates and manages workflow instances, coordinating execution across multiple agents while handling step sequencing and result aggregation.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow` | object | Workflow definition including name and steps |
| `context` | object | Execution context passed to workflow steps |

**Returns:** Workflow ID and execution status

### 2. Monitoring
**Name:** `monitoring`

Monitor and track agent health across the ecosystem. Provides aggregated health summaries and detailed status for individual agents.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_ids` | array | List of specific agent IDs to monitor (optional) |

**Returns:** Agent status list with health summary

### 3. Routing
**Name:** `routing`

Route tasks to the most appropriate agent based on capability matching and current load. Uses intelligent scoring to select the best available agent.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | object | Task definition to route |
| `requirements` | array | List of required capabilities |

**Returns:** Selected agent ID with confidence score

### 4. Agent Lifecycle Management
**Name:** `agent-lifecycle-management`

Manage agent lifecycle including registration, unregistration, and heartbeat processing. Controls agent states across the ecosystem.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Target agent ID |
| `action` | string | Action to perform: `register`, `unregister`, `heartbeat` |

**Returns:** Success status and new agent state

### 5. Workflow Coordination
**Name:** `workflow-coordination`

Coordinate complex multi-step workflows including listing, status checking, and cancellation.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow_id` | string | Workflow ID to operate on |
| `action` | string | Action: `list`, `status`, `cancel` |

**Returns:** Workflow details or list

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **ANP (Agent Network Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## Performance Specifications

| Metric | Value |
|--------|-------|
| Max Concurrent Requests | 1,000 |
| Average Latency | 100ms |
| Uptime Target | 99.99% |

## API Usage Examples

### Using curl

#### Execute a Workflow
```bash
curl -X POST http://localhost:8100/agents/supervisor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "orchestration",
    "input_data": {
      "workflow": {
        "name": "data-analysis-pipeline",
        "steps": [
          {
            "name": "collect-data",
            "agent": "data-processor",
            "capability": "etl",
            "parameters": {"source": "api"}
          },
          {
            "name": "analyze-data",
            "agent": "research-analyzer",
            "capability": "market-analysis",
            "parameters": {"market": "technology"}
          }
        ]
      },
      "context": {
        "project_id": "proj-123"
      }
    }
  }'
```

#### Monitor Agent Health
```bash
curl -X POST http://localhost:8100/agents/supervisor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "monitoring",
    "input_data": {
      "agent_ids": ["research-analyzer", "data-processor", "finance-analyst"]
    }
  }'
```

#### Get All Agent Status
```bash
curl -X POST http://localhost:8100/agents/supervisor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "monitoring",
    "input_data": {}
  }'
```

#### Route a Task
```bash
curl -X POST http://localhost:8100/agents/supervisor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "routing",
    "input_data": {
      "task": {
        "type": "analysis",
        "description": "Analyze market trends"
      },
      "requirements": ["market-analysis", "report-generation"]
    }
  }'
```

#### Register a New Agent
```bash
curl -X POST http://localhost:8100/agents/supervisor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "agent-lifecycle-management",
    "input_data": {
      "agent_id": "custom-agent-001",
      "action": "register",
      "name": "Custom Agent",
      "capabilities": ["custom-analysis", "data-processing"]
    }
  }'
```

#### Check Workflow Status
```bash
curl -X POST http://localhost:8100/agents/supervisor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "workflow-coordination",
    "input_data": {
      "workflow_id": "wf-abc123",
      "action": "status"
    }
  }'
```

#### List All Workflows
```bash
curl -X POST http://localhost:8100/agents/supervisor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "workflow-coordination",
    "input_data": {
      "action": "list"
    }
  }'
```

## Python SDK Examples

### Basic Usage

```python
from sdk import AgentServiceClient

# Initialize the client
client = AgentServiceClient("http://localhost:8100")

# Execute a simple workflow
result = client.execute_agent(
    agent_id="supervisor-agent",
    capability="orchestration",
    input_data={
        "workflow": {
            "name": "quick-analysis",
            "steps": [
                {
                    "name": "analyze",
                    "agent": "research-analyzer",
                    "capability": "market-analysis",
                    "parameters": {"market": "fintech"}
                }
            ]
        },
        "context": {}
    }
)

print(f"Workflow ID: {result.output['workflow_id']}")
print(f"Status: {result.output['status']}")
```

### Monitoring Agent Health

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Get health status for all agents
health_result = client.execute_agent(
    agent_id="supervisor-agent",
    capability="monitoring",
    input_data={}
)

# Process health data
agents = health_result.output['agents']
summary = health_result.output['summary']

print(f"Total Agents: {summary['total']}")
print(f"Healthy: {summary['healthy']}")
print(f"Unhealthy: {summary['unhealthy']}")

for agent in agents:
    status_icon = "[OK]" if agent['status'] == 'healthy' else "[!!]"
    print(f"  {status_icon} {agent['name']}: {agent['status']}")
```

### Async Client Usage

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def run_workflow():
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Start a workflow
        result = await client.execute_agent(
            agent_id="supervisor-agent",
            capability="orchestration",
            input_data={
                "workflow": {
                    "name": "comprehensive-analysis",
                    "steps": [
                        {
                            "name": "collect",
                            "agent": "data-processor",
                            "capability": "etl"
                        },
                        {
                            "name": "analyze",
                            "agent": "research-analyzer",
                            "capability": "market-analysis"
                        },
                        {
                            "name": "report",
                            "agent": "research-analyzer",
                            "capability": "report-generation"
                        }
                    ]
                },
                "context": {"region": "north-america"}
            }
        )

        workflow_id = result.output['workflow_id']

        # Poll for completion
        while True:
            status = await client.execute_agent(
                agent_id="supervisor-agent",
                capability="workflow-coordination",
                input_data={
                    "workflow_id": workflow_id,
                    "action": "status"
                }
            )

            workflow_status = status.output['workflow']['status']
            if workflow_status in ['completed', 'failed', 'cancelled']:
                break

            await asyncio.sleep(1)

        return status.output['workflow']

# Run the async workflow
workflow_result = asyncio.run(run_workflow())
print(f"Workflow completed with status: {workflow_result['status']}")
```

### Task Routing

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Route a task to the best available agent
routing_result = client.execute_agent(
    agent_id="supervisor-agent",
    capability="routing",
    input_data={
        "task": {
            "type": "code-review",
            "description": "Review pull request #123"
        },
        "requirements": ["code-analysis", "security-scanning"]
    }
)

if routing_result.success:
    selected_agent = routing_result.output['agent_id']
    confidence = routing_result.output['confidence']
    print(f"Task routed to: {selected_agent} (confidence: {confidence:.2%})")
else:
    print("No suitable agent found for task")
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPERVISOR_MAX_WORKFLOWS` | Maximum concurrent workflows | 100 |
| `SUPERVISOR_HEARTBEAT_INTERVAL` | Agent heartbeat check interval (seconds) | 30 |
| `SUPERVISOR_WORKFLOW_TIMEOUT` | Default workflow timeout (seconds) | 3600 |
| `SUPERVISOR_LOG_LEVEL` | Logging level | INFO |

### Workflow Configuration

```python
workflow_config = {
    "name": "my-workflow",
    "steps": [
        {
            "name": "step-1",
            "agent": "agent-id",
            "capability": "capability-name",
            "parameters": {},
            "timeout": 300,  # Step-specific timeout
            "retry": {
                "max_attempts": 3,
                "backoff": "exponential"
            }
        }
    ],
    "on_failure": "stop",  # or "continue", "rollback"
    "notifications": {
        "on_complete": ["webhook-url"],
        "on_failure": ["webhook-url"]
    }
}
```

## Best Practices

### 1. Workflow Design
- Keep workflows focused on a single business objective
- Use meaningful step names for easier debugging
- Include appropriate context in workflow execution
- Set realistic timeouts for long-running workflows

### 2. Agent Registration
- Register agents with complete capability lists
- Implement heartbeat mechanisms for health tracking
- Use descriptive agent names and IDs
- Include version information for compatibility tracking

### 3. Monitoring
- Regularly poll agent health status
- Set up alerts for unhealthy agent counts
- Monitor workflow completion rates
- Track routing efficiency metrics

### 4. Error Handling
- Implement retry logic for transient failures
- Use the workflow `on_failure` configuration
- Monitor failed workflow counts
- Review workflow error logs regularly

### 5. Performance
- Batch related operations when possible
- Use async client for high-throughput scenarios
- Monitor supervisor latency metrics
- Scale horizontally for high agent counts

## Related Agents

- **Router Agent:** Handles detailed request routing logic
- **Registry Agent:** Manages agent discovery and registration
- **Monitor Agent:** Provides detailed monitoring and alerting

## Troubleshooting

### Common Issues

**Workflow stuck in "running" state:**
- Check if target agents are healthy
- Verify network connectivity between agents
- Review step timeout configurations

**Agent not receiving tasks:**
- Verify agent registration status
- Check capability matching
- Ensure heartbeat is being sent

**High latency on orchestration:**
- Monitor concurrent workflow count
- Check target agent response times
- Review workflow step dependencies

## Implementation Reference

**Source:** `built_in_agents/system/supervisor/agent.py`
