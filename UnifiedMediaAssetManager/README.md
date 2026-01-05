# Unified Media Asset Manager

A full-stack platform for designing, generating, and managing multi-modal media assets and story elements. Create universes, populate them with elements (characters, locations, props), and attach rich multi-modal components (text, images, video, audio, 3D models, attributes, and relationships).

## Features

- **Universe Management**: Create and organize story worlds/projects
- **Element System**: Add characters, locations, props, and other entities to your universes
- **Multi-Modal Components**: Attach various types of content to elements:
  - Text components (descriptions, notes, dialogue)
  - Image components with AI generation support
  - Video, Audio, and 3D Model components
  - Attribute components (stats, properties)
  - Relationship components (connections between elements)
- **AI Image Generation**: Pluggable AI provider system for generating images from text prompts
- **Media Storage**: Support for local filesystem or S3-compatible cloud storage
- **Authentication**: JWT-based authentication with role-based access control

## Project Structure

This project is a monorepo containing two main packages:

-   `/frontend`: A [Next.js](https://nextjs.org/) 16 application (React 19) that serves as the user interface
-   `/backend`: A [FastAPI](https://fastapi.tiangolo.com/) application (Python 3.11+) that provides the API and manages data

## Getting Started

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 20+** (for frontend)
- **Docker & Docker Compose** (optional, for containerized deployment)

### Option 1: Docker Compose (Recommended for Quick Start)

The fastest way to get started:

```bash
# Start all services
docker-compose up

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend Setup

1.  Navigate to the `backend` directory: `cd backend`

2.  Create and activate a virtual environment:

		- macOS / Linux:
			```bash
			python3 -m venv venv
			source venv/bin/activate
			```

		- Windows (PowerShell):
			```powershell
			python -m venv venv
			.\venv\Scripts\Activate.ps1
			```

3.  Install dependencies:
		```bash
		pip install -r requirements.txt
		```

4.  Set up environment variables:
		```bash
		cp .env.example .env
		# Edit .env with your configuration
		```

5.  Run database migrations:
		```bash
		alembic upgrade head
		```

6.  Start the development server:
		```bash
		uvicorn main:app --reload --host 0.0.0.0 --port 8000
		```

The API will be available at `http://127.0.0.1:8000`. API documentation at `http://127.0.0.1:8000/docs`.

#### Frontend Setup

1.  Navigate to the `frontend` directory: `cd frontend`

2.  Install dependencies:
		```bash
		npm install
		```

3.  Set up environment variables:
		```bash
		cp .env.example .env.local
		# Edit .env.local if needed (defaults to http://127.0.0.1:8000)
		```

4.  Start the development server:
		```bash
		npm run dev
		```

The application will be available at `http://localhost:3000`.

## Configuration

### Backend Environment Variables

Key configuration options in `.env` (see `.env.example` for all options):

```bash
# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./sql_app.db

# JWT Authentication - MUST change in production!
JWT_SECRET=your-secure-random-secret-here
JWT_ALGO=HS256

# CORS (comma-separated allowed origins)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Media Storage
MEDIA_STORAGE=local  # or 's3'

# AI Provider
AI_PROVIDER=placeholder  # or 'http' for custom endpoint
```

**Security Note**: Always generate a secure JWT_SECRET for production:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Frontend Environment Variables

In `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
# NEXT_PUBLIC_AUTH_TOKEN=your-jwt-token (optional)
```

## Usage

### Getting an Authentication Token

1. Start the backend server
2. Get a development token:
   ```bash
   curl -X POST http://localhost:8000/auth/dev-token
   ```
3. Use the returned token in requests or store in browser localStorage

### Basic Workflow

1. **Create a Universe**: Go to home page and create a new universe (e.g., "My Sci-Fi World")
2. **Add Elements**: Click on your universe and add elements (characters, locations, etc.)
3. **Add Components**: Click on an element to add various components:
   - Add text descriptions
   - Generate AI images from prompts
   - Attach media files
   - Define attributes and relationships

## Database Migrations

We include an Alembic scaffold in `backend/alembic/`. To create and run migrations:

```bash
cd backend
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"
# Apply migrations
alembic upgrade head
```

Alembic uses `DATABASE_URL` environment variable (defaults to `sqlite:///./sql_app.db`).

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify Python version: `python --version` (should be 3.11+)
- Run migrations: `alembic upgrade head`
- Check environment variables in `.env`

### Frontend won't start
- Check if port 3000 is already in use
- Verify Node version: `node --version` (should be 20+)
- Clear cache: `rm -rf .next node_modules && npm install`
- Check `NEXT_PUBLIC_API_URL` points to backend

### Images not displaying
- Verify MEDIA_STORAGE configuration
- Check media directory exists: `backend/media/`
- Check CORS settings if accessing from different origin

### Authentication errors
- Verify JWT_SECRET is consistent
- Check if token expired (24 hour default)
- Get new dev token: `curl -X POST http://localhost:8000/auth/dev-token`

## Production Deployment

### Security Checklist

- ✅ **Change default JWT_SECRET** to a secure random value
- ✅ **Use PostgreSQL** instead of SQLite
- ✅ **Configure CORS_ORIGINS** to only allow your production domain
- ✅ **Use HTTPS** in production
- ✅ **Store secrets securely** (use secrets management service)
- ✅ **Disable DISABLE_AUTH** in production
- ✅ **Run migrations** before deployment: `alembic upgrade head`

### Infrastructure

- **Secrets / env:** Set `JWT_SECRET`, `DATABASE_URL`, `MEDIA_STORAGE`, `S3_BUCKET`, `S3_REGION`, `CORS_ORIGINS`
- **Auth:** Ensure `DISABLE_AUTH` is not set
- **Storage:** Provision S3 or compatible object storage
- **Database:** Provision managed PostgreSQL and run migrations
- **CI/CD:** Configure secrets securely, run tests and security scans
- **TLS & networking:** Serve backend behind TLS, configure CORS properly
- **Monitoring:** Add logging, metrics, and alerting

See `docs/runbook.md` for detailed production operations.

## Development

### Running Tests

Backend tests:
```bash
cd backend
pytest
```

Frontend E2E tests:
```bash
cd frontend
npm run test:e2e
```

### Code Quality

Backend linting:
```bash
cd backend
black app/
flake8 app/
```

Frontend linting:
```bash
cd frontend
npm run lint
```

