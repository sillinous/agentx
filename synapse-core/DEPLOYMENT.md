# Synapse Core Deployment Guide

This guide covers deploying Synapse Core to production environments.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 16+ with pgvector extension (included in Docker setup)
- OpenAI API key
- Domain name (for production SSL)

## Environment Variables

Create a `.env.production` file with the following variables:

```bash
# Required for Production
OPENAI_API_KEY=sk-your-production-key
POSTGRES_USER=synapse
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=synapse
JWT_SECRET=<generate-256-bit-secret>

# Optional Configuration
NODE_ENV=production
LOG_LEVEL=INFO
BACKEND_PORT=8000
FRONTEND_PORT=3000
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Generating Secure Secrets

```bash
# Generate JWT secret
openssl rand -base64 32

# Generate database password
openssl rand -base64 24
```

## Deployment Options

### Option 1: Docker Compose (Recommended for single-server)

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Option 2: Kubernetes (Coming soon)

Helm charts available in `/deploy/kubernetes/`

### Option 3: Cloud Platforms

#### Vercel (Frontend) + Railway (Backend)

1. **Frontend on Vercel:**
   ```bash
   cd apps/web
   vercel --prod
   ```
   Set environment variable: `FASTAPI_BASE_URL=https://your-backend.railway.app`

2. **Backend on Railway:**
   - Connect GitHub repository
   - Set root directory: `synapse-core/packages/marketing-agent`
   - Add environment variables from `.env.production`

#### Render

Deploy using `render.yaml` blueprint (coming soon).

## Database Migrations

Run migrations before starting the application:

```bash
# Using Docker
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Using Poetry locally
cd packages/marketing-agent
poetry run alembic upgrade head
```

## Health Checks

The backend exposes a health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": {"connected": true, "database_type": "postgresql"},
  "agents": {"scribe": "ready", "architect": "ready", "sentry": "ready"}
}
```

## SSL/TLS Configuration

### Using Nginx (included in docker-compose.prod.yml)

1. Place SSL certificates in `nginx/ssl/`:
   - `nginx/ssl/cert.pem`
   - `nginx/ssl/key.pem`

2. Start with nginx profile:
   ```bash
   docker-compose -f docker-compose.prod.yml --profile with-nginx up -d
   ```

### Using Let's Encrypt

```bash
# Install certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy to nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

## Monitoring

### Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Metrics

The backend uses structured JSON logging. Configure log aggregation with:
- Datadog
- CloudWatch
- Loki + Grafana

## Scaling

### Horizontal Scaling

Increase backend workers in `docker-compose.prod.yml`:

```yaml
backend:
  deploy:
    replicas: 3
```

### Database Connection Pooling

For high traffic, add PgBouncer:

```yaml
pgbouncer:
  image: edoburu/pgbouncer:latest
  environment:
    DATABASE_URL: postgresql://synapse:password@postgres:5432/synapse
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 100
```

## Backup & Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U synapse synapse > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U synapse synapse < backup_20240101.sql
```

## Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check `OPENAI_API_KEY` is set
   - Verify database is healthy: `docker-compose exec postgres pg_isready`

2. **Database connection failed**
   - Ensure `DATABASE_URL` is correct
   - Check postgres container is running

3. **JWT errors**
   - Verify `JWT_SECRET` is set and consistent across restarts

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG docker-compose -f docker-compose.prod.yml up
```

## Security Checklist

- [ ] Changed default passwords
- [ ] Set strong JWT_SECRET
- [ ] Enabled SSL/TLS
- [ ] Configured firewall rules
- [ ] Set up log monitoring
- [ ] Enabled database backups
- [ ] Reviewed CORS settings
