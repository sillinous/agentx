# Documentation Generator Agent

**Agent ID:** `documentation-generator`
**Version:** 1.0.0
**Type:** Worker
**Domain:** Utility
**Status:** Production

## Overview

The Documentation Generator Agent automates documentation creation and maintenance. It generates documentation from source code, creates API documentation, builds user guides and tutorials, generates code examples, and maintains existing documentation.

This agent is essential for keeping documentation up-to-date and reducing the manual effort required to document codebases and APIs.

## Capabilities

### 1. Auto-Documentation
**Name:** `auto-documentation`

Generate documentation from source code automatically.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | string | Source code or file path |
| `format` | string | Output format: `markdown`, `html`, `rst` |
| `include_private` | boolean | Include private members |
| `depth` | number | Documentation depth level |

**Returns:** Generated documentation with coverage metrics

### 2. API Doc Generation
**Name:** `api-doc-generation`

Generate comprehensive API documentation.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `spec` | object | API specification (OpenAPI, etc.) |
| `format` | string | Output format: `openapi`, `swagger`, `postman` |
| `include_examples` | boolean | Include request/response examples |

**Returns:** API documentation with endpoints and schemas

### 3. Guide Creation
**Name:** `guide-creation`

Create user guides and tutorials.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `topic` | string | Guide topic |
| `audience` | string | Target audience: `developers`, `users`, `admins` |
| `sections` | array | Specific sections to include (optional) |
| `depth` | string | Detail level: `overview`, `detailed`, `comprehensive` |

**Returns:** Generated guide with sections and metadata

### 4. Example Generation
**Name:** `example-generation`

Generate code examples and snippets.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `topic` | string | Example topic |
| `language` | string | Programming language |
| `complexity` | string | Complexity: `basic`, `intermediate`, `advanced` |
| `count` | number | Number of examples |

**Returns:** Code examples with descriptions

### 5. Doc Maintenance
**Name:** `doc-maintenance`

Update and maintain existing documentation.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `check`, `update`, `sync` |
| `doc_path` | string | Documentation path (optional) |
| `source_path` | string | Source code path (optional) |

**Returns:** Maintenance status and updates

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Generate Documentation
```bash
curl -X POST http://localhost:8100/agents/documentation-generator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "auto-documentation",
    "input_data": {
      "source": "class User:\n    \"\"\"User model.\"\"\"\n    def __init__(self, name):\n        self.name = name",
      "format": "markdown"
    }
  }'
```

#### Generate API Docs
```bash
curl -X POST http://localhost:8100/agents/documentation-generator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "api-doc-generation",
    "input_data": {
      "spec": {
        "title": "My API",
        "version": "1.0.0",
        "endpoints": ["/api/users", "/api/orders"]
      },
      "format": "openapi"
    }
  }'
```

#### Create Guide
```bash
curl -X POST http://localhost:8100/agents/documentation-generator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "guide-creation",
    "input_data": {
      "topic": "Getting Started",
      "audience": "developers",
      "depth": "detailed"
    }
  }'
```

#### Generate Examples
```bash
curl -X POST http://localhost:8100/agents/documentation-generator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "example-generation",
    "input_data": {
      "topic": "API Authentication",
      "language": "python",
      "complexity": "intermediate"
    }
  }'
```

#### Check Documentation
```bash
curl -X POST http://localhost:8100/agents/documentation-generator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "doc-maintenance",
    "input_data": {
      "action": "check"
    }
  }'
```

## Python SDK Examples

### Auto-Documentation Generation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

source_code = '''
class DataProcessor:
    """
    Process and transform data from various sources.

    Attributes:
        config: Configuration dictionary
        logger: Logger instance
    """

    def __init__(self, config: dict):
        """Initialize the processor with configuration."""
        self.config = config

    def process(self, data: list) -> list:
        """
        Process a list of data items.

        Args:
            data: List of items to process

        Returns:
            Processed list of items
        """
        return [self._transform(item) for item in data]

    def _transform(self, item):
        """Internal transformation method."""
        return item
'''

result = client.execute_agent(
    agent_id="documentation-generator",
    capability="auto-documentation",
    input_data={
        "source": source_code,
        "format": "markdown",
        "include_private": False
    }
)

