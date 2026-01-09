# Content Creator Agent

**Agent ID:** `content-creator`
**Version:** 1.0.0
**Type:** Worker
**Domain:** Business
**Status:** Production

## Overview

The Content Creator Agent handles content generation, editing, publishing, and optimization. It creates various types of content including articles, blog posts, and marketing materials, while ensuring quality, SEO optimization, and style consistency.

This agent is essential for marketing teams, content operations, and any workflow requiring automated content creation and management.

## Capabilities

### 1. Content Generation
**Name:** `content-generation`

Generate articles, posts, and other content types.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Content type: `article`, `blog`, `social`, `email` |
| `topic` | string | Content topic |
| `tone` | string | Writing tone: `professional`, `casual`, `formal` |
| `length` | string | Content length: `short`, `medium`, `long` |
| `keywords` | array | Target keywords (optional) |

**Returns:** Generated content with metadata

### 2. Editing
**Name:** `editing`

Edit, proofread, and improve existing content.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `content_id` | string | Content ID to edit |
| `content` | string | Content text (if no ID) |
| `edit_type` | string | Edit type: `proofread`, `rewrite`, `enhance` |

**Returns:** Edit suggestions and changes

### 3. Publishing
**Name:** `publishing`

Manage content publishing and scheduling.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Action: `schedule`, `publish`, `queue`, `unpublish` |
| `content_id` | string | Content ID |
| `publish_date` | string | Scheduled publish date (ISO format) |
| `channels` | array | Publishing channels |

**Returns:** Publishing status and details

### 4. SEO Optimization
**Name:** `seo-optimization`

Optimize content for search engines.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `content_id` | string | Content ID to optimize |
| `content` | string | Content text (if no ID) |
| `keywords` | array | Target keywords |
| `target_score` | number | Target SEO score (0-1) |

**Returns:** SEO analysis and suggestions

### 5. Style Consistency
**Name:** `style-consistency`

Ensure consistent tone and style across content.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `content_id` | string | Content ID to check |
| `content` | string | Content text (if no ID) |
| `style_guide` | string | Style guide to apply |

**Returns:** Style analysis and issues

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Generate Content
```bash
curl -X POST http://localhost:8100/agents/content-creator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "content-generation",
    "input_data": {
      "type": "article",
      "topic": "Benefits of AI in Business",
      "tone": "professional",
      "length": "medium"
    }
  }'
```

#### Edit Content
```bash
curl -X POST http://localhost:8100/agents/content-creator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "editing",
    "input_data": {
      "content_id": "content-123",
      "edit_type": "proofread"
    }
  }'
```

#### Schedule Publishing
```bash
curl -X POST http://localhost:8100/agents/content-creator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "publishing",
    "input_data": {
      "action": "schedule",
      "content_id": "content-123",
      "publish_date": "2026-01-15T10:00:00Z",
      "channels": ["website", "newsletter"]
    }
  }'
```

#### Optimize for SEO
```bash
curl -X POST http://localhost:8100/agents/content-creator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "seo-optimization",
    "input_data": {
      "content_id": "content-123",
      "keywords": ["AI business", "automation", "efficiency"]
    }
  }'
```

#### Check Style
```bash
curl -X POST http://localhost:8100/agents/content-creator/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "style-consistency",
    "input_data": {
      "content_id": "content-123",
      "style_guide": "corporate"
    }
  }'
```

## Python SDK Examples

### Content Generation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Generate a professional article
result = client.execute_agent(
    agent_id="content-creator",
    capability="content-generation",
    input_data={
        "type": "article",
        "topic": "The Future of Remote Work",
        "tone": "professional",
        "length": "medium",
        "keywords": ["remote work", "productivity", "collaboration"]
    }
)

if result.success:
    content = result.output
    print(f"Content ID: {content['content_id']}")
    print(f"Title: {content['title']}")
    print(f"Type: {content['type']}")
    print(f"Tone: {content['tone']}")
    print(f"Word Count: {content['word_count']}")
    print(f"Status: {content['status']}")
    print(f"\nPreview: {content['preview']}")
