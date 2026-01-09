# Task Decomposer Agent

**Agent ID:** `task-decomposer`
**Version:** 1.0.0
**Type:** Worker
**Domain:** Utility
**Status:** Production

## Overview

The Task Decomposer Agent breaks down complex tasks into manageable subtasks, analyzes dependencies, creates execution plans, prioritizes work, and assesses task-related risks. It is essential for project planning and workflow optimization.

This agent helps teams tackle complex problems by systematically breaking them into smaller, actionable pieces with clear dependencies and priorities.

## Capabilities

### 1. Task Decomposition
**Name:** `task-decomposition`

Break complex tasks into manageable subtasks.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | string | Task description to decompose |
| `depth` | number | Decomposition depth level (1-5) |
| `max_subtasks` | number | Maximum subtasks per level (optional) |
| `context` | object | Additional context (optional) |

**Returns:** Hierarchical task breakdown with effort estimates

### 2. Dependency Analysis
**Name:** `dependency-analysis`

Analyze dependencies between tasks.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `tasks` | array | List of tasks to analyze |
| `include_graph` | boolean | Include dependency graph |

**Returns:** Dependency graph, critical path, and bottlenecks

### 3. Execution Planning
**Name:** `execution-planning`

Create optimal execution plans for task sets.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `tasks` | array | Tasks to plan |
| `strategy` | string | Strategy: `parallel`, `sequential`, `hybrid` |
| `constraints` | object | Resource/time constraints (optional) |

**Returns:** Phased execution plan with optimization notes

### 4. Prioritization
**Name:** `prioritization`

Prioritize tasks by importance and urgency.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `tasks` | array | Tasks to prioritize |
| `criteria` | array | Prioritization criteria |
| `weights` | object | Criteria weights (optional) |

**Returns:** Prioritized task list with scores

### 5. Risk Analysis
**Name:** `risk-analysis`

Analyze risks associated with tasks.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | string | Task to analyze |
| `context` | object | Task context (optional) |
| `categories` | array | Risk categories to assess |

**Returns:** Risk assessment with mitigations

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Decompose Task
```bash
curl -X POST http://localhost:8100/agents/task-decomposer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "task-decomposition",
    "input_data": {
      "task": "Implement user authentication system",
      "depth": 2
    }
  }'
```

#### Analyze Dependencies
```bash
curl -X POST http://localhost:8100/agents/task-decomposer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "dependency-analysis",
    "input_data": {
      "tasks": [
        "Design database schema",
        "Implement API endpoints",
        "Create frontend forms",
        "Write tests"
      ],
      "include_graph": true
    }
  }'
```

#### Create Execution Plan
```bash
curl -X POST http://localhost:8100/agents/task-decomposer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "execution-planning",
    "input_data": {
      "tasks": ["Setup", "Development", "Testing", "Deployment"],
      "strategy": "hybrid"
    }
  }'
```

#### Prioritize Tasks
```bash
curl -X POST http://localhost:8100/agents/task-decomposer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "prioritization",
    "input_data": {
      "tasks": [
        "Fix critical bug",
        "Add new feature",
        "Refactor code",
        "Update documentation"
      ],
      "criteria": ["urgency", "importance", "effort"]
    }
  }'
```

#### Analyze Risks
```bash
curl -X POST http://localhost:8100/agents/task-decomposer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "risk-analysis",
    "input_data": {
      "task": "Migrate to new database",
      "categories": ["technical", "resource", "schedule"]
    }
  }'
```

## Python SDK Examples

### Task Decomposition

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Decompose a complex task
result = client.execute_agent(
    agent_id="task-decomposer",
    capability="task-decomposition",
    input_data={
        "task": "Build and deploy a microservices architecture",
        "depth": 2,
        "context": {
            "team_size": 5,
            "timeline": "3 months"
        }
    }
)

if result.success:
    decomposition = result.output
    print(f"Task ID: {decomposition['task_id']}")
    print(f"Task: {decomposition['name']}")
    print(f"Total Subtasks: {decomposition['total_subtasks']}")
    print(f"Estimated Total Effort: {decomposition['estimated_total_effort']}")

    print("\nBreakdown:")
    for subtask in decomposition['subtasks']:
        print(f"\n  {subtask['id']}: {subtask['name']}")
        print(f"    Effort: {subtask['effort']}")

        if subtask.get('subtasks'):
            for sub in subtask['subtasks']:
                print(f"      - {sub['id']}: {sub['name']} ({sub['effort']})")
