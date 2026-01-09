# Monitor Agent

**Agent ID:** `monitor-agent`
**Version:** 1.0.0
**Type:** Analyst
**Domain:** System
**Status:** Production

## Overview

The Monitor Agent provides comprehensive monitoring for the entire agent ecosystem. It tracks agent health, collects and aggregates metrics, monitors performance over time, generates alerts, and provides system-wide observability dashboards.

This agent is essential for maintaining operational visibility across all agents, enabling proactive issue detection and performance optimization.

## Capabilities

### 1. Health Monitoring
**Name:** `health-monitoring`

Monitor and report agent health status across the ecosystem.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `status`, `check`, `history` |
| `agent_ids` | array | Specific agents to monitor (optional) |
| `agent_id` | string | Single agent for history action |

**Returns:** Agent health status with summary statistics

### 2. Metrics Collection
**Name:** `metrics-collection`

Collect, record, and query metrics from agents.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `record`, `query`, `aggregate` |
| `metric` | string | Metric name |
| `value` | number | Metric value (for record) |
| `agent_id` | string | Agent ID for the metric |
| `tags` | object | Additional tags |
| `aggregation` | string | Aggregation type: `avg`, `sum`, `min`, `max`, `count` |
| `window` | string | Time window: `1m`, `5m`, `15m`, `1h`, `1d` |

**Returns:** Recorded confirmation or query results

### 3. Performance Tracking
**Name:** `performance-tracking`

Track and analyze performance metrics over time.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Specific agent to track (optional for system-wide) |
| `window` | string | Time window for analysis |

**Returns:** Performance statistics including latency percentiles

### 4. Alerting
**Name:** `alerting`

Manage alerts and notifications based on metric thresholds.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `list`, `acknowledge`, `configure` |
| `alert_id` | string | Alert ID (for acknowledge) |
| `severity` | string | Filter by severity |
| `acknowledged` | boolean | Filter by acknowledgment status |
| `rule_name` | string | Alert rule name (for configure) |
| `rule` | object | Alert rule configuration |

**Returns:** Alert list or operation result

### 5. Observability
**Name:** `observability`

System-wide observability dashboard providing aggregated views.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `view` | string | View type: `summary`, `detailed`, `topology` |

**Returns:** Aggregated system health and metrics

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **ANP (Agent Network Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Get Health Status
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "health-monitoring",
    "input_data": {
      "action": "status"
    }
  }'
```

#### Check Specific Agents
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "health-monitoring",
    "input_data": {
      "action": "check",
      "agent_ids": ["research-analyzer", "data-processor", "finance-analyst"]
    }
  }'
```

#### Get Agent History
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "health-monitoring",
    "input_data": {
      "action": "history",
      "agent_id": "research-analyzer"
    }
  }'
```

#### Record a Metric
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "metrics-collection",
    "input_data": {
      "action": "record",
      "metric": "request_latency",
      "value": 125.5,
      "agent_id": "research-analyzer",
      "tags": {
        "capability": "market-analysis",
        "region": "us-east"
      }
    }
  }'
```

#### Query Metrics
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "metrics-collection",
    "input_data": {
      "action": "query",
      "metric": "request_latency",
      "agent_id": "research-analyzer",
      "window": "5m"
    }
  }'
```

#### Aggregate Metrics
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "metrics-collection",
    "input_data": {
      "action": "aggregate",
      "metric": "request_latency",
      "aggregation": "avg",
      "window": "1h"
    }
  }'
```

#### Get Performance Stats
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "performance-tracking",
    "input_data": {
      "agent_id": "data-processor",
      "window": "15m"
    }
  }'
```

#### List Alerts
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "alerting",
    "input_data": {
      "action": "list",
      "severity": "critical",
      "acknowledged": false
    }
  }'
```

#### Acknowledge Alert
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "alerting",
    "input_data": {
      "action": "acknowledge",
      "alert_id": "alert-123"
    }
  }'
```

#### Get Observability Summary
```bash
curl -X POST http://localhost:8100/agents/monitor-agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "observability",
    "input_data": {
      "view": "summary"
    }
  }'
