# Router Agent

**Agent ID:** `router-agent`
**Version:** 1.0.0
**Type:** Coordinator
**Domain:** System
**Status:** Production

## Overview

The Router Agent is an intelligent request routing system that directs incoming requests to the most appropriate agents based on capability matching, load balancing, and pattern-based rules. It serves as the traffic controller for the agent ecosystem, ensuring requests reach the right destination efficiently.

The Router Agent maintains a capability index and routing table, enabling fast lookups and intelligent agent selection. It supports multiple load balancing strategies and can handle both explicit routing rules and dynamic capability-based routing.

## Capabilities

### 1. Request Routing
**Name:** `request-routing`

Route a request to the most appropriate agent using pattern matching, capability matching, or preferred agent selection.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | object | Request details including path, capability, and domain |
| `preferred_agent` | string | Optional preferred agent ID |

**Returns:** Selected agent ID, endpoint, and routing method used

### 2. Agent Discovery
**Name:** `agent-discovery`

Discover available agents matching specified criteria such as capability or domain.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `capability` | string | Required capability filter |
| `domain` | string | Domain filter (optional) |

**Returns:** List of matching agents with their capabilities and load status

### 3. Load Balancing
**Name:** `load-balancing`

Get a load-balanced agent selection using various strategies.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `capability` | string | Required capability |
| `strategy` | string | Load balancing strategy: `round-robin`, `least-loaded`, `weighted` |

**Returns:** Selected agent ID with current load information

### 4. Capability Matching
**Name:** `capability-matching`

Find agents that match a set of capability requirements.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `capabilities` | array | List of required capabilities |
| `match_mode` | string | Match mode: `all` (must have all) or `any` (must have at least one) |

