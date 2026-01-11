# 🚀 Quick Start Guide - Unified Media Ecosystem

## Prerequisites

- **Docker Desktop** (recommended for easiest setup)
- **Python 3.11+** (for local Media Manager backend)
- **Node.js 18+** (for StoryForge and frontends)
- **Git** (already have it!)

## 🎯 Quick Start Options

### Option 1: Docker Compose (Recommended - All Services at Once)

1. **Set up environment variables**
   ```bash
   # Copy and edit the environment file
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start all services**
   ```bash
   docker compose up
   ```

3. **Access the applications**
   - Media Manager Frontend: http://localhost:3000
   - Media Manager Backend: http://localhost:8000
   - Media Manager API Docs: http://localhost:8000/docs
   - StoryForge Frontend: http://localhost:5173
   - StoryForge Backend: http://localhost:3001
   - Flower (Task Monitor): http://localhost:5555

### Option 2: Individual Development (For Active Development)

#### Media Manager (FastAPI + Next.js)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on port 3000
```

**Worker (Celery):**
```bash
cd backend
source venv/bin/activate
celery -A app.celery_worker.celery_app worker --loglevel=info
```

#### StoryForge (Node.js + React)

**Backend:**
```bash
cd apps/story-forge/backend
npm install
npm start  # Runs on port 3001
```

**Frontend:**
```bash
cd apps/story-forge/frontend
npm install
npm run dev  # Runs on port 5173
```

## 📋 Environment Variables Needed

### Media Manager
- `ANTHROPIC_API_KEY` - For Claude AI image generation
- `LTX_API_KEY` - For LTX Video generation (optional)
- `ELEVENLABS_API_KEY` - For audio generation (optional)

### StoryForge
- `GEMINI_API_KEY` - For Google Gemini AI
- Firebase credentials (see `.env.example`)

## 🔧 Troubleshooting

### Docker Issues

**Containers restarting?**
```bash
docker compose logs media-manager-backend
docker compose logs story-forge-backend
```

**Port conflicts?**
```bash
docker compose down
# Check what's using ports
netstat -ano | findstr :3000
netstat -ano | findstr :8000
```

### Missing Dependencies

**Media Manager:**
```bash
cd backend
pip install -r requirements.txt
```

**StoryForge:**
```bash
cd apps/story-forge/backend && npm install
cd apps/story-forge/frontend && npm install
```

### Database Issues

**Media Manager - Reset database:**
```bash
cd backend
rm sql_app.db
alembic upgrade head
```

**StoryForge - Check Firestore:**
- Ensure Firebase project is set up
- Check service account credentials

## 📁 Project Structure

```
unified-media-ecosystem/
├── apps/
│   ├── media-manager/          # Junction to ./backend + ./frontend
│   │   ├── backend/            # FastAPI
│   │   └── frontend/           # Next.js
│   └── story-forge/            # Junction to ../StoryBiblePortfolioApp
│       ├── backend/            # Node.js/Express
│       └── frontend/           # React/Vite
├── packages/
│   ├── shared/                 # Common types
│   ├── shared-ui/              # Shared components
│   └── shared-utils/           # Utilities
├── docker-compose.yml
├── .env                        # Your environment variables (DO NOT COMMIT)
└── START_HERE.md              # This file
```

## 🎨 Features by App

### Media Manager
- Universe/Project management
- Multi-modal asset creation (text, image, video, audio, 3D)
- AI generation with Claude, LTX Video, ElevenLabs
- Human-in-the-loop review system
- Media gallery with filtering

### StoryForge
- Story Bible editor (multi-tab interface)
- Entity library (characters, items, locations)
- Timeline system with event visualization
- AI-powered narrative simulation
- Real-time sync via Firebase

## 🔗 API Documentation

- **Media Manager API**: http://localhost:8000/docs (FastAPI Swagger)
- **StoryForge API**: No auto-docs (Express), check `apps/story-forge/backend/api-server.js`

## 💡 Development Tips

1. **Use workspaces**: `npm install --workspace=apps/story-forge/backend`
2. **Shared packages**: Import from `@unified/shared`, `@unified/shared-ui`, etc.
3. **Docker logs**: `docker compose logs -f media-manager-backend`
4. **Hot reload**: All frontends support hot module replacement
5. **Database migrations**: Media Manager uses Alembic (`alembic revision --autogenerate -m "message"`)

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Port 3000 already in use | Stop other Next.js apps or change port in `frontend/package.json` |
| Celery worker not starting | Ensure Redis is running: `docker compose up redis` |
| Firebase errors | Check `.env` Firebase credentials |
| Module not found | Run `npm install` in the relevant workspace |
| Python import errors | Activate venv: `source venv/bin/activate` |

## 📚 Next Steps

1. ✅ Set up environment variables (`.env`)
2. ✅ Start services (Docker or individual)
3. ✅ Create your first Universe in Media Manager
4. ✅ Create your first Story Bible in StoryForge
5. ✅ Explore AI generation features
6. ✅ Review HITL workflow in Media Manager

---

**Need Help?** Check the main [README.md](./README.md) for detailed documentation.
