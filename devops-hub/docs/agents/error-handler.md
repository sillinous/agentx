# Error Handler Agent

**Agent ID:** `error-handler`
**Version:** 1.0.0
**Type:** Worker
**Domain:** Utility
**Status:** Production

## Overview

The Error Handler Agent provides comprehensive error analysis, root cause determination, recovery recommendations, escalation routing, and incident tracking. It helps teams respond to and resolve errors efficiently while maintaining a history of incidents for analysis.

This agent is essential for operational reliability, helping teams understand errors, recover from failures, and prevent recurrence.

## Capabilities

### 1. Error Analysis
**Name:** `error-analysis`

Analyze errors and their context to understand what went wrong.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Error type/class |
| `message` | string | Error message |
| `stack_trace` | string | Stack trace (optional) |
| `context` | object | Additional context |

**Returns:** Error classification, severity, and related errors

### 2. Root Cause Analysis
**Name:** `root-cause-analysis`

Determine the root cause of errors and issues.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `error_id` | string | Error ID to analyze |
| `symptoms` | array | Observed symptoms |
| `timeline` | array | Event timeline (optional) |

**Returns:** Root cause with confidence and contributing factors

### 3. Recovery Recommendation
**Name:** `recovery-recommendation`

Recommend actions to recover from errors.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `error_type` | string | Type of error |
| `context` | object | Error context |
| `constraints` | object | Recovery constraints (optional) |

**Returns:** Immediate actions, manual steps, and preventive measures

### 4. Escalation Routing
**Name:** `escalation-routing`

Route issues to appropriate handlers based on severity and type.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `severity` | string | Issue severity: `low`, `medium`, `high`, `critical` |
| `error_type` | string | Type of error |
| `context` | object | Additional context |

**Returns:** Escalation path and tracking ID

### 5. Incident Tracking
**Name:** `incident-tracking`

Track and manage error incidents.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `create`, `update`, `list`, `resolve` |
| `incident_id` | string | Incident ID (for update/resolve) |
| `error_type` | string | Error type (for create) |
| `message` | string | Error message (for create) |
| `severity` | string | Severity (for create) |
| `status` | string | Filter by status (for list) |