```

### Dependency Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Analyze task dependencies
result = client.execute_agent(
    agent_id="task-decomposer",
    capability="dependency-analysis",
    input_data={
        "tasks": [
            "Design API schema",
            "Implement backend services",
            "Create database models",
            "Build frontend components",
            "Integration testing",
            "Deploy to staging"
        ],
        "include_graph": True
    }
)

if result.success:
    analysis = result.output
    graph = analysis['dependency_graph']

    print("Dependency Graph:")
    print(f"  Nodes: {', '.join(graph['nodes'])}")

    print("\nDependencies:")
    for edge in graph['edges']:
        print(f"  {edge['from']} -> {edge['to']} ({edge['type']})")

    print(f"\nCritical Path: {' -> '.join(analysis['critical_path'])}")

    print("\nParallel Groups:")
    for group in analysis['parallel_groups']:
        tasks = ', '.join(group['tasks'])
        print(f"  Phase {group['group']}: {tasks}")

    if analysis['bottlenecks']:
        print(f"\nBottlenecks: {', '.join(analysis['bottlenecks'])}")

    if analysis['circular_dependencies']:
        print(f"\nWARNING: Circular dependencies detected!")
```

### Execution Planning

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Create execution plan
result = client.execute_agent(
    agent_id="task-decomposer",
    capability="execution-planning",
    input_data={
        "tasks": [
            "Requirements gathering",
            "Architecture design",
            "Backend development",
            "Frontend development",
            "Testing",
            "Documentation",
            "Deployment"
        ],
        "strategy": "hybrid",
        "constraints": {
            "max_parallel": 3,
            "deadline": "2026-04-01"
        }
    }
)

if result.success:
    plan = result.output
    print(f"Plan ID: {plan['plan_id']}")
    print(f"Strategy: {plan['strategy']}")
    print(f"Total Phases: {plan['total_phases']}")

    print("\nExecution Phases:")
    for phase in plan['phases']:
        parallel_status = "Parallel" if phase['parallel'] else "Sequential"
        tasks = ', '.join(phase['tasks'])
        print(f"\n  Phase {phase['phase']}: {phase['name']} ({parallel_status})")
        print(f"    Tasks: {tasks}")

    print("\nOptimization Notes:")
    for note in plan['optimization_notes']:
        print(f"  - {note}")
```

### Task Prioritization

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Prioritize tasks
result = client.execute_agent(
    agent_id="task-decomposer",
    capability="prioritization",
    input_data={
        "tasks": [
            "Critical security patch",
            "New user dashboard",
            "Performance optimization",
            "Code documentation",
            "Technical debt cleanup"
        ],
        "criteria": ["urgency", "importance", "effort"],
        "weights": {
            "urgency": 0.4,
            "importance": 0.4,
            "effort": 0.2
        }
    }
)

if result.success:
    prioritization = result.output
    print(f"Criteria Used: {', '.join(prioritization['criteria_used'])}")
    print(f"Scoring Method: {prioritization['scoring_method']}")

    print("\nPrioritized Tasks:")
    for task in prioritization['prioritized_tasks']:
        print(f"\n  #{task['priority']}: {task['task']}")
        print(f"    Score: {task['score']:.2f}")
        print(f"    Reason: {task['reason']}")

    print("\nRecommendations:")
    for rec in prioritization['recommendations']:
        print(f"  - {rec}")
```

### Risk Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Analyze task risks
result = client.execute_agent(
    agent_id="task-decomposer",
    capability="risk-analysis",
    input_data={
        "task": "Migrate legacy system to cloud infrastructure",
        "context": {
            "system_age": "10 years",
            "users": "5000",
            "downtime_tolerance": "minimal"
        },
        "categories": ["technical", "resource", "schedule"]
    }
)

if result.success:
    risk = result.output
    print(f"Overall Risk: {risk['overall_risk']:.2f}")
    print(f"Risk Level: {risk['risk_level']}")

    print("\nIdentified Risks:")
    for r in risk['risks']:
        print(f"\n  Category: {r['category']}")
        print(f"  Description: {r['description']}")
        print(f"  Probability: {r['probability']:.0%}")
        print(f"  Impact: {r['impact']}")
        print(f"  Mitigation: {r['mitigation']}")

    print("\nRisk Matrix:")
    matrix = risk['risk_matrix']
    print(f"  High Prob / High Impact: {matrix['high_probability_high_impact']}")
    print(f"  High Prob / Low Impact: {matrix['high_probability_low_impact']}")
    print(f"  Low Prob / High Impact: {matrix['low_probability_high_impact']}")
    print(f"  Low Prob / Low Impact: {matrix['low_probability_low_impact']}")
