from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel
import time
import urllib.parse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure structured logging before anything else
from .logging_config import configure_logging, get_logger
configure_logging()

logger = get_logger("main")

from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
from pathlib import Path
from contextlib import asynccontextmanager

from .models.core import Universe, Element, AnyComponent, TextComponent, ImageComponent
from .models.database import UniverseDB, ElementDB, ComponentDB
from .models.database import UserDB, AgentJobDB, VideoJobDB, AudioJobDB
from .database import SessionLocal, engine, get_db, create_db_and_tables
from . import storage
from .ai_provider import generate_image as provider_generate_image
from . import auth
from .agents.tasks import process_agent_job, get_job_stats
from .agents.video_strategy_agent import VideoStrategyAgent
from .monitoring import init_sentry, init_prometheus, capture_exception
from .agents.video_generation_agent import VideoGenerationAgent
from .agents.audio_agent import AudioAgent
from .services.video_storage import get_video_storage

# Import Phase 1 API routers
from .api import world_config, entity_traits, timeline
# Import Phase 4 API routers
from .api import providers
# Import authentication API router
from .api import auth as auth_api
# Import HITL API router
from .api import hitl
# Import story deconstruction API router
from .api import deconstruction
# Import templates API router
from .api import templates
# Import 3D models API router
from .api import models
# Import analytics API router
from .api import analytics
# Import image generation API router
from .api import image

