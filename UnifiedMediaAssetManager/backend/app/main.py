from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import uuid
from pydantic import BaseModel
import time
import urllib.parse
from sqlalchemy.orm import Session, joinedload
import os
import logging

logger = logging.getLogger(__name__)

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
from .agents.video_generation_agent import VideoGenerationAgent
from .agents.audio_agent import AudioAgent
from .services.video_storage import get_video_storage

# Import Phase 1 API routers
from .api import world_config, entity_traits, timeline
# Import Phase 4 API routers
from .api import providers

@asynccontextmanager
async def lifespan(app):
    # Ensure media directories exist at startup and the database schema is ready
    try:
        storage.ensure_dirs()
    except Exception:
        pass
    try:
        create_db_and_tables()
    except Exception:
        pass

    # Security warnings
    if getattr(auth, "JWT_SECRET", None) == "dev-secret":
        print("\n" + "="*80)
        print("WARNING: Using default JWT_SECRET! This is insecure for production.")
        print("Please set JWT_SECRET environment variable to a secure random value.")
        print("Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        print("="*80 + "\n")

    yield


app = FastAPI(title="Unified Media Asset Manager API", lifespan=lifespan)

# Register Phase 1 API routers (World Building)
app.include_router(world_config.router)
app.include_router(entity_traits.router)
app.include_router(timeline.router)
# Register Phase 4 API routers (Provider Integration)
app.include_router(providers.router)

# Ensure DB and media dirs exist at import time for tests that instantiate
# `TestClient(app)` at module import (some test files do this at top-level).
try:
    storage.ensure_dirs()
except Exception:
    pass
try:
    create_db_and_tables()
except Exception:
    pass


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
    return {"message": "Welcome to the Unified Media Asset Manager API"}

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
def get_all_universes(db: Session = Depends(get_db)):
    """Retrieves all Universes."""
    universes = db.query(UniverseDB).options(joinedload(UniverseDB.elements).joinedload(ElementDB.components)).all()
    return [convert_universe_db_to_pydantic(uni) for uni in universes]

@app.get("/universes/{universe_id}", response_model=Universe)
def get_universe(universe_id: str, db: Session = Depends(get_db)):
    """Retrieves a single Universe by its ID."""
    universe = db.query(UniverseDB).options(joinedload(UniverseDB.elements).joinedload(ElementDB.components)).filter(UniverseDB.id == universe_id).first()
    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")
    
    return convert_universe_db_to_pydantic(universe)

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
def get_elements_in_universe(universe_id: str, db: Session = Depends(get_db)):
    """Retrieves all Elements within a specific Universe."""
    universe = db.query(UniverseDB).filter(UniverseDB.id == universe_id).first()
    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")
    
    elements = db.query(ElementDB).options(joinedload(ElementDB.components)).filter(ElementDB.universe_id == universe_id).all()
    return [convert_element_db_to_pydantic(el) for el in elements]

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
            "mood": request.mood,
            "platform": request.platform or "youtube",
            "num_variations": 1
        })

        if not strategy_result.get("success"):
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
            provider="mock",
            status="pending"
        )

        db.add(video_job)
        db.commit()
        db.refresh(video_job)

        # Step 3: Start video generation (async)
        generation_agent = VideoGenerationAgent()
        generation_result = await generation_agent.process({
            "prompt": video_job.prompt,
            "duration": video_job.duration,
            "aspect_ratio": video_job.aspect_ratio
        })

        # Update job with provider info
        if generation_result.get("success"):
            video_job.provider_job_id = generation_result.get("provider_job_id")
            video_job.status = "processing"
            db.commit()

        return {
            "job_id": video_job.id,
            "status": video_job.status,
            "provider_job_id": video_job.provider_job_id,
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
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    """List video generation jobs with optional filtering."""
    query = db.query(VideoJobDB)

    if universe_id:
        query = query.filter(VideoJobDB.universe_id == universe_id)
    if status:
        query = query.filter(VideoJobDB.status == status)

    jobs = query.order_by(VideoJobDB.created_at.desc()).limit(limit).all()

    return {
        "jobs": [
            {
                "id": job.id,
                "universe_id": job.universe_id,
                "generation_type": job.generation_type,
                "prompt": job.prompt,
                "status": job.status,
                "provider": job.provider,
                "mood_category": job.mood_category,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in jobs
        ],
        "total": len(jobs)
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
                    job.output_video_url = result.get("public_url")
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
        "output_video_url": job.output_video_url,
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
            "mood": request.mood,
            "platform": request.platform,
            "num_variations": request.num_variations
        })

        return result

    except Exception as e:
        logger.error(f"Strategy generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    provider: str = "mock"


class AudioAnalyzeRequest(BaseModel):
    audio_url: str
    universe_id: Optional[str] = None
    provider: str = "mock"


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
        agent = AudioAgent(config={"default_provider": request.provider})
        result = await agent.process({
            "task": "tts",
            "text": request.text,
            "voice": request.voice,
            "provider": request.provider
        })

        # Update job
        if result.get("success"):
            audio_job.status = "completed"
            audio_job.output_audio_url = result.get("audio_url")
            audio_job.duration = result.get("duration")
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
        agent = AudioAgent(config={"default_provider": request.provider})
        result = await agent.process({
            "task": "analyze",
            "audio_url": request.audio_url,
            "provider": request.provider
        })

        return result

    except Exception as e:
        logger.error(f"Audio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
