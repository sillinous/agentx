# Project Manager Agent

**Agent ID:** `project-manager`
**Version:** 1.0.0
**Type:** Coordinator
**Domain:** Business
**Status:** Production

## Overview

The Project Manager Agent handles project tracking, scheduling, resource allocation, progress monitoring, and risk management. It provides comprehensive project management capabilities to coordinate work across teams and track project health.

This agent is essential for managing complex projects, ensuring timely delivery, and maintaining visibility into project status and risks.

## Capabilities

### 1. Project Tracking
**Name:** `project-tracking`

Track project status, milestones, and deliverables.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `create`, `status`, `update`, `list` |
| `project_id` | string | Project ID (for status/update) |
| `name` | string | Project name (for create) |
| `status` | string | New status (for update) |

**Returns:** Project details or project list

### 2. Scheduling
**Name:** `scheduling`

Create and manage project schedules and timelines.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project ID |
| `action` | string | Action: `view`, `update`, `optimize` |
| `milestones` | array | Milestone updates (optional) |

**Returns:** Schedule with milestones and critical path

### 3. Resource Allocation
**Name:** `resource-allocation`

Allocate and manage resources across project tasks.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | Task to allocate resources to |
| `resources` | array | Resources to allocate |
| `action` | string | Action: `allocate`, `view`, `optimize` |

**Returns:** Allocation status with availability and recommendations

### 4. Progress Monitoring
**Name:** `progress-monitoring`

Monitor progress and generate status reports.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project ID (optional for all projects) |
| `include_burndown` | boolean | Include burndown data |
| `include_blockers` | boolean | Include blocker details |

**Returns:** Progress metrics, burndown, and blockers

### 5. Risk Tracking
**Name:** `risk-tracking`

Identify, track, and mitigate project risks.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Project ID |
| `action` | string | Action: `list`, `add`, `update`, `assess` |
| `risk` | object | Risk details (for add/update) |

**Returns:** Risk assessment with mitigations

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Create Project
```bash
curl -X POST http://localhost:8100/agents/project-manager/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "project-tracking",
    "input_data": {
      "action": "create",
      "name": "New Product Launch"
    }
  }'
```

#### Get Project Status
```bash
curl -X POST http://localhost:8100/agents/project-manager/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "project-tracking",
    "input_data": {
      "action": "status",
      "project_id": "proj-123"
    }
  }'
```

#### List All Projects
```bash
curl -X POST http://localhost:8100/agents/project-manager/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "project-tracking",
    "input_data": {
      "action": "list"
    }
  }'
```

#### View Schedule
```bash
curl -X POST http://localhost:8100/agents/project-manager/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "scheduling",
    "input_data": {
      "project_id": "proj-123",
      "action": "view"
    }
  }'
```

#### Allocate Resources
```bash
curl -X POST http://localhost:8100/agents/project-manager/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "resource-allocation",
    "input_data": {
      "task_id": "task-456",
      "resources": [
        {"name": "Developer A", "allocation": "100%"},
        {"name": "Designer B", "allocation": "50%"}
      ]
    }
  }'
```

#### Monitor Progress
```bash
curl -X POST http://localhost:8100/agents/project-manager/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "progress-monitoring",
    "input_data": {
      "project_id": "proj-123",
      "include_burndown": true,
      "include_blockers": true
    }
  }'
```

#### Track Risks
```bash
curl -X POST http://localhost:8100/agents/project-manager/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "risk-tracking",
    "input_data": {
      "project_id": "proj-123"
    }
  }'
```

## Python SDK Examples

### Project Lifecycle Management

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Create a new project
result = client.execute_agent(
    agent_id="project-manager",
    capability="project-tracking",
    input_data={
        "action": "create",
        "name": "Q1 Platform Upgrade"
    }
)

if result.success:
    project = result.output
    project_id = project['project_id']
    print(f"Created project: {project['name']}")
    print(f"Project ID: {project_id}")
    print(f"Status: {project['status']}")

# Get project status
result = client.execute_agent(
    agent_id="project-manager",
    capability="project-tracking",
    input_data={
        "action": "status",
        "project_id": project_id
    }
)