if result.success:
    docs = result.output
    print(f"Documentation ID: {docs['doc_id']}")
    print(f"Format: {docs['format']}")
    print(f"Coverage: {docs['coverage']:.0%}")

    print("\nSections Generated:")
    for section in docs['sections']:
        items = section.get('items', 0)
        print(f"  - {section['name']}: {items} items")

    if docs['warnings']:
        print("\nWarnings:")
        for warning in docs['warnings']:
            print(f"  - {warning}")
```

### API Documentation Generation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Generate API documentation
result = client.execute_agent(
    agent_id="documentation-generator",
    capability="api-doc-generation",
    input_data={
        "spec": {
            "title": "Agent Service API",
            "version": "1.0.0",
            "base_url": "http://localhost:8100"
        },
        "format": "openapi",
        "include_examples": True
    }
)

if result.success:
    api_docs = result.output
    print(f"Format: {api_docs['format']}")
    print(f"Endpoints Documented: {api_docs['endpoints_documented']}")
    print(f"Schemas Documented: {api_docs['schemas_documented']}")

    print("\nEndpoints:")
    for endpoint in api_docs['documentation']['endpoints']:
        methods = ', '.join(endpoint['methods'])
        print(f"  {endpoint['path']} [{methods}]")

    print("\nSchemas:")
    for schema in api_docs['documentation']['schemas']:
        print(f"  - {schema}")

    print(f"\nOutput Formats: {', '.join(api_docs['output_formats'])}")
```

### Guide Creation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Create a developer guide
result = client.execute_agent(
    agent_id="documentation-generator",
    capability="guide-creation",
    input_data={
        "topic": "Agent Integration",
        "audience": "developers",
        "depth": "comprehensive"
    }
)

if result.success:
    guide = result.output
    print(f"Guide ID: {guide['guide_id']}")
    print(f"Title: {guide['title']}")
    print(f"Audience: {guide['audience']}")
    print(f"Reading Time: {guide['reading_time']}")
    print(f"Total Words: {guide['total_word_count']}")
    print(f"Includes Examples: {guide['includes_examples']}")

    print("\nSections:")
    for section in guide['sections']:
        print(f"  - {section['title']} ({section['word_count']} words)")
```

### Code Example Generation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Generate code examples
result = client.execute_agent(
    agent_id="documentation-generator",
    capability="example-generation",
    input_data={
        "topic": "agent_execution",
        "language": "python",
        "complexity": "intermediate"
    }
)

if result.success:
    examples = result.output
    print(f"Topic: {examples['topic']}")
    print(f"Language: {examples['language']}")
    print(f"Total Examples: {examples['total_examples']}")

    print("\nGenerated Examples:")
    for example in examples['examples']:
        print(f"\n  === {example['title']} ===")
        print(f"  Description: {example['description']}")
        print(f"  Runnable: {example['runnable']}")
        print(f"\n  Code:\n{example['code']}")
```

### Documentation Maintenance

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Check documentation health
result = client.execute_agent(
    agent_id="documentation-generator",
    capability="doc-maintenance",
    input_data={
        "action": "check"
    }
)

if result.success:
    check = result.output
    print(f"Status: {check['status']}")
    print(f"Last Updated: {check['last_updated']}")

    print("\nCoverage:")
    for item, percent in check['coverage'].items():
        print(f"  {item}: {percent}")

    if check['issues']:
        print("\nIssues Found:")
        for issue in check['issues']:
            print(f"  [{issue['severity'].upper()}] {issue['type']}")
            print(f"    File: {issue['file']}")
            if issue.get('section'):
                print(f"    Section: {issue['section']}")
            if issue.get('description'):
                print(f"    Description: {issue['description']}")

# Update documentation
result = client.execute_agent(
    agent_id="documentation-generator",
    capability="doc-maintenance",
    input_data={
        "action": "update"
    }
)

if result.success:
    update = result.output
    print(f"\nUpdated: {update['updated']}")
    print(f"Files Updated: {update['files_updated']}")

    print("\nChanges:")
    for change in update['changes']:
        print(f"  - {change['file']}: {change['change']}")
