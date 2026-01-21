# Brandiverse Portfolio API - Revenue Stream Documentation

## Overview

The **brandiverse-portfolio** (DevOps Hub) provides a comprehensive API for portfolio management, analysis, and automation. This API can be **monetized** as a SaaS service for developers, agencies, and enterprises.

---

## Revenue Model

### Target Markets
1. **Solo Developers** - Portfolio management and automation
2. **Development Agencies** - Multi-project oversight and client reporting
3. **Enterprise Teams** - Repository intelligence and monetization analysis
4. **AI Agents** - Programmatic access to portfolio insights

### Pricing Tiers

| Tier | Price/Month | Projects | API Calls/Month | Features |
|------|-------------|----------|-----------------|----------|
| **Free** | $0 | 5 | 100 | Basic analytics, manual sync |
| **Pro** | $29 | 25 | 5,000 | Real-time analysis, automation workflows |
| **Agency** | $99 | 100 | 25,000 | Multi-tenant, team collaboration, webhooks |
| **Enterprise** | $299 | Unlimited | Unlimited | Custom integrations, dedicated support, SLA |

### Revenue Potential
- **Year 1**: 50 users (40 Free, 7 Pro, 2 Agency, 1 Enterprise) = **$701/month** = **$8,412/year**
- **Year 2**: 200 users (150 Free, 35 Pro, 12 Agency, 3 Enterprise) = **$3,103/month** = **$37,236/year**
- **Year 3**: 1,000 users = **$15,000+/month** = **$180,000+/year**

---

## API Endpoints

### Authentication

All API requests require an API key in the header:
```
Authorization: Bearer {api_key}
```

**Create API Key:**
```bash
POST /auth/keys
Content-Type: application/json

{
  "name": "my-api-key",
  "scopes": ["portfolio:read", "automation:execute"]
}
```

**Response:**
```json
{
  "key": "bv_live_1234567890abcdef",
  "key_id": "key_abc123",
  "name": "my-api-key",
  "scopes": ["portfolio:read", "automation:execute"]
}
```

---

### Portfolio Endpoints

#### 1. Get Portfolio Summary
**Endpoint:** `GET /portfolio/summary`

**Description:** High-level overview of all projects with monetization insights.

**Example Request:**
```bash
curl -H "Authorization: Bearer bv_live_xxx" \
  https://api.brandiverse.io/portfolio/summary
```

**Response:**
```json
{
  "total_projects": 72,
  "by_potential": {
    "high": 12,
    "medium": 28,
    "low": 32
  },
  "revenue_ready": 8,
  "total_recommendations": 234,
  "critical_actions": 18,
  "revenue_opportunities": 42,
  "top_projects": [
    {
      "name": "FlipFlow",
      "monetization_score": 95,
      "revenue_streams": ["Payments", "Subscription"],
      "status": "revenue_ready"
    }
  ],
  "updated_at": "2026-01-11T10:30:00Z"
}
```

**Use Cases:**
- Dashboard metrics display
- Portfolio health monitoring
- Revenue opportunity discovery
- Automated decision-making by AI agents

---

#### 2. List All Projects
**Endpoint:** `GET /portfolio/projects`

**Description:** Detailed analysis of all projects in the portfolio.

**Query Parameters:**
- `min_score` (integer): Filter by minimum monetization score (0-100)
- `category` (string): Filter by category (high, medium, low)
- `has_revenue` (boolean): Only show projects with revenue signals

**Example Request:**
```bash
curl -H "Authorization: Bearer bv_live_xxx" \
  "https://api.brandiverse.io/portfolio/projects?min_score=70&has_revenue=true"
```

**Response:**
```json
{
  "projects": [
    {
      "name": "FlipFlow",
      "path": "C:/GitHub/GitHubRoot/sillinous/FlipFlow",
      "type": "Next.js Application",
      "git": {
        "is_repo": true,
        "branch": "main",
        "remote": "https://github.com/user/FlipFlow",
        "ahead": 2,
        "behind": 0,
        "modified": 5,
        "untracked": 3,
        "last_commit": "feat: Add Stripe integration",
        "last_commit_date": "2026-01-09 10:30:00"
      },
      "monetization": {
        "score": 95,
        "category": "High Potential",
        "signals": ["stripe", "payment", "subscription", "analytics"],
        "tech_stack": ["nextjs", "react", "typescript", "stripe", "supabase"],
        "revenue_streams": ["Direct Payments", "Subscription Model"],
        "estimated_mrr": "$789-$1,974"
      },
      "health": {
        "score": 82,
        "status": "Good",
        "issues": ["pending_migrations", "test_coverage_low"]
      },
      "recommendations": [
        {
          "type": "revenue",
          "priority": "critical",
          "action": "Fix database schema and launch payment flow",
          "impact": "Enable $789-$1,974 MRR within 7-10 days",
          "effort": "4-8 hours"
        }
      ]
    }
  ],
  "total": 12,
  "filtered_from": 72
}
```

**Use Cases:**
- Portfolio overview dashboards
- Project prioritization
- Revenue planning
- Technology stack analysis

---