```

## Python SDK Examples

### Health Monitoring

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Get overall health status
result = client.execute_agent(
    agent_id="monitor-agent",
    capability="health-monitoring",
    input_data={
        "action": "status"
    }
)

if result.success:
    summary = result.output['summary']
    print(f"System Health: {summary['health_percentage']:.1f}%")
    print(f"Total Agents: {summary['total']}")
    print(f"Healthy: {summary['healthy']}")
    print(f"Unhealthy: {summary['unhealthy']}")

    print("\nAgent Details:")
    for agent in result.output['agents']:
        uptime = agent['uptime_seconds'] / 3600  # Convert to hours
        print(f"  {agent['agent_id']}: {agent['status']}")
        print(f"    Requests: {agent['request_count']}, Errors: {agent['error_count']}")
        print(f"    Uptime: {uptime:.1f} hours")
```

### Metrics Collection

```python
from sdk import AgentServiceClient
import time

client = AgentServiceClient("http://localhost:8100")

# Record metrics
def record_metric(metric_name, value, agent_id, tags=None):
    result = client.execute_agent(
        agent_id="monitor-agent",
        capability="metrics-collection",
        input_data={
            "action": "record",
            "metric": metric_name,
            "value": value,
            "agent_id": agent_id,
            "tags": tags or {}
        }
    )
    return result.success

# Example: Record request latency
record_metric("request_latency_ms", 150.5, "my-agent", {"endpoint": "/api/analyze"})
record_metric("request_latency_ms", 120.3, "my-agent", {"endpoint": "/api/analyze"})
record_metric("request_latency_ms", 180.1, "my-agent", {"endpoint": "/api/analyze"})

# Query the metrics
result = client.execute_agent(
    agent_id="monitor-agent",
    capability="metrics-collection",
    input_data={
        "action": "query",
        "metric": "request_latency_ms",
        "agent_id": "my-agent",
        "window": "5m"
    }
)

if result.success:
    print(f"Metric: {result.output['metric']}")
    for point in result.output['data']:
        print(f"  {point['timestamp']}: {point['value']}ms")
```

### Performance Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Get detailed performance metrics
result = client.execute_agent(
    agent_id="monitor-agent",
    capability="performance-tracking",
    input_data={
        "agent_id": "research-analyzer",
        "window": "1h"
    }
)

if result.success:
    perf = result.output['performance']
    print(f"Performance for {result.output['agent_id']}:")
    print(f"  Average Response: {perf['avg_response_time_ms']:.2f}ms")
    print(f"  Min Response: {perf['min_response_time_ms']:.2f}ms")
    print(f"  Max Response: {perf['max_response_time_ms']:.2f}ms")
    print(f"  P50 Response: {perf['p50_response_time_ms']:.2f}ms")
    print(f"  P95 Response: {perf['p95_response_time_ms']:.2f}ms")
    print(f"  Request Count: {perf['request_count']}")
    print(f"  Error Rate: {perf['error_rate']:.2%}")
```

### Alert Management

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Configure an alert rule
result = client.execute_agent(
    agent_id="monitor-agent",
    capability="alerting",
    input_data={
        "action": "configure",
        "rule_name": "high_error_rate",
        "rule": {
            "metric": "error_rate",
            "threshold": 0.05,
            "comparison": "greater_than",
            "severity": "critical",
            "window": "5m",
            "notification_channels": ["slack", "pagerduty"]
        }
    }
)

# List unacknowledged critical alerts
result = client.execute_agent(
    agent_id="monitor-agent",
    capability="alerting",
    input_data={
        "action": "list",
        "severity": "critical",
        "acknowledged": False
    }
)

if result.success:
    alerts = result.output['alerts']
    print(f"Critical unacknowledged alerts: {result.output['total']}")

    for alert in alerts:
        print(f"\n  Alert: {alert['id']}")
        print(f"  Agent: {alert['agent_id']}")
        print(f"  Message: {alert['message']}")
        print(f"  Metric: {alert['metric']} = {alert['value']} (threshold: {alert['threshold']})")
        print(f"  Time: {alert['timestamp']}")

        # Acknowledge the alert
        ack_result = client.execute_agent(
            agent_id="monitor-agent",
            capability="alerting",
            input_data={
                "action": "acknowledge",
                "alert_id": alert['id']
            }
        )
        if ack_result.success:
            print(f"  [Acknowledged]")
```

### Observability Dashboard

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Get summary view
result = client.execute_agent(
    agent_id="monitor-agent",
    capability="observability",
    input_data={
        "view": "summary"
    }
)

