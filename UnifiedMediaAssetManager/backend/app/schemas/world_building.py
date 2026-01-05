"""
Pydantic schemas for world building features (world config, entity traits, timeline)
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Entity Subtype Constants
ENTITY_SUBTYPES = [
    "character",
    "location",
    "item",
    "faction",
    "event",
    "concept",
    "species",
    "technology"
]


# ============================================================================
# World Configuration Schemas
# ============================================================================

class WorldConfigBase(BaseModel):
    """Base schema for world configuration"""
    genre: str = Field(..., description="Genre of the universe (e.g., Cyberpunk, Fantasy)")
    physics: Optional[str] = Field(None, description="Physics system (Standard, Alternative, Hybrid)")
    magic_system: Optional[str] = Field(None, description="Magic system (None, Traditional, Digital Surrealism)")
    tech_level: Optional[str] = Field(None, description="Tech level (Medieval, Modern, Post-Scarcity)")
    tone: Optional[str] = Field(None, description="Tone (Gritty, Neon, Hopeful, Dark)")
    color_palette: Optional[Dict[str, str]] = Field(None, description="Color palette (hex codes)")
    art_style_notes: Optional[str] = Field(None, description="Free-form art style notes")
    reference_images: Optional[List[str]] = Field(None, description="Array of reference image URLs")


class WorldConfigCreate(WorldConfigBase):
    """Schema for creating world configuration"""
    pass


class WorldConfigUpdate(BaseModel):
    """Schema for updating world configuration (all fields optional)"""
    genre: Optional[str] = None
    physics: Optional[str] = None
    magic_system: Optional[str] = None
    tech_level: Optional[str] = None
    tone: Optional[str] = None
    color_palette: Optional[Dict[str, str]] = None
    art_style_notes: Optional[str] = None
    reference_images: Optional[List[str]] = None


class WorldConfigResponse(WorldConfigBase):
    """Schema for world configuration response"""
    id: UUID
    universe_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Entity Trait Schemas
# ============================================================================

class EntityTraitBase(BaseModel):
    """Base schema for entity trait"""
    trait_key: str = Field(..., max_length=100, description="Trait key (e.g., 'personality', 'backstory')")
    trait_value: Optional[str] = Field(None, description="Trait value")
    trait_type: Optional[str] = Field("text", description="Type: text, number, boolean, list, json")
    trait_category: Optional[str] = Field(None, description="Category: core, physical, behavioral, historical")
    display_order: int = Field(0, description="Display order")
    is_ai_visible: bool = Field(True, description="Include in AI context?")


class EntityTraitCreate(EntityTraitBase):
    """Schema for creating entity trait"""
    pass


class EntityTraitUpdate(BaseModel):
    """Schema for updating entity trait (all fields optional)"""
    trait_key: Optional[str] = Field(None, max_length=100)
    trait_value: Optional[str] = None
    trait_type: Optional[str] = None
    trait_category: Optional[str] = None
    display_order: Optional[int] = None
    is_ai_visible: Optional[bool] = None


class EntityTraitResponse(EntityTraitBase):
    """Schema for entity trait response"""
    id: UUID
    element_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Trait Template Schemas
# ============================================================================

class TraitTemplate(BaseModel):
    """Template for a suggested trait"""
    key: str = Field(..., description="Trait key")
    label: str = Field(..., description="Display label")
    type: str = Field("text", description="Input type")
    category: str = Field("core", description="Trait category")
    description: Optional[str] = Field(None, description="Trait description")
    placeholder: Optional[str] = Field(None, description="Placeholder text")


class TraitTemplatesResponse(BaseModel):
    """Response with trait templates for an entity type"""
    entity_type: str
    templates: List[TraitTemplate]


# ============================================================================
# Timeline Event Schemas
# ============================================================================

class TimelineEventBase(BaseModel):
    """Base schema for timeline event"""
    title: str = Field(..., max_length=255, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    event_timestamp: datetime = Field(..., description="When the event occurred")
    event_type: Optional[str] = Field(None, description="Event type (battle, discovery, meeting)")
    participants: Optional[List[str]] = Field(None, description="Array of participant element IDs (as strings)")
    location_id: Optional[UUID] = Field(None, description="Location element ID")
    significance: Optional[str] = Field(None, description="Significance: minor, major, pivotal")
    consequences: Optional[str] = Field(None, description="Event consequences")


class TimelineEventCreate(TimelineEventBase):
    """Schema for creating timeline event"""
    pass


class TimelineEventUpdate(BaseModel):
    """Schema for updating timeline event (all fields optional)"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    event_timestamp: Optional[datetime] = None
    event_type: Optional[str] = None
    participants: Optional[List[str]] = None
    location_id: Optional[UUID] = None
    significance: Optional[str] = None
    consequences: Optional[str] = None


class TimelineEventResponse(TimelineEventBase):
    """Schema for timeline event response"""
    id: UUID
    universe_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Trait Template Definitions
# ============================================================================

