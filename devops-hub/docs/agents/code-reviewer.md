# Code Reviewer Agent

**Agent ID:** `code-reviewer`
**Version:** 1.0.0
**Type:** Analyst
**Domain:** Utility
**Status:** Production

## Overview

The Code Reviewer Agent provides automated code review and analysis capabilities. It analyzes code quality, scans for security vulnerabilities, checks coding style consistency, suggests refactoring improvements, and identifies performance issues.

This agent is essential for development teams looking to maintain code quality, ensure security standards, and improve code maintainability.

## Capabilities

### 1. Code Analysis
**Name:** `code-analysis`

Analyze code quality, complexity, and patterns.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Code to analyze |
| `language` | string | Programming language |
| `file_path` | string | File path (optional) |
| `metrics` | array | Specific metrics to calculate (optional) |

**Returns:** Quality score, metrics, and issues

### 2. Security Scanning
**Name:** `security-scanning`

Scan code for security vulnerabilities and issues.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Code to scan |
| `language` | string | Programming language |
| `severity_threshold` | string | Minimum severity: `low`, `medium`, `high`, `critical` |

**Returns:** Vulnerabilities, passed checks, and recommendations

### 3. Style Checking
**Name:** `style-checking`

Check code against style guidelines.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Code to check |
| `language` | string | Programming language |
| `style_guide` | string | Style guide: `pep8`, `google`, `airbnb`, etc. |

**Returns:** Compliance score and violations

### 4. Refactoring Suggestions
**Name:** `refactoring-suggestions`

Suggest code refactoring improvements.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Code to analyze |
| `language` | string | Programming language |
| `focus` | array | Focus areas: `readability`, `performance`, `patterns` |

**Returns:** Refactoring suggestions with effort estimates

### 5. Performance Analysis
**Name:** `performance-analysis`

Analyze code for potential performance issues.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Code to analyze |
| `language` | string | Programming language |
| `context` | string | Execution context: `web`, `cli`, `service` |

**Returns:** Performance issues, hotspots, and recommendations

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Analyze Code
```bash
curl -X POST http://localhost:8100/agents/code-reviewer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "code-analysis",
    "input_data": {
      "code": "def calculate_total(items):\n    total = 0\n    for item in items:\n        total += item.price * item.quantity\n    return total",
      "language": "python"
    }
  }'
```

#### Security Scan
```bash
curl -X POST http://localhost:8100/agents/code-reviewer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "security-scanning",
    "input_data": {
      "code": "query = \"SELECT * FROM users WHERE id = \" + user_id",
      "language": "python",
      "severity_threshold": "medium"
    }
  }'
```

#### Style Check
```bash
curl -X POST http://localhost:8100/agents/code-reviewer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "style-checking",
    "input_data": {
      "code": "def MyFunction(x,y):\n  return x+y",
      "language": "python",
      "style_guide": "pep8"
    }
  }'
```

#### Get Refactoring Suggestions
```bash
curl -X POST http://localhost:8100/agents/code-reviewer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "refactoring-suggestions",
    "input_data": {
      "code": "if x == 1:\n    do_a()\nelif x == 2:\n    do_b()\nelif x == 3:\n    do_c()",
      "language": "python",
      "focus": ["readability", "patterns"]
    }
  }'
```

#### Performance Analysis
```bash
curl -X POST http://localhost:8100/agents/code-reviewer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "performance-analysis",
    "input_data": {
      "code": "for user in users:\n    orders = db.query(\"SELECT * FROM orders WHERE user_id = ?\", user.id)",
      "language": "python",
      "context": "web"
    }
  }'
```

## Python SDK Examples

### Code Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

code = '''
def process_data(items):
    """Process a list of items."""
    results = []
    for i in range(len(items)):
        item = items[i]
        if item.valid:
            result = item.value * 2
            if result > 100:
                result = 100
            results.append(result)
    return results
'''

result = client.execute_agent(
    agent_id="code-reviewer",
    capability="code-analysis",
    input_data={
        "code": code,
        "language": "python"
    }
)

if result.success:
    analysis = result.output
    print(f"Review ID: {analysis['review_id']}")
    print(f"Language: {analysis['language']}")
    print(f"Quality Score: {analysis['score']:.0%}")

    print("\nMetrics:")
    metrics = analysis['metrics']
    print(f"  Cyclomatic Complexity: {metrics['complexity']['cyclomatic']}")
    print(f"  Cognitive Complexity: {metrics['complexity']['cognitive']}")
    print(f"  Maintainability: {metrics['maintainability']:.0%}")
    print(f"  Test Coverage: {metrics['test_coverage']:.0%}")
    print(f"  Duplication: {metrics['duplication']:.0%}")

    print("\nIssues Found:")
    for issue in analysis['issues']:
        print(f"  [{issue['severity'].upper()}] Line {issue['line']}: {issue['message']}")

    print(f"\nSummary: {analysis['summary']}")
