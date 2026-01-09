# Data Processor Agent

**Agent ID:** `data-processor`
**Version:** 1.0.0
**Type:** Worker
**Domain:** Business
**Status:** Production

## Overview

The Data Processor Agent handles ETL (Extract, Transform, Load) operations, data transformations, aggregations, and data quality assurance. It is the backbone of data operations in the DevOps Hub, ensuring data flows correctly between systems while maintaining quality and consistency.

This agent supports various data formats, transformation rules, and validation schemas, making it essential for data pipeline operations.

## Capabilities

### 1. Data Transformation
**Name:** `data-transformation`

Transform data between different formats and structures.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `source_format` | string | Source data format (json, csv, xml, etc.) |
| `target_format` | string | Target data format |
| `data` | array/object | Data to transform |
| `mapping` | object | Field mapping rules (optional) |

**Returns:** Transformed data with record count

### 2. ETL
**Name:** `etl`

Run extract, transform, load pipelines.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | ETL job name |
| `source` | string | Data source identifier |
| `destination` | string | Data destination identifier |
| `record_count` | number | Expected record count (optional) |
| `transforms` | array | Transformation rules (optional) |

**Returns:** Job status with records processed and errors

### 3. Aggregation
**Name:** `aggregation`

Aggregate and summarize large datasets.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | array | Data to aggregate |
| `group_by` | array | Fields to group by |
| `aggregations` | array | Aggregation functions: `sum`, `count`, `avg`, `min`, `max` |

**Returns:** Aggregated results with sample data

### 4. Quality Assurance
**Name:** `quality-assurance`

Validate and ensure data quality.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | array | Data to validate |
| `rules` | array | Quality rules to apply (optional) |

**Returns:** Quality score, issues found, and recommendations

### 5. Schema Validation
**Name:** `schema-validation`

Validate data against defined schemas.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | object | Data to validate |
| `schema` | object | JSON Schema definition |

**Returns:** Validation result with errors and warnings

## Supported Protocols

- **A2A (Agent-to-Agent):** Version 1.0
- **ACP (Agent Communication Protocol):** Version 1.0
- **MCP (Model Context Protocol):** Version 1.0

## API Usage Examples

### Using curl

#### Transform Data
```bash
curl -X POST http://localhost:8100/agents/data-processor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "data-transformation",
    "input_data": {
      "source_format": "json",
      "target_format": "csv",
      "data": [
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "LA"}
      ]
    }
  }'
```

#### Run ETL Job
```bash
curl -X POST http://localhost:8100/agents/data-processor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "etl",
    "input_data": {
      "name": "daily_sales_sync",
      "source": "sales_db",
      "destination": "analytics_warehouse",
      "record_count": 10000
    }
  }'
```

#### Aggregate Data
```bash
curl -X POST http://localhost:8100/agents/data-processor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "aggregation",
    "input_data": {
      "group_by": ["region", "product_category"],
      "aggregations": ["sum", "count", "avg"]
    }
  }'
```

#### Check Data Quality
```bash
curl -X POST http://localhost:8100/agents/data-processor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "quality-assurance",
    "input_data": {
      "data": [
        {"id": 1, "email": "user@example.com", "name": "User"},
        {"id": 2, "email": "", "name": ""}
      ],
      "rules": ["no_empty_values", "valid_email"]
    }
  }'
```

#### Validate Schema
```bash
curl -X POST http://localhost:8100/agents/data-processor/execute \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "schema-validation",
    "input_data": {
      "data": {
        "id": 123,
        "name": "Product",
        "price": 29.99
      },
      "schema": {
        "type": "object",
        "required": ["id", "name", "price"],
        "properties": {
          "id": {"type": "integer"},
          "name": {"type": "string"},
          "price": {"type": "number"}
        }
      }
    }
  }'
```

## Python SDK Examples

### Data Transformation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Transform JSON to normalized structure
data = [
    {"user_name": "alice", "user_email": "alice@example.com", "signup_date": "2025-01-15"},
    {"user_name": "bob", "user_email": "bob@example.com", "signup_date": "2025-01-16"},
]

