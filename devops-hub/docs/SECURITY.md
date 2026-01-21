# Security Guide

> **Last Updated:** 2026-01-12

This guide covers security features and best practices for DevOps Hub.

## Security Features

| Feature | Status | Location |
|---------|--------|----------|
| API Key Authentication | Enabled | `core/auth.py` |
| Scope-based Authorization | Enabled | `core/auth.py` |
| Rate Limiting | Enabled | `service/rate_limiter.py` |
| Security Headers | Enabled | `service/security.py` |
| Input Validation | Available | `service/security.py` |
| Audit Logging | Available | `service/security.py` |

## Authentication

All API requests require an API key:

```bash
curl -H "Authorization: Bearer dh_xxxxxxxxxxxx" \
  http://localhost:8100/api/agents
```

## Authorization Scopes

| Scope | Permissions |
|-------|-------------|
| `read` | List and get resources |
| `write` | Create and update resources |
| `execute` | Execute agents and workflows |
| `admin` | All permissions + key management |

## Input Validation

Use the security utilities in `service/security.py`:

```python
from service.security import validate_id, validate_name, sanitize_string

agent_id = validate_id(request.path_params["agent_id"])
name = validate_name(data.get("name"))
```

## Security Headers

All responses include:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

## Rate Limiting

Configure via environment:

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
```

## Security Checklist

### Pre-Deployment
- [ ] HTTPS enabled
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] Secrets in secrets manager
- [ ] API keys stored securely

### Periodic Tasks
- Rotate API keys every 90 days
- Review access logs weekly
- Update dependencies monthly