```

### Content Editing

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Edit content for quality
result = client.execute_agent(
    agent_id="content-creator",
    capability="editing",
    input_data={
        "content_id": "content-123",
        "edit_type": "enhance"
    }
)

if result.success:
    edit = result.output
    print(f"Content ID: {edit['content_id']}")
    print(f"Edit Type: {edit['edit_type']}")
    print(f"Readability Score: {edit['readability_score']}")

    print("\nChanges Made:")
    for change in edit['changes']:
        print(f"  - {change['type']}: {change['count']} fixes")

    print("\nSuggestions:")
    for suggestion in edit['suggestions']:
        print(f"  - {suggestion}")
```

### Publishing Workflow

```python
from sdk import AgentServiceClient
from datetime import datetime, timedelta

client = AgentServiceClient("http://localhost:8100")

# Schedule content for publishing
publish_date = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

result = client.execute_agent(
    agent_id="content-creator",
    capability="publishing",
    input_data={
        "action": "schedule",
        "content_id": "content-123",
        "publish_date": publish_date,
        "channels": ["website", "newsletter", "social"]
    }
)

if result.success:
    pub = result.output
    print(f"Content ID: {pub['content_id']}")
    print(f"Scheduled: {pub['scheduled']}")
    print(f"Publish Date: {pub['publish_date']}")
    print(f"Channels: {', '.join(pub['channels'])}")

# View publishing queue
result = client.execute_agent(
    agent_id="content-creator",
    capability="publishing",
    input_data={
        "action": "queue"
    }
)

if result.success:
    queue = result.output
    print(f"\nPublishing Queue ({queue['total']} items):")
    for item in queue['queue']:
        print(f"  - {item['title']}: {item['scheduled']}")
```

### SEO Optimization

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Optimize content for SEO
result = client.execute_agent(
    agent_id="content-creator",
    capability="seo-optimization",
    input_data={
        "content_id": "content-123",
        "keywords": ["digital transformation", "business innovation", "technology"]
    }
)

if result.success:
    seo = result.output
    print(f"Content ID: {seo['content_id']}")
    print(f"SEO Score: {seo['seo_score']:.0%}")

    print("\nAnalysis:")
    for metric, data in seo['analysis'].items():
        print(f"  {metric}: {data['score']:.0%} - {data['status']}")

    print("\nSuggestions:")
    for suggestion in seo['suggestions']:
        print(f"  - {suggestion}")

    print(f"\nKeywords Analyzed: {', '.join(seo['keywords_analyzed'])}")
```

### Style Consistency Check

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Check style consistency
result = client.execute_agent(
    agent_id="content-creator",
    capability="style-consistency",
    input_data={
        "content_id": "content-123",
        "style_guide": "corporate"
    }
)

if result.success:
    style = result.output
    print(f"Content ID: {style['content_id']}")
    print(f"Style Guide: {style['style_guide']}")
    print(f"Consistency Score: {style['consistency_score']:.0%}")
    print(f"Brand Alignment: {style['brand_alignment']:.0%}")

    print("\nVoice Analysis:")
    voice = style['voice_analysis']
    print(f"  Active Voice: {voice['active_voice']}")
    print(f"  Passive Voice: {voice['passive_voice']}")
    print(f"  Recommendation: {voice['recommendation']}")

    if style['issues']:
        print("\nIssues Found:")
        for issue in style['issues']:
            print(f"  - [{issue['type']}] {issue['location']}: {issue['suggestion']}")
```