```

### Security Scanning

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

code = '''
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

def render_page(user_input):
    return f"<div>{user_input}</div>"
'''

result = client.execute_agent(
    agent_id="code-reviewer",
    capability="security-scanning",
    input_data={
        "code": code,
        "language": "python",
        "severity_threshold": "low"
    }
)

if result.success:
    scan = result.output
    print(f"Security Score: {scan['security_score']:.0%}")

    print("\nVulnerabilities Found:")
    for vuln in scan['vulnerabilities']:
        print(f"\n  [{vuln['severity'].upper()}] {vuln['id']}")
        print(f"  Type: {vuln['type']}")
        print(f"  Location: {vuln['location']}")
        print(f"  Description: {vuln['description']}")
        print(f"  Fix: {vuln['fix']}")

    print("\nPassed Checks:")
    for check in scan['passed_checks']:
        print(f"  [PASS] {check}")

    print("\nRecommendations:")
    for rec in scan['recommendations']:
        print(f"  - {rec}")
```

### Style Checking

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

code = '''
def MyFunction(x,y):
  z=x+y
  if z>10:
    return True
  else:
    return False
'''

result = client.execute_agent(
    agent_id="code-reviewer",
    capability="style-checking",
    input_data={
        "code": code,
        "language": "python",
        "style_guide": "pep8"
    }
)

if result.success:
    style = result.output
    print(f"Style Guide: {style['style_guide']}")
    print(f"Compliance Score: {style['compliance_score']:.0%}")

    print("\nViolations:")
    for violation in style['violations']:
        print(f"  {violation['rule']}: {violation['count']} occurrences ({violation['severity']})")

    print(f"\nAuto-fixable: {style['auto_fixable']} issues")
    print(f"Manual Review: {style['manual_review']} issues")
```

### Refactoring Suggestions

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

code = '''
class UserHandler:
    def process_user(self, user, action):
        if action == "create":
            # 20 lines of create logic
            pass
        elif action == "update":
            # 20 lines of update logic
            pass
        elif action == "delete":
            # 20 lines of delete logic
            pass
        elif action == "archive":
            # 20 lines of archive logic
            pass
'''

result = client.execute_agent(
    agent_id="code-reviewer",
    capability="refactoring-suggestions",
    input_data={
        "code": code,
        "language": "python",
        "focus": ["readability", "patterns"]
    }
)

if result.success:
    refactor = result.output
    print(f"Total Suggestions: {refactor['total_suggestions']}")
    print(f"Estimated Improvement: {refactor['estimated_improvement']}")

    print("\nSuggestions:")
    for suggestion in refactor['suggestions']:
        print(f"\n  Type: {suggestion['type']}")
        print(f"  Location: {suggestion['location']}")
        print(f"  Description: {suggestion['description']}")
        print(f"  Benefit: {suggestion['benefit']}")
        print(f"  Effort: {suggestion['effort']}")
```

### Performance Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

code = '''
def get_user_orders(db, users):
    results = []
    for user in users:
        orders = db.query(f"SELECT * FROM orders WHERE user_id = {user.id}")
        for order in orders:
            order.items = db.query(f"SELECT * FROM items WHERE order_id = {order.id}")
        results.append({"user": user, "orders": orders})
    return results
'''

result = client.execute_agent(
    agent_id="code-reviewer",
    capability="performance-analysis",
    input_data={
        "code": code,
        "language": "python",
        "context": "web"
    }
)

if result.success:
    perf = result.output
    print(f"Performance Score: {perf['performance_score']:.0%}")

    print("\nIssues Found:")
    for issue in perf['issues']:
        print(f"\n  [{issue['impact'].upper()}] {issue['type']}")
        print(f"  Location: {issue['location']}")
        print(f"  Description: {issue['description']}")
        print(f"  Fix: {issue['fix']}")

    print("\nHotspots:")
    for hotspot in perf['hotspots']:
        print(f"  - {hotspot['location']}: {hotspot.get('cpu_impact', hotspot.get('io_impact', 'N/A'))} impact")

    print("\nRecommendations:")
    for rec in perf['recommendations']:
        print(f"  - {rec}")
