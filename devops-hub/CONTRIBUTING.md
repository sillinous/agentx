# Contributing to DevOps Hub

Thank you for your interest in contributing to DevOps Hub! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Docker (optional, for containerized development)
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sillinous/devops-hub.git
   cd devops-hub
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start the backend**
   ```bash
   python -m uvicorn service.api:app --reload --port 8100
   ```

4. **Set up frontend (optional)**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Run tests**
   ```bash
   python -m pytest tests/ -v
   ```

## Project Structure

```
devops-hub/
├── factory/           # Agent factory and registry
├── service/           # FastAPI REST API
├── core/              # Authentication and database
├── sdk/               # Python SDK client
├── built_in_agents/   # 13 built-in agent implementations
├── frontend/          # React TypeScript UI
├── tests/             # Test suite
└── docs/              # Documentation
```

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include steps to reproduce for bugs
- Provide system information (OS, Python version, etc.)

### Pull Requests

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Write tests** for new functionality

4. **Run the test suite** to ensure nothing is broken
   ```bash
   python -m pytest tests/ -v
   ```

5. **Commit with a clear message**
   ```bash
   git commit -m "feat: Add new capability to supervisor agent"
   ```

6. **Push and create a Pull Request**

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Examples:
```
feat(agents): Add sentiment analysis capability to research agent
fix(api): Handle timeout errors in workflow execution
docs: Update README with new installation steps
```

## Code Style

### Python

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for public functions and classes
- Maximum line length: 100 characters

```python
def execute_capability(
    self,
    capability: str,
    parameters: dict[str, Any],
    timeout: float = 30.0
) -> AgentResponse:
    """Execute a specific capability of this agent.

    Args:
        capability: The capability to execute
        parameters: Parameters for the capability
        timeout: Maximum execution time in seconds

    Returns:
        AgentResponse with the execution result

    Raises:
        ValueError: If capability is not supported
    """
    ...
```

### TypeScript/React

- Use functional components with hooks
- Follow the existing Tailwind CSS patterns
- Use TypeScript strict mode
- Export types from dedicated type files

## Creating New Agents

1. **Create agent directory** under `built_in_agents/<domain>/`

2. **Implement the agent class** extending `BaseAgent`:
   ```python
   from built_in_agents.base import BaseAgent, AgentCapability

   class MyAgent(BaseAgent):
       def __init__(self):
           super().__init__(
               agent_id="my-agent",
               name="My Agent",
               description="Does something useful",
               domain="utility",
               agent_type="worker"
           )
           self._register_capabilities()

       def _register_capabilities(self):
           self.register_capability(AgentCapability(
               name="my-capability",
               description="Does the thing",
               parameters={"input": "string"},
               returns="Result of the thing"
           ))

       async def _execute_capability(self, capability, parameters, context):
           if capability == "my-capability":
               return await self._do_thing(parameters)
           raise ValueError(f"Unknown capability: {capability}")
   ```

3. **Register in AGENT_REGISTRY.json**

4. **Add documentation** in `docs/agents/`

5. **Write tests** in `tests/`

## Testing

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_api.py -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use pytest fixtures from `conftest.py`
- Test both success and error cases

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_my_feature(test_client: AsyncClient):
    response = await test_client.get("/my-endpoint")
    assert response.status_code == 200
    assert "expected_key" in response.json()
```

## Documentation

- Update README.md for user-facing changes
- Add agent docs to `docs/agents/` for new agents
- Include code examples in documentation
- Keep API documentation in sync with endpoints

## Security

- Never commit secrets or API keys
- Report security vulnerabilities privately
- Follow OWASP guidelines for web security
- Validate all user inputs

## Questions?

- Open a GitHub Discussion for questions
- Check existing issues before creating new ones
- Join our community channels (if available)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to DevOps Hub!
