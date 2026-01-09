# Research Analyzer Agent

**Agent ID:** `research-analyzer`
**Version:** 1.0.0
**Type:** Analyst
**Domain:** Business
**Status:** Production

## Overview

The Research Analyzer Agent is a comprehensive market research and competitive intelligence tool. It conducts market analysis, predicts trends, tracks competitors, aggregates data from multiple sources, and generates detailed research reports.

This agent is essential for business intelligence operations, providing actionable insights for strategic decision-making.

## Capabilities

### 1. Market Analysis
**Name:** `market-analysis`

Analyze market trends, size, and opportunities in specified markets and regions.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `market` | string | Target market to analyze (default: "general") |
| `region` | string | Geographic region (default: "global") |

**Returns:** Market size estimates, growth rates, key trends, opportunities, and risks

### 2. Trend Prediction
**Name:** `trend-prediction`

Predict future trends based on historical data and market indicators.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `topic` | string | Topic area for prediction (default: "technology") |
| `horizon` | string | Prediction timeframe: `3_months`, `6_months`, `12_months` |

**Returns:** Trend predictions with probabilities and impact assessments

### 3. Competitive Intelligence
**Name:** `competitive-intelligence`

Track and analyze competitor activities, market positions, and strategies.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `industry` | string | Industry sector (default: "technology") |
| `competitors` | array | Specific competitors to analyze (optional) |

**Returns:** Competitive landscape analysis with market share and recommendations

### 4. Data Aggregation
**Name:** `data-aggregation`

Aggregate data from multiple sources for comprehensive analysis.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `sources` | array | Data sources to aggregate from |
| `query` | object | Query parameters for data collection |

**Returns:** Aggregated data with quality metrics and summary

### 5. Report Generation
**Name:** `report-generation`

Generate comprehensive research reports on specified topics.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Report type: `market_analysis`, `competitive`, `trend` |
| `topic` | string | Report topic |

**Returns:** Generated report with findings and confidence scores

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Market Analysis
```bash
curl -X POST http://localhost:8100/agents/research-analyzer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "market-analysis",
    "input_data": {
      "market": "artificial-intelligence",
      "region": "north-america"
    }
  }'
```

#### Trend Prediction
```bash
curl -X POST http://localhost:8100/agents/research-analyzer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "trend-prediction",
    "input_data": {
      "topic": "cloud-computing",
      "horizon": "12_months"
    }
  }'
```

#### Competitive Intelligence
```bash
curl -X POST http://localhost:8100/agents/research-analyzer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "competitive-intelligence",
    "input_data": {
      "industry": "fintech",
      "competitors": ["Company A", "Company B", "Company C"]
    }
  }'
```

#### Data Aggregation
```bash
curl -X POST http://localhost:8100/agents/research-analyzer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "data-aggregation",
    "input_data": {
      "sources": ["market-reports", "news-feeds", "financial-data"],
      "query": {
        "keywords": ["AI", "machine learning"],
        "date_range": "last_30_days"
      }
    }
  }'
```

#### Generate Report
```bash
curl -X POST http://localhost:8100/agents/research-analyzer/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "report-generation",
    "input_data": {
      "type": "market_analysis",
      "topic": "Electric Vehicle Market 2026"
    }
  }'
```

## Python SDK Examples

### Market Analysis

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Analyze the AI market
result = client.execute_agent(
    agent_id="research-analyzer",
    capability="market-analysis",
    input_data={
        "market": "artificial-intelligence",
        "region": "global"
    }
)

if result.success:
    analysis = result.output
    print(f"Market: {analysis['market']} ({analysis['region']})")
    print(f"Market Size: {analysis['size_estimate']}")
    print(f"Growth Rate: {analysis['growth_rate']}")
    print(f"Confidence: {analysis['confidence']:.0%}")

    print("\nKey Trends:")
    for trend in analysis['key_trends']:
        print(f"  - {trend}")

    print("\nOpportunities:")
    for opp in analysis['opportunities']:
        print(f"  - {opp['area']}: {opp['potential']} potential")

    print("\nRisks:")
    for risk in analysis['risks']:
        print(f"  - {risk}")
