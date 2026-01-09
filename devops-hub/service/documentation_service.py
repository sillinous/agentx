"""
Documentation Service - Auto-generates and manages user guide content.

Provides:
- Auto-generated agent documentation from registry
- User guide content management
- Example generation and management
- Dynamic content updates
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.database import (
    get_documentation_repository,
    get_example_repository,
    DocumentationRepository,
    ExampleRepository,
)
from factory.agent_factory import AgentFactory
from factory.agent_registry import AgentMetadata


class DocumentationService:
    """Service for managing documentation content."""

    def __init__(self, factory: AgentFactory):
        self.factory = factory
        self.docs_repo = get_documentation_repository()
        self.examples_repo = get_example_repository()

    def initialize_default_content(self) -> Dict[str, int]:
        """Initialize default documentation content if not exists."""
        stats = {"guides": 0, "examples": 0}

        # Check if already initialized
        existing = self.docs_repo.list_all()
        if len(existing) > 0:
            return stats

        # Create default guides
        guides = self._get_default_guides()
        for guide in guides:
            self.docs_repo.save(guide)
            stats["guides"] += 1

        # Create default examples
        examples = self._get_default_examples()
        for example in examples:
            self.examples_repo.save(example)
            stats["examples"] += 1

        return stats

    def generate_agent_documentation(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Generate documentation for a specific agent."""
        agent = self.factory.get_agent(agent_id)
        if not agent:
            return None

        return self._generate_agent_guide(agent)

    def generate_all_agent_docs(self) -> List[Dict[str, Any]]:
        """Generate documentation for all registered agents."""
        agents = self.factory.registry.list_all()
        docs = []
        for agent in agents:
            doc = self._generate_agent_guide(agent)
            docs.append(doc)
        return docs

    def get_handbook_structure(self) -> Dict[str, Any]:
        """Get the complete handbook structure with table of contents."""
        guides = self.docs_repo.list_all()
        examples = self.examples_repo.list_all()
        agents = self.factory.registry.list_all()

        # Organize by category
        categories = {}
        for guide in guides:
            cat = guide["category"]
            if cat not in categories:
                categories[cat] = {"guides": [], "examples": []}
            categories[cat]["guides"].append({
                "id": guide["id"],
                "slug": guide["slug"],
                "title": guide["title"],
                "order_index": guide["order_index"],
            })

        for example in examples:
            cat = example["category"]
            if cat not in categories:
                categories[cat] = {"guides": [], "examples": []}
            categories[cat]["examples"].append({
                "id": example["id"],
                "title": example["title"],
                "agent_ids": example["agent_ids"],
            })

        # Sort guides within categories
        for cat in categories.values():
            cat["guides"].sort(key=lambda x: x["order_index"])

        return {
            "categories": categories,
            "agent_count": len(agents),
            "guide_count": len(guides),
            "example_count": len(examples),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _generate_agent_guide(self, agent: AgentMetadata) -> Dict[str, Any]:
        """Generate a guide document for an agent."""
        content = self._format_agent_content(agent)

        return {
            "id": f"agent-{agent.id}",
            "slug": f"agents/{agent.id}",
            "title": agent.name,
            "category": "agents",
            "content": content,
            "order_index": 0,
            "metadata": {
                "agent_id": agent.id,
                "domain": agent.domain.value,
                "type": agent.agent_type.value,
                "auto_generated": True,
            },
        }

    def _format_agent_content(self, agent: AgentMetadata) -> str:
        """Format agent metadata into readable documentation."""
        content = f"""# {agent.name}

## Overview

{agent.description}

**Domain:** {agent.domain.value}
**Type:** {agent.agent_type.value}
**Version:** {agent.version}
**Status:** {agent.status.value}

## Capabilities

This agent provides the following capabilities:

"""
        for cap in agent.capabilities:
            content += f"- **{cap}**: Execute this capability to leverage the agent's {cap} functionality\n"

        content += f"""
## Protocols

Supported communication protocols:

"""
        for protocol in agent.protocols:
            content += f"- `{protocol}`\n"

        content += f"""
## Performance Metrics

| Metric | Value |
|--------|-------|
| Max Concurrent Requests | {agent.performance.max_concurrent_requests} |
| Average Latency | {agent.performance.average_latency_ms}ms |
| Uptime | {agent.performance.uptime_percent}% |

## Usage Example

To execute this agent, send a POST request to `/agents/{agent.id}/execute`:

```json
{{
  "capability": "{agent.capabilities[0] if agent.capabilities else 'example-capability'}",
  "input_data": {{}},
  "timeout_seconds": 300
}}
```

## Integration Tips

1. **Error Handling**: Always check the `status` field in the response
2. **Timeouts**: Adjust `timeout_seconds` based on expected workload
3. **Chaining**: This agent can be combined with others in workflows

"""
        return content

    def _get_default_guides(self) -> List[Dict[str, Any]]:
        """Get default guide content for initialization."""
        return [
            {
                "id": "welcome",
                "slug": "welcome",
                "title": "Welcome to DevOps Hub",
                "category": "getting-started",
                "order_index": 0,
                "content": """# Welcome to DevOps Hub

DevOps Hub is your unified platform for agent operations, providing centralized management for agent discovery, execution, and workflow orchestration.

## What is DevOps Hub?

DevOps Hub consolidates the agent management ecosystem into a single solution:

- **Agent Discovery**: Find and explore available agents by domain, capability, or type
- **Agent Execution**: Execute agent capabilities with custom input data
- **Workflow Orchestration**: Run multi-agent workflows for complex tasks
- **Evaluation System**: Rate and provide feedback on agent performance

## Quick Start

1. **Browse Agents**: Navigate to the Agents page to see all available agents
2. **Execute an Agent**: Click on an agent to view details and execute capabilities
3. **Run Workflows**: Visit Workflows to execute multi-step agent pipelines
4. **Provide Feedback**: Rate your experience to help improve the platform

## Need Help?

- Check the [API Documentation](/api/docs) for technical details
- Browse agent-specific guides in the Agents section
- Review workflow examples for common use cases
""",
            },
            {
                "id": "agent-basics",
                "slug": "agent-basics",
                "title": "Understanding Agents",
                "category": "getting-started",
                "order_index": 1,
                "content": """# Understanding Agents

Agents are specialized AI components that perform specific tasks. Each agent has defined capabilities, input requirements, and output formats.

## Agent Structure

Every agent in DevOps Hub has:

- **ID**: Unique identifier (e.g., `research-analyzer`)
- **Name**: Human-readable name
- **Domain**: Category (system, business, utility)
- **Type**: Role (supervisor, coordinator, worker, analyst)
- **Capabilities**: List of executable functions
- **Protocols**: Supported communication standards

## Agent Domains

### System Agents
Core infrastructure agents that manage the platform:
- Supervisor Agent: Orchestrates other agents
- Router Agent: Handles request routing
- Registry Agent: Manages agent discovery
- Monitor Agent: Tracks health and metrics

### Business Agents
Task-specific agents for business operations:
- Research Analyzer: Market analysis and trends
- Data Processor: ETL and transformation
- Finance Analyst: Financial analysis
- Project Manager: Project tracking
- Content Creator: Content generation

### Utility Agents
Supporting agents for development tasks:
- Code Reviewer: Code analysis
- Documentation Generator: Auto-docs
- Task Decomposer: Task breakdown
- Error Handler: Error analysis

## Agent Types

| Type | Role | Example |
|------|------|---------|
| Supervisor | Orchestrates multiple agents | supervisor-agent |
| Coordinator | Routes and coordinates tasks | router-agent |
| Analyst | Analyzes data and provides insights | research-analyzer |
| Worker | Executes specific tasks | content-creator |

## Executing Agents

To execute an agent:

1. Select the agent from the catalog
2. Choose a capability
3. Provide input data (JSON format)
4. Click Execute
5. Review the results

```json
{
  "capability": "market-analysis",
  "input_data": {
    "market": "technology",
    "region": "global"
  }
}
```
""",
            },
            {
                "id": "workflows-guide",
                "slug": "workflows-guide",
                "title": "Working with Workflows",
                "category": "getting-started",
                "order_index": 2,
                "content": """# Working with Workflows

Workflows allow you to chain multiple agents together to accomplish complex tasks. Each workflow defines a sequence of steps that execute in order.

## Workflow Structure

A workflow consists of:

- **Steps**: Ordered list of agent executions
- **Input Schema**: Expected input format
- **Output Schema**: Result format
- **Context**: Shared data between steps

## Built-in Workflows

### Research & Report Generation
Conducts market research and generates comprehensive reports.

**Steps:**
1. Market Analysis (research-analyzer)
2. Trend Prediction (research-analyzer)
3. Report Generation (content-creator)

### Comprehensive Code Review
Full code analysis with security scanning.

**Steps:**
1. Security Scan (code-reviewer)
2. Style Check (code-reviewer)
3. Performance Analysis (code-reviewer)
4. Generate Recommendations

### Project Planning
Task decomposition and planning.

**Steps:**
1. Task Decomposition (task-decomposer)
2. Dependency Analysis
3. Risk Analysis
4. Create Execution Plan

## Creating Custom Workflows

You can create custom workflows via the API:

```json
{
  "name": "My Custom Workflow",
  "description": "Description of what it does",
  "steps": [
    {
      "name": "Step 1",
      "type": "agent",
      "agent_id": "research-analyzer",
      "capability": "market-analysis"
    },
    {
      "name": "Step 2",
      "type": "agent",
      "agent_id": "content-creator",
      "capability": "content-generation"
    }
  ]
}
```

## Monitoring Execution

When you execute a workflow:

1. The status updates in real-time
2. Each step shows progress
3. Results accumulate as steps complete
4. Errors are captured and reported

## Best Practices

1. **Keep workflows focused**: Each workflow should have a clear purpose
2. **Handle errors**: Check for failures between steps
3. **Test incrementally**: Verify each step before adding more
4. **Document inputs**: Specify required input data clearly
""",
            },
            {
                "id": "api-usage",
                "slug": "api-usage",
                "title": "API Usage Guide",
                "category": "reference",
                "order_index": 0,
                "content": """# API Usage Guide

DevOps Hub provides a RESTful API for programmatic access to all features.

## Base URL

All API endpoints are relative to: `http://localhost:8100`

## Authentication

Most read operations are public. Write and execute operations may require an API key:

```bash
curl -H "X-API-Key: your_key_here" http://localhost:8100/agents
```

## Common Endpoints

### Health Check
```bash
GET /health
```

### List Agents
```bash
GET /agents
GET /agents?status=production
```

### Discover Agents
```bash
GET /agents/discover?domain=business&capability=market-analysis
```

### Get Agent Details
```bash
GET /agents/{agent_id}
```

### Execute Agent
```bash
POST /agents/{agent_id}/execute
Content-Type: application/json

{
  "capability": "market-analysis",
  "input_data": {"market": "AI"},
  "timeout_seconds": 300
}
```

### List Workflows
```bash
GET /workflows
```

### Execute Workflow
```bash
POST /workflows/{workflow_id}/execute
Content-Type: application/json

{
  "market": "technology"
}
```

### Check Execution Status
```bash
GET /workflow-executions/{execution_id}
```

## Response Formats

All responses are JSON. Successful responses include the requested data. Errors include:

```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

Currently no rate limiting is enforced. This may change in future versions.

## SDK Usage

For Python applications, use the built-in SDK:

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# List agents
agents = client.list_agents()

# Execute agent
result = client.execute_agent(
    "research-analyzer",
    "market-analysis",
    {"market": "AI"}
)
print(result.output)
```
""",
            },
            {
                "id": "combining-agents",
                "slug": "combining-agents",
                "title": "Combining Agents",
                "category": "advanced",
                "order_index": 0,
                "content": """# Combining Agents

One of the most powerful features of DevOps Hub is the ability to combine multiple agents to accomplish complex tasks.

## Agent Synergies

### Research + Content Pipeline
Combine research and content creation for comprehensive outputs:

1. **research-analyzer** → Market analysis
2. **data-processor** → Data transformation
3. **content-creator** → Report generation

### Analysis + Documentation
Analyze code and generate documentation:

1. **code-reviewer** → Code analysis
2. **documentation-generator** → Auto-generate docs

### Planning + Execution
Plan and track project work:

1. **task-decomposer** → Break down tasks
2. **project-manager** → Track progress

## Communication Patterns

### Sequential Execution
Each agent runs after the previous completes:
```
Agent A → Agent B → Agent C
```

### Parallel Execution
Multiple agents run simultaneously:
```
        → Agent B →
Agent A              Agent D
        → Agent C →
```

### Conditional Execution
Agents run based on conditions:
```
Agent A → if success → Agent B
        → if error   → Error Handler
```

## Data Flow

Agents share data through the workflow context:

1. **Input Mapping**: Map workflow input to agent input
2. **Output Keys**: Store agent output in context
3. **Context Access**: Subsequent agents access previous results

```json
{
  "steps": [
    {
      "name": "Analyze",
      "agent_id": "research-analyzer",
      "capability": "market-analysis",
      "output_key": "analysis_result"
    },
    {
      "name": "Generate Report",
      "agent_id": "content-creator",
      "capability": "content-generation",
      "input_mapping": {
        "source_data": "analysis_result"
      }
    }
  ]
}
```

## Best Practices

1. **Start Simple**: Begin with 2-3 agents before building complex chains
2. **Validate Outputs**: Check each agent's output before passing to the next
3. **Handle Failures**: Plan for what happens when an agent fails
4. **Monitor Performance**: Track execution times to identify bottlenecks
5. **Document Workflows**: Clearly describe what each combination achieves
""",
            },
        ]

    def _get_default_examples(self) -> List[Dict[str, Any]]:
        """Get default example content for initialization."""
        return [
            {
                "id": "example-market-analysis",
                "title": "Market Analysis",
                "description": "Analyze a specific market segment using the research-analyzer agent",
                "category": "single-agent",
                "agent_ids": ["research-analyzer"],
                "input_example": {
                    "market": "artificial-intelligence",
                    "region": "north-america",
                    "timeframe": "2024-2025"
                },
                "expected_output": "Market analysis report with trends, competitors, and opportunities",
                "tags": ["research", "analysis", "market"],
                "order_index": 0,
            },
            {
                "id": "example-code-review",
                "title": "Code Review",
                "description": "Perform comprehensive code review with security scanning",
                "category": "single-agent",
                "agent_ids": ["code-reviewer"],
                "input_example": {
                    "code_path": "/src/main.py",
                    "review_type": "comprehensive",
                    "include_security": True
                },
                "expected_output": "Code review report with issues, suggestions, and security findings",
                "tags": ["code", "review", "security"],
                "order_index": 1,
            },
            {
                "id": "example-research-report-workflow",
                "title": "Research & Report Workflow",
                "description": "Complete research pipeline from analysis to report generation",
                "category": "workflow",
                "agent_ids": ["research-analyzer", "content-creator"],
                "workflow_id": "research-report",
                "input_example": {
                    "topic": "Cloud Computing Trends",
                    "depth": "comprehensive",
                    "format": "executive-summary"
                },
                "expected_output": "Executive summary report with analysis, trends, and recommendations",
                "tags": ["workflow", "research", "report"],
                "order_index": 0,
            },
            {
                "id": "example-data-pipeline",
                "title": "Data Processing Pipeline",
                "description": "Process and transform data using the data-processor agent",
                "category": "single-agent",
                "agent_ids": ["data-processor"],
                "input_example": {
                    "source": "raw_data.csv",
                    "transformations": ["clean", "normalize", "aggregate"],
                    "output_format": "json"
                },
                "expected_output": "Transformed data in specified format",
                "tags": ["data", "etl", "transformation"],
                "order_index": 2,
            },
            {
                "id": "example-multi-agent-analysis",
                "title": "Multi-Agent Analysis",
                "description": "Combine multiple analysts for comprehensive insights",
                "category": "multi-agent",
                "agent_ids": ["research-analyzer", "finance-analyst", "data-processor"],
                "input_example": {
                    "company": "TechCorp",
                    "analysis_types": ["market", "financial", "operational"],
                    "period": "Q4-2024"
                },
                "expected_output": "Combined analysis report from multiple perspectives",
                "tags": ["multi-agent", "analysis", "comprehensive"],
                "order_index": 0,
            },
        ]


# Global service instance
_docs_service: Optional[DocumentationService] = None


def get_documentation_service(factory: AgentFactory) -> DocumentationService:
    """Get the documentation service instance."""
    global _docs_service
    if _docs_service is None:
        _docs_service = DocumentationService(factory)
    return _docs_service
