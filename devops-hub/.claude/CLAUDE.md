# DevOps Hub - AI Assistant Instructions

## Session Startup Protocol

**Every AI assistant session MUST perform these steps:**

1. **Read the Production Roadmap**
   ```
   Read: PRODUCTION_ROADMAP.md
   ```
   This contains the current project status, priorities, and pending work.

2. **Check Recent Git Activity**
   ```
   git log --oneline -10
   git status
   ```
   Understand what has changed recently.

3. **Understand the Architecture**
   - Backend: FastAPI at `service/api.py`
   - Agents: `built_in_agents/` (13 agents)
   - Factory: `factory/` (registration, validation)
   - Frontend: `frontend/` (React + TypeScript)
   - Tests: `tests/` (178+ tests)

---

## Working Guidelines

### When Making Changes

1. **Run tests before and after changes**
   ```bash
   python -m pytest tests/ -v --tb=short
   ```

2. **Update PRODUCTION_ROADMAP.md** when:
   - Completing a roadmap item (check the box, add date)
   - Discovering new issues (add to appropriate priority)
   - Making architectural decisions (add to ADR section)

3. **Follow existing patterns**
   - API endpoints: Follow FastAPI patterns in `service/api.py`
   - Agents: Extend `BaseAgent` from `built_in_agents/base.py`
   - Tests: Follow pytest patterns in `tests/`

### Code Standards

- Python: Follow existing style (type hints, async-first)
- Frontend: TypeScript strict mode, React functional components
- Tests: Maintain high coverage, test edge cases
- Documentation: Update relevant docs when changing behavior

### Commit Messages

Use conventional commits:
```
feat: Add rate limiting to API endpoints
fix: Correct CORS configuration for production
docs: Update deployment documentation
test: Add tests for new health endpoints
```

---

## Key Files Reference

| Purpose | Location |
|---------|----------|
| Main API | `service/api.py` |
| Agent Base Class | `built_in_agents/base.py` |
| Agent Factory | `factory/agent_factory.py` |
| Database Layer | `core/database.py` |
| Authentication | `core/auth.py` |
| Workflow Engine | `service/workflow_engine.py` |
| Frontend App | `frontend/src/App.tsx` |
| API Client | `frontend/src/api/client.ts` |
| Docker Config | `Dockerfile`, `docker-compose.yml` |
| CI/CD | `.github/workflows/ci.yml` |
| **Roadmap** | `PRODUCTION_ROADMAP.md` |

---

## Current Priorities (Quick Reference)

Check `PRODUCTION_ROADMAP.md` for full details, but current focus is:

### Priority 1 - Critical
- [ ] `.env.example` - Environment documentation
- [ ] CORS fix - Remove wildcard origins
- [ ] Rate limiting - Apply to endpoints
- [ ] Frontend Docker - Containerize React app
- [ ] Production compose - Full stack deployment

### Priority 2 - Recommended
- [ ] Nginx reverse proxy
- [ ] Structured logging
- [ ] Database migrations
- [ ] Enhanced health checks
- [ ] Frontend UX improvements

---

## Common Tasks

### Adding a New Agent
1. Create directory in `built_in_agents/{domain}/`
2. Extend `BaseAgent` class
3. Register in `AGENT_REGISTRY.json`
4. Add tests in `tests/`
5. Add documentation in `docs/agents/`

### Adding an API Endpoint
1. Add to `service/api.py`
2. Add Pydantic models for request/response
3. Apply appropriate auth decorator (`require_read`, `require_write`, etc.)
4. Add tests in `tests/test_api.py`

### Updating Frontend
1. Work in `frontend/src/`
2. Run `npm run dev` for development
3. Run `npm run build` to verify production build
4. Run `npm run lint` before committing

---

## Environment Setup

```bash
# Backend
pip install -r requirements.txt
python -m uvicorn service.api:app --host 0.0.0.0 --port 8100 --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
python -m pytest tests/ -v

# Docker
docker-compose up -d
```

---

## Important Notes

- **Bootstrap API Key**: Generated on first start, save it securely
- **Redis**: Optional, system works without it
- **SQLite**: Database auto-created at `data/devops_hub.db`
- **Tests**: Must pass before merging any changes
- **CORS**: Currently insecure (`*`), fixing is Priority 1

---

**Remember:** Always update `PRODUCTION_ROADMAP.md` when completing work!
