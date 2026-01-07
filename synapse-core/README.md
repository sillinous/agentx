# 🧠 Synapse Core

**Multi-Agent Autonomous Business Ecosystem**

> "We do not build tools for creators. We build the mind that manages the creation."

Synapse replaces traditional creator tools (website builders, email marketing platforms, content management systems) with **autonomous AI agents** that execute business tasks on your behalf. You provide the **intent**, the agents provide the **action**.

---

## 🌟 Overview

Synapse is an AI-powered platform featuring three specialized autonomous agents:

1. **The Scribe** (Marketing Agent) - Generates brand-consistent content, copy, and marketing materials
2. **The Architect** (Builder Agent) - Creates and modifies React UI components in real-time
3. **The Sentry** (Analytics Agent) - Monitors metrics, detects anomalies, and provides actionable insights

### Key Features

- ⚡ **45-second deployments**: Landing page + copy + payment processing in under a minute
- 🤖 **Autonomous execution**: Agents work independently with smart safety controls
- 🎨 **Brand consistency**: "Brand DNA" system maintains your voice and visual identity
- 📊 **Data-driven decisions**: Semantic memory and context-aware recommendations
- 🛡️ **Smart authorization**: Green/Amber/Red zone security model

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [OpenAI API Key](https://platform.openai.com/api-keys)

### One-Command Setup

**Unix/Linux/Mac:**
```bash
./setup.sh
```

**Windows PowerShell:**
```powershell
.\setup.ps1
```

**Manual Setup:**
```bash
# 1. Copy environment files
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local

# 2. Add your OpenAI API key to .env
# OPENAI_API_KEY=sk-your-actual-key-here

# 3. Start with Docker
docker-compose up -d

# 4. Initialize database
docker-compose exec backend python init_db.py
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main UI Dashboard |
| **Backend API** | http://localhost:8000 | FastAPI Server |
| **API Docs** | http://localhost:8000/docs | Interactive API Documentation |
| **PgAdmin** | http://localhost:5050 | Database UI (optional) |

---

## 📋 Project Structure

```
synapse-core/
├── apps/
│   └── web/                      # Next.js Frontend (React 19 + Tailwind CSS 4)
│       ├── src/
│       │   ├── app/             # App Router pages
│       │   │   ├── page.tsx     # Main dual-mode interface
│       │   │   └── api/         # API routes (proxy to backend)
│       │   └── components/       # Reusable React components
│       ├── Dockerfile
│       └── package.json
│
├── packages/
│   ├── marketing-agent/          # The Scribe (Python + FastAPI + LangGraph)
│   │   ├── main.py              # FastAPI server with all agent endpoints
│   │   ├── scribe.py            # Marketing content generation agent
│   │   ├── auth.py              # JWT authentication system
│   │   ├── database_utils.py    # PostgreSQL utilities
│   │   ├── tests/               # Comprehensive test suite (61 tests)
│   │   │   ├── test_auth.py     # Authentication tests
│   │   │   ├── test_api.py      # API endpoint tests
│   │   │   └── test_database.py # Database utility tests
│   │   └── Dockerfile
│   │
│   ├── builder-agent/            # The Architect (React component builder)
│   │   ├── architect.py         # UI/UX component generation agent
│   │   ├── tests/               # Test suite (31 tests)
│   │   │   └── test_architect.py
│   │   └── pyproject.toml
│   │
│   └── analytics-agent/          # The Sentry (Analytics & insights)
│       ├── sentry.py            # Performance monitoring agent
│       ├── tests/               # Test suite (27 tests)
│       │   └── test_sentry.py
│       └── pyproject.toml
│
├── database/
│   ├── schema.sql               # Complete PostgreSQL schema
│   ├── seed.sql                 # Sample data
│   └── init.sql                 # Docker initialization
│
├── docker-compose.yml           # Orchestrates all services
├── setup.sh                     # Automated setup (Unix)
├── setup.ps1                    # Automated setup (Windows)
├── .env.example                 # Environment configuration template
├── QUICKSTART.md               # Quick start guide
└── README.md                    # This file
```

---

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- Next.js 16.1 with React 19 & TypeScript
- Tailwind CSS 4 (Dark Glass aesthetic)
- Framer Motion for animations
- Jest + Playwright for testing

**Backend:**
- Python 3.12+ with FastAPI
- LangChain + LangGraph for agent orchestration
- OpenAI GPT-4-Turbo
- JWT authentication with PyJWT
- JSON structured logging

**Database:**
- PostgreSQL 16+ with pgvector extension
- Vector embeddings (1536-dim) for semantic memory
- Alembic for migrations

**Infrastructure:**
- Docker + Docker Compose
- Node.js monorepo with npm workspaces
- Poetry for Python dependency management

### Agent Communication Protocol

Agents communicate via structured JSON packets:

```json
{
  "trace_id": "unique-request-id",
  "agent": "scribe|architect|sentry",
  "action": "draft_content|build_component|analyze_metrics",
  "priority": "low|medium|high|critical",
  "constraints": {
    "max_tokens": 500,
    "brand_voice": "retrieved_from_db"
  },
  "payload": {...}
}
```

### Security Model

**Authority Levels:**
- **Green Zone** (Autonomous): Content drafting, data analysis - agents execute freely
- **Amber Zone** (Review): Website changes, scheduling - requires >90% confidence
- **Red Zone** (Restricted): Payments, bulk emails, deletions - requires human confirmation

---

## 🔌 API Reference

### Authentication

#### Get Development Token
```http
POST /auth/dev-token
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Verify Token
```http
GET /auth/verify
Authorization: Bearer <token>
```

### Agent Endpoints

#### Invoke The Scribe (Marketing Agent)
```http
POST /invoke/scribe
Authorization: Bearer <token>
Content-Type: application/json

{
  "thread_id": "conversation-123",
  "prompt": "Write a punchy headline for our new yoga app"
}
```

**Response:**
```json
{
  "response": {
    "type": "headline",
    "content": "Find Your Balance: Yoga That Fits Your Life"
  }
}
```

#### Invoke The Architect (Builder Agent)
```http
POST /invoke/architect
Authorization: Bearer <token>
Content-Type: application/json

{
  "thread_id": "build-session-456",
  "prompt": "Create a modern pricing card component with 3 tiers"
}
```

**Response:**
```json
{
  "response": {
    "type": "component",
    "code": "export default function PricingCard() {...}",
    "description": "Three-tier pricing card with hover effects"
  }
}
```

#### Invoke The Sentry (Analytics Agent)
```http
POST /invoke/sentry
Authorization: Bearer <token>
Content-Type: application/json

{
  "thread_id": "analytics-789",
  "prompt": "Analyze my site performance for the last 7 days"
}
```

**Response:**
```json
{
  "response": {
    "type": "analytics_report",
    "insights": "Traffic increased 23% week-over-week...",
    "recommendations": "Consider scaling ad spend..."
  }
}
```

---

## 🧪 Testing

### Run All Tests

```bash
# Marketing agent tests (61 tests)
cd packages/marketing-agent && poetry run pytest -v

# Builder agent tests (31 tests)
cd packages/builder-agent && poetry run pytest -v

# Analytics agent tests (27 tests)
cd packages/analytics-agent && poetry run pytest -v

# Frontend unit tests
npm test -w apps/web

# Frontend E2E tests
npm run test:e2e -w apps/web
```

### Test Coverage (119 total tests)

- **Marketing Agent (61 tests)**:
  - Authentication: JWT token generation, validation, expiration handling
  - API Endpoints: All agent invocations with auth, error handling
  - Database utilities: Connection management, CRUD operations, mock fallbacks

- **Builder Agent (31 tests)**:
  - Component structure analysis
  - React/JSX syntax validation
  - UI component library operations
  - Component test generation

- **Analytics Agent (27 tests)**:
  - Performance metrics retrieval
  - Anomaly detection algorithms
  - Traffic trend analysis
  - Insights report generation
  - Alert threshold management

---

## 🔧 Development

### Running Locally (Without Docker)

**Backend:**
```bash
cd packages/marketing-agent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install poetry
poetry install
python init_db.py
uvicorn main:app --reload
```

**Frontend:**
```bash
cd apps/web
npm install
npm run dev
```

### Environment Variables

See `.env.example` for all configuration options. Key variables:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://...

# Security
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Optional
LOG_LEVEL=INFO
DEBUG=true
```

### Code Quality

```bash
# Python formatting
cd packages/marketing-agent
black .
flake8 .

# Frontend linting
npm run lint -w apps/web
```

---

## 📊 Database Schema

### Core Tables

- **users**: User accounts with subscription tiers
- **brand_dna**: Brand voice parameters (JSON)
- **agents**: Registry of available agents
- **context_lake**: Long-term memory with vector embeddings
- **task_queue**: Agent task assignments
- **audit_log**: Security and action history

### Migrations

```bash
# Create new migration
docker-compose exec backend alembic revision -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f backend  # Specific service

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Clean everything (including data!)
docker-compose down -v

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Run commands in containers
docker-compose exec backend python init_db.py
docker-compose exec postgres psql -U synapse
```

---

## 🚨 Troubleshooting

### Common Issues

**"Connection refused" errors:**
```bash
docker-compose ps  # Check service status
docker-compose restart
```

**Database connection errors:**
```bash
docker-compose exec postgres pg_isready
docker-compose exec backend python init_db.py
```

**Port conflicts:**
Edit `.env` and change ports:
```bash
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

**Agent errors:**
```bash
# Check OpenAI API key is set
docker-compose exec backend python -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# View detailed logs
docker-compose logs -f backend
```

---

## 📈 Roadmap

- [ ] Real-time agent collaboration (multi-agent conversations)
- [ ] Voice interface for command mode
- [ ] Advanced analytics dashboard with custom metrics
- [ ] Stripe integration for payment processing
- [ ] Email automation agent
- [ ] Social media management agent
- [ ] Multi-language support
- [ ] Agent marketplace (community-contributed agents)

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🙏 Acknowledgments

Built with:
- [OpenAI GPT-4](https://openai.com/)
- [LangChain](https://langchain.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [pgvector](https://github.com/pgvector/pgvector)

---

## 📞 Support

- **Documentation**: See [QUICKSTART.md](./QUICKSTART.md)
- **API Docs**: http://localhost:8000/docs
- **Issues**: Create an issue in this repository

---

**Made with ❤️ by the Synapse Team**

*Transform intent into action. Autonomously.*