#### 3. Get Project Details
**Endpoint:** `GET /portfolio/projects/{project_name}`

**Description:** In-depth analysis of a specific project.

**Example Request:**
```bash
curl -H "Authorization: Bearer bv_live_xxx" \
  https://api.brandiverse.io/portfolio/projects/FlipFlow
```

**Response:**
```json
{
  "name": "FlipFlow",
  "path": "C:/GitHub/GitHubRoot/sillinous/FlipFlow",
  "type": "Next.js Application",
  "created_at": "2025-12-15T08:00:00Z",
  "last_updated": "2026-01-11T09:45:00Z",
  "size_mb": 85.3,
  "file_count": 247,
  "git": { ... },
  "monetization": { ... },
  "health": { ... },
  "dependencies": {
    "next": "15.1.4",
    "react": "19.0.0",
    "stripe": "17.5.0",
    "@supabase/supabase-js": "2.50.1"
  },
  "recommendations": [ ... ],
  "deployment": {
    "platform": "vercel",
    "status": "deployed",
    "url": "https://flipflow.vercel.app",
    "last_deploy": "2026-01-10T14:20:00Z"
  }
}
```

---

#### 4. Get Revenue Recommendations
**Endpoint:** `GET /portfolio/recommendations`

**Description:** Prioritized list of revenue-generating actions across all projects.

**Query Parameters:**
- `type` (string): Filter by type (revenue, technical, deployment)
- `priority` (string): Filter by priority (critical, high, medium, low)
- `limit` (integer): Maximum recommendations to return

**Example Request:**
```bash
curl -H "Authorization: Bearer bv_live_xxx" \
  "https://api.brandiverse.io/portfolio/recommendations?type=revenue&priority=critical"
```

**Response:**
```json
{
  "recommendations": [
    {
      "id": "rec_flipflow_001",
      "project": "FlipFlow",
      "type": "revenue",
      "category": "Monetization",
      "priority": "critical",
      "action": "Fix database schema and launch payment flow",
      "impact": "Enable $789-$1,974 MRR within 7-10 days",
      "effort": "4-8 hours",
      "blockers": ["database_migration", "email_verification"],
      "monetization_score": 95,
      "estimated_revenue": "$789-$1,974/month",
      "timeframe": "7-10 days"
    }
  ],
  "total": 18,
  "revenue_opportunities": 18,
  "total_potential_mrr": "$3,500-$8,000"
}
```

---

### Automation Endpoints

#### 5. Get Executable Actions
**Endpoint:** `GET /automation/actions`

**Description:** List of actions that can be executed autonomously.

**Example Request:**
```bash
curl -H "Authorization: Bearer bv_live_xxx" \
  https://api.brandiverse.io/automation/actions
```

**Response:**
```json
{
  "actions": [
    {
      "id": "FlipFlow_git_commit_001",
      "project": "FlipFlow",
      "project_path": "C:/GitHub/GitHubRoot/sillinous/FlipFlow",
      "type": "git_commit",
      "recommendation": {
        "action": "Commit pending changes",
        "impact": "Prepare for deployment"
      },
      "monetization_score": 95,
      "estimated_impact": 50,
      "risk_level": 10,
      "auto_executable": true
    }
  ],
  "total": 23,
  "auto_executable_count": 15
}
```

---

#### 6. Execute Automation Action
**Endpoint:** `POST /automation/actions/{action_id}/execute`

**Description:** Execute a specific automation action with optional dry-run.

**Query Parameters:**
- `dry_run` (boolean): Preview action without executing (default: true)

**Example Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer bv_live_xxx" \
  "https://api.brandiverse.io/automation/actions/FlipFlow_git_commit_001/execute?dry_run=false"
```

**Response:**
```json
{
  "success": true,
  "dry_run": false,
  "action": {
    "id": "FlipFlow_git_commit_001",
    "type": "git_commit",
    "project": "FlipFlow"
  },
  "result": {
    "committed": true,
    "files_changed": 5,
    "commit_hash": "abc123def",
    "message": "feat: Fix database schema for payment flow"
  },
  "timestamp": "2026-01-11T10:35:00Z"
}
```

**Scopes Required:** `automation:execute`

---

#### 7. List Workflows
**Endpoint:** `GET /automation/workflows`

**Description:** Available automation workflows for portfolio management.

**Response:**
```json
{
  "workflows": [
    {
      "type": "sync_all",
      "name": "Sync All Projects",
      "description": "Commit and push all pending changes across projects",
      "risk": "low",
      "auto_executable": true,
      "estimated_time": "2-5 minutes"
    },
    {
      "type": "prepare_top_projects",
      "name": "Prepare Top Revenue Projects",
      "description": "Prepare top 5 monetization projects for launch",
      "risk": "low",
      "auto_executable": true,
      "estimated_time": "5-10 minutes"
    },
    {
      "type": "revenue_push",
      "name": "Revenue Push",
      "description": "Identify and prepare high-revenue projects for monetization",
      "risk": "medium",
      "auto_executable": false,
      "estimated_time": "15-30 minutes"
    }
  ]
}
```

---

#### 8. Execute Workflow
**Endpoint:** `POST /automation/workflows/{workflow_type}/execute`

**Description:** Execute a revenue-generating workflow across multiple projects.

**Body (optional):**
```json
{
  "target_projects": ["FlipFlow", "UnifiedMediaAssetManager"],
  "dry_run": false
}
```

**Example Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer bv_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' \
  https://api.brandiverse.io/automation/workflows/prepare_top_projects/execute
```