```

### Complete Documentation Workflow

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def generate_project_docs(project_name, source_code, api_spec):
    """Generate complete project documentation."""

    docs = {}

    # 1. Auto-generate code documentation
    code_docs = client.execute_agent(
        agent_id="documentation-generator",
        capability="auto-documentation",
        input_data={
            "source": source_code,
            "format": "markdown"
        }
    )
    docs['code'] = code_docs.output if code_docs.success else None

    # 2. Generate API documentation
    api_docs = client.execute_agent(
        agent_id="documentation-generator",
        capability="api-doc-generation",
        input_data={
            "spec": api_spec,
            "format": "openapi",
            "include_examples": True
        }
    )
    docs['api'] = api_docs.output if api_docs.success else None

    # 3. Create getting started guide
    guide = client.execute_agent(
        agent_id="documentation-generator",
        capability="guide-creation",
        input_data={
            "topic": f"Getting Started with {project_name}",
            "audience": "developers",
            "depth": "detailed"
        }
    )
    docs['guide'] = guide.output if guide.success else None

    # 4. Generate examples
    examples = client.execute_agent(
        agent_id="documentation-generator",
        capability="example-generation",
        input_data={
            "topic": f"{project_name} usage",
            "language": "python",
            "complexity": "basic"
        }
    )
    docs['examples'] = examples.output if examples.success else None

    return docs

# Generate documentation
source = '''
class MyService:
    """Main service class."""
    def execute(self, command):
        """Execute a command."""
        pass
'''

api = {
    "title": "MyService API",
    "version": "1.0.0"
}

docs = generate_project_docs("MyService", source, api)

print("Documentation Generation Complete:")
print(f"  Code Docs: {'Yes' if docs['code'] else 'No'}")
print(f"  API Docs: {'Yes' if docs['api'] else 'No'}")
print(f"  Guide: {'Yes' if docs['guide'] else 'No'}")
print(f"  Examples: {'Yes' if docs['examples'] else 'No'}")
```

### Async Documentation Operations

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def parallel_doc_generation(modules):
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Generate docs for all modules in parallel
        tasks = [
            client.execute_agent(
                agent_id="documentation-generator",
                capability="auto-documentation",
                input_data={
                    "source": code,
                    "format": "markdown"
                }
            )
            for name, code in modules
        ]

        results = await asyncio.gather(*tasks)

        print("Documentation Generation Summary:")
        for (name, _), result in zip(modules, results):
            if result.success:
                coverage = result.output['coverage']
                print(f"  {name}: {coverage:.0%} coverage")
            else:
                print(f"  {name}: Generation failed")

# Example modules
modules = [
    ("users", "class UserService:\n    pass"),
    ("orders", "class OrderService:\n    pass"),
    ("payments", "class PaymentService:\n    pass"),
]

asyncio.run(parallel_doc_generation(modules))
```

## Configuration Options

### Output Formats

| Format | Description |
|--------|-------------|
| `markdown` | Markdown format |
| `html` | HTML format |
| `rst` | reStructuredText |
| `openapi` | OpenAPI/Swagger spec |
| `postman` | Postman collection |

### Guide Types

| Type | Audience | Typical Sections |
|------|----------|------------------|
| `quickstart` | All | Installation, First steps |
| `tutorial` | Developers | Step-by-step instructions |
| `reference` | Developers | Complete API reference |
| `admin` | Admins | Configuration, deployment |

### Coverage Metrics

| Metric | Target |
|--------|--------|
| Classes | 100% |
| Functions | 100% |
| Public Methods | 100% |
| Private Methods | Optional |

## Best Practices

### 1. Auto-Documentation
- Use docstrings consistently
- Include type hints
- Document parameters and returns
- Keep docs near code

### 2. API Documentation
- Keep spec in sync with code
- Include examples
- Document error responses
- Version your APIs

### 3. Guide Creation
- Know your audience
- Start simple, add detail
- Include working examples
- Review and update regularly

### 4. Example Generation
- Cover common use cases
- Test all examples
- Include error handling
- Show best practices

### 5. Maintenance
- Run checks in CI/CD
- Address issues promptly
- Track documentation coverage
- Schedule regular reviews

## Related Agents

- **Code Reviewer Agent:** Review code documentation
- **Content Creator Agent:** Marketing documentation
- **Task Decomposer Agent:** Plan documentation work

## Troubleshooting

### Common Issues

**Low coverage:**
- Add missing docstrings
- Document all public APIs
- Review coverage report

**Outdated documentation:**
- Run maintenance checks
- Sync with source code
- Update after code changes

**Missing examples:**
- Generate for common cases
- Test example validity
- Include error handling

## Implementation Reference

**Source:** `built_in_agents/utility/doc_generator/agent.py`
