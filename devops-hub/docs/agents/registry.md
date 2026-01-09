# Registry Agent

**Agent ID:** `registry-agent`
**Version:** 1.0.0
**Type:** Coordinator
**Domain:** System
**Status:** Production

## Overview

The Registry Agent manages ANP (Agent Network Protocol) discovery and agent registration across the network. It serves as the central directory for all agents in the ecosystem, maintaining detailed agent cards with capabilities, endpoints, and metadata.

The Registry Agent provides comprehensive indexing by capability, domain, and tags, enabling efficient agent discovery. It also manages the network topology, tracking nodes and their interconnections.

## Capabilities

### 1. Agent Registration
**Name:** `agent-registration`

Register, unregister, or refresh agents in the network registry.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action to perform: `register`, `unregister`, `refresh` |
| `agent_card` | object | Agent card data (for registration) |
| `agent_id` | string | Agent ID (for unregister/refresh) |

**Returns:** Registration status with agent ID and expiration time

### 2. Agent Discovery
**Name:** `agent-discovery`

Discover agents matching various search criteria including capability, domain, tags, and protocol support.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `capability` | string | Required capability filter |
| `domain` | string | Domain filter |
| `tags` | array | Tag filters |
| `protocol` | string | Required protocol support |

**Returns:** List of matching agent cards with full details

### 3. Capability Indexing
**Name:** `capability-indexing`

Index and query agent capabilities across the registry.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `list`, `query`, `stats` |
| `capability` | string | Specific capability to query |

**Returns:** Capability index, agent list, or statistics

### 4. Network Topology Management
**Name:** `network-topology-management`

Manage the agent network topology including nodes and connections.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `status`, `add-node`, `remove-node`, `connect` |
| `node` | object | Node data for add operations |
| `source` | string | Source node ID for connections |
| `target` | string | Target node ID for connections |

**Returns:** Topology status or operation result

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **ANP (Agent Network Protocol):** Version 1.0

## Agent Card Structure

```json
{
  "agent_id": "my-agent",
  "name": "My Custom Agent",
  "version": "1.0.0",
  "description": "Agent description",
  "capabilities": ["capability-1", "capability-2"],
  "protocols": ["a2a/1.0", "acp/1.0"],
  "endpoint": "http://localhost:8200",
  "domain": "business",
  "tags": ["analysis", "reporting"],
  "metadata": {
    "author": "Team A",
    "license": "MIT"
  },
  "ttl_seconds": 300
}
```

## API Usage Examples

### Using curl

#### Register an Agent
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "agent-registration",
    "input_data": {
      "action": "register",
      "agent_card": {
        "agent_id": "custom-analyzer",
        "name": "Custom Analyzer Agent",
        "version": "1.0.0",
        "description": "Analyzes custom data formats",
        "capabilities": ["custom-analysis", "data-parsing", "report-generation"],
        "protocols": ["a2a/1.0", "acp/1.0"],
        "endpoint": "http://localhost:8200",
        "domain": "utility",
        "tags": ["analysis", "custom"],
        "ttl_seconds": 600
      }
    }
  }'
```

#### Unregister an Agent
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "agent-registration",
    "input_data": {
      "action": "unregister",
      "agent_id": "custom-analyzer"
    }
  }'
```

#### Refresh Agent Registration
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "agent-registration",
    "input_data": {
      "action": "refresh",
      "agent_id": "custom-analyzer"
    }
  }'
```

#### Discover Agents by Capability
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "agent-discovery",
    "input_data": {
      "capability": "market-analysis"
    }
  }'
```

#### Discover Agents by Domain and Tags
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "agent-discovery",
    "input_data": {
      "domain": "business",
      "tags": ["analysis", "finance"]
    }
  }'
```

#### List All Capabilities
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "capability-indexing",
    "input_data": {
      "action": "list"
    }
  }'
```

#### Get Registry Statistics
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "capability-indexing",
    "input_data": {
      "action": "stats"
    }
  }'
```

#### Get Network Topology
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "network-topology-management",
    "input_data": {
      "action": "status"
    }
  }'
```

#### Add a Network Node
```bash
curl -X POST http://localhost:8100/agents/registry-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "network-topology-management",
    "input_data": {
      "action": "add-node",
      "node": {
        "node_id": "node-east-1",
        "endpoint": "http://east-1.example.com:8100",
        "agents": ["agent-1", "agent-2"]
      }
    }
  }'
```

## Python SDK Examples

### Agent Registration

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Register a new agent
result = client.execute_agent(
    agent_id="registry-agent",
    capability="agent-registration",
    input_data={
        "action": "register",
        "agent_card": {
            "agent_id": "my-custom-agent",
            "name": "My Custom Agent",
            "version": "1.0.0",
            "description": "Handles custom processing tasks",
            "capabilities": ["custom-processing", "data-validation"],
            "protocols": ["a2a/1.0", "acp/1.0"],
            "endpoint": "http://localhost:8300",
            "domain": "utility",
            "tags": ["processing", "validation"],
            "ttl_seconds": 300
        }
    }
)

if result.success:
    print(f"Agent registered: {result.output['agent_id']}")
    print(f"Expires at: {result.output['expires_at']}")
```

### Heartbeat/Refresh Pattern

```python
import time
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

agent_id = "my-custom-agent"

