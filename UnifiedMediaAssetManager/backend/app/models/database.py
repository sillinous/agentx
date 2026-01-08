import uuid
from sqlalchemy import Column, String, ForeignKey, Text, JSON, Float, Boolean, DateTime, BigInteger, Integer
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Stores UUID values as strings in the DB and returns python uuid.UUID on load.
    """
    impl = String

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return uuid.UUID(value)
        except Exception:
            return value
    # Allow SQLAlchemy caching for this type where safe
    cache_ok = True


class UniverseDB(Base):
    __tablename__ = "universes"
    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String, index=True, nullable=True)

    elements = relationship("ElementDB", back_populates="universe", cascade="all, delete-orphan")
    world_config = relationship("WorldConfigDB", uselist=False, back_populates="universe", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEventDB", back_populates="universe", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Universe(id='{self.id}', name='{self.name}')>"


class ElementDB(Base):
    __tablename__ = "elements"
    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    universe_id = Column(GUID(), ForeignKey("universes.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    element_type = Column(String, nullable=False, default="Generic")
    entity_subtype = Column(String(50), nullable=True, index=True)  # character, location, item, etc.

    universe = relationship("UniverseDB", back_populates="elements")
    components = relationship("ComponentDB", back_populates="element", cascade="all, delete-orphan")
    traits = relationship("EntityTraitDB", back_populates="element", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Element(id='{self.id}', name='{self.name}', universe_id='{self.universe_id}')>"


class ComponentDB(Base):
    __tablename__ = "components"
    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    element_id = Column(GUID(), ForeignKey("elements.id"), nullable=False)
    type = Column(String, nullable=False) # e.g., "TextComponent", "ImageComponent"
    data = Column(JSON, nullable=False, default={}) # Stores the component-specific data

    element = relationship("ElementDB", back_populates="components")

    def __repr__(self):
        return f"<Component(id='{self.id}', type='{self.type}', element_id='{self.element_id}')>"


class UserDB(Base):
    __tablename__ = "users"
    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    display_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    roles = Column(JSON, default=["viewer"])
    is_active = Column(Boolean, default=True)
    is_test_user = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}')>"


class AgentJobDB(Base):
    """Tracks AI agent jobs for content generation and processing."""
    __tablename__ = "agent_jobs"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    universe_id = Column(GUID(), ForeignKey("universes.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_type = Column(String(50), nullable=False, index=True)  # 'narrative', 'spatial', 'consistency', etc.
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, processing, completed, failed
    input_data = Column(JSON, nullable=False, default={})
    output_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    human_review_required = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    universe = relationship("UniverseDB")

    def __repr__(self):
        return f"<AgentJob(id='{self.id}', agent_type='{self.agent_type}', status='{self.status}')>"


class UserPreferenceDB(Base):
    """Stores user preferences for agent behavior and personalization."""
    __tablename__ = "user_preferences"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    preference_key = Column(String(100), nullable=False, index=True)
    preference_value = Column(JSON, nullable=True)
    weight = Column(Float, nullable=False, default=1.0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserDB")

    def __repr__(self):
        return f"<UserPreference(id='{self.id}', user_id='{self.user_id}', key='{self.preference_key}')>"


class VideoJobDB(Base):
    """Tracks video generation jobs for text-to-video and image-to-video."""
    __tablename__ = "video_jobs"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    universe_id = Column(GUID(), ForeignKey("universes.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_job_id = Column(GUID(), ForeignKey("agent_jobs.id", ondelete="SET NULL"), nullable=True)

    # Request parameters
    generation_type = Column(String(50), nullable=False)  # 'text_to_video', 'image_to_video'
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    reference_image_url = Column(Text, nullable=True)

    # Strategy parameters
    mood_category = Column(String(50), nullable=True)  # 'high_energy', 'luxury_reveal', etc.
    camera_movement = Column(String(100), nullable=True)
    aspect_ratio = Column(String(10), nullable=False, default='16:9')
    duration = Column(Integer, nullable=False, default=5)

    # External API details
    provider = Column(String(50), nullable=True)  # 'kling', 'runway', 'pika', 'mock'
    provider_job_id = Column(String(255), nullable=True)
    provider_status = Column(String(50), nullable=True)

    # Generated content
    video_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    local_path = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)

    # Metadata
    status = Column(String(20), nullable=False, default='pending', index=True)
    error_message = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    universe = relationship("UniverseDB")
    agent_job = relationship("AgentJobDB")

    def __repr__(self):
        return f"<VideoJob(id='{self.id}', type='{self.generation_type}', status='{self.status}')>"


class AudioJobDB(Base):
    """Tracks audio generation and processing jobs."""
    __tablename__ = "audio_jobs"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    universe_id = Column(GUID(), ForeignKey("universes.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_job_id = Column(GUID(), ForeignKey("agent_jobs.id", ondelete="SET NULL"), nullable=True)

    # Request parameters
    generation_type = Column(String(50), nullable=False)  # 'text_to_music', 'text_to_speech', 'transcription'
    prompt = Column(Text, nullable=True)
    audio_input_path = Column(Text, nullable=True)

    # Generation parameters
    duration = Column(Integer, nullable=True)
    voice_id = Column(String(255), nullable=True)
    language = Column(String(10), nullable=True)
    parameters = Column(JSON, nullable=True)

    # External API details
    provider = Column(String(50), nullable=True)  # 'suno', 'elevenlabs', 'whisper', 'mock'
    provider_job_id = Column(String(255), nullable=True)

    # Generated content
    audio_url = Column(Text, nullable=True)
    local_path = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    transcription = Column(JSON, nullable=True)

    # Metadata
    status = Column(String(20), nullable=False, default='pending', index=True)
    error_message = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    universe = relationship("UniverseDB")
    agent_job = relationship("AgentJobDB")

    def __repr__(self):
        return f"<AudioJob(id='{self.id}', type='{self.generation_type}', status='{self.status}')>"


class MediaAssetDB(Base):
    """Stores all media assets (video, audio, images) for a universe."""
    __tablename__ = "media_assets"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    universe_id = Column(GUID(), ForeignKey("universes.id", ondelete="CASCADE"), nullable=True, index=True)
    element_id = Column(GUID(), ForeignKey("elements.id", ondelete="SET NULL"), nullable=True, index=True)

    # Asset details
    asset_type = Column(String(20), nullable=False, index=True)  # 'video', 'audio', 'image'
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # File details
    file_path = Column(Text, nullable=False)
    public_url = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    duration = Column(Float, nullable=True)  # For video/audio (seconds)
    dimensions = Column(JSON, nullable=True)  # {"width": 1920, "height": 1080}

    # Source tracking
    source_job_id = Column(GUID(), nullable=True)
    source_type = Column(String(50), nullable=True)  # 'generated', 'uploaded', 'imported'

    # Metadata
    tags = Column(JSON, nullable=True)  # Store as JSON array for SQLite compatibility
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    universe = relationship("UniverseDB")
    element = relationship("ElementDB")

    def __repr__(self):
        return f"<MediaAsset(id='{self.id}', type='{self.asset_type}', title='{self.title}')>"


class WorldConfigDB(Base):
    """World configuration for a universe (genre, physics, magic system, etc.)"""
    __tablename__ = "world_configs"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    universe_id = Column(GUID(), ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Core Parameters
    genre = Column(String(100), nullable=False)
    physics = Column(String(100), nullable=True)
    magic_system = Column(String(100), nullable=True)
    tech_level = Column(String(100), nullable=True)
    tone = Column(String(100), nullable=True)

    # Extended Configuration
    color_palette = Column(JSON, nullable=True)  # {"primary": "#FF5733", "secondary": "#33FF57"}
    art_style_notes = Column(Text, nullable=True)
    reference_images = Column(JSON, nullable=True)  # Array of image URLs

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    universe = relationship("UniverseDB", back_populates="world_config")

    def __repr__(self):
        return f"<WorldConfig(id='{self.id}', universe_id='{self.universe_id}', genre='{self.genre}')>"


class EntityTraitDB(Base):
    """Type-specific traits for elements (character backstory, location geography, etc.)"""
    __tablename__ = "entity_traits"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    element_id = Column(GUID(), ForeignKey("elements.id", ondelete="CASCADE"), nullable=False, index=True)

    # Trait Definition
    trait_key = Column(String(100), nullable=False)  # 'personality', 'backstory', 'powers'
    trait_value = Column(Text, nullable=True)
    trait_type = Column(String(50), nullable=True)  # 'text', 'number', 'boolean', 'list', 'json'
    trait_category = Column(String(50), nullable=True)  # 'core', 'physical', 'behavioral', 'historical'

    # Display & AI Settings
    display_order = Column(Integer, nullable=False, default=0)
    is_ai_visible = Column(Boolean, nullable=False, default=True)  # Include in AI context?

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    element = relationship("ElementDB", back_populates="traits")

    def __repr__(self):
        return f"<EntityTrait(id='{self.id}', element_id='{self.element_id}', key='{self.trait_key}')>"


class TimelineEventDB(Base):
    """Timeline events with participants for narrative tracking"""
    __tablename__ = "timeline_events"

    id = Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    universe_id = Column(GUID(), ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=True, index=True)  # 'battle', 'discovery', 'meeting'

    # Relationships
    participants = Column(JSON, nullable=True)  # Array of element IDs
    location_id = Column(GUID(), ForeignKey("elements.id", ondelete="SET NULL"), nullable=True)

    # Impact & Consequences
    significance = Column(String(20), nullable=True)  # 'minor', 'major', 'pivotal'
    consequences = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    universe = relationship("UniverseDB", back_populates="timeline_events")
    location = relationship("ElementDB", foreign_keys=[location_id])

    def __repr__(self):
        return f"<TimelineEvent(id='{self.id}', title='{self.title}', timestamp='{self.event_timestamp}')>"
