# DevOps Hub

**Unified Agent Operations Platform** - Central hub for agent registration, discovery, validation, and orchestration.

---

## 🚀 For AI Agents & New Developers - START HERE

**📖 READ FIRST:** [`CODEBASE_ASSESSMENT.md`](./CODEBASE_ASSESSMENT.md)

This comprehensive assessment document contains:
- Complete architecture overview (backend + frontend)
- Technology stack and component deep dive
- Current capabilities (13 agents, 30+ API endpoints, 5 workflows)
- Production readiness status (95% ready)
- Development workflow and best practices
- Recommended next steps

**All AI assistants, developers, and contributors should read this file at the start of each session.**

---

## Overview

DevOps Hub consolidates the agent management ecosystem into a single solution:

- **Agent Factory** - Registration, validation, lifecycle management
- **Agent Registry** - Discovery, indexing, metadata management
- **REST API Service** - HTTP endpoints for agent operations
- **Workflow Engine** - Multi-agent workflow orchestration
- **Human-in-the-Loop (HITL)** - UI for agents to request human assistance
- **Python SDK** - Sync and async clients for integration
- **SQLite Persistence** - Durable storage for registry and events
- **API Key Authentication** - Secure access with scoped permissions

### 🤝 Human-in-the-Loop System

The HITL system enables AI agents to request human assistance for tasks they cannot perform autonomously:
- API keys and credentials
- Account registrations
- Legal document reviews
- Payment authorizations
- Business setup (LLC, tax registration)
- Strategic decisions

**📖 Full documentation:** [`HITL_IMPLEMENTATION_SUMMARY.md`](./HITL_IMPLEMENTATION_SUMMARY.md)

**Access the UI:** http://localhost:3000/human-actions (after starting the frontend)

## Quick Start

### Start the Agent Library Service

```bash
cd devops-hub
pip install -r requirements.txt
python -m uvicorn service.api:app --host 0.0.0.0 --port 8100 --reload
```

On first start, a bootstrap admin API key will be generated and printed to the console. **Save this key securely.**

### Test the Service

```bash
# Health check
curl http://localhost:8100/health

# List all agents
curl http://localhost:8100/agents

# Discover system agents
curl "http://localhost:8100/agents/discover?domain=system"

# Get statistics
curl http://localhost:8100/statistics

# Execute an agent
curl -X POST http://localhost:8100/agents/research-analyzer/execute \
  -H "Content-Type: application/json" \
  -d '{"capability": "market-analysis", "input_data": {"market": "AI"}}'
```

### With Authentication

```bash
# Check your key
curl -H "X-API-Key: dh_your_key_here" http://localhost:8100/auth/me

# Create a new API key (admin only)
curl -X POST http://localhost:8100/auth/keys \
  -H "X-API-Key: dh_admin_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-service", "scopes": ["read", "execute"]}'
```

### Access API Documentation

- Swagger UI: http://localhost:8100/docs
- ReDoc: http://localhost:8100/redoc

## Directory Structure