### Complete Content Workflow

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def content_workflow(topic, keywords):
    """Complete content creation workflow."""

    # Step 1: Generate content
    generation = client.execute_agent(
        agent_id="content-creator",
        capability="content-generation",
        input_data={
            "type": "article",
            "topic": topic,
            "tone": "professional",
            "length": "medium",
            "keywords": keywords
        }
    )

    if not generation.success:
        return None

    content_id = generation.output['content_id']
    print(f"1. Generated: {generation.output['title']}")

    # Step 2: Edit content
    editing = client.execute_agent(
        agent_id="content-creator",
        capability="editing",
        input_data={
            "content_id": content_id,
            "edit_type": "enhance"
        }
    )

    if editing.success:
        print(f"2. Edited: Readability score {editing.output['readability_score']}")

    # Step 3: SEO optimization
    seo = client.execute_agent(
        agent_id="content-creator",
        capability="seo-optimization",
        input_data={
            "content_id": content_id,
            "keywords": keywords
        }
    )

    if seo.success:
        print(f"3. Optimized: SEO score {seo.output['seo_score']:.0%}")

    # Step 4: Style check
    style = client.execute_agent(
        agent_id="content-creator",
        capability="style-consistency",
        input_data={
            "content_id": content_id,
            "style_guide": "corporate"
        }
    )

    if style.success:
        print(f"4. Style checked: Consistency {style.output['consistency_score']:.0%}")

    # Step 5: Schedule publishing
    from datetime import datetime, timedelta
    publish_date = (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"

    publishing = client.execute_agent(
        agent_id="content-creator",
        capability="publishing",
        input_data={
            "action": "schedule",
            "content_id": content_id,
            "publish_date": publish_date,
            "channels": ["website", "newsletter"]
        }
    )

    if publishing.success:
        print(f"5. Scheduled for: {publishing.output['publish_date']}")

    return content_id

# Run workflow
content_id = content_workflow(
    topic="Machine Learning in Healthcare",
    keywords=["ML healthcare", "medical AI", "diagnosis automation"]
)
print(f"\nWorkflow complete. Content ID: {content_id}")
```

### Async Content Operations

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def batch_content_generation():
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Generate multiple pieces of content in parallel
        topics = [
            {"topic": "Cloud Computing Trends", "type": "article"},
            {"topic": "DevOps Best Practices", "type": "blog"},
            {"topic": "Security in 2026", "type": "article"},
        ]

        tasks = [
            client.execute_agent(
                agent_id="content-creator",
                capability="content-generation",
                input_data={
                    "type": t["type"],
                    "topic": t["topic"],
                    "tone": "professional",
                    "length": "medium"
                }
            )
            for t in topics
        ]

        results = await asyncio.gather(*tasks)

        print("Generated Content:")
        for topic, result in zip(topics, results):
            if result.success:
                print(f"  - {topic['topic']}: {result.output['content_id']}")
            else:
                print(f"  - {topic['topic']}: FAILED")

asyncio.run(batch_content_generation())
```

## Configuration Options

### Content Types

| Type | Description | Typical Length |
|------|-------------|----------------|
| `article` | Long-form article | 1000-3000 words |
| `blog` | Blog post | 500-1500 words |
| `social` | Social media post | 50-280 characters |
| `email` | Email content | 200-500 words |
| `landing` | Landing page copy | 300-800 words |

### Tone Options

| Tone | Description |
|------|-------------|
| `professional` | Business-appropriate, formal |
| `casual` | Friendly, conversational |
| `formal` | Very formal, traditional |
| `technical` | Technical, detailed |
| `persuasive` | Marketing-focused, compelling |

### Style Guides

```python
style_config = {
    "corporate": {
        "tone": "professional",
        "voice": "active",
        "terminology": "business",
        "contractions": False
    },
    "casual": {
        "tone": "friendly",
        "voice": "conversational",
        "terminology": "simple",
        "contractions": True
    }
}
```

## Best Practices

### 1. Content Generation
- Provide clear, specific topics
- Include target keywords
- Specify appropriate tone
- Review generated content

### 2. Editing
- Run multiple edit passes
- Check readability scores
- Apply grammar fixes
- Review suggestions carefully

### 3. Publishing
- Use scheduling for consistency
- Select appropriate channels
- Review before publishing
- Track performance

### 4. SEO
- Target relevant keywords
- Optimize titles and meta
- Use internal links
- Monitor rankings

### 5. Style
- Define clear style guides
- Check consistently
- Train team on standards
- Update guides as needed

## Related Agents

- **Research Analyzer Agent:** Research for content topics
- **Project Manager Agent:** Content calendar management
- **Documentation Generator Agent:** Technical content

## Troubleshooting

### Common Issues

**Low SEO scores:**
- Add more keywords naturally
- Improve title optimization
- Add meta descriptions
- Increase internal links

**Style inconsistencies:**
- Review style guide settings
- Check terminology usage
- Verify tone consistency

**Publishing failures:**
- Verify channel configuration
- Check scheduling conflicts
- Review permissions

## Implementation Reference

**Source:** `built_in_agents/business/content_creator/agent.py`