@asynccontextmanager
async def lifespan(app):
    # Initialize monitoring (Sentry, Prometheus)
    sentry_enabled = init_sentry()
    prometheus_enabled = init_prometheus(app)
    if sentry_enabled or prometheus_enabled:
        logger.info(f"Monitoring initialized: Sentry={sentry_enabled}, Prometheus={prometheus_enabled}")

    # Ensure media directories exist at startup and the database schema is ready
    try:
        storage.ensure_dirs()
    except Exception as e:
        logger.warning(f"Could not create media directories: {e}")
    try:
        create_db_and_tables()
    except Exception as e:
        logger.warning(f"Could not initialize database tables: {e}")

    # Security warnings
    if getattr(auth, "JWT_SECRET", None) == "dev-secret":
        print("\n" + "="*80)
        print("WARNING: Using default JWT_SECRET! This is insecure for production.")
        print("Please set JWT_SECRET environment variable to a secure random value.")
        print("Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        print("="*80 + "\n")

    yield


app = FastAPI(title="Aetheria Studio API", lifespan=lifespan)

# Register Phase 1 API routers (World Building)
app.include_router(world_config.router)
app.include_router(entity_traits.router)
app.include_router(timeline.router)
# Register Phase 4 API routers (Provider Integration)
app.include_router(providers.router)
# Register authentication API router
app.include_router(auth_api.router)
# Register HITL API router
app.include_router(hitl.router)
# Register story deconstruction API router
app.include_router(deconstruction.router)
# Register templates API router
app.include_router(templates.router)
# Register 3D models API router
app.include_router(models.router)
# Register analytics API router
app.include_router(analytics.router)
# Register image generation API router
app.include_router(image.router)

# Ensure DB and media dirs exist at import time for tests that instantiate
# `TestClient(app)` at module import (some test files do this at top-level).
try:
    storage.ensure_dirs()
except Exception as e:
    # Silent failure OK during test imports - will be retried in lifespan
    logging.debug(f"Initial storage setup deferred: {e}")
try:
    create_db_and_tables()
except Exception as e:
    # Silent failure OK during test imports - will be retried in lifespan
    logging.debug(f"Initial database setup deferred: {e}")


@app.post("/auth/dev-token")
def dev_token():
    """Return a development token for quick local testing. Do not expose in production."""
    token = auth.issue_dev_token(subject="dev")
    return {"token": token}

# (startup logic moved into lifespan handler)

# Set up CORS middleware
# Configure via CORS_ORIGINS environment variable (comma-separated)
# Default to localhost for development, change in production
cors_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [origin.strip() for origin in cors_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware (must be added first to wrap everything)
from .middleware.request_logging import RequestLoggingMiddleware
request_logging_enabled = os.environ.get("REQUEST_LOGGING_ENABLED", "true").lower() == "true"
if request_logging_enabled:
    app.add_middleware(RequestLoggingMiddleware)

# Add rate limiting middleware
from .middleware.rate_limit import RateLimitMiddleware
rate_limit_enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
app.add_middleware(RateLimitMiddleware, enabled=rate_limit_enabled)


# Note: mounting static files must happen after routes that handle /media/*
# to avoid Shadowing POST routes like /media/upload. The mount is added
# at the bottom of the file after all endpoint definitions.


@app.post("/media/upload")
def upload_media(file: UploadFile = File(...), current_user: dict = Depends(auth.get_current_user)):
    """Upload a file and return a stable URL to access it under /media."""
    try:
        content = file.file.read()
        saved_path, public_url = storage.save_uploaded_file(content, filename=file.filename)
        return {"url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

# --- Request Models ---

class CreateElementRequest(BaseModel):
    name: str
    element_type: str = "Generic"


class UpdateUniverseRequest(BaseModel):
    """Request model for updating a universe."""
    name: Optional[str] = None
    description: Optional[str] = None


class UpdateElementRequest(BaseModel):
    """Request model for updating an element."""
    name: Optional[str] = None
    element_type: Optional[str] = None


class UpdateComponentRequest(BaseModel):
    """Request model for updating a component."""
    type: Optional[str] = None
    data: Optional[Dict] = None


class GenerateImageRequest(BaseModel):
    prompt: str

class CreateAgentJobRequest(BaseModel):
    agent_type: str  # 'narrative', 'spatial', or 'consistency'
    input_data: Dict  # Agent-specific input parameters
    universe_id: str = None  # Optional universe context

def convert_component_db_to_pydantic(comp_db: ComponentDB) -> AnyComponent:
    if comp_db.type == "TextComponent":
        return TextComponent(id=comp_db.id, data=comp_db.data)
    elif comp_db.type == "ImageComponent":
        return ImageComponent(id=comp_db.id, data=comp_db.data)
    # Add other component types here as they are implemented
    else:
        return AnyComponent(id=comp_db.id, type=comp_db.type, data=comp_db.data)

def convert_element_db_to_pydantic(el_db: ElementDB) -> Element:
    components_pydantic = [convert_component_db_to_pydantic(comp_db) for comp_db in el_db.components]
    return Element(
        id=el_db.id,
        universe_id=el_db.universe_id,
        name=el_db.name,
        element_type=el_db.element_type,
        components=components_pydantic
    )

def convert_universe_db_to_pydantic(uni_db: UniverseDB) -> Universe:
    elements_pydantic = [convert_element_db_to_pydantic(el_db) for el_db in uni_db.elements]
    return Universe(
        id=uni_db.id,
        name=uni_db.name,
        description=uni_db.description,
        owner=uni_db.owner_id or "",
        elements=elements_pydantic
    )

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Aetheria Studio API"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint for production monitoring.

    Returns status of all critical components:
    - Database connectivity
    - External providers (if configured)
    - System resources
    - Application version
    """
    import sys
    import platform
    from datetime import datetime

    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {}
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
        health["checks"]["database"] = {
            "status": "healthy",
            "type": "postgresql" if "postgresql" in str(db.bind.url) else "sqlite"
        }
    except Exception as e:
        health["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "unhealthy"

    # Redis check (optional)
    redis_url = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            health["checks"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
            # Redis failure is non-critical for basic operation
    else:
        health["checks"]["redis"] = {"status": "not_configured"}

    # Provider configuration check
    providers = {
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "runway": bool(os.getenv("RUNWAY_API_KEY")),
        "ltx": bool(os.getenv("LTX_API_KEY")),
        "elevenlabs": bool(os.getenv("ELEVENLABS_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }
    health["checks"]["providers"] = {
        "configured": [k for k, v in providers.items() if v],
        "not_configured": [k for k, v in providers.items() if not v]
    }

    # System info
    health["system"] = {
        "python_version": sys.version.split()[0],
        "platform": platform.system(),
        "architecture": platform.machine()
    }

    return health


@app.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes-style readiness probe.
    Returns 200 if the service is ready to accept traffic.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi import Response
        return Response(content='{"status": "not_ready"}', status_code=503, media_type="application/json")


@app.get("/health/live")
def liveness_check():
    """
    Kubernetes-style liveness probe.
    Returns 200 if the service is alive.
    """
    return {"status": "alive"}


# --- Universe & Element Endpoints ---

@app.post("/universes", response_model=Universe, status_code=201)
def create_universe(universe: Universe, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    """Creates a new Universe. Owner is set to token subject by default."""
    owner_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    db_universe = UniverseDB(id=universe.id, name=universe.name, description=universe.description, owner_id=owner_sub)
    db.add(db_universe)
    db.commit()
    db.refresh(db_universe)
    uni = convert_universe_db_to_pydantic(db_universe)
    uni.owner = db_universe.owner_id or ""
    return uni


@app.post("/users", status_code=201)
def create_user(username: str, display_name: str = "", db: Session = Depends(get_db)):
    """Create a lightweight user record. Returns created user id and username."""
    existing = db.query(UserDB).filter(UserDB.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = UserDB(username=username, display_name=display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}


@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    return [{"id": u.id, "username": u.username, "display_name": u.display_name} for u in users]

@app.get("/universes", response_model=List[Universe])
def get_all_universes(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves all Universes with pagination and search support.
    
    Args:
        limit: Maximum number of results (default 100, max 1000)
        offset: Number of results to skip (default 0)
        search: Optional search query to filter by name or description
    """
    # Enforce max limit to prevent abuse
    limit = min(limit, 1000)
    
    # Base query
    query = db.query(UniverseDB).options(
        joinedload(UniverseDB.elements).joinedload(ElementDB.components)
    )
    
    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (UniverseDB.name.ilike(search_pattern)) |
            (UniverseDB.description.ilike(search_pattern))
        )
    
    # Apply pagination
    universes = query.offset(offset).limit(limit).all()
    return [convert_universe_db_to_pydantic(uni) for uni in universes]

@app.get("/universes/{universe_id}", response_model=Universe)
def get_universe(universe_id: str, db: Session = Depends(get_db)):
    """Retrieves a single Universe by its ID."""
    universe = db.query(UniverseDB).options(joinedload(UniverseDB.elements).joinedload(ElementDB.components)).filter(UniverseDB.id == universe_id).first()
    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")
    
    return convert_universe_db_to_pydantic(universe)

@app.put("/universes/{universe_id}", response_model=Universe)
def update_universe(
    universe_id: str,
    update_data: UpdateUniverseRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update an existing universe. Only the owner or admin can update."""
    universe = db.query(UniverseDB).options(
        joinedload(UniverseDB.elements).joinedload(ElementDB.components)
    ).filter(UniverseDB.id == universe_id).first()

    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")

    # Permission check: owner or admin
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    # Update fields if provided
    if update_data.name is not None:
        universe.name = update_data.name
    if update_data.description is not None:
        universe.description = update_data.description

    db.commit()
    db.refresh(universe)

    return convert_universe_db_to_pydantic(universe)


@app.delete("/universes/{universe_id}", status_code=204)
def delete_universe(
    universe_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Delete a universe and all its elements/components. Only the owner or admin can delete."""
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()

    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")

    # Permission check: owner or admin
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    # Delete universe (cascade will handle elements and components)
    db.delete(universe)
    db.commit()

    return None


@app.post("/universes/{universe_id}/elements", response_model=Element, status_code=201)
def add_element_to_universe(universe_id: str, element_data: CreateElementRequest, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    """Adds a new Element to a specific Universe. Allowed for universe owner or admin."""
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")

    # Permission: allow if admin or owner
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    new_element_db = ElementDB(
        universe_id=universe_id,
        name=element_data.name,
        element_type=element_data.element_type
    )
    db.add(new_element_db)
    db.commit()
    db.refresh(new_element_db)
    return convert_element_db_to_pydantic(new_element_db)

@app.get("/universes/{universe_id}/elements", response_model=List[Element])
def get_elements_in_universe(
    universe_id: str,
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    element_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves all Elements within a specific Universe with pagination and filtering.
    
    Args:
        universe_id: UUID of the universe
        limit: Maximum number of results (default 100, max 1000)
        offset: Number of results to skip (default 0)
        search: Optional search query to filter by element name
        element_type: Optional filter by element type (e.g., "Character", "Location")
    """
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")
    
    # Enforce max limit
    limit = min(limit, 1000)
    
    # Base query
    query = db.query(ElementDB).options(
        joinedload(ElementDB.components)
    ).filter(ElementDB.universe_id == universe_id)
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(ElementDB.name.ilike(search_pattern))
    
    # Apply type filter
    if element_type:
        query = query.filter(ElementDB.element_type == element_type)
    
    # Apply pagination
    elements = query.offset(offset).limit(limit).all()
    return [convert_element_db_to_pydantic(el) for el in elements]


@app.get("/universes/{universe_id}/elements/{element_id}", response_model=Element)
def get_element(
    universe_id: str,
    element_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single element by ID within a universe."""
    element = db.query(ElementDB).options(
        joinedload(ElementDB.components)
    ).filter(
        ElementDB.id == element_id,
        ElementDB.universe_id == universe_id
    ).first()

    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    return convert_element_db_to_pydantic(element)


@app.put("/universes/{universe_id}/elements/{element_id}", response_model=Element)
def update_element(
    universe_id: str,
    element_id: str,
    update_data: UpdateElementRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update an existing element. Only the universe owner or admin can update."""
    element = db.query(ElementDB).options(
        joinedload(ElementDB.components)
    ).filter(
        ElementDB.id == element_id,
        ElementDB.universe_id == universe_id
    ).first()

    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    # Permission check via universe ownership
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    # Update fields if provided
    if update_data.name is not None:
        element.name = update_data.name
    if update_data.element_type is not None:
        element.element_type = update_data.element_type

    db.commit()
    db.refresh(element)

    return convert_element_db_to_pydantic(element)


@app.delete("/universes/{universe_id}/elements/{element_id}", status_code=204)
def delete_element(
    universe_id: str,
    element_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Delete an element and all its components. Only the universe owner or admin can delete."""
    element = db.query(ElementDB).filter(
        ElementDB.id == element_id,
        ElementDB.universe_id == universe_id
    ).first()

    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    # Permission check via universe ownership
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    # Delete element (cascade will handle components)
    db.delete(element)
    db.commit()

    return None


@app.post("/universes/{universe_id}/elements/{element_id}/components", response_model=AnyComponent, status_code=201)
def add_component_to_element(universe_id: str, element_id: str, component: AnyComponent, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    """Adds a new Component to a specific Element. Allowed for universe owner or admin."""
    element = db.query(ElementDB).filter(ElementDB.id == element_id, ElementDB.universe_id == universe_id).first()
    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    # Permission: check universe owner or admin
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    new_component_db = ComponentDB(
        element_id=element_id,
        type=component.type,
        data=component.model_dump(exclude_unset=True) # Store the Pydantic model as a dictionary
    )
    db.add(new_component_db)
    db.commit()
    db.refresh(new_component_db)
    
    # Reconstruct the Pydantic model from the database object
    if new_component_db.type == "TextComponent":
        return TextComponent(id=new_component_db.id, data=new_component_db.data)
    elif new_component_db.type == "ImageComponent":
        return ImageComponent(id=new_component_db.id, data=new_component_db.data)
    # Add other component types here as they are implemented
    else:
        # Fallback for other component types not yet explicitly handled
        return AnyComponent(id=new_component_db.id, type=new_component_db.type, data=new_component_db.data)


@app.get("/universes/{universe_id}/elements/{element_id}/components", response_model=List[AnyComponent])
def get_components(
    universe_id: str,
    element_id: str,
    component_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all components for an element with optional type filtering."""
    element = db.query(ElementDB).filter(
        ElementDB.id == element_id,
        ElementDB.universe_id == universe_id
    ).first()

    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    query = db.query(ComponentDB).filter(ComponentDB.element_id == element_id)

    if component_type:
        query = query.filter(ComponentDB.type == component_type)

    components = query.all()
    return [convert_component_db_to_pydantic(comp) for comp in components]


@app.get("/universes/{universe_id}/elements/{element_id}/components/{component_id}", response_model=AnyComponent)
def get_component(
    universe_id: str,
    element_id: str,
    component_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve a single component by ID."""
    # Verify element exists in universe
    element = db.query(ElementDB).filter(
        ElementDB.id == element_id,
        ElementDB.universe_id == universe_id
    ).first()

    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    component = db.query(ComponentDB).filter(
        ComponentDB.id == component_id,
        ComponentDB.element_id == element_id
    ).first()

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    return convert_component_db_to_pydantic(component)


@app.put("/universes/{universe_id}/elements/{element_id}/components/{component_id}", response_model=AnyComponent)
def update_component(
    universe_id: str,
    element_id: str,
    component_id: str,
    update_data: UpdateComponentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Update an existing component. Only the universe owner or admin can update."""
    # Verify element exists in universe
    element = db.query(ElementDB).filter(
        ElementDB.id == element_id,
        ElementDB.universe_id == universe_id
    ).first()

    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    component = db.query(ComponentDB).filter(
        ComponentDB.id == component_id,
        ComponentDB.element_id == element_id
    ).first()

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    # Permission check via universe ownership
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    # Update fields if provided
    if update_data.type is not None:
        component.type = update_data.type
    if update_data.data is not None:
        component.data = update_data.data

    db.commit()
    db.refresh(component)

    return convert_component_db_to_pydantic(component)


@app.delete("/universes/{universe_id}/elements/{element_id}/components/{component_id}", status_code=204)
def delete_component(
    universe_id: str,
    element_id: str,
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Delete a component. Only the universe owner or admin can delete."""
    # Verify element exists in universe
    element = db.query(ElementDB).filter(
        ElementDB.id == element_id,
        ElementDB.universe_id == universe_id
    ).first()

    if not element:
        raise HTTPException(status_code=404, detail="Element not found")

    component = db.query(ComponentDB).filter(
        ComponentDB.id == component_id,
        ComponentDB.element_id == element_id
    ).first()

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    # Permission check via universe ownership
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    is_admin = auth.has_role(current_user, "admin")
    user_sub = current_user.get('sub') if isinstance(current_user, dict) else None
    if not (is_admin or (user_sub and universe and universe.owner_id == user_sub)):
        raise HTTPException(status_code=403, detail="Forbidden: requires owner or admin role")

    db.delete(component)
    db.commit()

    return None


# --- AI Service Endpoints ---

@app.post("/ai/generate/image")
def generate_image(request: GenerateImageRequest, current_user: dict = Depends(auth.get_current_user)):
    """
    Simulates generating an image from a prompt.
    In a real application, this would call a service like DALL-E or Stable Diffusion.
    """
    print(f"Simulating AI image generation for prompt: '{request.prompt}'")
    time.sleep(2) # Simulate the time it takes to generate an image

    try:
        prov_result = provider_generate_image(request.prompt)
        image_url = prov_result.get("url")
        provider = prov_result.get("provider")
        # If provider returned a remote URL, download and persist locally for stable serving
        if image_url:
            try:
                saved_path, public_url = storage.download_and_save(image_url)
                print(f"[{provider}] Saved generated image to: {saved_path}")
                return {"url": public_url, "provider": provider}
            except Exception as e:
                print(f"[{provider}] Failed to persist generated image: {e}")
                # Return remote URL as fallback
                return {"url": image_url, "provider": provider}
        else:
            raise HTTPException(status_code=500, detail="Provider did not return an image URL")
    except Exception as e:
        print(f"AI generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")


# --- Agent Job Endpoints ---

@app.post("/agents/jobs", status_code=202)
def create_agent_job(
    request: CreateAgentJobRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Create a new AI agent job for asynchronous processing.

    Supported agent types:
    - 'narrative': Generate narrative scenes and video prompts
    - 'spatial': Generate location descriptions and map layouts
    - 'consistency': Validate content against world rules

    Returns job ID for status tracking.
    """
    # Validate agent type
    valid_agent_types = ['narrative', 'spatial', 'consistency']
    if request.agent_type not in valid_agent_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_type. Must be one of: {', '.join(valid_agent_types)}"
        )

    # Validate universe_id if provided
    if request.universe_id:
        universe = db.query(UniverseDB).filter(UniverseDB.id == request.universe_id).first()
        if not universe:
            raise HTTPException(status_code=404, detail="Universe not found")

    # Create job record
    job = AgentJobDB(
        id=str(uuid.uuid4()),
        universe_id=request.universe_id,
        agent_type=request.agent_type,
        status='pending',
        input_data=request.input_data
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Queue the job for processing
    process_agent_job.delay(job.id)

    return {
        "job_id": job.id,
        "status": job.status,
        "agent_type": job.agent_type,
        "created_at": job.created_at.isoformat()
    }


@app.get("/agents/jobs")
def list_agent_jobs(
    universe_id: str = None,
    agent_type: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    List agent jobs with optional filtering.

    Query parameters:
    - universe_id: Filter by universe
    - agent_type: Filter by agent type
    - status: Filter by job status (pending, processing, completed, failed)
    - limit: Max results to return (default 50)
    - offset: Pagination offset (default 0)
    """
    query = db.query(AgentJobDB)

    # Apply filters
    if universe_id:
        query = query.filter(AgentJobDB.universe_id == universe_id)
    if agent_type:
        query = query.filter(AgentJobDB.agent_type == agent_type)
    if status:
        query = query.filter(AgentJobDB.status == status)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    jobs = query.order_by(AgentJobDB.created_at.desc()).limit(limit).offset(offset).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": [
            {
                "job_id": job.id,
                "universe_id": job.universe_id,
                "agent_type": job.agent_type,
                "status": job.status,
                "confidence_score": job.confidence_score,
                "human_review_required": job.human_review_required,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message
            }
            for job in jobs
        ]
    }


@app.get("/agents/jobs/{job_id}")
def get_agent_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Get detailed information about a specific agent job, including results.
    """
    job = db.query(AgentJobDB).filter(AgentJobDB.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "universe_id": job.universe_id,
        "agent_type": job.agent_type,
        "status": job.status,
        "input_data": job.input_data,
        "output_data": job.output_data,
        "confidence_score": job.confidence_score,
        "human_review_required": job.human_review_required,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


@app.post("/agents/jobs/{job_id}/retry", status_code=202)
def retry_agent_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Retry a failed agent job.

    Only jobs with status 'failed' can be retried.
    """
    job = db.query(AgentJobDB).filter(AgentJobDB.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != 'failed':
        raise HTTPException(
            status_code=400,
            detail=f"Can only retry failed jobs. Current status: {job.status}"
        )

    # Reset job status
    job.status = 'pending'
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    db.commit()

    # Queue the job for processing
    process_agent_job.delay(job.id)

    return {
        "job_id": job.id,
        "status": job.status,
        "message": "Job queued for retry"
    }


@app.get("/agents/stats")
def get_agent_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Get statistics about agent job processing.

    Returns counts by status, agent type, and average confidence scores.
    """
    # Use the Celery task to get stats
    stats = get_job_stats()
    return stats


# ============================================================================
# Video Generation Endpoints
# ============================================================================

class VideoGenerateRequest(BaseModel):
    universe_id: Optional[str] = None
    generation_type: str = "text_to_video"  # 'text_to_video' or 'image_to_video'
    prompt: str
    negative_prompt: Optional[str] = None
    reference_image_url: Optional[str] = None
    mood: Optional[int] = 50  # 0-100 slider
    aspect_ratio: str = "16:9"
    duration: int = 5
    platform: Optional[str] = "youtube"  # Platform optimization
    
    # Provider selection
    provider: Optional[str] = None  # 'ltx', 'runway', 'mock', or None for auto
    
    # LTX-2 specific parameters
    ltx_model: Optional[str] = "ltx-2-pro"  # 'ltx-2-fast' or 'ltx-2-pro'
    ltx_resolution: Optional[str] = "1920x1080"  # '1920x1080', '2560x1440', '3840x2160'
    ltx_fps: Optional[int] = 25  # 25 or 50
    audio_sync_enabled: Optional[bool] = False


class VideoStrategyRequest(BaseModel):
    prompt: str
    mood: int = 50  # 0-100
    platform: Optional[str] = "youtube"
    num_variations: int = 3


@app.post("/api/video/generate")
async def generate_video(
    request: VideoGenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Create a video generation job.

    Process:
    1. Generate strategy using VideoStrategyAgent
    2. Create VideoGenerationAgent job
    3. Return job ID for status polling
    """
    try:
        # Step 1: Generate video strategy
        strategy_agent = VideoStrategyAgent()
        strategy_result = await strategy_agent.process({
            "prompt": request.prompt,
            "mood_slider": request.mood or 50,
            "platform": request.platform or "youtube",
            "num_variations": 1
        })

        if not strategy_result.get("variations"):
            raise HTTPException(status_code=500, detail="Strategy generation failed")

        # Get first variation
        variation = strategy_result.get("variations", [{}])[0]

        # Step 2: Create video job in database
        video_job = VideoJobDB(
            id=str(uuid.uuid4()),
            universe_id=request.universe_id,
            generation_type=request.generation_type,
            prompt=variation.get("enriched_prompt", request.prompt),
            negative_prompt=request.negative_prompt,
            reference_image_url=request.reference_image_url,
            mood_category=variation.get("mood_category"),
            camera_movement=variation.get("camera_movement"),
            aspect_ratio=request.aspect_ratio,
            duration=request.duration,
            provider=request.provider,  # None means use agent's default
            ltx_model=request.ltx_model,
            ltx_resolution=request.ltx_resolution,
            ltx_fps=request.ltx_fps,
            audio_sync_enabled=request.audio_sync_enabled,
            status="pending"
        )

        db.add(video_job)
        db.commit()
        db.refresh(video_job)

        # Step 3: Start video generation (async)
        generation_agent = VideoGenerationAgent()
        generation_params = {
            "generation_type": request.generation_type,
            "prompt": video_job.prompt,
            "negative_prompt": request.negative_prompt,
            "duration": video_job.duration,
            "aspect_ratio": video_job.aspect_ratio,
            "reference_image_url": request.reference_image_url,
            "ltx_model": request.ltx_model,
            "ltx_resolution": request.ltx_resolution,
            "ltx_fps": request.ltx_fps,
            "audio_sync_enabled": request.audio_sync_enabled,
            "provider": request.provider
        }
        
        generation_result = await generation_agent.process(generation_params)

        # Update job with provider info
        if generation_result.get("success"):
            video_job.provider = generation_result.get("provider")
            video_job.provider_job_id = generation_result.get("provider_job_id")
            video_job.ltx_request_id = generation_result.get("ltx_request_id")
            
            # For LTX: save video data immediately
            if generation_result.get("video_data"):
                from pathlib import Path
                media_dir = Path("media/videos")
                media_dir.mkdir(parents=True, exist_ok=True)
                
                video_filename = f"{video_job.id}.mp4"
                video_path = media_dir / video_filename
                
                with open(video_path, "wb") as f:
                    f.write(generation_result["video_data"])
                
                video_job.local_path = str(video_path)
                video_job.file_size = generation_result.get("file_size")
                video_job.video_url = f"/media/videos/{video_filename}"
                video_job.status = "completed"
                video_job.completed_at = datetime.utcnow()
            else:
                video_job.status = "processing"
                
            db.commit()

        return {
            "job_id": video_job.id,
            "status": video_job.status,
            "provider": video_job.provider,
            "provider_job_id": video_job.provider_job_id,
            "video_url": video_job.video_url,
            "strategy": {
                "mood_category": video_job.mood_category,
                "camera_movement": video_job.camera_movement,
                "enriched_prompt": video_job.prompt
            }
        }

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/jobs")
def list_video_jobs(
    universe_id: Optional[str] = None,
    status: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    List video generation jobs with advanced filtering and pagination.
    
    Query Parameters:
    - universe_id: Filter by universe
    - status: Filter by status (pending, processing, completed, failed)
    - provider: Filter by provider (ltx, runway, mock)
    - limit: Number of results (default: 20, max: 100)
    - offset: Pagination offset
    - sort_by: Sort field (created_at, completed_at, duration)
    - sort_order: Sort order (asc, desc)
    """
    query = db.query(VideoJobDB)

    # Apply filters
    if universe_id:
        query = query.filter(VideoJobDB.universe_id == universe_id)
    if status:
        query = query.filter(VideoJobDB.status == status)
    if provider:
        query = query.filter(VideoJobDB.provider == provider)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_field = getattr(VideoJobDB, sort_by, VideoJobDB.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())

    # Apply pagination
    limit = min(limit, 100)  # Max 100 results
    jobs = query.offset(offset).limit(limit).all()

    return {
        "jobs": [
            {
                "id": job.id,
                "universe_id": job.universe_id,
                "generation_type": job.generation_type,
                "prompt": job.prompt,
                "negative_prompt": job.negative_prompt,
                "status": job.status,
                "provider": job.provider,
                "mood_category": job.mood_category,
                "camera_movement": job.camera_movement,
                "aspect_ratio": job.aspect_ratio,
                "duration": job.duration,
                "video_url": job.video_url,
                "thumbnail_url": job.thumbnail_url,
                "file_size": job.file_size,
                "ltx_model": job.ltx_model,
                "ltx_resolution": job.ltx_resolution,
                "ltx_fps": job.ltx_fps,
                "audio_sync_enabled": job.audio_sync_enabled,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message
            }
            for job in jobs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


@app.get("/api/video/jobs/{job_id}")
async def get_video_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get video job status and check provider for updates."""
    job = db.query(VideoJobDB).filter(VideoJobDB.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    # If still processing, check provider status
    if job.status == "processing" and job.provider_job_id:
        agent = VideoGenerationAgent()
        provider_status = await agent.check_job_status(job.provider, job.provider_job_id)

        if provider_status.get("status") == "completed":
            # Download and store video
            video_url = provider_status.get("video_url")
            if video_url:
                storage = get_video_storage()
                result = await storage.download_from_url(
                    video_url,
                    job.universe_id or "default",
                    job.id
                )

                if result.get("success"):
                    job.status = "completed"
                    job.video_url = result.get("public_url")
                    job.file_size = result.get("file_size")
                    job.duration_actual = result.get("duration")
                    job.completed_at = datetime.utcnow()
                    db.commit()

    return {
        "id": job.id,
        "universe_id": job.universe_id,
        "generation_type": job.generation_type,
        "prompt": job.prompt,
        "status": job.status,
        "provider": job.provider,
        "provider_job_id": job.provider_job_id,
        "mood_category": job.mood_category,
        "camera_movement": job.camera_movement,
        "output_video_url": job.video_url,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message
    }


@app.post("/api/video/strategy")
async def generate_video_strategy(
    request: VideoStrategyRequest,
    current_user: dict = Depends(auth.get_current_user)
):
    """Generate video strategy variations without creating a job."""
    try:
        agent = VideoStrategyAgent()
        result = await agent.process({
            "prompt": request.prompt,
            "mood_slider": request.mood,
            "platform": request.platform,
            "num_variations": request.num_variations
        })

        return result

    except Exception as e:
        logger.error(f"Strategy generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Video Transcoding Endpoints
# ============================================================================

class VideoTranscodeRequest(BaseModel):
    """Request model for video transcoding."""
    platforms: List[str]  # e.g., ["tiktok", "youtube", "instagram"]


@app.post("/api/video/jobs/{job_id}/transcode")
async def transcode_video(
    job_id: str,
    request: VideoTranscodeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Transcode a completed video to multiple platform formats.

    Requires FFmpeg to be installed on the system.

    Platforms available:
    - tiktok: 9:16, 1080x1920, 5Mbps
    - youtube: 16:9, 1920x1080, 8Mbps
    - youtube_4k: 16:9, 3840x2160, 20Mbps
    - instagram: 4:5, 1080x1350, 5Mbps
    - instagram_reels: 9:16, 1080x1920, 6Mbps
    - twitter: 16:9, 1280x720, 5Mbps
    - web: VP9 WebM, 1920x1080, 4Mbps
    - web_mobile: 9:16, 720x1280, 2Mbps
    """
    from .services.video_transcoding import get_transcoding_service

    # Get the video job
    job = db.query(VideoJobDB).filter(VideoJobDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Video job is not completed")

    if not job.local_path:
        raise HTTPException(
            status_code=400,
            detail="Video file not available locally for transcoding"
        )

    # Validate platforms
    service = get_transcoding_service()
    available_profiles = {p["name"] for p in service.get_available_profiles()}
    invalid_platforms = set(request.platforms) - available_profiles
    if invalid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platforms: {invalid_platforms}. Available: {available_profiles}"
        )

    # Perform transcoding
    try:
        results = service.transcode_multi(
            input_path=job.local_path,
            platforms=request.platforms,
            video_id=job_id
        )

        # Store results in job metadata
        existing_variants = job.encoding_variants or []
        if isinstance(existing_variants, str):
            import json
            existing_variants = json.loads(existing_variants)

        # Add new variants
        for variant in results["variants"]:
            if variant["success"]:
                existing_variants.append(variant)

        job.encoding_variants = existing_variants
        db.commit()

        return {
            "job_id": job_id,
            "success_count": results["success_count"],
            "failure_count": results["failure_count"],
            "variants": results["variants"]
        }

    except Exception as e:
        logger.error(f"Transcoding failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/jobs/{job_id}/variants")
async def get_video_variants(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get all encoding variants for a video job."""
    job = db.query(VideoJobDB).filter(VideoJobDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    variants = job.encoding_variants or []
    if isinstance(variants, str):
        import json
        variants = json.loads(variants)

    return {
        "job_id": job_id,
        "original_url": job.video_url,
        "original_path": job.local_path,
        "variants": variants
    }


@app.get("/api/video/transcode/profiles")
async def get_transcode_profiles(
    current_user: dict = Depends(auth.get_current_user)
):
    """Get available transcoding profiles."""
    from .services.video_transcoding import get_transcoding_service

    service = get_transcoding_service()
    return {"profiles": service.get_available_profiles()}


@app.get("/api/video/jobs/{job_id}/info")
async def get_video_info(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get detailed video file information using ffprobe."""
    from .services.video_transcoding import get_transcoding_service

    job = db.query(VideoJobDB).filter(VideoJobDB.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    if not job.local_path:
        raise HTTPException(
            status_code=400,
            detail="Video file not available locally"
        )

    service = get_transcoding_service()
    info = service.get_video_info(job.local_path)

    return {
        "job_id": job_id,
        "video_info": info
    }


# ============================================================================
# Audio Processing Endpoints
# ============================================================================

class AudioTranscribeRequest(BaseModel):
    audio_url: str
    universe_id: Optional[str] = None
    provider: str = "mock"  # 'mock' or 'whisper'


class AudioTTSRequest(BaseModel):
    text: str
    voice: str = "default"
    universe_id: Optional[str] = None
    provider: Optional[str] = None  # None uses AudioAgent's configured default


class AudioAnalyzeRequest(BaseModel):
    audio_url: str
    universe_id: Optional[str] = None
    provider: Optional[str] = None  # None uses AudioAgent's configured default


@app.post("/api/audio/transcribe")
async def transcribe_audio(
    request: AudioTranscribeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Transcribe audio to text."""
    try:
        # Create audio job
        audio_job = AudioJobDB(
            id=str(uuid.uuid4()),
            universe_id=request.universe_id,
            generation_type="transcription",
            audio_input_path=request.audio_url,
            provider=request.provider,
            status="processing"
        )
        db.add(audio_job)
        db.commit()

        # Process transcription
        agent = AudioAgent(config={"default_provider": request.provider})
        result = await agent.process({
            "task": "transcribe",
            "audio_url": request.audio_url,
            "provider": request.provider
        })

        # Update job
        if result.get("success"):
            audio_job.status = "completed"
            audio_job.output_data = result
            audio_job.completed_at = datetime.utcnow()
        else:
            audio_job.status = "failed"
            audio_job.error_message = result.get("error")

        db.commit()

        return {
            "job_id": audio_job.id,
            "status": audio_job.status,
            "result": result
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/audio/tts")
async def text_to_speech(
    request: AudioTTSRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Convert text to speech."""
    try:
        # Create audio job
        audio_job = AudioJobDB(
            id=str(uuid.uuid4()),
            universe_id=request.universe_id,
            generation_type="text_to_speech",
            prompt=request.text,
            voice_id=request.voice,
            provider=request.provider,
            status="processing"
        )
        db.add(audio_job)
        db.commit()

        # Process TTS
        agent = AudioAgent()
        tts_inputs = {
            "task": "tts",
            "text": request.text,
            "voice": request.voice,
        }
        # Only override provider if explicitly specified
        if request.provider:
            tts_inputs["provider"] = request.provider
        result = await agent.process(tts_inputs)

        # Update job
        if result.get("success"):
            # Save audio data if provided
            if result.get("audio_data"):
                from pathlib import Path
                media_dir = Path("media/audio")
                media_dir.mkdir(parents=True, exist_ok=True)

                audio_filename = f"{audio_job.id}.mp3"
                audio_path = media_dir / audio_filename

                with open(audio_path, "wb") as f:
                    f.write(result["audio_data"])

                audio_job.local_path = str(audio_path)
                audio_job.file_size = len(result["audio_data"])
                audio_job.audio_url = f"/media/audio/{audio_filename}"
                # Remove bytes from result before storing (not JSON serializable)
                del result["audio_data"]
            else:
                audio_job.audio_url = result.get("audio_url")

            audio_job.status = "completed"
            audio_job.duration = result.get("duration")
            audio_job.extra_metadata = result
            audio_job.completed_at = datetime.utcnow()
        else:
            audio_job.status = "failed"
            audio_job.error_message = result.get("error")

        db.commit()

        return {
            "job_id": audio_job.id,
            "status": audio_job.status,
            "audio_url": audio_job.audio_url,
            "duration": audio_job.duration,
            "result": result
        }

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/audio/analyze")
async def analyze_audio(
    request: AudioAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Analyze audio characteristics."""
    try:
        agent = AudioAgent()
        analyze_inputs = {
            "task": "analyze",
            "audio_url": request.audio_url,
        }
        if request.provider:
            analyze_inputs["provider"] = request.provider
        result = await agent.process(analyze_inputs)

        return result

    except Exception as e:
        logger.error(f"Audio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio/jobs")
def list_audio_jobs(
    universe_id: Optional[str] = None,
    generation_type: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    List audio generation jobs with advanced filtering and pagination.
    
    Query Parameters:
    - generation_type: Filter by type (text_to_speech, transcription, text_to_music)
    - provider: Filter by provider (elevenlabs, whisper, suno, mock)
    - status: Filter by status (pending, processing, completed, failed)
    - limit: Number of results (default: 20, max: 100)
    - offset: Pagination offset
    - sort_by: Sort field (created_at, created_at, duration)
    - sort_order: Sort order (asc, desc)
    """
    query = db.query(AudioJobDB)

    # Apply filters
    if universe_id:
        query = query.filter(AudioJobDB.universe_id == universe_id)
    if generation_type:
        query = query.filter(AudioJobDB.generation_type == generation_type)
    if provider:
        query = query.filter(AudioJobDB.provider == provider)
    if status:
        query = query.filter(AudioJobDB.status == status)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_field = getattr(AudioJobDB, sort_by, AudioJobDB.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())

    # Apply pagination
    limit = min(limit, 100)
    jobs = query.offset(offset).limit(limit).all()

    return {
        "jobs": [
            {
                "id": job.id,
                "universe_id": job.universe_id,
                "generation_type": job.generation_type,
                "prompt": job.prompt,
                "status": job.status,
                "provider": job.provider,
                "voice_id": job.voice_id,
                "language": job.language,
                "audio_url": job.audio_url,
                "local_path": job.local_path,
                "file_size": job.file_size,
                "duration": job.duration,
                "transcription": job.transcription,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message
            }
            for job in jobs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total
    }


@app.get("/api/audio/jobs/{job_id}")
def get_audio_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """Get specific audio job details."""
    job = db.query(AudioJobDB).filter(AudioJobDB.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Audio job not found")
    
    return {
        "id": job.id,
        "universe_id": job.universe_id,
        "generation_type": job.generation_type,
        "prompt": job.prompt,
        "status": job.status,
        "provider": job.provider,
        "voice_id": job.voice_id,
        "language": job.language,
        "audio_url": job.audio_url,
        "local_path": job.local_path,
        "file_size": job.file_size,
        "duration": job.duration,
        "transcription": job.transcription,
        "parameters": job.parameters,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message
    }


# Serve generated media files under /media (mount after route definitions)
media_dir = "media"
try:
    # prefer absolute path inside backend folder
    media_dir_path = str((Path(__file__).resolve().parent.parent / "media").resolve())
except Exception:
    media_dir_path = "media"

# Ensure media directory exists before mounting StaticFiles to avoid import-time errors
try:
    storage.ensure_dirs()
except Exception:
    # If ensure_dirs fails, continue — StaticFiles may still serve if path exists
    pass

app.mount("/media", StaticFiles(directory=media_dir_path), name="media")
