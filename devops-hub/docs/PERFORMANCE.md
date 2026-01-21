# Performance Optimization Guide

> **Last Updated:** 2026-01-12
> **Version:** 1.0.0

This guide covers performance optimization strategies for DevOps Hub.

---

## Table of Contents

1. [Response Caching](#response-caching)
2. [Connection Pooling](#connection-pooling)
3. [Async Best Practices](#async-best-practices)
4. [Database Optimization](#database-optimization)
5. [Resource Tuning](#resource-tuning)
6. [Profiling & Benchmarking](#profiling--benchmarking)

---

## Response Caching

### Overview

DevOps Hub includes a caching layer (`service/cache.py`) that supports:
- In-memory caching (default)
- Redis-backed caching (production)
- Automatic fallback from Redis to memory

### Using the Cache

```python
from service.cache import cached, get_cache_manager, invalidate_cache

# Cache function results for 5 minutes
@cached(ttl=300)
async def get_agents():
    return await agent_repository.list_all()

# Cache with custom key prefix
@cached(ttl=60, key_prefix="agent")
async def get_agent(agent_id: str):
    return await agent_repository.get(agent_id)

# Invalidate cache after writes
@invalidate_cache(key_pattern="agents")
async def create_agent(agent_data):
    return await agent_repository.save(agent_data)
```

### Manual Cache Operations

```python
cache = await get_cache_manager()

# Get value
value = await cache.get("my_key")

# Set value with TTL
await cache.set("my_key", {"data": "value"}, ttl=60)

# Delete key
await cache.delete("my_key")

# Clear all
await cache.clear()

# Get stats
stats = cache.stats
```

### Configuration

```env
# Use Redis for caching (recommended for production)
REDIS_URL=redis://localhost:6379/0

# Cache settings
CACHE_DEFAULT_TTL=300
CACHE_MAX_SIZE=1000
```

### Cache Strategy by Endpoint

| Endpoint | TTL | Notes |
|----------|-----|-------|
| `/agents` (list) | 60s | Moderate cache, invalidate on changes |
| `/agents/{id}` | 300s | Longer cache for individual agents |
| `/workflows` (list) | 60s | Moderate cache |
| `/discover` | 300s | Stable data, cache longer |
| `/health` | No cache | Real-time status needed |
| `/metrics` | No cache | Must be current |

---

## Connection Pooling

### HTTP Client Pooling

Use `httpx` with connection pooling for external requests:

```python
import httpx

# Create a reusable client with connection pooling
async def get_http_client():
    return httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
    )

# Use context manager for proper cleanup
async with get_http_client() as client:
    response = await client.get("https://api.example.com/data")
```

### Database Connection Pooling

For SQLite (development):
```python
# Thread-local connections are used automatically
# No explicit pooling needed for SQLite
```

For PostgreSQL (production):
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # Base pool size
    max_overflow=10,       # Additional connections allowed
    pool_timeout=30,       # Wait timeout for connection
    pool_recycle=1800,     # Recycle connections after 30 min
    pool_pre_ping=True,    # Verify connections before use
)
```

### Redis Connection Pooling

```python
import redis.asyncio as aioredis

# Create connection pool
pool = aioredis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=20,
    decode_responses=True
)

# Use the pool
redis_client = aioredis.Redis(connection_pool=pool)
```

---

## Async Best Practices

### Concurrent Execution

Use `asyncio.gather` for independent operations:

```python
# BAD - Sequential execution
result1 = await fetch_data_1()
result2 = await fetch_data_2()
result3 = await fetch_data_3()

# GOOD - Concurrent execution
result1, result2, result3 = await asyncio.gather(
    fetch_data_1(),
    fetch_data_2(),
    fetch_data_3()
)
```

### Avoid Blocking Operations

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

# BAD - Blocks the event loop
def blocking_io():
    return open("large_file.txt").read()

# GOOD - Run in executor
async def non_blocking_io():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, blocking_io)
```

### Semaphores for Rate Limiting

```python
# Limit concurrent external API calls
semaphore = asyncio.Semaphore(10)

async def rate_limited_request(url):
    async with semaphore:
        return await http_client.get(url)

# Process many URLs without overwhelming the API
results = await asyncio.gather(*[
    rate_limited_request(url) for url in urls
])
```

### Task Timeouts

```python
# Prevent hanging tasks
async def fetch_with_timeout(url, timeout=30):
    try:
        return await asyncio.wait_for(
            http_client.get(url),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Request to {url} timed out")
        return None
```

---

## Database Optimization

### Query Optimization

```python
# BAD - N+1 query problem
agents = await get_all_agents()
for agent in agents:
    capabilities = await get_capabilities(agent.id)  # N queries!

# GOOD - Single query with join or batch fetch
agents_with_capabilities = await get_agents_with_capabilities()
```

### Indexing Strategy

```sql
-- Frequently queried columns should be indexed
CREATE INDEX idx_agents_domain ON agents(domain);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

### Batch Operations

```python
# BAD - Individual inserts
for event in events:
    await save_event(event)

# GOOD - Batch insert
await save_events_batch(events)
```

### Query Result Limiting

```python
# Always limit results for list endpoints
async def get_events(limit: int = 100, offset: int = 0):
    return await db.fetch_all(
        "SELECT * FROM events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
```

---

## Resource Tuning

### Gunicorn Workers

```bash
# workers = (2 x CPU cores) + 1
# For 4 CPU cores:
gunicorn service.api:app -w 9 -k uvicorn.workers.UvicornWorker
```

**Environment variables:**
```env
GUNICORN_WORKERS=9
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=30
GUNICORN_KEEPALIVE=5
```

### Uvicorn Settings

```bash
uvicorn service.api:app \
    --workers 4 \
    --limit-concurrency 1000 \
    --limit-max-requests 10000 \
    --timeout-keep-alive 30
```

### Memory Limits (Docker)

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### Connection Limits

```env
# Redis
REDIS_MAX_CONNECTIONS=100

# PostgreSQL
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# HTTP Client
HTTP_MAX_CONNECTIONS=100
HTTP_MAX_KEEPALIVE=20
```

---

## Profiling & Benchmarking

### Request Profiling

Add profiling middleware (development only):

```python
import cProfile
import pstats
import io

@app.middleware("http")
async def profile_request(request: Request, call_next):
    if os.getenv("PROFILING_ENABLED") != "true":
        return await call_next(request)

    profiler = cProfile.Profile()
    profiler.enable()

    response = await call_next(request)

    profiler.disable()
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)
    logger.debug(f"Profile for {request.url.path}:\n{s.getvalue()}")

    return response
```

### Load Testing

Using `wrk`:
```bash
# Basic load test
wrk -t12 -c400 -d30s http://localhost:8100/api/agents

# With POST data
wrk -t12 -c400 -d30s -s post.lua http://localhost:8100/api/agents
```

Using `hey`:
```bash
hey -n 10000 -c 100 http://localhost:8100/api/agents
```

Using `locust`:
```python
# locustfile.py
from locust import HttpUser, task, between

class DevOpsHubUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_agents(self):
        self.client.get("/api/agents")

    @task(1)
    def get_health(self):
        self.client.get("/health")
```

### Memory Profiling

```python
# Using memory_profiler
from memory_profiler import profile

@profile
async def memory_intensive_function():
    # Your code here
    pass
```

### Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| P95 Latency | < 100ms | > 500ms |
| Error Rate | < 0.1% | > 1% |
| Memory Usage | < 70% | > 85% |
| CPU Usage | < 60% | > 80% |
| Cache Hit Rate | > 80% | < 50% |
| Connection Pool Usage | < 70% | > 90% |

---

## Quick Wins Checklist

- [ ] Enable response caching for read endpoints
- [ ] Use connection pooling for all external connections
- [ ] Add database indexes for frequently queried columns
- [ ] Use `asyncio.gather` for concurrent operations
- [ ] Set appropriate Gunicorn worker count
- [ ] Configure Redis for production caching
- [ ] Add query result limits to all list endpoints
- [ ] Use batch operations for bulk inserts
- [ ] Profile slow endpoints and optimize
- [ ] Set up load testing for capacity planning

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment configuration
- [MONITORING.md](./MONITORING.md) - Performance monitoring
- [DATABASE_MIGRATION.md](./DATABASE_MIGRATION.md) - Database setup