**Response:**
```json
{
  "success": true,
  "workflow": "prepare_top_projects",
  "dry_run": false,
  "projects_processed": 5,
  "actions_executed": 12,
  "results": [
    {
      "project": "FlipFlow",
      "actions": ["git_commit", "git_push"],
      "status": "success"
    }
  ],
  "timestamp": "2026-01-11T10:40:00Z",
  "duration_seconds": 145
}
```

**Scopes Required:** `automation:execute`

---

### Cache Management Endpoints

#### 9. Get Cache Statistics
**Endpoint:** `GET /portfolio/cache/stats`

**Description:** View portfolio cache statistics and status.

**Response:**
```json
{
  "cache_enabled": true,
  "cache_size": 1024,
  "last_scan": "2026-01-11T10:30:00Z",
  "ttl_seconds": 3600,
  "hit_rate": 0.85
}
```

---

#### 10. Invalidate Cache
**Endpoint:** `POST /portfolio/cache/invalidate`

**Description:** Force refresh of portfolio cache.

**Response:**
```json
{
  "invalidated": true,
  "timestamp": "2026-01-11T10:45:00Z"
}
```

---

## Webhooks (Agency & Enterprise Tiers)

Configure webhooks to receive real-time notifications for portfolio events.

### Webhook Events

- `portfolio.project.added` - New project detected
- `portfolio.project.updated` - Project analysis updated
- `portfolio.revenue.opportunity` - New revenue opportunity identified
- `automation.action.completed` - Automation action completed
- `health.score.changed` - Project health score changed significantly

### Webhook Payload Example

```json
{
  "event": "portfolio.revenue.opportunity",
  "timestamp": "2026-01-11T10:50:00Z",
  "data": {
    "project": "FlipFlow",
    "recommendation": {
      "action": "Launch payment flow",
      "estimated_revenue": "$789-$1,974/month",
      "priority": "critical"
    }
  }
}
```

---

## SDK Examples

### Python SDK
```python
from brandiverse import PortfolioClient

client = PortfolioClient(api_key="bv_live_xxx")

# Get portfolio summary
summary = client.portfolio.summary()
print(f"Total projects: {summary.total_projects}")
print(f"Revenue ready: {summary.revenue_ready}")

# Get revenue recommendations
recommendations = client.portfolio.recommendations(type="revenue", priority="critical")
for rec in recommendations:
    print(f"{rec.project}: {rec.action} - {rec.estimated_revenue}")

# Execute automation workflow
result = client.automation.execute_workflow("prepare_top_projects", dry_run=False)
print(f"Processed {result.projects_processed} projects")
```

### JavaScript SDK
```javascript
import { PortfolioClient } from '@brandiverse/sdk';

const client = new PortfolioClient({ apiKey: 'bv_live_xxx' });

// Get portfolio summary
const summary = await client.portfolio.summary();
console.log(`Total projects: ${summary.total_projects}`);

// Get high-potential projects
const projects = await client.portfolio.projects({ min_score: 70 });
projects.forEach(project => {
  console.log(`${project.name}: $${project.monetization.score}`);
});

// Execute automation
const result = await client.automation.executeAction('FlipFlow_git_commit_001', { dryRun: false });
console.log(`Action completed: ${result.success}`);
```

---

## Rate Limits

| Tier | Requests/Minute | Requests/Day |
|------|----------------|--------------|
| Free | 10 | 100 |
| Pro | 100 | 5,000 |
| Agency | 500 | 25,000 |
| Enterprise | 1,000 | Unlimited |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673452800
```

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions/scopes |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Next Steps to Monetize

1. **Add Stripe Integration** - Implement subscription billing
2. **Create Pricing Page** - Build public-facing pricing page
3. **Implement API Key Management** - User portal for API keys
4. **Add Usage Tracking** - Monitor API calls per user/tier
5. **Build Developer Portal** - Documentation, examples, playground
6. **Launch Beta Program** - Invite 10-20 early users
7. **Create Marketing Site** - Landing page + SEO optimization
8. **Integrate Analytics** - Track conversions and revenue

---

## Estimated Time to Revenue

- **Week 1**: Stripe integration + Pricing page (8-12 hours)
- **Week 2**: API key management + Usage tracking (6-10 hours)
- **Week 3**: Developer portal + Documentation (10-15 hours)
- **Week 4**: Beta launch + First paying customer (5-8 hours)

**Total**: 29-45 hours to first revenue  
**Potential MRR (3 months)**: $200-$500  
**Potential MRR (12 months)**: $2,000-$5,000

---

**Last Updated**: 2026-01-11  
**API Version**: v1.0  
**Base URL**: `https://api.brandiverse.io` (when deployed)