**Returns:** List of matching agents with match details

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **ANP (Agent Network Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Route a Request
```bash
curl -X POST http://localhost:8100/agents/router-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "request-routing",
    "input_data": {
      "request": {
        "path": "/api/analyze",
        "capability": "market-analysis",
        "domain": "business"
      }
    }
  }'
```

#### Route with Preferred Agent
```bash
curl -X POST http://localhost:8100/agents/router-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "request-routing",
    "input_data": {
      "request": {
        "capability": "code-analysis"
      },
      "preferred_agent": "code-reviewer"
    }
  }'
```

#### Discover Agents by Capability
```bash
curl -X POST http://localhost:8100/agents/router-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "agent-discovery",
    "input_data": {
      "capability": "report-generation"
    }
  }'
```

#### Get Load-Balanced Agent
```bash
curl -X POST http://localhost:8100/agents/router-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "load-balancing",
    "input_data": {
      "capability": "data-transformation",
      "strategy": "least-loaded"
    }
  }'
```

#### Match Multiple Capabilities
```bash
curl -X POST http://localhost:8100/agents/router-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "capability-matching",
    "input_data": {
      "capabilities": ["code-analysis", "security-scanning", "style-checking"],
      "match_mode": "all"
    }
  }'
```

#### Find Agents with Any Matching Capability
```bash
curl -X POST http://localhost:8100/agents/router-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "capability-matching",
    "input_data": {
      "capabilities": ["forecasting", "risk-assessment", "trend-prediction"],
      "match_mode": "any"
    }
  }'
```

## Python SDK Examples

### Basic Routing

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Route a request to the best agent
result = client.execute_agent(
    agent_id="router-agent",
    capability="request-routing",
    input_data={
        "request": {
            "capability": "financial-analysis",
            "domain": "business"
        }
    }
)

if result.success:
    print(f"Routed to: {result.output['agent_id']}")
    print(f"Endpoint: {result.output['endpoint']}")
    print(f"Method: {result.output['method']}")
```

### Load Balancing Strategies

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Use different load balancing strategies
strategies = ["round-robin", "least-loaded", "weighted"]

for strategy in strategies:
    result = client.execute_agent(
        agent_id="router-agent",
        capability="load-balancing",
        input_data={
            "capability": "data-transformation",
            "strategy": strategy
        }
    )

    if result.success:
        print(f"Strategy: {strategy}")
        print(f"  Selected: {result.output['agent_id']}")
        print(f"  Current Load: {result.output['load']}")
        print(f"  Max Load: {result.output['max_load']}")
```

### Agent Discovery

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Discover all agents with a specific capability
result = client.execute_agent(
    agent_id="router-agent",
    capability="agent-discovery",
    input_data={
        "capability": "report-generation"
    }
)

if result.success:
    agents = result.output['agents']
    print(f"Found {result.output['total']} agents with report-generation capability:")

    for agent in agents:
        health = "Healthy" if agent['healthy'] else "Unhealthy"
        load_pct = (agent['load'] / agent['max_load']) * 100
        print(f"  - {agent['agent_id']}: {health}, Load: {load_pct:.1f}%")
        print(f"    Capabilities: {', '.join(agent['capabilities'])}")
```

### Capability Matching

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Find agents that have ALL required capabilities
result = client.execute_agent(
    agent_id="router-agent",
    capability="capability-matching",
    input_data={
        "capabilities": ["market-analysis", "report-generation"],
        "match_mode": "all"
    }
)

if result.success:
    print(f"Agents with ALL capabilities ({result.output['total']} found):")
    for agent in result.output['agents']:
        print(f"  - {agent['agent_id']}")
        print(f"    Matched: {agent['matched_capabilities']}")
        if agent.get('additional_capabilities'):
            print(f"    Additional: {agent['additional_capabilities']}")

# Find agents that have ANY of the capabilities
result = client.execute_agent(
    agent_id="router-agent",
    capability="capability-matching",
    input_data={
        "capabilities": ["financial-analysis", "market-analysis", "code-analysis"],
        "match_mode": "any"
    }
)

if result.success:
    print(f"\nAgents with ANY capability ({result.output['total']} found):")
    for agent in sorted(result.output['agents'], key=lambda x: -x.get('match_ratio', 0)):
        ratio = agent.get('match_ratio', 0) * 100
        print(f"  - {agent['agent_id']}: {ratio:.0f}% match")
        print(f"    Matched: {agent['matched_capabilities']}")
```

### Async Routing

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def route_requests():
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Route multiple requests concurrently
        tasks = [
            client.execute_agent(
                agent_id="router-agent",
                capability="request-routing",
                input_data={"request": {"capability": cap}}
            )
            for cap in ["market-analysis", "code-analysis", "data-transformation"]
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            if result.success:
                print(f"Capability routed to: {result.output['agent_id']}")

asyncio.run(route_requests())
```

## Configuration Options

### Routing Table Configuration

```python
# Add custom routing rules programmatically
router.add_route(
    pattern=r"/api/v1/analyze/.*",
    agent_id="research-analyzer",
    capability="market-analysis",
    priority=10  # Higher priority routes are checked first
)

router.add_route(
    pattern=r"/api/v1/code/.*",
    agent_id="code-reviewer",
    capability="code-analysis",
    priority=10
)
```

### Endpoint Registration

```python
# Register agents for routing
router.register_endpoint(
    agent_id="custom-agent",
    capabilities=["custom-analysis", "data-processing"],
    weight=1.0,  # Weight for weighted load balancing
    max_load=100  # Maximum concurrent requests
)
```

### Load Balancing Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `round-robin` | Cycles through agents sequentially | Even distribution |
| `least-loaded` | Routes to agent with lowest current load | Variable processing times |
| `weighted` | Routes based on capacity and weight | Heterogeneous agent pools |

## Best Practices

### 1. Route Configuration
- Define explicit routes for predictable request patterns
- Use capability-based routing for dynamic scenarios
- Set appropriate priorities for overlapping patterns
- Review route effectiveness regularly

### 2. Load Balancing
- Choose strategy based on workload characteristics
- Use `least-loaded` for CPU-intensive tasks
- Use `weighted` when agents have different capacities
- Monitor load distribution metrics

### 3. Agent Registration
- Register agents with complete capability lists
- Update registrations when capabilities change
- Remove agents before shutdown
- Set realistic max_load values

### 4. Performance
- Use pattern-based routing for high-frequency paths
- Cache routing decisions where appropriate
- Monitor routing latency
- Scale router for high request volumes

### 5. Reliability
- Handle routing failures gracefully
- Implement circuit breakers for unhealthy agents
- Log routing decisions for debugging
- Set up alerts for routing failures

## Related Agents

- **Supervisor Agent:** High-level workflow orchestration
- **Registry Agent:** Agent registration and discovery
- **Monitor Agent:** Health monitoring for routing decisions

## Troubleshooting

### Common Issues

**No route found:**
- Verify agent has required capability registered
- Check if agent is healthy
- Review routing table patterns
- Ensure capability index is up to date

**Uneven load distribution:**
- Verify load reporting is accurate
- Check load balancing strategy
- Review agent weights
- Monitor actual vs. reported load

**Routing to unhealthy agents:**
- Verify health check integration
- Check health status update frequency
- Review circuit breaker configuration

## Implementation Reference

**Source:** `built_in_agents/system/router/agent.py`