```

### Trend Prediction

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Predict trends for the next year
result = client.execute_agent(
    agent_id="research-analyzer",
    capability="trend-prediction",
    input_data={
        "topic": "enterprise-software",
        "horizon": "12_months"
    }
)

if result.success:
    prediction = result.output
    print(f"Topic: {prediction['topic']}")
    print(f"Horizon: {prediction['horizon']}")
    print(f"Methodology: {prediction['methodology']}")
    print(f"Overall Confidence: {prediction['confidence']:.0%}")

    print("\nPredictions:")
    for pred in sorted(prediction['predictions'], key=lambda x: -x['probability']):
        print(f"  {pred['trend']}")
        print(f"    Probability: {pred['probability']:.0%}")
        print(f"    Impact: {pred['impact']}")
```

### Competitive Intelligence

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Analyze competitive landscape
result = client.execute_agent(
    agent_id="research-analyzer",
    capability="competitive-intelligence",
    input_data={
        "industry": "cloud-services"
    }
)

if result.success:
    intel = result.output
    print(f"Industry: {intel['industry']}")
    print(f"Competitors Analyzed: {intel['competitors_analyzed']}")
    print(f"Landscape: {intel['competitive_landscape']}")

    print("\nMarket Leaders:")
    for leader in intel['market_leaders']:
        print(f"  {leader['name']}")
        print(f"    Market Share: {leader['market_share']}")
        print(f"    Key Strength: {leader['strength']}")

    print("\nDifferentiators:")
    for diff in intel['differentiators']:
        print(f"  - {diff}")

    print("\nRecommendations:")
    for rec in intel['recommendations']:
        print(f"  - {rec}")
```

### Data Aggregation Pipeline

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Aggregate data from multiple sources
result = client.execute_agent(
    agent_id="research-analyzer",
    capability="data-aggregation",
    input_data={
        "sources": [
            "internal-sales-data",
            "market-research-reports",
            "social-media-analytics",
            "web-traffic-data"
        ],
        "query": {
            "topic": "customer-behavior",
            "segment": "enterprise",
            "time_period": "q4_2025"
        }
    }
)

if result.success:
    agg = result.output
    print(f"Sources Queried: {agg['sources_queried']}")
    print(f"Records Collected: {agg['records_collected']}")
    print(f"Data Quality: {agg['data_quality']}")

    summary = agg['aggregation_summary']
    print(f"\nSummary:")
    print(f"  Total Records: {summary['total_records']}")
    print(f"  Unique Entities: {summary['unique_entities']}")
    print(f"  Time Range: {summary['time_range']}")
```

### Research Report Generation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Generate a comprehensive market report
result = client.execute_agent(
    agent_id="research-analyzer",
    capability="report-generation",
    input_data={
        "type": "market_analysis",
        "topic": "Sustainable Energy Market"
    }
)

if result.success:
    report = result.output
    print(f"Report ID: {report['report_id']}")
    print(f"Title: {report['title']}")
    print(f"Summary: {report['summary']}")
    print(f"Confidence: {report['confidence']:.0%}")
    print(f"Created: {report['created_at']}")

    print(f"\nFindings ({report['findings_count']}):")
    # Findings would be in the full report
