# API Versioning Guide

> **Last Updated:** 2026-01-12
> **Version:** 1.0.0

This guide covers API versioning strategy, implementation, and deprecation policies for DevOps Hub.

---

## Table of Contents

1. [Versioning Strategy](#versioning-strategy)
2. [Version Headers](#version-headers)
3. [URL Versioning](#url-versioning)
4. [Deprecation Policy](#deprecation-policy)
5. [Migration Guide](#migration-guide)
6. [Implementation](#implementation)

---

## Versioning Strategy

### Current Version

| API Version | Status | Supported Until |
|-------------|--------|-----------------|
| v1 (default) | Current | - |

### Versioning Approach

DevOps Hub uses a hybrid versioning strategy:

1. **URL Path Versioning** (Primary): `/api/v1/agents`
2. **Header Versioning** (Alternative): `Accept: application/vnd.devops-hub.v1+json`

Both methods are supported; URL versioning is recommended for simplicity.

### Semantic Versioning for APIs

- **Major version** (v1 → v2): Breaking changes
- **Minor additions**: Non-breaking, no version bump
- **Patches**: Bug fixes, no version bump

**Breaking changes include:**
- Removing endpoints
- Removing required request fields
- Changing response structure
- Changing field types
- Removing response fields

**Non-breaking changes include:**
- Adding new endpoints
- Adding optional request fields
- Adding response fields
- Performance improvements
- Bug fixes

---

## Version Headers

### Request Headers

```http
# Specify API version (optional - defaults to latest)
Accept: application/vnd.devops-hub.v1+json

# Alternative header
X-API-Version: 1
```

### Response Headers

```http
# Current API version
X-API-Version: 1

# Deprecation warning (when applicable)
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/agents>; rel="successor-version"
```

### Version Negotiation

```python
# Example: Parse version from headers
def get_api_version(request: Request) -> int:
    # Check Accept header
    accept = request.headers.get("Accept", "")
    if "vnd.devops-hub.v" in accept:
        match = re.search(r"vnd\.devops-hub\.v(\d+)", accept)
        if match:
            return int(match.group(1))

    # Check X-API-Version header
    version_header = request.headers.get("X-API-Version")
    if version_header:
        return int(version_header)

    # Default to latest version
    return 1
```

---

## URL Versioning

### Endpoint Structure

```
/api/v1/agents          # List agents
/api/v1/agents/{id}     # Get agent
/api/v1/workflows       # List workflows
/api/v1/discover        # Discovery endpoint
/api/v1/health          # Health check
```

### Router Configuration

```python
from fastapi import APIRouter

# Version 1 router
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/agents")
async def list_agents():
    ...

@v1_router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    ...

# Mount versioned router
app.include_router(v1_router)

# Also mount at /api for backwards compatibility
app.include_router(v1_router, prefix="/api")
```

### Backwards Compatibility

During the transition period, unversioned endpoints remain available:

| Versioned | Unversioned (Deprecated) |
|-----------|--------------------------|
| `/api/v1/agents` | `/api/agents` |
| `/api/v1/workflows` | `/workflows` |

Unversioned endpoints will return a deprecation warning header.

---

## Deprecation Policy

### Timeline

| Phase | Duration | Actions |
|-------|----------|---------|
| Announcement | - | Document in changelog, notify users |
| Deprecation | 6 months | Add deprecation headers, log warnings |
| Sunset | 3 months | Return 410 Gone with migration info |
| Removal | - | Remove code |

### Deprecation Headers

When an endpoint or field is deprecated:

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jul 2027 00:00:00 GMT
Link: </api/v2/agents>; rel="successor-version"
X-Deprecation-Notice: This endpoint is deprecated. Use /api/v2/agents instead.
```

### Deprecation Response Body

```json
{
  "data": [...],
  "_deprecation": {
    "message": "This endpoint is deprecated",
    "sunset_date": "2027-07-01",
    "successor": "/api/v2/agents",
    "documentation": "https://docs.devops-hub.io/migration/v1-to-v2"
  }
}
```

### Field Deprecation

For deprecated fields within a response:

```json
{
  "id": "agent-123",
  "name": "My Agent",
  "type": "worker",           // Current field
  "agent_type": "worker",     // Deprecated alias
  "_deprecated_fields": ["agent_type"]
}
```

---

## Migration Guide

### v1 (Current)

This is the current stable version. All new integrations should use v1.

### Future: v1 to v2 Migration

When v2 is released, this section will contain:

1. **Breaking Changes Summary**
   - List of removed endpoints
   - Changed field names
   - New required fields

2. **Migration Steps**
   - Update base URL from `/api/` to `/api/v2/`
   - Update request/response handling for changed fields
   - Test all integrations

3. **Compatibility Shims**
   - Temporary aliases for renamed fields
   - Redirect rules for moved endpoints

### Migration Testing

```bash
# Test against v1 (current)
curl -H "X-API-Version: 1" http://localhost:8100/api/v1/agents

# Test against v2 (when available)
curl -H "X-API-Version: 2" http://localhost:8100/api/v2/agents
```

---

## Implementation

### Version Middleware

```python
# service/versioning.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

CURRENT_VERSION = 1
SUPPORTED_VERSIONS = [1]
DEPRECATED_VERSIONS = []

class VersioningMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Parse requested version
        version = self._get_version(request)

        # Validate version
        if version not in SUPPORTED_VERSIONS:
            return JSONResponse(
                status_code=400,
                content={"error": f"API version {version} is not supported"}
            )

        # Store version in request state
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version header
        response.headers["X-API-Version"] = str(version)

        # Add deprecation headers if needed
        if version in DEPRECATED_VERSIONS:
            response.headers["Deprecation"] = "true"
            response.headers["X-Deprecation-Notice"] = (
                f"API version {version} is deprecated. "
                f"Please migrate to version {CURRENT_VERSION}."
            )

        return response

    def _get_version(self, request: Request) -> int:
        # Check URL path
        path = request.url.path
        if "/v" in path:
            match = re.search(r"/v(\d+)/", path)
            if match:
                return int(match.group(1))

        # Check headers
        accept = request.headers.get("Accept", "")
        if "vnd.devops-hub.v" in accept:
            match = re.search(r"vnd\.devops-hub\.v(\d+)", accept)
            if match:
                return int(match.group(1))

        version_header = request.headers.get("X-API-Version")
        if version_header:
            return int(version_header)

        return CURRENT_VERSION
```

### Versioned Routers

```python
# service/api.py
from fastapi import FastAPI, APIRouter

app = FastAPI(title="DevOps Hub")

# Version 1 endpoints
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

@v1_router.get("/agents")
async def list_agents_v1():
    return await get_agents()

# Future: Version 2 endpoints
# v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
# @v2_router.get("/agents")
# async def list_agents_v2():
#     return await get_agents_v2()

# Mount routers
app.include_router(v1_router)
# app.include_router(v2_router)

# Backwards compatibility: mount v1 at root
legacy_router = APIRouter(prefix="/api", tags=["legacy"], deprecated=True)
app.include_router(legacy_router)
```

### OpenAPI Documentation

Each version has its own documentation:

- `/api/v1/docs` - Version 1 documentation
- `/api/v2/docs` - Version 2 documentation (when available)
- `/docs` - Latest version documentation

```python
app = FastAPI(
    title="DevOps Hub API",
    version="1.0.0",
    openapi_tags=[
        {"name": "v1", "description": "Current stable API"},
        {"name": "legacy", "description": "Deprecated endpoints"},
    ]
)
```

---

## Best Practices

### For API Developers

1. **Plan for versioning** from the start
2. **Use consistent naming** across versions
3. **Document all changes** in changelog
4. **Provide migration guides** for breaking changes
5. **Support old versions** for reasonable time
6. **Monitor usage** of deprecated endpoints

### For API Consumers

1. **Always specify version** in requests
2. **Monitor deprecation headers** in responses
3. **Subscribe to changelog** for updates
4. **Test against new versions** before migration
5. **Plan migration** well before sunset date

---

## Changelog

### v1.0.0 (Current)

Initial release with:
- Agent management endpoints
- Workflow execution
- Discovery and health checks
- WebSocket streaming
- API key authentication

---

## Related Documentation

- [API Reference](/docs) - Full API documentation
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- [../PRODUCTION_ROADMAP.md](../PRODUCTION_ROADMAP.md) - Project roadmap
