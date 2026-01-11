# 🚀 Quick Reference - Unified Media Ecosystem

## Quick Start Commands

### Start Everything (Docker)
```bash
docker compose up
```

### Start Individual Apps

**Media Manager**:
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

**StoryForge**:
```bash
# Backend
cd apps/story-forge/backend && npm start

# Frontend
cd apps/story-forge/frontend && npm run dev
```

## URLs

| Service | URL |
|---------|-----|
| Media Manager UI | http://localhost:3000 |
| Media Manager API | http://localhost:8000/docs |
| StoryForge UI | http://localhost:5173 |
| StoryForge API | http://localhost:3001 |
| Flower Monitoring | http://localhost:5555 |

## NPM Workspace Commands

```bash
# Install for specific workspace
npm install --workspace=packages/shared

# Run script in workspace
npm run build --workspace=packages/shared

# Install all workspaces
npm install
```

## Shared Package Usage

```typescript
// Import types
import { Universe, Element, MediaAsset } from '@unified/shared';

// Import utilities
import { formatDate, slugify, generateId } from '@unified/shared-utils';

// Example usage
const id = generateId('universe');
const slug = slugify('My Cool Universe');
const dateStr = formatDate(new Date(), 'relative');
```

## Docker Commands

```bash
# Start services
docker compose up

# Start specific service
docker compose up media-manager-backend

# Stop all
docker compose down

# View logs
docker compose logs -f media-manager-backend

# Rebuild
docker compose up --build
```

## Common Tasks

### Build Shared Packages
```bash
npm run build --workspace=packages/shared
npm run build --workspace=packages/shared-utils
```

### Install New Dependency
```bash
# In specific app
npm install axios --workspace=apps/story-forge/backend

# In shared package
npm install -D typescript --workspace=packages/shared
```

### Check Structure
```bash
# PowerShell
./test-setup.ps1

# Or manual
Test-Path apps/media-manager/backend
Test-Path apps/story-forge
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port in use | `docker compose down` or kill process |
| Env vars missing | Copy from `ENV_TEMPLATE.md` |
| Junction broken | Recreate: `New-Item -ItemType Junction` |
| Module not found | `npm install` in workspace |
| Python errors | Recreate venv in backend |

## File Locations

- **Docs**: `START_HERE.md`, `README.md`, `VERIFICATION_REPORT.md`
- **Apps**: `apps/media-manager/*`, `apps/story-forge/*`
- **Shared**: `packages/shared/*`, `packages/shared-utils/*`
- **Config**: `docker-compose.yml`, `package.json`, `ENV_TEMPLATE.md`

## Next Steps

1. ✅ Set environment variables (see `ENV_TEMPLATE.md`)
2. ✅ Start services: `docker compose up`
3. ✅ Create a Universe in Media Manager
4. ✅ Create a Story Bible in StoryForge
5. ✅ Try AI generation features

---

**Need help?** Check `START_HERE.md` for detailed guides.