```

### Comprehensive Analysis Workflow

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def comprehensive_market_analysis(market, region):
    """Run a full market analysis workflow."""

    results = {}

    # Step 1: Market Analysis
    market_result = client.execute_agent(
        agent_id="research-analyzer",
        capability="market-analysis",
        input_data={"market": market, "region": region}
    )
    results['market'] = market_result.output if market_result.success else None

    # Step 2: Trend Prediction
    trend_result = client.execute_agent(
        agent_id="research-analyzer",
        capability="trend-prediction",
        input_data={"topic": market, "horizon": "12_months"}
    )
    results['trends'] = trend_result.output if trend_result.success else None

    # Step 3: Competitive Intelligence
    comp_result = client.execute_agent(
        agent_id="research-analyzer",
        capability="competitive-intelligence",
        input_data={"industry": market}
    )
    results['competitive'] = comp_result.output if comp_result.success else None

    # Step 4: Generate Report
    report_result = client.execute_agent(
        agent_id="research-analyzer",
        capability="report-generation",
        input_data={
            "type": "market_analysis",
            "topic": f"{market} in {region}"
        }
    )
    results['report'] = report_result.output if report_result.success else None

    return results

# Run comprehensive analysis
analysis = comprehensive_market_analysis("cybersecurity", "europe")

print("=== Comprehensive Market Analysis ===")
if analysis['market']:
    print(f"\nMarket Size: {analysis['market']['size_estimate']}")
    print(f"Growth Rate: {analysis['market']['growth_rate']}")

if analysis['trends']:
    print(f"\nTop Predicted Trend: {analysis['trends']['predictions'][0]['trend']}")

if analysis['competitive']:
    print(f"\nMarket Leader: {analysis['competitive']['market_leaders'][0]['name']}")

if analysis['report']:
    print(f"\nReport ID: {analysis['report']['report_id']}")
```

### Async Research Operations

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def parallel_market_research():
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Run multiple analyses in parallel
        markets = ["fintech", "healthtech", "edtech", "cleantech"]

        tasks = [
            client.execute_agent(
                agent_id="research-analyzer",
                capability="market-analysis",
                input_data={"market": market, "region": "global"}
            )
            for market in markets
        ]

        results = await asyncio.gather(*tasks)

        print("Market Analysis Summary:")
        for market, result in zip(markets, results):
            if result.success:
                print(f"\n{market.upper()}:")
                print(f"  Size: {result.output['size_estimate']}")
                print(f"  Growth: {result.output['growth_rate']}")

asyncio.run(parallel_market_research())
```

## Configuration Options

### Analysis Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `confidence_threshold` | Minimum confidence for insights | 0.7 |
| `data_freshness` | Maximum age of data sources | 30 days |
| `source_diversity` | Minimum unique sources required | 3 |

### Report Configuration

```python
report_config = {
    "format": "detailed",  # or "executive", "brief"
    "include_methodology": True,
    "include_sources": True,
    "confidence_display": True,
    "visualization": True
}
```

## Best Practices

### 1. Market Analysis
- Define clear market boundaries
- Specify appropriate geographic scope
- Validate findings against multiple sources
- Consider market maturity in interpretation

### 2. Trend Prediction
- Use appropriate time horizons
- Consider confidence intervals
- Combine with expert judgment
- Update predictions regularly

### 3. Competitive Intelligence
- Maintain ethical data collection practices
- Verify competitor information accuracy
- Track changes over time
- Focus on actionable insights

### 4. Report Generation
- Define clear objectives before generating
- Review and validate findings
- Include methodology transparency
- Archive reports for future reference

### 5. Data Aggregation
- Verify source reliability
- Handle missing data appropriately
- Document data transformations
- Monitor data quality metrics

## Related Agents

- **Data Processor Agent:** Pre-process data for analysis
- **Finance Analyst Agent:** Financial aspects of market analysis
- **Content Creator Agent:** Create presentations from reports

## Troubleshooting

### Common Issues

**Low confidence scores:**
- Increase data sources
- Narrow analysis scope
- Check data freshness

**Incomplete analysis:**
- Verify all required parameters
- Check source availability
- Review capability requirements

**Slow report generation:**
- Reduce analysis scope
- Pre-aggregate data
- Use caching where appropriate

## Implementation Reference

**Source:** `built_in_agents/business/research/agent.py`
