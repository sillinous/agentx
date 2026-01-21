# Monitoring Guide

> **Last Updated:** 2026-01-12
> **Version:** 1.0.0

This guide covers setting up monitoring and alerting for DevOps Hub using Prometheus and Grafana.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Metrics Reference](#metrics-reference)
4. [Grafana Dashboard](#grafana-dashboard)
5. [Alerting](#alerting)
6. [Best Practices](#best-practices)

---

## Overview

DevOps Hub exposes Prometheus metrics at `/metrics` endpoint. The monitoring stack includes:

| Component | Purpose |
|-----------|---------|
| Prometheus | Metrics collection and storage |
| Grafana | Visualization and dashboards |
| Alertmanager | Alert routing and notification |
| Blackbox Exporter | Endpoint probing |

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  DevOps Hub │────▶│  Prometheus │────▶│   Grafana   │
│   /metrics  │     │             │     │             │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐     ┌─────────────┐
                   │Alertmanager │────▶│   Slack/    │
                   │             │     │  PagerDuty  │
                   └─────────────┘     └─────────────┘
```

---

## Quick Start

### Using Docker Compose

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access services
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
# Alertmanager: http://localhost:9093
```

### Manual Setup

1. **Configure Prometheus**
   ```bash
   cp monitoring/prometheus/prometheus.yml /etc/prometheus/
   cp monitoring/prometheus/alerts.yml /etc/prometheus/
   ```

2. **Import Grafana Dashboard**
   - Open Grafana → Dashboards → Import
   - Upload `monitoring/grafana/devops-hub-dashboard.json`
   - Select your Prometheus data source

3. **Configure Alertmanager**
   - Set up notification channels (Slack, PagerDuty, email)
   - Configure routing rules

---

## Metrics Reference

### HTTP Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `http_requests_in_progress` | Gauge | Currently processing requests |

Labels: `method`, `path`, `status`

### Agent Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `agent_executions_total` | Counter | Total agent executions |
| `agent_execution_duration_seconds` | Histogram | Agent execution time |
| `devops_hub_agents_total` | Gauge | Registered agents count |

Labels: `agent_id`, `domain`, `status`

### Workflow Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `workflow_executions_total` | Counter | Total workflow executions |
| `workflow_execution_duration_seconds` | Histogram | Workflow execution time |
| `devops_hub_workflows_total` | Gauge | Registered workflows count |

Labels: `workflow_id`, `status`

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `devops_hub_database_connected` | Gauge | Database connectivity (1=connected) |
| `devops_hub_redis_connected` | Gauge | Redis connectivity (1=connected) |
| `devops_hub_last_backup_timestamp` | Gauge | Unix timestamp of last backup |

### Example Queries

```promql
# Request rate per endpoint
sum(rate(http_requests_total[5m])) by (path)

# 95th percentile latency
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# Agent execution success rate
sum(rate(agent_executions_total{status="success"}[5m])) / sum(rate(agent_executions_total[5m])) * 100

# Top 5 slowest endpoints
topk(5, histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (path, le)))
```

---

## Grafana Dashboard

### Included Panels

The pre-built dashboard (`monitoring/grafana/devops-hub-dashboard.json`) includes:

**Overview Row:**
- API Status (up/down)
- Request Rate (5m)
- P95 Latency
- Error Rate
- Total Agents
- Total Workflows

**Request Metrics Row:**
- Request Rate by Method
- Request Latency Percentiles (p50, p90, p99)
- Request Rate by Status
- Top 10 Endpoints

**Agent Executions Row:**
- Agent Executions by Agent
- Workflow Executions by Workflow

### Importing the Dashboard

1. Open Grafana
2. Go to Dashboards → Import
3. Upload `monitoring/grafana/devops-hub-dashboard.json`
4. Select your Prometheus data source
5. Click Import

### Customizing

Edit the dashboard JSON or use Grafana UI to:
- Add business-specific panels
- Adjust thresholds and colors
- Add annotations for deployments
- Create team-specific views

---

## Alerting

### Alert Rules

The included alert rules (`monitoring/prometheus/alerts.yml`) cover:

| Alert | Severity | Description |
|-------|----------|-------------|
| DevOpsHubDown | Critical | API unreachable for 1 minute |
| DevOpsHubHighLatency | Warning | P95 latency > 1 second |
| DevOpsHubCriticalLatency | Critical | P95 latency > 5 seconds |
| DevOpsHubHighErrorRate | Warning | Error rate > 5% |
| DevOpsHubCriticalErrorRate | Critical | Error rate > 20% |
| DevOpsHubRateLimitingActive | Warning | Rate limiting triggered |
| DevOpsHubHighMemoryUsage | Warning | Memory > 85% |
| DevOpsHubHighCPUUsage | Warning | CPU > 85% |
| DevOpsHubDatabaseConnectionFailed | Critical | Database unreachable |
| DevOpsHubAgentExecutionFailures | Warning | Agent failure rate > 10% |
| DevOpsHubWorkflowExecutionFailures | Warning | Workflow failure rate > 10% |
| DevOpsHubBackupMissing | Warning | No backup in 24 hours |

### Alertmanager Configuration

Example Alertmanager config for Slack:

```yaml
# alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'slack-notifications'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#devops-alerts'
        send_resolved: true
        title: '{{ .Status | toUpper }}: {{ .CommonAnnotations.summary }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        severity: 'critical'
```

### Testing Alerts

```bash
# Trigger test alert (using amtool)
amtool alert add alertname=TestAlert severity=warning

# Check alert status
curl http://localhost:9090/api/v1/alerts

# Silence an alert
amtool silence add alertname=DevOpsHubHighLatency --duration=1h
```

---

## Best Practices

### Dashboard Organization

1. **Use template variables** for filtering by environment, service, etc.
2. **Group related panels** in rows
3. **Set appropriate time ranges** for different use cases
4. **Add annotations** for deployments and incidents

### Alert Design

1. **Avoid alert fatigue**
   - Start with fewer, high-signal alerts
   - Use appropriate thresholds (not too sensitive)
   - Group related alerts

2. **Make alerts actionable**
   - Include runbook links
   - Provide context in descriptions
   - Test response procedures

3. **Use severity levels correctly**
   - Critical: Requires immediate action (pager)
   - Warning: Investigate soon (Slack/email)
   - Info: Awareness only (dashboard)

### Retention and Performance

```yaml
# Prometheus storage settings
storage:
  tsdb:
    retention.time: 15d      # How long to keep data
    retention.size: 50GB     # Max storage size
```

### Security

1. **Protect metrics endpoint** with authentication in production
2. **Use HTTPS** for Prometheus and Grafana
3. **Limit access** to Alertmanager configuration
4. **Audit dashboard access** in Grafana

---

## Docker Compose for Monitoring

Create `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    networks:
      - devops-hub

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3001:3000"
    networks:
      - devops-hub

  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    ports:
      - "9093:9093"
    networks:
      - devops-hub

  blackbox-exporter:
    image: prom/blackbox-exporter:latest
    ports:
      - "9115:9115"
    networks:
      - devops-hub

volumes:
  prometheus_data:
  grafana_data:

networks:
  devops-hub:
    external: true
```

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [DISASTER_RECOVERY.md](./DISASTER_RECOVERY.md) - Backup and recovery
- [../PRODUCTION_ROADMAP.md](../PRODUCTION_ROADMAP.md) - Project roadmap
