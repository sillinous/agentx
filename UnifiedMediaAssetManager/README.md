# Aetheria Studio

**AI-powered creative studio for multi-modal media generation and story universe creation.**

Aetheria Studio is a unified platform combining powerful media asset management with AI-powered storytelling capabilities:
- **Media Generation**: Video (LTX-2), Audio (ElevenLabs), Images, 3D models
- **Story Universes**: Create and manage narrative worlds with characters, locations, events
- **Human-in-the-Loop**: AI-assisted workflows with human oversight and refinement

> **Current Status:** Production-ready infrastructure | Both apps fully functional
>
> **📋 REQUIRED READING:** [CODEBASE_ASSESSMENT.md](./CODEBASE_ASSESSMENT.md) - Comprehensive technical documentation
>
> **For AI/Agents:** See [.claude/CLAUDE.md](./.claude/CLAUDE.md) for session instructions

## What's Inside

### 🎨 Core Platform Features

Aetheria Studio is a full-stack creative platform for designing, generating, and managing multi-modal media assets and story universes.

**Media Generation:**
- **Video**: LTX-2 integration for text-to-video and image-to-video generation
- **Audio**: ElevenLabs TTS with 23+ professional voices and preview playback
- **Images**: AI image generation with pluggable provider system
- **3D Models**: Component-based 3D asset management

**Story Universe Management:**
- **Universe System**: Create and organize story worlds/projects
- **Element Library**: Characters, locations, props, and custom entities
- **Timeline System**: Create and visualize story chronology with linked events
- **Relationships**: Define connections between story elements

**AI-Powered Workflows:**
- **HITL System**: Human-in-the-loop workflow for AI-generated content review
- **Story Deconstruction**: Analyze existing narratives into structured elements
- **Multi-Modal Generation**: Combine text, audio, video, and 3D assets

**Infrastructure:**
- **Media Storage**: Local filesystem or S3-compatible cloud storage
- **Authentication**: JWT-based auth with role-based access control
- **Real-time Updates**: WebSocket support for live collaboration

**Tech Stack:**
- Backend: FastAPI (Python 3.8+), SQLAlchemy, Celery
- Frontend: Next.js 15, React 18, TypeScript, Tailwind CSS
- Database: SQLite (dev) / PostgreSQL (prod)
- AI Providers: LTX-2, ElevenLabs, OpenAI, Anthropic Claude

## Project Structure

```
aetheria-studio/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agents/            # AI generation agents (video, audio, story)
│   │   ├── api/               # API endpoints
│   │   ├── models/            # Database models
│   │   └── providers/         # AI provider integrations (LTX, ElevenLabs)
│   ├── media/                 # Local media storage
│   └── alembic/               # Database migrations
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js 15 App Router pages
│   │   ├── components/        # React components
│   │   └── services/          # API client services
│   └── public/                # Static assets
└── docker-compose.yml          # Docker setup
```

## Getting Started

### Prerequisites

- **Python 3.11+** (for Media Manager backend)
- **Node.js 20+** (for all frontends and StoryForge backend)
- **Docker & Docker Compose** (optional, for containerized deployment)
- **Firebase Account** (for StoryForge - free tier available)
- **Google Gemini API Key** (for StoryForge AI features)

### Option 1: Docker Compose (Recommended for Quick Start)

The fastest way to get both apps running:

```bash
# Start all services (both apps + shared services)
docker-compose up

# Access the applications:
# Media Manager Frontend: http://localhost:3000
# Media Manager Backend API: http://localhost:8000
# Media Manager API Docs: http://localhost:8000/docs
# StoryForge Frontend: http://localhost:5173
# StoryForge Backend: http://localhost:3001
# Flower (Celery monitoring): http://localhost:5555
```

### Option 2: Run Individual Apps

#### Media Manager Only

```bash
# Backend
cd apps/media-manager/backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd apps/media-manager/frontend
npm install
npm run dev
```

#### StoryForge Only

```bash
# Backend
cd apps/story-forge/backend
npm install
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and FIREBASE_PROJECT_ID
npm start

# Frontend (separate terminal)
cd apps/story-forge/frontend
npm install
cp .env.example .env
# Edit .env with your Firebase config
npm run dev
```

## Configuration

See individual app READMEs for detailed configuration:
- [Media Manager Configuration](./apps/media-manager/README.md)
- [StoryForge Configuration](./apps/story-forge/README.md)

### Quick Environment Setup

Copy the example file and configure:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Available Scripts

```bash
# Install all dependencies (all workspaces)
npm install

# Run specific app
npm run dev:media-manager:frontend
npm run dev:media-manager:backend
npm run dev:story-forge:frontend
npm run dev:story-forge:backend

# Build all apps
npm run build

# Run tests across all workspaces
npm run test
```

## Development

### Shared Packages

The monorepo includes shared packages for code reuse:

- `@unified/shared`: Common types and interfaces
- `@unified/shared-ui`: Reusable React components
- `@unified/shared-utils`: Utility functions

To use in your app:
```typescript
import { User, MediaAsset } from '@unified/shared';
import { formatDate } from '@unified/shared-utils';
```

## Architecture

Both apps share infrastructure while maintaining independence:

```
┌─────────────────────────────────────────────────────────────┐
│                    Unified Ecosystem                         │
├─────────────────────────┬───────────────────────────────────┤
│   Media Manager         │         StoryForge                │
├─────────────────────────┼───────────────────────────────────┤
│ Next.js → FastAPI       │   React/Vite → Node.js/Express    │
│      ↓         ↓        │        ↓              ↓           │
│   SQLite   Celery       │   Firestore    Gemini AI          │
│              ↓          │                                    │
│           Redis ←───────┴─────(shared services)─────────────┤
└─────────────────────────────────────────────────────────────┘
```

## Deployment

### Docker Deployment

```bash
# Production build and deploy
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Individual App Deployment

See deployment guides:
- [Media Manager Deployment](./apps/media-manager/docs/runbook.md)
- [StoryForge Deployment](./apps/story-forge/DEPLOYMENT_AND_TESTING.md)

## Documentation

- [Media Manager Docs](./apps/media-manager/)
  - [Codebase Assessment](./CODEBASE_ASSESSMENT.md)
  - [HITL System Guide](./HITL_SYSTEM_GUIDE.md)
  - [Project Status](./PROJECT_STATUS.md)
- [StoryForge Docs](./apps/story-forge/)
  - [README](./apps/story-forge/README.md)
  - [Architecture](./apps/story-forge/HITL_ARCHITECTURE.md)
  - [Quick Start](./apps/story-forge/QUICK_START.md)

## License

ISC

---

**Questions?** Check the individual app READMEs or open an issue.