result = client.execute_agent(
    agent_id="data-processor",
    capability="data-transformation",
    input_data={
        "source_format": "json",
        "target_format": "json",
        "data": data,
        "mapping": {
            "user_name": "name",
            "user_email": "email",
            "signup_date": "created_at"
        }
    }
)

if result.success:
    print(f"Transformed: {result.output['records_transformed']} records")
    print(f"Source format: {result.output['source_format']}")
    print(f"Target format: {result.output['target_format']}")
```

### ETL Pipeline

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Run an ETL job
result = client.execute_agent(
    agent_id="data-processor",
    capability="etl",
    input_data={
        "name": "customer_data_sync",
        "source": "crm_database",
        "destination": "data_warehouse",
        "transforms": [
            {"type": "filter", "condition": "status = 'active'"},
            {"type": "map", "field": "name", "transform": "uppercase"},
            {"type": "enrich", "lookup": "region_mapping"}
        ]
    }
)

if result.success:
    job = result.output
    print(f"Job ID: {job['job_id']}")
    print(f"Status: {job['status']}")
    print(f"Records Processed: {job['records_processed']}")
    print(f"Errors: {job['errors']}")
```

### Data Aggregation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Aggregate sales data
result = client.execute_agent(
    agent_id="data-processor",
    capability="aggregation",
    input_data={
        "group_by": ["product_category", "region"],
        "aggregations": ["sum", "count", "avg", "max"]
    }
)

if result.success:
    agg = result.output
    print(f"Aggregation complete: {agg['aggregated']}")
    print(f"Groups: {agg['group_by']}")
    print(f"Functions: {agg['aggregations_applied']}")
    print(f"Result count: {agg['result_count']}")

    print("\nSample Results:")
    for row in agg['sample_results']:
        print(f"  {row['group']}: sum={row['sum']}, count={row['count']}")
```

### Quality Assurance

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Check data quality
sample_data = [
    {"id": 1, "email": "valid@email.com", "phone": "123-456-7890"},
    {"id": 2, "email": "invalid-email", "phone": ""},
    {"id": 3, "email": "", "phone": "987-654-3210"},
]

result = client.execute_agent(
    agent_id="data-processor",
    capability="quality-assurance",
    input_data={
        "data": sample_data,
        "rules": [
            "no_empty_required_fields",
            "valid_email_format",
            "valid_phone_format"
        ]
    }
)

if result.success:
    qa = result.output
    print(f"Quality Score: {qa['quality_score']:.0%}")
    print(f"Issues Found: {qa['issues_found']}")

    print("\nIssues:")
    for issue in qa['issues']:
        print(f"  [{issue['severity'].upper()}] {issue['type']}: {issue['count']} occurrences")

    print("\nRecommendations:")
    for rec in qa['recommendations']:
        print(f"  - {rec}")
```

### Schema Validation

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

# Define schema
user_schema = {
    "type": "object",
    "required": ["id", "email", "name"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "email": {"type": "string", "format": "email"},
        "name": {"type": "string", "minLength": 1},
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
        "roles": {"type": "array", "items": {"type": "string"}}
    }
}

# Validate data
user_data = {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "age": 30,
    "roles": ["admin", "user"]
}

result = client.execute_agent(
    agent_id="data-processor",
    capability="schema-validation",
    input_data={
        "data": user_data,
        "schema": user_schema
    }
)

if result.success:
    validation = result.output
    print(f"Valid: {validation['valid']}")
    print(f"Fields Validated: {validation['fields_validated']}")

    if validation['errors']:
        print("\nErrors:")
        for error in validation['errors']:
            print(f"  - {error}")

    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  - {warning['path']}: {warning['message']}")
```

### Batch Processing Pipeline

```python
from sdk import AgentServiceClient

client = AgentServiceClient("http://localhost:8100")

