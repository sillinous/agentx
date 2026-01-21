# Deployment Guide

> **Last Updated:** 2026-01-12
> **Version:** 1.3.0

This guide covers deploying DevOps Hub to various environments.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployments](#cloud-deployments)
   - [AWS](#aws-ecs--fargate)
   - [Google Cloud](#google-cloud-run)
   - [Azure](#azure-container-apps)
6. [Configuration](#configuration)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/devops-hub.git
cd devops-hub

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

The application will be available at:
- Frontend: `http://localhost:80`
- API: `http://localhost:80/api`
- API Docs: `http://localhost:80/api/docs`

---

## Prerequisites

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| Memory | 2 GB | 4 GB |
| Storage | 10 GB | 20 GB SSD |

### Software Requirements

- Docker 24.0+ and Docker Compose 2.20+
- OR Python 3.10+ and Node.js 18+
- Git

### Network Requirements

| Port | Service | Description |
|------|---------|-------------|
| 80 | nginx | HTTP (redirects to HTTPS) |
| 443 | nginx | HTTPS |
| 8100 | backend | API (internal) |
| 3000 | frontend | Dev server (development only) |

---

## Docker Deployment

### Build Images

```bash
# Build backend
docker build -t devops-hub-backend:latest .

# Build frontend
docker build -t devops-hub-frontend:latest -f frontend/Dockerfile frontend/
```

### Production Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Scale backend replicas
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Update images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Create a `.env` file:

```env
# Required
SECRET_KEY=your-secure-secret-key-here
CORS_ORIGINS=https://your-domain.com

# Database
DATABASE_URL=sqlite:///./data/devops_hub.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@db:5432/devops_hub

# Optional
LOG_LEVEL=INFO
LOG_FORMAT=json
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
```

---

## Kubernetes Deployment

### Prerequisites

- kubectl configured
- Kubernetes cluster (1.25+)
- Container registry access

### Deploy

```bash
# Create namespace
kubectl create namespace devops-hub

# Create secrets
kubectl create secret generic devops-hub-secrets \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=db-password=$(openssl rand -hex 16) \
  -n devops-hub

# Apply manifests
kubectl apply -f k8s/ -n devops-hub

# Check status
kubectl get pods -n devops-hub
kubectl get svc -n devops-hub
```

### Manifests Overview

```
k8s/
├── namespace.yaml       # Namespace definition
├── configmap.yaml       # Configuration
├── secrets.yaml         # Secret references
├── backend-deployment.yaml
├── backend-service.yaml
├── frontend-deployment.yaml
├── frontend-service.yaml
├── ingress.yaml         # Ingress for external access
├── hpa.yaml             # Horizontal Pod Autoscaler
└── pdb.yaml             # Pod Disruption Budget
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment backend --replicas=5 -n devops-hub

# Auto-scaling is configured via HPA
kubectl get hpa -n devops-hub
```

---

## Cloud Deployments

### AWS (ECS + Fargate)

#### Using AWS CLI

```bash
# Create ECR repositories
aws ecr create-repository --repository-name devops-hub-backend
aws ecr create-repository --repository-name devops-hub-frontend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t <account>.dkr.ecr.us-east-1.amazonaws.com/devops-hub-backend:latest .
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/devops-hub-backend:latest

# Deploy using CloudFormation or Terraform (templates in infra/aws/)
```

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │   ALB    │──▶│  ECS Fargate │──▶│  RDS PostgreSQL    │  │
│  │          │   │  (Backend)   │   │                    │  │
│  └──────────┘   └──────────────┘   └────────────────────┘  │
│       │         ┌──────────────┐   ┌────────────────────┐  │
│       └────────▶│  ECS Fargate │   │  ElastiCache Redis │  │
│                 │  (Frontend)  │   │                    │  │
│                 └──────────────┘   └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Google Cloud Run

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/PROJECT_ID/devops-hub-backend .
gcloud builds submit --tag gcr.io/PROJECT_ID/devops-hub-frontend frontend/

# Deploy backend
gcloud run deploy devops-hub-backend \
  --image gcr.io/PROJECT_ID/devops-hub-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "LOG_LEVEL=INFO,CORS_ORIGINS=https://your-domain.com"

# Deploy frontend
gcloud run deploy devops-hub-frontend \
  --image gcr.io/PROJECT_ID/devops-hub-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Apps

```bash
# Create resource group
az group create --name devops-hub-rg --location eastus

# Create Container App Environment
az containerapp env create \
  --name devops-hub-env \
  --resource-group devops-hub-rg \
  --location eastus

# Deploy backend
az containerapp create \
  --name devops-hub-backend \
  --resource-group devops-hub-rg \
  --environment devops-hub-env \
  --image your-registry/devops-hub-backend:latest \
  --target-port 8100 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10

# Deploy frontend
az containerapp create \
  --name devops-hub-frontend \
  --resource-group devops-hub-rg \
  --environment devops-hub-env \
  --image your-registry/devops-hub-frontend:latest \
  --target-port 80 \
  --ingress external
```

---

## Configuration

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Secret key for signing |
| `DATABASE_URL` | No | sqlite:///... | Database connection URL |
| `REDIS_URL` | No | None | Redis URL (optional) |
| `CORS_ORIGINS` | No | * | Allowed CORS origins |
| `LOG_LEVEL` | No | INFO | Logging level |
| `LOG_FORMAT` | No | text | Log format (text/json) |
| `AUTH_ENABLED` | No | true | Enable authentication |
| `RATE_LIMIT_ENABLED` | No | true | Enable rate limiting |
| `RATE_LIMIT_REQUESTS` | No | 100 | Requests per minute |

### Health Checks

```bash
# Liveness probe
curl http://localhost:8100/health/live

# Readiness probe (checks dependencies)
curl http://localhost:8100/health/ready

# Full health check
curl http://localhost:8100/health
```

---

## SSL/TLS Setup

### Using Let's Encrypt with Certbot

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (add to crontab)
0 0 * * * certbot renew --quiet
```

### Using Cloud Load Balancer (Recommended)

Most cloud providers handle SSL termination at the load balancer level:

- **AWS**: Use ACM certificates with ALB
- **GCP**: Use Google-managed certificates with Cloud Load Balancer
- **Azure**: Use Azure-managed certificates with Application Gateway

---

## Monitoring

### Prometheus Metrics

The backend exposes metrics at `/metrics`:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'devops-hub'
    static_configs:
      - targets: ['backend:8100']
    metrics_path: '/metrics'
```

### Key Metrics

| Metric | Description |
|--------|-------------|
| `http_requests_total` | Total HTTP requests |
| `http_request_duration_seconds` | Request latency histogram |
| `agent_executions_total` | Agent execution count |
| `workflow_executions_total` | Workflow execution count |

### Logging

Logs are output in JSON format when `LOG_FORMAT=json`:

```json
{
  "timestamp": "2026-01-12T10:00:00Z",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "abc-123",
  "method": "GET",
  "path": "/api/agents",
  "status": 200,
  "duration_ms": 45
}
```

---

## Troubleshooting

### Common Issues

#### Container won't start

```bash
# Check logs
docker logs devops-hub-backend

# Common causes:
# - Missing environment variables
# - Database connection failed
# - Port already in use
```

#### Database connection refused

```bash
# For Docker Compose
# Ensure database service is healthy before backend starts
docker-compose -f docker-compose.prod.yml ps

# For Kubernetes
kubectl describe pod <backend-pod> -n devops-hub
```

#### Frontend can't reach API

```bash
# Check nginx configuration
docker exec devops-hub-frontend cat /etc/nginx/conf.d/default.conf

# Ensure API_URL is correctly set
# Check CORS configuration
```

#### High memory usage

```bash
# Check container stats
docker stats

# Increase limits in docker-compose.prod.yml
# Or adjust Gunicorn workers: GUNICORN_WORKERS=2
```

### Getting Help

1. Check logs: `docker-compose logs -f`
2. Review [PRODUCTION_ROADMAP.md](../PRODUCTION_ROADMAP.md) for known issues
3. Open an issue on GitHub

---

## Next Steps

- Configure [database migrations](./DATABASE_MIGRATION.md)
- Set up [monitoring and alerting](./MONITORING.md) (coming soon)
- Review [security best practices](./SECURITY.md) (coming soon)