if result.success:
    data = result.output
    print("=== System Observability Dashboard ===")
    print(f"Timestamp: {data['timestamp']}")

    print("\nAgents:")
    print(f"  Total: {data['agents']['total']}")
    print(f"  Healthy: {data['agents']['healthy']}")
    print(f"  Unhealthy: {data['agents']['unhealthy']}")

    print("\nAlerts:")
    print(f"  Total: {data['alerts']['total']}")
    print(f"  Unacknowledged: {data['alerts']['unacknowledged']}")
    print(f"  Critical: {data['alerts']['critical']}")

    print("\nMetrics:")
    print(f"  Total Tracked: {data['metrics']['total_metrics']}")

# Get detailed view
result = client.execute_agent(
    agent_id="monitor-agent",
    capability="observability",
    input_data={
        "view": "detailed"
    }
)

if result.success:
    print("\n=== Detailed Agent View ===")
    for agent in result.output['agents']:
        print(f"\n{agent['agent_id']}:")
        print(f"  Status: {agent['status']}")
        print(f"  Requests: {agent['request_count']}")
        print(f"  Errors: {agent['error_count']}")
        print(f"  Avg Response: {agent['avg_response_time']:.2f}ms")
```

### Async Monitoring Loop

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def monitoring_loop():
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        while True:
            # Get health status
            health = await client.execute_agent(
                agent_id="monitor-agent",
                capability="health-monitoring",
                input_data={"action": "status"}
            )

            # Check for critical alerts
            alerts = await client.execute_agent(
                agent_id="monitor-agent",
                capability="alerting",
                input_data={
                    "action": "list",
                    "severity": "critical",
                    "acknowledged": False
                }
            )

            # Log status
            if health.success:
                summary = health.output['summary']
                print(f"Health: {summary['healthy']}/{summary['total']} agents healthy")

            if alerts.success and alerts.output['total'] > 0:
                print(f"WARNING: {alerts.output['total']} critical alerts!")

            await asyncio.sleep(30)  # Check every 30 seconds

asyncio.run(monitoring_loop())
```

## Configuration Options

### Alert Rule Configuration

```python
alert_rule = {
    "metric": "error_rate",
    "threshold": 0.05,
    "comparison": "greater_than",  # greater_than, less_than, equals
    "severity": "critical",  # critical, high, medium, low
    "window": "5m",
    "cooldown": "15m",  # Don't re-alert within this period
    "notification_channels": ["slack", "email", "pagerduty"]
}
```

### Metric Retention

| Window | Retention | Resolution |
|--------|-----------|------------|
| 1m - 15m | 24 hours | Full |
| 1h | 7 days | 1 minute |
| 1d | 30 days | 5 minutes |

## Best Practices

### 1. Health Monitoring
- Set up regular health checks (every 30 seconds recommended)
- Define clear health criteria for each agent type
- Implement automatic recovery actions for unhealthy agents
- Track health trends over time

### 2. Metrics Collection
- Use consistent metric naming conventions
- Add relevant tags for filtering and grouping
- Set appropriate retention policies
- Avoid high-cardinality tag values

### 3. Alerting
- Define alert thresholds based on baseline performance
- Use severity levels appropriately
- Implement alert escalation policies
- Avoid alert fatigue with proper cooldowns

### 4. Performance Tracking
- Track percentiles (p50, p95, p99) not just averages
- Monitor error rates alongside latency
- Set up SLO/SLI tracking
- Review performance trends weekly

### 5. Observability
- Create dashboards for different audiences
- Include business metrics alongside technical metrics
- Set up anomaly detection for key metrics
- Document metric meanings and thresholds

## Related Agents

- **Supervisor Agent:** Uses monitoring data for orchestration decisions
- **Error Handler Agent:** Handles issues detected by monitoring
- **Router Agent:** Uses health data for routing decisions

## Troubleshooting

### Common Issues

**High latency in metrics queries:**
- Reduce query time windows
- Add metric aggregation
- Check storage backend performance

**Missing health data:**
- Verify agent heartbeats are being sent
- Check network connectivity
- Review registration status

**Alert storms:**
- Increase alert cooldown periods
- Review threshold settings
- Implement alert grouping

## Implementation Reference

**Source:** `built_in_agents/system/monitor/agent.py`
