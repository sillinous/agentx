# Agent Documentation

This directory contains detailed documentation for all 13 built-in agents in the DevOps Hub.

## Agent Categories

### System Agents (4)
Core infrastructure agents for platform operations.

| Agent | Description | Status |
|-------|-------------|--------|
| [Supervisor](supervisor.md) | Orchestration & workflow coordination | Production |
| [Router](router.md) | Request routing & load balancing | Production |
| [Registry](registry.md) | Agent discovery & registration | Production |
| [Monitor](monitor.md) | Health monitoring & metrics | Production |

### Business Agents (5)
Domain-specific agents for business operations.

| Agent | Description | Status |
|-------|-------------|--------|
| [Research Analyzer](research.md) | Market analysis & trends | Production |
| [Data Processor](data-processor.md) | ETL & transformation | Production |
| [Finance Analyst](finance.md) | Financial analysis | Production |
| [Project Manager](project-manager.md) | Project tracking | Production |
| [Content Creator](content-creator.md) | Content generation | Production |

### Utility Agents (4)
General-purpose utility agents.

| Agent | Description | Status |
|-------|-------------|--------|
| [Code Reviewer](code-reviewer.md) | Code analysis & security | Production |
| [Documentation Generator](doc-generator.md) | Auto-documentation | Production |
| [Task Decomposer](task-decomposer.md) | Task breakdown & planning | Production |
| [Error Handler](error-handler.md) | Error analysis & recovery | Production |

## Quick Reference

### Discover Agents by Domain
```bash
curl "http://localhost:8100/agents/discover?domain=system"
curl "http://localhost:8100/agents/discover?domain=business"
curl "http://localhost:8100/agents/discover?domain=utility"
```

### Execute an Agent
```bash
curl -X POST "http://localhost:8100/agents/supervisor-agent/execute" \
  -H "Content-Type: application/json" \
  -d '{"capability": "orchestration", "parameters": {"workflow": "my-workflow"}}'
```

### Validate an Agent
```bash
curl -X POST "http://localhost:8100/agents/supervisor-agent/validate"
```

## Protocol Support

All agents support one or more of these protocols:

- **A2A** (Agent-to-Agent) - Direct agent communication
- **ACP** (Agent Communication Protocol) - Standardized messaging
- **ANP** (Agent Network Protocol) - Network discovery
- **MCP** (Model Context Protocol) - LLM integration

## Creating Custom Agents

See the [Agent Development Guide](../guides/agent-development.md) for instructions on creating custom agents.