```

### Complete Planning Workflow

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def plan_project(project_description):
    """Complete project planning workflow."""

    results = {}

    # 1. Decompose the main task
    decomposition = client.execute_agent(
        agent_id="task-decomposer",
        capability="task-decomposition",
        input_data={
            "task": project_description,
            "depth": 2
        }
    )
    results['decomposition'] = decomposition.output if decomposition.success else None

    if results['decomposition']:
        # Extract task names for further analysis
        tasks = []
        for subtask in results['decomposition']['subtasks']:
            tasks.append(subtask['name'])

        # 2. Analyze dependencies
        dependencies = client.execute_agent(
            agent_id="task-decomposer",
            capability="dependency-analysis",
            input_data={
                "tasks": tasks,
                "include_graph": True
            }
        )
        results['dependencies'] = dependencies.output if dependencies.success else None

        # 3. Create execution plan
        plan = client.execute_agent(
            agent_id="task-decomposer",
            capability="execution-planning",
            input_data={
                "tasks": tasks,
                "strategy": "hybrid"
            }
        )
        results['plan'] = plan.output if plan.success else None

        # 4. Prioritize tasks
        priority = client.execute_agent(
            agent_id="task-decomposer",
            capability="prioritization",
            input_data={
                "tasks": tasks,
                "criteria": ["urgency", "importance", "effort"]
            }
        )
        results['priority'] = priority.output if priority.success else None

        # 5. Risk analysis
        risk = client.execute_agent(
            agent_id="task-decomposer",
            capability="risk-analysis",
            input_data={
                "task": project_description
            }
        )
        results['risk'] = risk.output if risk.success else None

    return results

# Plan a project
project = "Develop a real-time analytics dashboard for IoT devices"
plan = plan_project(project)

print("=" * 60)
print("PROJECT PLAN")
print("=" * 60)

if plan['decomposition']:
    print(f"\nTotal Tasks: {plan['decomposition']['total_subtasks']}")

if plan['dependencies']:
    print(f"Critical Path: {' -> '.join(plan['dependencies']['critical_path'])}")

if plan['plan']:
    print(f"Execution Phases: {plan['plan']['total_phases']}")

if plan['priority']:
    top_task = plan['priority']['prioritized_tasks'][0]
    print(f"Top Priority: {top_task['task']}")

if plan['risk']:
    print(f"Risk Level: {plan['risk']['risk_level']}")
```

### Async Task Operations

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def parallel_decomposition(tasks):
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Decompose multiple tasks in parallel
        decomposition_tasks = [
            client.execute_agent(
                agent_id="task-decomposer",
                capability="task-decomposition",
                input_data={"task": task, "depth": 1}
            )
            for task in tasks
        ]

        results = await asyncio.gather(*decomposition_tasks)

        print("Task Decomposition Summary:")
        total_subtasks = 0
        for task, result in zip(tasks, results):
            if result.success:
                subtasks = result.output['total_subtasks']
                total_subtasks += subtasks
                print(f"  {task}: {subtasks} subtasks")
            else:
                print(f"  {task}: Decomposition failed")

        print(f"\nTotal subtasks across all tasks: {total_subtasks}")

# Example tasks
tasks = [
    "Build authentication system",
    "Create data pipeline",
    "Develop API gateway"
]

asyncio.run(parallel_decomposition(tasks))
```

## Configuration Options

### Decomposition Depth

| Depth | Description |
|-------|-------------|
| 1 | High-level breakdown |
| 2 | Detailed breakdown |
| 3 | Granular breakdown |
| 4-5 | Very detailed |

### Planning Strategies

| Strategy | Description |
|----------|-------------|
| `parallel` | Maximize parallel execution |
| `sequential` | Execute in strict order |
| `hybrid` | Balance parallel and sequential |

### Prioritization Criteria

| Criterion | Description |
|-----------|-------------|
| `urgency` | Time sensitivity |
| `importance` | Business value |
| `effort` | Resource required |
| `risk` | Associated risks |
| `dependencies` | Blocking other tasks |

## Best Practices

### 1. Task Decomposition
- Start at high level, then refine
- Keep subtasks actionable
- Estimate effort for each task
- Review with stakeholders

### 2. Dependency Analysis
- Identify all dependencies early
- Avoid circular dependencies
- Minimize critical path length
- Plan for bottlenecks

### 3. Execution Planning
- Use hybrid strategy for flexibility
- Account for resource constraints
- Build in buffer time
- Review plan regularly

### 4. Prioritization
- Define criteria upfront
- Weight criteria appropriately
- Reprioritize as needed
- Communicate priorities clearly

### 5. Risk Analysis
- Assess risks early
- Plan mitigations proactively
- Monitor risk indicators
- Update as situation changes

## Related Agents

- **Project Manager Agent:** Project execution
- **Supervisor Agent:** Workflow orchestration
- **Error Handler Agent:** Handle planning issues

## Troubleshooting

### Common Issues

**Decomposition too shallow:**
- Increase depth parameter
- Provide more context
- Review task scope

**Circular dependencies:**
- Review task definitions
- Identify true dependencies
- Restructure if needed

**Suboptimal prioritization:**
- Review criteria weights
- Update task information
- Consider additional criteria

## Implementation Reference

**Source:** `built_in_agents/utility/task_decomposer/agent.py`