if result.success:
    status = result.output
    print(f"\nProject: {status['name']}")
    print(f"Status: {status['status']}")
    print(f"Progress: {status['progress']:.0%}")
    print(f"Tasks: {status['task_count']}")
```

### Schedule Management

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# View project schedule
result = client.execute_agent(
    agent_id="project-manager",
    capability="scheduling",
    input_data={
        "project_id": "proj-123",
        "action": "view"
    }
)

if result.success:
    schedule = result.output
    print(f"Project On Track: {schedule['on_track']}")
    print(f"Buffer Days: {schedule['buffer_days']}")

    print("\nMilestones:")
    for milestone in schedule['milestones']:
        status_icon = "[x]" if milestone['status'] == 'completed' else "[ ]"
        print(f"  {status_icon} {milestone['name']}: {milestone['date']} ({milestone['status']})")

    print("\nCritical Path:")
    print(f"  {' -> '.join(schedule['critical_path'])}")
```

### Resource Allocation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Allocate resources to a task
result = client.execute_agent(
    agent_id="project-manager",
    capability="resource-allocation",
    input_data={
        "task_id": "task-frontend-dev",
        "resources": [
            {"name": "Alice", "allocation": "100%", "role": "Lead"},
            {"name": "Bob", "allocation": "50%", "role": "Support"}
        ]
    }
)

if result.success:
    allocation = result.output
    print(f"Task: {allocation['task_id']}")
    print(f"Allocated: {allocation['allocated']}")

    print("\nResources:")
    for resource in allocation['resources']:
        print(f"  - {resource['name']}: {resource['allocation']} ({resource['role']})")

    print("\nAvailability:")
    for name, status in allocation['availability'].items():
        print(f"  - {name}: {status}")

    print("\nRecommendations:")
    for rec in allocation['recommendations']:
        print(f"  - {rec}")
```

### Progress Monitoring

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Get detailed progress report
result = client.execute_agent(
    agent_id="project-manager",
    capability="progress-monitoring",
    input_data={
        "project_id": "proj-123",
        "include_burndown": True,
        "include_blockers": True
    }
)

if result.success:
    progress = result.output
    print(f"Overall Progress: {progress['overall_progress']:.0%}")
    print(f"Status: {progress['status']}")

    metrics = progress['metrics']
    print(f"\nTask Metrics:")
    print(f"  Completed: {metrics['tasks_completed']}")
    print(f"  Remaining: {metrics['tasks_remaining']}")
    print(f"  Overdue: {metrics['tasks_overdue']}")
    print(f"  Velocity: {metrics['velocity']}")

    print("\nBurndown:")
    for point in progress['burndown']:
        bar = "#" * int(point['remaining'] / 2)
        print(f"  Week {point['week']}: {bar} ({point['remaining']})")

    if progress['blockers']:
        print("\nBlockers:")
        for blocker in progress['blockers']:
            print(f"  - [{blocker['severity'].upper()}] {blocker['task']}")
            print(f"    Issue: {blocker['blocker']}")
```

### Risk Management

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Assess project risks
result = client.execute_agent(
    agent_id="project-manager",
    capability="risk-tracking",
    input_data={
        "project_id": "proj-123"
    }
)

if result.success:
    risk = result.output
    print(f"Risk Score: {risk['risk_score']:.2f}")
    print(f"Status: {risk['status']}")

    print("\nIdentified Risks:")
    for r in risk['risks']:
        print(f"\n  {r['id']}: {r['description']}")
        print(f"    Probability: {r['probability']:.0%}")
        print(f"    Impact: {r['impact']}")
        print(f"    Mitigation: {r['mitigation']}")

    print(f"\nMitigations in Progress: {risk['mitigations_in_progress']}")
    print(f"Risks Closed: {risk['risks_closed']}")