```

### Comprehensive Code Review

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def full_code_review(code, language):
    """Perform a comprehensive code review."""

    results = {}

    # 1. Code Analysis
    analysis = client.execute_agent(
        agent_id="code-reviewer",
        capability="code-analysis",
        input_data={"code": code, "language": language}
    )
    results['quality'] = analysis.output if analysis.success else None

    # 2. Security Scan
    security = client.execute_agent(
        agent_id="code-reviewer",
        capability="security-scanning",
        input_data={"code": code, "language": language}
    )
    results['security'] = security.output if security.success else None

    # 3. Style Check
    style = client.execute_agent(
        agent_id="code-reviewer",
        capability="style-checking",
        input_data={"code": code, "language": language, "style_guide": "pep8"}
    )
    results['style'] = style.output if style.success else None

    # 4. Performance
    performance = client.execute_agent(
        agent_id="code-reviewer",
        capability="performance-analysis",
        input_data={"code": code, "language": language}
    )
    results['performance'] = performance.output if performance.success else None

    # 5. Refactoring
    refactoring = client.execute_agent(
        agent_id="code-reviewer",
        capability="refactoring-suggestions",
        input_data={"code": code, "language": language}
    )
    results['refactoring'] = refactoring.output if refactoring.success else None

    return results

# Example usage
code = '''
def process_orders(db, user_id):
    query = "SELECT * FROM orders WHERE user_id = " + str(user_id)
    orders = db.execute(query)
    total = 0
    for order in orders:
        for item in order.items:
            total = total + item.price
    return total
'''

review = full_code_review(code, "python")

print("=" * 60)
print("COMPREHENSIVE CODE REVIEW")
print("=" * 60)

if review['quality']:
    print(f"\nQuality Score: {review['quality']['score']:.0%}")
    print(f"  Issues: {len(review['quality']['issues'])}")

if review['security']:
    print(f"\nSecurity Score: {review['security']['security_score']:.0%}")
    print(f"  Vulnerabilities: {len(review['security']['vulnerabilities'])}")

if review['style']:
    print(f"\nStyle Compliance: {review['style']['compliance_score']:.0%}")
    print(f"  Violations: {sum(v['count'] for v in review['style']['violations'])}")

if review['performance']:
    print(f"\nPerformance Score: {review['performance']['performance_score']:.0%}")
    print(f"  Issues: {len(review['performance']['issues'])}")

if review['refactoring']:
    print(f"\nRefactoring Suggestions: {review['refactoring']['total_suggestions']}")

print("\n" + "=" * 60)
```

### Async Code Review

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def review_multiple_files(files):
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Review all files in parallel
        tasks = [
            client.execute_agent(
                agent_id="code-reviewer",
                capability="code-analysis",
                input_data={"code": content, "language": lang}
            )
            for path, content, lang in files
        ]

        results = await asyncio.gather(*tasks)

        print("Code Review Summary:")
        for (path, _, _), result in zip(files, results):
            if result.success:
                score = result.output['score']
                issues = len(result.output['issues'])
                print(f"  {path}: {score:.0%} quality, {issues} issues")
            else:
                print(f"  {path}: Review failed")

# Example files
files = [
    ("app/models.py", "class User:\n    pass", "python"),
    ("app/views.py", "def index():\n    return 'Hello'", "python"),
    ("app/utils.py", "def helper(x):\n    return x * 2", "python"),
]

asyncio.run(review_multiple_files(files))
```

## Configuration Options

### Style Guides

| Guide | Language | Description |
|-------|----------|-------------|
| `pep8` | Python | PEP 8 style guide |
| `google` | Python/JS | Google style guide |
| `airbnb` | JavaScript | Airbnb JavaScript guide |
| `standard` | JavaScript | StandardJS |
| `prettier` | Multiple | Prettier formatting |

### Security Rules

| Category | Examples |
|----------|----------|
| `injection` | SQL injection, command injection |
| `xss` | Cross-site scripting |
| `auth` | Authentication issues |
| `crypto` | Weak cryptography |
| `secrets` | Hardcoded credentials |

### Complexity Thresholds

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Cyclomatic | < 10 | 10-20 | > 20 |
| Cognitive | < 15 | 15-25 | > 25 |
| Maintainability | > 80% | 60-80% | < 60% |

## Best Practices

### 1. Code Analysis
- Review regularly, not just at PR time
- Track quality trends over time
- Set team quality baselines
- Prioritize high-impact issues

### 2. Security
- Scan before every deployment
- Use appropriate severity thresholds
- Fix high/critical issues immediately
- Track vulnerability patterns

### 3. Style
- Agree on style guide early
- Use auto-formatting tools
- Review style in CI/CD
- Document exceptions

### 4. Refactoring
- Prioritize by effort/benefit
- Refactor incrementally
- Test before and after
- Document significant changes

### 5. Performance
- Profile before optimizing
- Focus on hotspots
- Measure improvements
- Consider context (web vs CLI)

## Related Agents

- **Documentation Generator Agent:** Document reviewed code
- **Error Handler Agent:** Handle review errors
- **Task Decomposer Agent:** Plan refactoring work

## Troubleshooting

### Common Issues

**Analysis timeout:**
- Split large files
- Increase timeout
- Use sampling

**False positives:**
- Review rule configuration
- Add suppressions where appropriate
- Update rule sets

**Missing language support:**
- Check supported languages
- Use generic analysis
- Request language addition

## Implementation Reference

**Source:** `built_in_agents/utility/code_reviewer/agent.py`