TRAIT_TEMPLATES = {
    "character": [
        TraitTemplate(key="age", label="Age", type="number", category="core", description="Character age"),
        TraitTemplate(key="gender", label="Gender", type="text", category="core", description="Character gender"),
        TraitTemplate(key="role", label="Role", type="text", category="core", description="Character role in story"),
        TraitTemplate(key="appearance", label="Appearance", type="text", category="physical", description="Physical appearance"),
        TraitTemplate(key="personality", label="Personality", type="text", category="behavioral", description="Personality traits"),
        TraitTemplate(key="motivations", label="Motivations", type="text", category="behavioral", description="What drives them"),
        TraitTemplate(key="fears", label="Fears", type="text", category="behavioral", description="What they fear"),
        TraitTemplate(key="backstory", label="Backstory", type="text", category="historical", description="Character backstory"),
        TraitTemplate(key="strengths", label="Strengths", type="text", category="behavioral", description="Character strengths"),
        TraitTemplate(key="weaknesses", label="Weaknesses", type="text", category="behavioral", description="Character weaknesses"),
    ],
    "location": [
        TraitTemplate(key="geography", label="Geography", type="text", category="physical", description="Geographic features"),
        TraitTemplate(key="climate", label="Climate", type="text", category="physical", description="Weather and climate"),
        TraitTemplate(key="population", label="Population", type="number", category="demographic", description="Population size"),
        TraitTemplate(key="culture", label="Culture", type="text", category="demographic", description="Cultural characteristics"),
        TraitTemplate(key="landmarks", label="Landmarks", type="text", category="physical", description="Notable landmarks"),
        TraitTemplate(key="government", label="Government", type="text", category="political", description="Type of government"),
        TraitTemplate(key="resources", label="Resources", type="text", category="economic", description="Natural resources"),
        TraitTemplate(key="history", label="History", type="text", category="historical", description="Location history"),
    ],
    "item": [
        TraitTemplate(key="material", label="Material", type="text", category="physical", description="What it's made of"),
        TraitTemplate(key="size", label="Size", type="text", category="physical", description="Size description"),
        TraitTemplate(key="weight", label="Weight", type="text", category="physical", description="Weight"),
        TraitTemplate(key="purpose", label="Purpose", type="text", category="functional", description="What it's used for"),
        TraitTemplate(key="powers", label="Powers", type="text", category="functional", description="Special abilities"),
        TraitTemplate(key="limitations", label="Limitations", type="text", category="functional", description="Limitations or weaknesses"),
        TraitTemplate(key="creator", label="Creator", type="text", category="historical", description="Who created it"),
        TraitTemplate(key="rarity", label="Rarity", type="text", category="value", description="How rare it is"),
    ],
    "faction": [
        TraitTemplate(key="structure", label="Structure", type="text", category="organizational", description="Organizational structure"),
        TraitTemplate(key="size", label="Size", type="number", category="organizational", description="Number of members"),
        TraitTemplate(key="goals", label="Goals", type="text", category="ideological", description="Faction goals"),
        TraitTemplate(key="beliefs", label="Beliefs", type="text", category="ideological", description="Core beliefs"),
        TraitTemplate(key="methods", label="Methods", type="text", category="ideological", description="How they operate"),
        TraitTemplate(key="key_members", label="Key Members", type="text", category="membership", description="Important members"),
        TraitTemplate(key="assets", label="Assets", type="text", category="resources", description="Resources and assets"),
        TraitTemplate(key="territory", label="Territory", type="text", category="resources", description="Controlled territory"),
    ],
    "event": [
        TraitTemplate(key="causes", label="Causes", type="text", category="historical", description="What caused the event"),
        TraitTemplate(key="consequences", label="Consequences", type="text", category="historical", description="Results of the event"),
        TraitTemplate(key="participants", label="Participants", type="text", category="involvement", description="Who was involved"),
        TraitTemplate(key="location", label="Location", type="text", category="physical", description="Where it happened"),
        TraitTemplate(key="duration", label="Duration", type="text", category="temporal", description="How long it lasted"),
        TraitTemplate(key="significance", label="Significance", type="text", category="impact", description="Historical significance"),
    ],
    "concept": [
        TraitTemplate(key="philosophy", label="Philosophy", type="text", category="ideological", description="Core philosophy"),
        TraitTemplate(key="principles", label="Principles", type="text", category="ideological", description="Key principles"),
        TraitTemplate(key="implications", label="Implications", type="text", category="impact", description="Implications"),
        TraitTemplate(key="adherents", label="Adherents", type="text", category="social", description="Who believes in it"),
        TraitTemplate(key="opposition", label="Opposition", type="text", category="social", description="Who opposes it"),
        TraitTemplate(key="origin", label="Origin", type="text", category="historical", description="Where it came from"),
    ],
    "species": [
        TraitTemplate(key="biology", label="Biology", type="text", category="physical", description="Biological characteristics"),
        TraitTemplate(key="lifespan", label="Lifespan", type="text", category="physical", description="Typical lifespan"),
        TraitTemplate(key="culture", label="Culture", type="text", category="social", description="Cultural traits"),
        TraitTemplate(key="abilities", label="Abilities", type="text", category="functional", description="Special abilities"),
        TraitTemplate(key="weaknesses", label="Weaknesses", type="text", category="functional", description="Vulnerabilities"),
        TraitTemplate(key="origin", label="Origin", type="text", category="historical", description="Species origin"),
        TraitTemplate(key="habitat", label="Habitat", type="text", category="physical", description="Natural habitat"),
    ],
    "technology": [
        TraitTemplate(key="function", label="Function", type="text", category="functional", description="What it does"),
        TraitTemplate(key="mechanisms", label="Mechanisms", type="text", category="functional", description="How it works"),
        TraitTemplate(key="limitations", label="Limitations", type="text", category="functional", description="Technical limitations"),
        TraitTemplate(key="inventors", label="Inventors", type="text", category="historical", description="Who created it"),
        TraitTemplate(key="impact", label="Impact", type="text", category="social", description="Impact on society"),
        TraitTemplate(key="requirements", label="Requirements", type="text", category="functional", description="What's needed to use it"),
        TraitTemplate(key="availability", label="Availability", type="text", category="economic", description="How available it is"),
    ],
}