```
devops-hub/
├── factory/                    # Agent Factory core
│   ├── agent_factory.py       # Central factory hub
│   ├── agent_registry.py      # Discovery & indexing
│   └── agent_validator.py     # 8 principles validation
├── service/                    # REST API
│   ├── api.py                 # FastAPI endpoints
│   ├── agent_loader.py        # Agent lifecycle management
│   ├── workflow_engine.py     # Workflow orchestration
│   └── message_bus.py         # Event pub/sub system
├── core/                       # Core infrastructure
│   ├── database.py            # SQLite persistence layer
│   └── auth.py                # API key authentication
├── sdk/                        # Python SDK client
│   ├── __init__.py
│   └── client.py              # Sync & async clients
├── built_in_agents/           # Agent implementations
│   ├── base.py                # Base agent framework
│   ├── system/                # System agents (4)
│   ├── business/              # Business agents (5)
│   └── utility/               # Utility agents (4)
├── tests/                      # Test suite (169+ tests)
├── data/                       # SQLite database (auto-created)
├── AGENT_REGISTRY.json        # Agent catalog (13 agents)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## API Endpoints

### Agents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | GET | List all agents |
| `/agents/discover` | GET | Discover agents by criteria |
| `/agents/{id}` | GET | Get agent details |
| `/agents/{id}/capabilities` | GET | Get agent capabilities |
| `/agents/{id}/execute` | POST | Execute an agent capability |
| `/agents/{id}/validate` | POST | Validate against 8 principles |

### Workflows

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflows` | GET | List all workflows |
| `/workflows` | POST | Create custom workflow |
| `/workflows/{id}` | GET | Get workflow details |
| `/workflows/{id}/execute` | POST | Execute a workflow |
| `/workflow-executions` | GET | List workflow executions |
| `/workflow-executions/{id}` | GET | Get execution details |

### Events

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events` | GET | Get event history |
| `/events` | POST | Publish custom event |
| `/events/subscriptions` | GET | List event subscriptions |

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/me` | GET | Get current API key info |
| `/auth/keys` | GET | List all API keys (admin) |
| `/auth/keys` | POST | Create new API key (admin) |
| `/auth/keys/{id}` | DELETE | Revoke API key (admin) |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/statistics` | GET | Registry statistics |
| `/capabilities` | GET | List all capabilities |
| `/domains` | GET | List all domains |

## Authentication

DevOps Hub uses API key authentication with scoped permissions.

### Scopes

- `read` - Read access to agents, workflows, events
- `write` - Create/update agents, workflows
- `execute` - Execute agents and workflows
- `admin` - Full access including key management

### Environment Variables

```bash
# Disable authentication (development only)
AUTH_ENABLED=false

# Allow anonymous read access (default: true)
ALLOW_ANONYMOUS_READ=true
```

## Python SDK

### Synchronous Client

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# List agents
agents = client.list_agents()

# Execute agent
result = client.execute_agent(
    "research-analyzer",
    "market-analysis",
    {"market": "AI", "region": "global"}
)
print(result.output)

# Execute workflow
execution = client.execute_workflow("research-report", {"market": "Technology"})
print(execution.results)
```

### Asynchronous Client

```python
from sdk import AsyncAgentServiceClient

async with AsyncAgentServiceClient("http://localhost:8100") as client:
    agents = await client.discover_agents(domain="business")
    result = await client.execute_agent("finance-analyst", "portfolio-analysis", {})
```

## Built-in Workflows

| Workflow | Description |
|----------|-------------|
| `research-report` | Market research with report generation |
| `comprehensive-code-review` | Multi-step code analysis |
| `project-planning` | Task decomposition and planning |
| `content-pipeline` | Content research and creation |
| `data-analysis-pipeline` | Data processing and analysis |

## Registered Agents (13)

### System (4)
- `supervisor-agent` - Orchestration, monitoring, routing
- `router-agent` - Request routing, load balancing
- `registry-agent` - Agent discovery, registration
- `monitor-agent` - Health monitoring, metrics

### Business (5)
- `research-analyzer` - Market analysis, trends
- `data-processor` - ETL, transformation
- `finance-analyst` - Financial analysis
- `project-manager` - Project tracking
- `content-creator` - Content generation

### Utility (4)
- `code-reviewer` - Code analysis, security
- `documentation-generator` - Auto-docs
- `task-decomposer` - Task breakdown
- `error-handler` - Error analysis

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f agent-library

# Stop
docker-compose down
```

## Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Results

```
169+ tests covering:
- Base agent framework
- Agent factory & registry
- REST API endpoints
- Workflow engine
- Message bus
- SDK clients
- Database persistence
- Authentication
```

## Version

- **Version**: 1.1.0
- **Status**: Production Ready
- **Last Updated**: 2026-01-07