**Returns:** Incident details or list

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **ANP (Agent Network Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Analyze Error
```bash
curl -X POST http://localhost:8100/agents/error-handler/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "error-analysis",
    "input_data": {
      "type": "DatabaseError",
      "message": "Connection timeout after 30 seconds",
      "context": {
        "database": "production",
        "query_type": "SELECT"
      }
    }
  }'
```

#### Root Cause Analysis
```bash
curl -X POST http://localhost:8100/agents/error-handler/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "root-cause-analysis",
    "input_data": {
      "error_id": "err-123",
      "symptoms": [
        "High response times",
        "Connection errors",
        "Increased error rate"
      ]
    }
  }'
```

#### Get Recovery Recommendations
```bash
curl -X POST http://localhost:8100/agents/error-handler/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "recovery-recommendation",
    "input_data": {
      "error_type": "OutOfMemoryError",
      "context": {
        "service": "data-processor",
        "memory_usage": "95%"
      }
    }
  }'
```

#### Route Escalation
```bash
curl -X POST http://localhost:8100/agents/error-handler/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "escalation-routing",
    "input_data": {
      "severity": "critical",
      "error_type": "SecurityBreach",
      "context": {
        "affected_systems": ["auth", "user-data"]
      }
    }
  }'
```

#### Create Incident
```bash
curl -X POST http://localhost:8100/agents/error-handler/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "incident-tracking",
    "input_data": {
      "action": "create",
      "error_type": "ServiceOutage",
      "message": "Payment service unavailable",
      "severity": "high"
    }
  }'
```

#### List Open Incidents
```bash
curl -X POST http://localhost:8100/agents/error-handler/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "incident-tracking",
    "input_data": {
      "action": "list",
      "status": "open"
    }
  }'
```

## Python SDK Examples

### Error Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Analyze an error
result = client.execute_agent(
    agent_id="error-handler",
    capability="error-analysis",
    input_data={
        "type": "ValidationError",
        "message": "Invalid email format for user registration",
        "stack_trace": "at validate_email (validators.py:45)\nat register_user (users.py:120)",
        "context": {
            "input_field": "email",
            "input_value": "invalid-email",
            "endpoint": "/api/users/register"
        }
    }
)

if result.success:
    analysis = result.output
    print(f"Error Type: {analysis['error_type']}")
    print(f"Classification: {analysis['classification']}")
    print(f"Severity: {analysis['severity']}")

    print("\nAnalysis:")
    for key, value in analysis['analysis'].items():
        print(f"  {key}: {value}")

    print("\nRelated Errors:")
    for related in analysis['related_errors']:
        print(f"  - {related['type']}: {related['similarity']:.0%} similar")

    print("\nContext Analysis:")
    ctx = analysis['context_analysis']
    print(f"  User Impact: {ctx['user_impact']}")
    print(f"  System Impact: {ctx['system_impact']}")
    print(f"  Data Integrity: {ctx['data_integrity']}")
```

### Root Cause Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Perform root cause analysis
result = client.execute_agent(
    agent_id="error-handler",
    capability="root-cause-analysis",
    input_data={
        "error_id": "err-456",
        "symptoms": [
            "Slow API responses",
            "Database connection pool exhausted",
            "Increased memory usage"
        ],
        "timeline": [
            {"time": "-10min", "event": "Traffic spike began"},
            {"time": "-5min", "event": "Connection pool warnings"},
            {"time": "0", "event": "Service degradation"}
        ]
    }
)

if result.success:
    rca = result.output
    print("Root Cause Analysis:")

    root_cause = rca['root_cause']
    print(f"\nPrimary Cause: {root_cause['primary']}")
    print(f"Confidence: {root_cause['confidence']:.0%}")

    print("\nEvidence:")
    for evidence in root_cause['evidence']:
        print(f"  - {evidence}")

    print("\nContributing Factors:")
    for factor in rca['contributing_factors']:
        print(f"  - {factor['factor']}: {factor['contribution']:.0%} contribution")

    print("\nTimeline:")
    for event in rca['timeline']:
        print(f"  {event['time']}: {event['event']}")

    print(f"\nSimilar Incidents: {rca['similar_incidents']}")
```

### Recovery Recommendations

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Get recovery recommendations
result = client.execute_agent(
    agent_id="error-handler",
    capability="recovery-recommendation",
    input_data={
        "error_type": "DatabaseConnectionError",
        "context": {
            "database": "orders-db",
            "connection_attempts": 5,
            "last_successful": "2 minutes ago"
        },
        "constraints": {
            "downtime_tolerance": "5 minutes",
            "data_loss_tolerance": "none"
        }
    }
)

if result.success:
    recovery = result.output

    print("Recovery Recommendations:")
    print(f"\nRecovery Probability: {recovery['recovery_probability']:.0%}")
    print(f"Estimated Recovery Time: {recovery['estimated_recovery_time']}")

    print("\nImmediate Actions (Automated):")
    for action in recovery['immediate_actions']:
        status = "Auto" if action['automated'] else "Manual"
        print(f"  {action['priority']}. {action['action']} [{status}]")

    print("\nManual Actions:")
    for action in recovery['manual_actions']:
        print(f"  {action['priority']}. {action['action']}")
        print(f"     Owner: {action['owner']}")

    print("\nPreventive Measures:")
    for measure in recovery['preventive_measures']:
        print(f"  - {measure}")
```

### Escalation Routing

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Route escalation
result = client.execute_agent(
    agent_id="error-handler",
    capability="escalation-routing",
    input_data={
        "severity": "high",
        "error_type": "DataCorruption",
        "context": {
            "affected_records": 1500,
            "data_source": "customer-orders"
        }
    }
)

if result.success:
    escalation = result.output

    print("Escalation Details:")
    esc = escalation['escalation']
    print(f"\n  Routed To: {esc['routed_to']}")
    print(f"  Channel: {esc['channel']}")
    print(f"  SLA: {esc['sla']}")
    print(f"  Severity: {esc['severity']}")

    print(f"\nNotification Sent: {escalation['notification_sent']}")
    print(f"Tracking ID: {escalation['tracking_id']}")

    print("\nEscalation Path:")
    for level in escalation['escalation_path']:
        print(f"  Level {level['level']}: {level['team']} (timeout: {level['timeout']})")
```

### Incident Tracking

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Create incident
create_result = client.execute_agent(
    agent_id="error-handler",
    capability="incident-tracking",
    input_data={
        "action": "create",
        "error_type": "ServiceDegradation",
        "message": "API response times exceeded threshold",
        "severity": "medium"
    }
)

if create_result.success:
    incident = create_result.output
    incident_id = incident['incident_id']
    print(f"Incident Created: {incident_id}")
    print(f"Status: {incident['status']}")
    print(f"Severity: {incident['severity']}")

# List open incidents
list_result = client.execute_agent(
    agent_id="error-handler",
    capability="incident-tracking",
    input_data={
        "action": "list",
        "status": "open"
    }
)

if list_result.success:
    incidents = list_result.output
    print(f"\nOpen Incidents: {incidents['open']}")
    print(f"Resolved: {incidents['resolved']}")
    print(f"Total: {incidents['total']}")

    print("\nIncident List:")
    for inc in incidents['incidents']:
        print(f"  [{inc['severity'].upper()}] {inc['id']}: {inc['type']}")
        print(f"    Created: {inc['created_at']}")

# Update incident (resolve)
if create_result.success:
    update_result = client.execute_agent(
        agent_id="error-handler",
        capability="incident-tracking",
        input_data={
            "action": "update",
            "incident_id": incident_id,
            "status": "resolved",
            "root_cause": "Database connection pool size was insufficient"
        }
    )

    if update_result.success:
        print(f"\nIncident {incident_id} resolved")
```

### Complete Error Handling Workflow

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def handle_error(error_type, error_message, context):
    """Complete error handling workflow."""

    results = {}

    # 1. Analyze the error
    analysis = client.execute_agent(
        agent_id="error-handler",
        capability="error-analysis",
        input_data={
            "type": error_type,
            "message": error_message,
            "context": context
        }
    )
    results['analysis'] = analysis.output if analysis.success else None

    if not results['analysis']:
        return results

    severity = results['analysis']['severity']

    # 2. Create incident
    incident = client.execute_agent(
        agent_id="error-handler",
        capability="incident-tracking",
        input_data={
            "action": "create",
            "error_type": error_type,
            "message": error_message,
            "severity": severity
        }
    )
    results['incident'] = incident.output if incident.success else None

    # 3. Get root cause
    rca = client.execute_agent(
        agent_id="error-handler",
        capability="root-cause-analysis",
        input_data={
            "error_id": results['incident']['incident_id'] if results['incident'] else "unknown"
        }
    )
    results['root_cause'] = rca.output if rca.success else None

    # 4. Get recovery recommendations
    recovery = client.execute_agent(
        agent_id="error-handler",
        capability="recovery-recommendation",
        input_data={
            "error_type": error_type,
            "context": context
        }
    )
    results['recovery'] = recovery.output if recovery.success else None

    # 5. Route escalation if high severity
    if severity in ['high', 'critical']:
        escalation = client.execute_agent(
            agent_id="error-handler",
            capability="escalation-routing",
            input_data={
                "severity": severity,
                "error_type": error_type,
                "context": context
            }
        )
        results['escalation'] = escalation.output if escalation.success else None

    return results

# Handle an error
result = handle_error(
    error_type="AuthenticationFailure",
    error_message="Multiple failed login attempts detected",
    context={
        "user_id": "user-123",
        "ip_address": "192.168.1.100",
        "attempts": 10,
        "timeframe": "5 minutes"
    }
)

print("=" * 60)
print("ERROR HANDLING REPORT")
print("=" * 60)

if result['analysis']:
    print(f"\nSeverity: {result['analysis']['severity']}")

if result['incident']:
    print(f"Incident ID: {result['incident']['incident_id']}")

if result['root_cause']:
    print(f"Root Cause: {result['root_cause']['root_cause']['primary']}")

if result['recovery']:
    print(f"Recovery Time: {result['recovery']['estimated_recovery_time']}")
    print(f"Top Action: {result['recovery']['immediate_actions'][0]['action']}")

if result.get('escalation'):
    print(f"Escalated To: {result['escalation']['escalation']['routed_to']}")
```

### Async Error Handling

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def batch_error_analysis(errors):
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Analyze multiple errors in parallel
        tasks = [
            client.execute_agent(
                agent_id="error-handler",
                capability="error-analysis",
                input_data={
                    "type": error['type'],
                    "message": error['message']
                }
            )
            for error in errors
        ]

        results = await asyncio.gather(*tasks)

        print("Error Analysis Summary:")
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for error, result in zip(errors, results):
            if result.success:
                sev = result.output['severity']
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                print(f"  [{sev.upper()}] {error['type']}")

        print(f"\nSeverity Distribution:")
        for sev, count in severity_counts.items():
            if count > 0:
                print(f"  {sev}: {count}")

# Example errors
errors = [
    {"type": "ValidationError", "message": "Invalid input"},
    {"type": "TimeoutError", "message": "Request timeout"},
    {"type": "AuthError", "message": "Invalid token"},
]

asyncio.run(batch_error_analysis(errors))
```

## Configuration Options

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| `critical` | System down, data loss | Immediate |
| `high` | Major functionality impacted | < 1 hour |
| `medium` | Partial functionality impacted | < 4 hours |
| `low` | Minor issues | < 24 hours |

### Escalation Matrix

| Severity | Team | Channel | SLA |
|----------|------|---------|-----|
| Critical | On-Call SRE | PagerDuty | 15 min |
| High | Engineering Lead | Slack | 1 hour |
| Medium | Support Team | Ticket | 4 hours |
| Low | Development | Backlog | 1 week |

### Error Categories

| Category | Examples |
|----------|----------|
| `runtime` | NullPointer, OutOfMemory |
| `validation` | Invalid input, Schema violation |
| `integration` | API timeout, Connection refused |
| `security` | Auth failure, Access denied |
| `data` | Corruption, Inconsistency |

## Best Practices

### 1. Error Analysis
- Include full context
- Capture stack traces
- Log related events
- Track error frequency

### 2. Root Cause Analysis
- Document symptoms clearly
- Build timeline of events
- Consider contributing factors
- Validate hypotheses

### 3. Recovery
- Prioritize automated recovery
- Document manual steps
- Test recovery procedures
- Update runbooks

### 4. Escalation
- Define clear escalation paths
- Set appropriate SLAs
- Track escalation metrics
- Review escalation effectiveness

### 5. Incident Tracking
- Create incidents promptly
- Update status regularly
- Document resolution steps
- Conduct post-mortems

## Related Agents

- **Monitor Agent:** Detect errors proactively
- **Supervisor Agent:** Coordinate recovery
- **Task Decomposer Agent:** Plan remediation

## Troubleshooting

### Common Issues

**Incorrect severity classification:**
- Review error context
- Update classification rules
- Add more context to analysis

**Slow root cause analysis:**
- Provide more symptoms
- Include timeline data
- Check historical incidents

**Escalation not working:**
- Verify team configurations
- Check notification channels
- Review routing rules

## Implementation Reference

**Source:** `built_in_agents/utility/error_handler/agent.py`