def process_data_batch(data, schema):
    """Complete data processing pipeline."""

    # Step 1: Validate schema
    validation = client.execute_agent(
        agent_id="data-processor",
        capability="schema-validation",
        input_data={"data": data, "schema": schema}
    )

    if not validation.success or not validation.output['valid']:
        print("Schema validation failed")
        return None

    # Step 2: Quality check
    quality = client.execute_agent(
        agent_id="data-processor",
        capability="quality-assurance",
        input_data={"data": data}
    )

    if quality.output['quality_score'] < 0.8:
        print(f"Quality score too low: {quality.output['quality_score']:.0%}")
        return None

    # Step 3: Transform
    transformed = client.execute_agent(
        agent_id="data-processor",
        capability="data-transformation",
        input_data={
            "source_format": "json",
            "target_format": "json",
            "data": data
        }
    )

    # Step 4: Load via ETL
    etl_result = client.execute_agent(
        agent_id="data-processor",
        capability="etl",
        input_data={
            "name": "batch_load",
            "source": "memory",
            "destination": "target_db"
        }
    )

    return etl_result.output

# Usage
batch_data = [
    {"id": 1, "value": 100},
    {"id": 2, "value": 200}
]

schema = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "value"],
        "properties": {
            "id": {"type": "integer"},
            "value": {"type": "number"}
        }
    }
}

result = process_data_batch(batch_data, schema)
if result:
    print(f"Batch processed: {result['records_processed']} records")
```

### Async Data Processing

```python
import asyncio
from sdk import AsyncAgentServiceClient

async def parallel_etl_jobs():
    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        # Define multiple ETL jobs
        jobs = [
            {"name": "sales_sync", "source": "sales_db", "destination": "warehouse"},
            {"name": "customer_sync", "source": "crm_db", "destination": "warehouse"},
            {"name": "inventory_sync", "source": "inventory_db", "destination": "warehouse"},
        ]

        # Run jobs in parallel
        tasks = [
            client.execute_agent(
                agent_id="data-processor",
                capability="etl",
                input_data=job
            )
            for job in jobs
        ]

        results = await asyncio.gather(*tasks)

        print("ETL Jobs Summary:")
        total_records = 0
        for job, result in zip(jobs, results):
            if result.success:
                records = result.output['records_processed']
                total_records += records
                print(f"  {job['name']}: {records} records")
            else:
                print(f"  {job['name']}: FAILED")

        print(f"\nTotal records processed: {total_records}")

asyncio.run(parallel_etl_jobs())
```

## Configuration Options

### ETL Configuration

```python
etl_config = {
    "batch_size": 1000,
    "parallel_workers": 4,
    "error_threshold": 0.01,  # Max 1% errors
    "retry_failed": True,
    "retry_attempts": 3,
    "checkpoint_enabled": True
}
```

### Quality Rules

| Rule | Description |
|------|-------------|
| `no_empty_values` | Check for null/empty values |
| `no_duplicates` | Check for duplicate records |
| `valid_email` | Validate email format |
| `valid_phone` | Validate phone format |
| `in_range` | Check numeric ranges |
| `regex_match` | Match against regex pattern |

### Transformation Types

| Transform | Description |
|-----------|-------------|
| `map` | Map field to new name/value |
| `filter` | Filter records by condition |
| `enrich` | Add data from lookup |
| `aggregate` | Group and aggregate |
| `split` | Split field into multiple |
| `merge` | Merge multiple fields |

## Best Practices

### 1. Data Transformation
- Define clear mapping rules
- Handle missing fields gracefully
- Validate after transformation
- Log transformation decisions

### 2. ETL Operations
- Use appropriate batch sizes
- Implement checkpointing for large jobs
- Monitor error rates
- Set up retry mechanisms

### 3. Data Quality
- Define quality thresholds
- Run quality checks before processing
- Track quality metrics over time
- Automate remediation where possible

### 4. Schema Validation
- Use strict schemas for critical data
- Version your schemas
- Validate early in pipelines
- Handle validation errors gracefully

### 5. Performance
- Process in batches for large datasets
- Use parallel processing where applicable
- Monitor memory usage
- Optimize transformation rules

## Related Agents

- **Research Analyzer Agent:** Uses processed data for analysis
- **Finance Analyst Agent:** Financial data processing
- **Error Handler Agent:** Handles processing errors

## Troubleshooting

### Common Issues

**ETL job failures:**
- Check source connectivity
- Verify destination permissions
- Review transformation rules
- Check error logs

**Low quality scores:**
- Review data source quality
- Adjust quality rules
- Implement data cleansing

**Transformation errors:**
- Verify field mappings
- Check data types
- Handle edge cases

## Implementation Reference

**Source:** `built_in_agents/business/data_processor/agent.py`
