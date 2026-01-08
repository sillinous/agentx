# 🚀 Synapse Core - Quick Start Guide

Get your AI-powered business ecosystem running in **under 5 minutes**.

## Prerequisites

- **Docker Desktop** ([Download here](https://www.docker.com/products/docker-desktop))
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))

## Setup (One-Time)

### Option A: Automated Setup (Recommended)

**On Unix/Linux/Mac:**
```bash
./setup.sh
```

**On Windows PowerShell:**
```powershell
.\setup.ps1
```

### Option B: Manual Setup

1. **Copy environment files:**
   ```bash
   cp .env.example .env
   cp apps/web/.env.example apps/web/.env.local
   ```

2. **Edit `.env` and add your OpenAI API key:**
   ```bash
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. **Start everything with Docker:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database:**
   ```bash
   docker-compose exec backend python init_db.py
   ```

## Access Your Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main UI (Control Dashboard + Command Mode) |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Database** | localhost:5432 | PostgreSQL + pgvector |

### Optional: PgAdmin (Database UI)

```bash
docker-compose --profile tools up -d
```
Access at http://localhost:5050 (admin@synapse.local / admin)

## Daily Development Workflow

### Start services
```bash
docker-compose up -d
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop services
```bash
docker-compose down
```

### Restart after code changes
```bash
# Backend auto-reloads on code changes
# Frontend auto-reloads on code changes

# If needed, restart specific service:
docker-compose restart backend
```

### Reset everything (clean slate)
```bash
docker-compose down -v  # Deletes database data too!
docker-compose up -d
docker-compose exec backend python init_db.py
```

## Common Tasks

### Run database migrations
```bash
docker-compose exec backend alembic upgrade head
```

### Access Python shell with app context
```bash
docker-compose exec backend python
```

### Run backend tests
```bash
docker-compose exec backend pytest
```

### Run frontend tests
```bash
# Unit tests
npm test -w apps/web

# E2E tests
npm run test:e2e -w apps/web
```

### Rebuild after dependency changes
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Project Structure

```
synapse-core/
├── apps/
│   └── web/              # Next.js Frontend
│       ├── src/
│       │   ├── app/      # App Router pages
│       │   └── components/
│       └── Dockerfile
├── packages/
│   ├── marketing-agent/  # The Scribe (FastAPI Backend)
│   ├── builder-agent/    # The Architect (coming soon)
│   └── analytics-agent/  # The Sentry (coming soon)
├── database/
│   ├── schema.sql       # Database schema
│   └── init.sql         # Docker initialization
├── docker-compose.yml   # Orchestrates all services
└── .env                 # Your configuration
```

## Troubleshooting

### "Connection refused" errors
```bash
# Check if services are running
docker-compose ps

# Restart services
docker-compose restart
```

### Frontend can't connect to backend
- Ensure `.env` has correct `FASTAPI_BASE_URL=http://localhost:8000`
- Check backend logs: `docker-compose logs backend`

### Database connection errors
```bash
# Check if PostgreSQL is healthy
docker-compose exec postgres pg_isready

# Reinitialize database
docker-compose exec backend python init_db.py
```

### Port conflicts (3000, 8000, or 5432 already in use)
Edit `.env` and change the ports:
```bash
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

### "Image not found" errors
```bash
docker-compose build --no-cache
```

### WSL2 Build Failures (Windows)

If you're using WSL2 and see I/O errors during `npm run build`:
```
Input/output error (os error 5)
EIO: i/o error, write
```

**Solutions:**

1. **Use Docker (Recommended):**
   ```bash
   docker-compose up -d
   ```

2. **Move project to WSL2 native filesystem:**
   ```bash
   # Clone to ~/projects instead of /mnt/c/...
   mkdir -p ~/projects
   cd ~/projects
   git clone <repo-url> synapse-core
   ```

3. **Disable Turbopack temporarily:**
   ```bash
   # In apps/web/package.json, change:
   # "build": "next build"
   # To use webpack instead of Turbopack
   ```

This is a known issue with Turbopack + WSL2 + Windows filesystem (NTFS) interactions.

## Next Steps

1. **Customize your brand DNA** - Edit database to add your brand parameters
2. **Test the Scribe agent** - Create marketing content via the Command Mode
3. **Explore the API** - Visit http://localhost:8000/docs
4. **Implement missing agents** - Builder and Analytics agents are placeholders

## Need Help?

- Check the logs: `docker-compose logs -f`
- View API documentation: http://localhost:8000/docs
- Database UI: Run PgAdmin (see above)

---

**You're ready! Visit http://localhost:3000 to start using Synapse** 🎉