```

### Complete Project Dashboard

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def project_dashboard(project_id):
    """Generate comprehensive project dashboard."""

    dashboard = {}

    # Get project status
    status = client.execute_agent(
        agent_id="project-manager",
        capability="project-tracking",
        input_data={"action": "status", "project_id": project_id}
    )
    dashboard['status'] = status.output if status.success else None

    # Get schedule
    schedule = client.execute_agent(
        agent_id="project-manager",
        capability="scheduling",
        input_data={"project_id": project_id, "action": "view"}
    )
    dashboard['schedule'] = schedule.output if schedule.success else None

    # Get progress
    progress = client.execute_agent(
        agent_id="project-manager",
        capability="progress-monitoring",
        input_data={
            "project_id": project_id,
            "include_burndown": True,
            "include_blockers": True
        }
    )
    dashboard['progress'] = progress.output if progress.success else None

    # Get risks
    risks = client.execute_agent(
        agent_id="project-manager",
        capability="risk-tracking",
        input_data={"project_id": project_id}
    )
    dashboard['risks'] = risks.output if risks.success else None

    return dashboard

# Generate dashboard
dashboard = project_dashboard("proj-123")

print("=" * 50)
print("PROJECT DASHBOARD")
print("=" * 50)

if dashboard['status']:
    print(f"\nProject: {dashboard['status'].get('name', 'N/A')}")
    print(f"Status: {dashboard['status'].get('status', 'N/A')}")

if dashboard['progress']:
    print(f"Progress: {dashboard['progress']['overall_progress']:.0%}")

if dashboard['schedule']:
    print(f"On Track: {'Yes' if dashboard['schedule']['on_track'] else 'No'}")

if dashboard['risks']:
    print(f"Risk Level: {dashboard['risks']['status']}")

if dashboard['progress'] and dashboard['progress'].get('blockers'):
    print(f"\nActive Blockers: {len(dashboard['progress']['blockers'])}")
```

### Async Project Operations

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def monitor_multiple_projects(project_ids):
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Monitor all projects in parallel
        tasks = [
            client.execute_agent(
                agent_id="project-manager",
                capability="progress-monitoring",
                input_data={"project_id": pid}
            )
            for pid in project_ids
        ]

        results = await asyncio.gather(*tasks)

        print("Project Status Summary:")
        for pid, result in zip(project_ids, results):
            if result.success:
                progress = result.output['overall_progress']
                status = result.output['status']
                print(f"  {pid}: {progress:.0%} - {status}")
            else:
                print(f"  {pid}: ERROR")

asyncio.run(monitor_multiple_projects(["proj-1", "proj-2", "proj-3"]))
```

## Configuration Options

### Project Configuration

```python
project_config = {
    "default_methodology": "agile",  # or "waterfall", "hybrid"
    "sprint_duration_weeks": 2,
    "working_days": ["mon", "tue", "wed", "thu", "fri"],
    "default_task_duration": "1d",
    "auto_schedule": True
}
```

### Risk Matrix

| Probability / Impact | Low | Medium | High |
|---------------------|-----|--------|------|
| High | Medium | High | Critical |
| Medium | Low | Medium | High |
| Low | Low | Low | Medium |

### Status Definitions

| Status | Description |
|--------|-------------|
| `planning` | Project in planning phase |
| `active` | Project actively being worked |
| `on_hold` | Project temporarily paused |
| `at_risk` | Project has significant risks |
| `completed` | Project finished |
| `cancelled` | Project cancelled |

## Best Practices

### 1. Project Tracking
- Keep project status current
- Define clear milestones
- Track dependencies
- Document decisions

### 2. Scheduling
- Build in buffer time
- Identify critical path early
- Review schedules weekly
- Update based on actuals

### 3. Resource Allocation
- Avoid over-allocation
- Plan for availability gaps
- Cross-train team members
- Track utilization

### 4. Progress Monitoring
- Use consistent metrics
- Track velocity trends
- Address blockers quickly
- Communicate status regularly

### 5. Risk Management
- Identify risks early
- Assign risk owners
- Review risks regularly
- Track mitigation effectiveness

## Related Agents

- **Task Decomposer Agent:** Break down project tasks
- **Finance Analyst Agent:** Project financial tracking
- **Content Creator Agent:** Project documentation

## Troubleshooting

### Common Issues

**Project not updating:**
- Check project ID validity
- Verify update permissions
- Review action parameters

**Schedule conflicts:**
- Check resource availability
- Review task dependencies
- Validate milestone dates

**Missing progress data:**
- Ensure tasks are tracked
- Check time entry submissions
- Verify metric calculations

## Implementation Reference

**Source:** `built_in_agents/business/project_manager/agent.py`