# Registration refresh loop
def maintain_registration():
    while True:
        result = client.execute_agent(
            agent_id="registry-agent",
            capability="agent-registration",
            input_data={
                "action": "refresh",
                "agent_id": agent_id
            }
        )

        if result.success:
            print(f"Registration refreshed for {agent_id}")
        else:
            print(f"Failed to refresh: {result.error}")
            # Re-register if refresh fails
            register_agent()

        # Refresh before TTL expires (e.g., at 80% of TTL)
        time.sleep(240)  # For 300s TTL
```

### Agent Discovery

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Discover agents by multiple criteria
result = client.execute_agent(
    agent_id="registry-agent",
    capability="agent-discovery",
    input_data={
        "capability": "report-generation",
        "domain": "business",
        "tags": ["analysis"]
    }
)

if result.success:
    agents = result.output['agents']
    print(f"Found {result.output['total']} matching agents:")

    for agent in agents:
        print(f"\n  Agent: {agent['name']} ({agent['agent_id']})")
        print(f"  Version: {agent['version']}")
        print(f"  Description: {agent['description']}")
        print(f"  Endpoint: {agent['endpoint']}")
        print(f"  Capabilities: {', '.join(agent['capabilities'])}")
        print(f"  Last seen: {agent['last_seen']}")
```

### Capability Index Management

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# List all capabilities in the registry
result = client.execute_agent(
    agent_id="registry-agent",
    capability="capability-indexing",
    input_data={
        "action": "list"
    }
)

if result.success:
    capabilities = result.output['capabilities']
    print(f"Total capabilities: {result.output['total']}")

    for cap, agents in capabilities.items():
        print(f"\n  {cap}:")
        for agent_id in agents:
            print(f"    - {agent_id}")

# Query specific capability
result = client.execute_agent(
    agent_id="registry-agent",
    capability="capability-indexing",
    input_data={
        "action": "query",
        "capability": "market-analysis"
    }
)

if result.success:
    print(f"\nAgents with 'market-analysis' ({result.output['count']}):")
    for agent in result.output['agents']:
        print(f"  - {agent['name']} at {agent['endpoint']}")
```

### Network Topology Management

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Add nodes
for i, region in enumerate(["east", "west", "central"]):
    client.execute_agent(
        agent_id="registry-agent",
        capability="network-topology-management",
        input_data={
            "action": "add-node",
            "node": {
                "node_id": f"node-{region}",
                "endpoint": f"http://{region}.example.com:8100",
                "agents": []
            }
        }
    )

# Connect nodes
connections = [
    ("node-east", "node-central"),
    ("node-west", "node-central"),
]

for source, target in connections:
    client.execute_agent(
        agent_id="registry-agent",
        capability="network-topology-management",
        input_data={
            "action": "connect",
            "source": source,
            "target": target
        }
    )

# Get topology status
result = client.execute_agent(
    agent_id="registry-agent",
    capability="network-topology-management",
    input_data={
        "action": "status"
    }
)

if result.success:
    print(f"Network has {result.output['total_nodes']} nodes")
    print(f"Total agents: {result.output['total_agents']}")

    for node in result.output['nodes']:
        print(f"\n  Node: {node['node_id']}")
        print(f"  Endpoint: {node['endpoint']}")
        print(f"  Connected to: {', '.join(node['connected_nodes'])}")
```

## Configuration Options

### TTL Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `ttl_seconds` | Time-to-live for registrations | 300 |
| `cleanup_interval` | Interval for expired entry cleanup | 60s |
| `max_ttl` | Maximum allowed TTL | 3600 |

### Index Configuration

```python
registry_config = {
    "capability_index": {
        "enabled": True,
        "rebuild_interval": 300
    },
    "domain_index": {
        "enabled": True
    },
    "tag_index": {
        "enabled": True,
        "max_tags_per_agent": 20
    }
}
```

## Best Practices

### 1. Agent Registration
- Use descriptive, unique agent IDs
- Include comprehensive capability lists
- Set appropriate TTL values based on agent stability
- Include meaningful metadata

### 2. Discovery
- Use the most specific filters possible
- Cache discovery results where appropriate
- Handle empty results gracefully
- Consider capability aliases for flexibility

### 3. TTL Management
- Implement heartbeat patterns for long-running agents
- Set TTL shorter than expected downtime tolerance
- Refresh registrations at 80% of TTL
- Handle refresh failures with re-registration

### 4. Network Topology
- Keep topology information up to date
- Use topology for routing optimization
- Monitor node connectivity
- Plan for node failures

### 5. Performance
- Index frequently queried capabilities
- Use batch registration for multiple agents
- Monitor registry size and cleanup
- Consider sharding for large deployments

## Related Agents

- **Supervisor Agent:** Uses registry for agent coordination
- **Router Agent:** Uses registry for routing decisions
- **Monitor Agent:** Monitors registered agents

## Troubleshooting

### Common Issues

**Agent not found in discovery:**
- Check if registration succeeded
- Verify TTL hasn't expired
- Confirm capability/domain/tag spelling
- Check filter combinations

**Registration rejected:**
- Verify agent card schema
- Check for duplicate agent IDs
- Ensure required fields are present

**Stale entries in registry:**
- Check cleanup job is running
- Verify TTL values are appropriate
- Monitor for failed unregistrations

## Implementation Reference

**Source:** `built_in_agents/system/registry/agent.py`
