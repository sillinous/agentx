# Phase 1: Story Design & Worldbuilding - Implementation Plan

**Status**: 🚀 **READY TO START**
**Start Date**: January 4, 2026
**Estimated Duration**: 1-2 weeks
**Phase**: 1 of 6
**Dependencies**: Phase 2 (Agent Infrastructure), Phase 3 (Media Generation)

---

## Executive Summary

Phase 1 builds the foundational story design and worldbuilding features that enable content creators to define rich, consistent story universes. This phase provides the structural framework that AI agents will use to generate contextually appropriate media in later phases.

### Key Objectives

1. **World Configuration**: Define universe parameters (genre, physics, magic, tech level, tone)
2. **Extended Entity Types**: Support 8 specialized entity types with type-specific traits
3. **Timeline Management**: Create chronological event tracking with participants
4. **Style Guide System**: Define visual consistency guidelines for AI generation

---

## Architecture Overview

### Data Flow
```
User → World Config Form → Backend API → Database → AI Agent Context
         ↓
    Entity Creation → Traits & Relationships → Timeline Events
         ↓
    Style Guide → Image/Video Generation Parameters
```

### Component Structure
```
Frontend (Next.js 16 / React 19)
├── WorldConfigEditor.tsx      # Genre, physics, magic, etc.
├── EntityTypeSelector.tsx     # 8 entity types
├── EntityTraitEditor.tsx      # Type-specific traits
├── TimelineViewer.tsx         # Chronological event display
└── StyleGuideEditor.tsx       # Visual consistency rules

Backend (FastAPI / Python 3.11+)
├── models/
│   ├── world_config.py        # WorldConfigDB
│   ├── entity_traits.py       # EntityTraitDB
│   └── timeline.py            # TimelineEventDB
├── api/
│   ├── world_config.py        # CRUD endpoints
│   ├── entity_traits.py       # Trait management
│   └── timeline.py            # Event management
└── services/
    └── context_builder.py     # Build AI context from world config
```

---

## Database Schema

### 1. World Configuration Table

```sql
CREATE TABLE world_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID UNIQUE REFERENCES universes(id) ON DELETE CASCADE,

    -- Core Parameters
    genre VARCHAR(100) NOT NULL,              -- 'Cyberpunk', 'Fantasy', 'Sci-Fi', etc.
    physics VARCHAR(100),                     -- 'Standard', 'Alternative', 'Hybrid'
    magic_system VARCHAR(100),                -- 'None', 'Traditional', 'Digital Surrealism'
    tech_level VARCHAR(100),                  -- 'Medieval', 'Modern', 'Post-Scarcity'
    tone VARCHAR(100),                        -- 'Gritty', 'Neon', 'Hopeful', 'Dark'

    -- Extended Configuration
    color_palette JSON,                       -- {"primary": "#FF5733", "secondary": "#33FF57"}
    art_style_notes TEXT,                     -- Free-form style notes
    reference_images JSON,                    -- Array of image URLs

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_world_configs_universe (universe_id)
);
```

### 2. Entity Traits Table

```sql
CREATE TABLE entity_traits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID REFERENCES elements(id) ON DELETE CASCADE,

    -- Trait Definition
    trait_key VARCHAR(100) NOT NULL,          -- 'personality', 'backstory', 'powers'
    trait_value TEXT,                         -- Actual value
    trait_type VARCHAR(50),                   -- 'text', 'number', 'boolean', 'list', 'json'
    trait_category VARCHAR(50),               -- 'core', 'physical', 'behavioral', 'historical'

    -- Metadata
    display_order INTEGER DEFAULT 0,
    is_ai_visible BOOLEAN DEFAULT true,       -- Include in AI context?
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_entity_traits_element (element_id),
    INDEX idx_entity_traits_key (element_id, trait_key),
    UNIQUE (element_id, trait_key)
);
```

### 3. Timeline Events Table

```sql
CREATE TABLE timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID REFERENCES universes(id) ON DELETE CASCADE,

    -- Event Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(50),                   -- 'battle', 'discovery', 'meeting'

    -- Relationships
    participants JSON,                        -- Array of element IDs
    location_id UUID REFERENCES elements(id) ON DELETE SET NULL,

    -- Impact & Consequences
    significance VARCHAR(20),                 -- 'minor', 'major', 'pivotal'
    consequences TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_timeline_universe (universe_id),
    INDEX idx_timeline_timestamp (event_timestamp),
    INDEX idx_timeline_type (event_type)
);
```

### 4. Update Elements Table

```sql
ALTER TABLE elements
ADD COLUMN entity_subtype VARCHAR(50) CHECK (
    entity_subtype IN ('character', 'location', 'item', 'faction',
                       'event', 'concept', 'species', 'technology')
);

CREATE INDEX idx_elements_subtype ON elements(entity_subtype);
```

---

## Implementation Tasks

### Task 1: Database Migrations ✅

**File**: `backend/alembic/versions/[timestamp]_add_world_building_schema.py`

**Actions**:
- Create `world_configs` table
- Create `entity_traits` table
- Create `timeline_events` table
- Add `entity_subtype` column to `elements`
- Create all indexes

**Dependencies**: None
**Estimated Time**: 1 hour

---

### Task 2: Database Models

**File**: `backend/app/models/database.py`

**Models to Add**:
```python
class WorldConfigDB(Base):
    __tablename__ = "world_configs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    universe_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("universes.id"))
    genre: Mapped[str] = mapped_column(String(100))
    physics: Mapped[Optional[str]] = mapped_column(String(100))
    magic_system: Mapped[Optional[str]] = mapped_column(String(100))
    tech_level: Mapped[Optional[str]] = mapped_column(String(100))
    tone: Mapped[Optional[str]] = mapped_column(String(100))
    color_palette: Mapped[Optional[dict]] = mapped_column(JSON)
    art_style_notes: Mapped[Optional[str]] = mapped_column(Text)
    reference_images: Mapped[Optional[list]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    universe: Mapped["UniverseDB"] = relationship(back_populates="world_config")

class EntityTraitDB(Base):
    __tablename__ = "entity_traits"
    # ... (similar structure)

class TimelineEventDB(Base):
    __tablename__ = "timeline_events"
    # ... (similar structure)
```

**Dependencies**: Task 1
**Estimated Time**: 2 hours

---

### Task 3: Pydantic Schemas

**File**: `backend/app/schemas/world_building.py`

**Schemas**:
```python
class WorldConfigCreate(BaseModel):
    universe_id: UUID
    genre: str
    physics: Optional[str] = None
    magic_system: Optional[str] = None
    tech_level: Optional[str] = None
    tone: Optional[str] = None
    color_palette: Optional[Dict[str, str]] = None
    art_style_notes: Optional[str] = None
    reference_images: Optional[List[str]] = None

class WorldConfigResponse(BaseModel):
    id: UUID
    universe_id: UUID
    genre: str
    physics: Optional[str]
    # ... all fields
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Similar for EntityTrait, TimelineEvent
```

**Dependencies**: Task 2
**Estimated Time**: 1.5 hours

---

### Task 4: API Endpoints - World Configuration

**File**: `backend/app/api/world_config.py`

**Endpoints**:
```python
@router.post("/api/universes/{universe_id}/world-config")
async def create_world_config(
    universe_id: UUID,
    config: WorldConfigCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
) -> WorldConfigResponse:
    """Create world configuration for a universe"""

@router.get("/api/universes/{universe_id}/world-config")
async def get_world_config(
    universe_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
) -> WorldConfigResponse:
    """Get world configuration"""

@router.put("/api/universes/{universe_id}/world-config")
async def update_world_config(
    universe_id: UUID,
    config: WorldConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
) -> WorldConfigResponse:
    """Update world configuration"""
```

**Dependencies**: Task 3
**Estimated Time**: 2 hours

---

### Task 5: API Endpoints - Entity Traits

**File**: `backend/app/api/entity_traits.py`

**Endpoints**:
```python
@router.get("/api/entity-types/{entity_type}/traits")
async def get_trait_templates(entity_type: str) -> List[TraitTemplate]:
    """Get suggested traits for an entity type"""
    # Returns predefined trait templates for each type

@router.post("/api/elements/{element_id}/traits")
async def add_trait(
    element_id: UUID,
    trait: EntityTraitCreate,
    db: Session = Depends(get_db)
) -> EntityTraitResponse:
    """Add a trait to an element"""

@router.put("/api/elements/{element_id}/traits/{trait_id}")
async def update_trait(...) -> EntityTraitResponse:
    """Update a trait"""

@router.delete("/api/elements/{element_id}/traits/{trait_id}")
async def delete_trait(...) -> Dict[str, str]:
    """Delete a trait"""
```

**Dependencies**: Task 3
**Estimated Time**: 2.5 hours

---

### Task 6: API Endpoints - Timeline

**File**: `backend/app/api/timeline.py`

**Endpoints**:
```python
@router.post("/api/universes/{universe_id}/timeline")
async def create_event(
    universe_id: UUID,
    event: TimelineEventCreate,
    db: Session = Depends(get_db)
) -> TimelineEventResponse:
    """Create a timeline event"""

@router.get("/api/universes/{universe_id}/timeline")
async def list_events(
    universe_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[TimelineEventResponse]:
    """List timeline events (chronologically sorted)"""

@router.put("/api/timeline/{event_id}")
async def update_event(...) -> TimelineEventResponse:
    """Update a timeline event"""

@router.delete("/api/timeline/{event_id}")
async def delete_event(...) -> Dict[str, str]:
    """Delete a timeline event"""
```

**Dependencies**: Task 3
**Estimated Time**: 2 hours

---

### Task 7: Context Builder Service

**File**: `backend/app/services/context_builder.py`

**Purpose**: Build rich AI context from world configuration

```python
class ContextBuilder:
    """Builds AI context from universe world configuration"""

    def build_world_context(self, universe_id: UUID, db: Session) -> Dict[str, Any]:
        """
        Gathers all world-building information for AI context

        Returns:
        {
            "world_config": {...},
            "key_entities": [...],
            "timeline_summary": [...],
            "style_guide": {...}
        }
        """
        world_config = self._get_world_config(universe_id, db)
        entities = self._get_key_entities(universe_id, db)
        timeline = self._get_timeline_context(universe_id, db)

        return {
            "genre": world_config.genre,
            "tone": world_config.tone,
            "physics": world_config.physics,
            "magic_system": world_config.magic_system,
            "tech_level": world_config.tech_level,
            "key_entities": [self._format_entity(e) for e in entities],
            "timeline_summary": timeline,
            "visual_style": {
                "art_style": world_config.art_style_notes,
                "color_palette": world_config.color_palette
            }
        }

    def _format_entity(self, entity: ElementDB) -> Dict[str, Any]:
        """Format entity with traits for AI context"""
        traits = {t.trait_key: t.trait_value for t in entity.traits if t.is_ai_visible}
        return {
            "type": entity.entity_subtype,
            "name": entity.name,
            "traits": traits,
            "description": entity.description
        }
```

**Dependencies**: Task 2
**Estimated Time**: 3 hours

---

### Task 8: Frontend - World Config Editor

**File**: `frontend/src/components/WorldConfigEditor.tsx`

**Component**:
```tsx
export function WorldConfigEditor({ universeId }: { universeId: string }) {
  const [config, setConfig] = useState<WorldConfig | null>(null);

  const genreOptions = [
    'Cyberpunk', 'Fantasy', 'Sci-Fi', 'Historical', 'Horror',
    'Mystery', 'Romance', 'Western', 'Post-Apocalyptic'
  ];

  const physicsOptions = ['Standard', 'Alternative', 'Hybrid', 'Variable'];
  const magicOptions = ['None', 'Traditional', 'Digital Surrealism', 'Elemental', 'Cosmic'];
  const techOptions = ['Stone Age', 'Medieval', 'Industrial', 'Modern', 'Post-Scarcity', 'Transcendent'];
  const toneOptions = ['Gritty', 'Neon', 'Melancholy', 'Hopeful', 'Dark', 'Whimsical'];

  return (
    <div className="world-config-editor">
      <h2>World Configuration</h2>
      <SelectField label="Genre" options={genreOptions} value={config?.genre} />
      <SelectField label="Physics" options={physicsOptions} value={config?.physics} />
      <SelectField label="Magic System" options={magicOptions} value={config?.magic_system} />
      <SelectField label="Tech Level" options={techOptions} value={config?.tech_level} />
      <SelectField label="Tone" options={toneOptions} value={config?.tone} />

      <ColorPaletteEditor palette={config?.color_palette} />
      <TextArea label="Art Style Notes" value={config?.art_style_notes} />

      <Button onClick={handleSave}>Save Configuration</Button>
    </div>
  );
}
```

**Dependencies**: Task 4
**Estimated Time**: 4 hours

---

### Task 9: Frontend - Entity Trait Editor

**File**: `frontend/src/components/EntityTraitEditor.tsx`

**Features**:
- Load trait templates based on entity type
- Add/edit/delete traits
- Type-specific trait inputs (text, number, boolean, list)
- Drag-and-drop trait reordering

**Dependencies**: Task 5
**Estimated Time**: 5 hours

---

### Task 10: Frontend - Timeline Viewer

**File**: `frontend/src/components/TimelineViewer.tsx`

**Features**:
- Chronological event display
- Expandable event details
- Add/edit/delete events
- Participant entity links
- Date range filtering

**Dependencies**: Task 6
**Estimated Time**: 6 hours

---

## Entity Type Trait Templates

### Character Traits
```json
{
  "core": ["name", "age", "gender", "role"],
  "physical": ["appearance", "height", "build", "distinctive_features"],
  "behavioral": ["personality", "motivations", "fears", "strengths", "weaknesses"],
  "historical": ["backstory", "origin", "key_events"],
  "relationships": ["allies", "enemies", "family"]
}
```

### Location Traits
```json
{
  "geographic": ["climate", "terrain", "size", "coordinates"],
  "demographic": ["population", "culture", "language"],
  "political": ["government", "laws", "conflicts"],
  "economic": ["resources", "trade", "wealth_level"],
  "landmarks": ["notable_places", "architecture", "secrets"]
}
```

### Item Traits
```json
{
  "physical": ["material", "size", "weight", "appearance"],
  "functional": ["purpose", "powers", "limitations", "usage"],
  "historical": ["creator", "origin_date", "history"],
  "value": ["rarity", "significance", "monetary_value"]
}
```

### Faction Traits
```json
{
  "organizational": ["structure", "hierarchy", "size"],
  "ideological": ["goals", "beliefs", "methods"],
  "membership": ["key_members", "recruitment", "initiation"],
  "resources": ["assets", "territory", "allies", "enemies"],
  "history": ["founding", "major_events", "current_status"]
}
```

(Similar templates for Event, Concept, Species, Technology)

---

## Integration with Existing Systems

### 1. AI Agents Use World Context
All AI agents (NarrativeAgent, ImageAgent, VideoStrategyAgent) will receive world context:

```python
# In agent processing
world_context = context_builder.build_world_context(universe_id, db)
prompt = f"""
You are generating content for a {world_context['genre']} universe with:
- Tone: {world_context['tone']}
- Tech Level: {world_context['tech_level']}
- Magic System: {world_context['magic_system']}

Key Entities:
{format_entities(world_context['key_entities'])}

User Request: {user_prompt}

Generate content that is consistent with this world.
"""
```

### 2. Entity Subtypes in UI
When creating an element, users select subtype which determines:
- Available trait templates
- UI form fields
- Default components

### 3. Timeline Integration with Events
Timeline events can link to:
- Character entities (participants)
- Location entities (where it happened)
- Item entities (artifacts involved)
- Faction entities (organizations participating)

---

## Testing Strategy

### Unit Tests
- World config CRUD operations
- Entity trait validation
- Timeline event sorting
- Context builder accuracy

### Integration Tests
- End-to-end world creation flow
- AI agent context usage
- Frontend-backend data flow

### Manual Tests
- Create complete universe with all 8 entity types
- Build timeline with interconnected events
- Verify AI generation uses world context

---

## Success Criteria

### Phase 1.1: Foundation (Days 1-3)
- ✅ Database schema created
- ✅ Backend models and endpoints functional
- ✅ Basic CRUD operations working
- ✅ Unit tests passing

### Phase 1.2: UI Implementation (Days 4-7)
- ✅ World config editor functional
- ✅ Entity trait editor supports all 8 types
- ✅ Timeline viewer displays events
- ✅ Frontend integration complete

### Phase 1.3: AI Integration (Days 8-10)
- ✅ Context builder provides rich world data
- ✅ AI agents use world context in prompts
- ✅ Generated content respects world rules
- ✅ End-to-end testing complete

---

## Risk Mitigation

### Risk 1: Complex Entity Type System
**Mitigation**: Start with 3 core types (Character, Location, Item), expand incrementally

### Risk 2: UI Complexity
**Mitigation**: Use reusable components, progressive disclosure for advanced features

### Risk 3: AI Context Size
**Mitigation**: Implement context summarization, prioritize relevant entities

---

## Dependencies

- **Phase 2**: Agent infrastructure (complete)
- **Phase 3**: Video/audio generation (complete)
- **External**: None

---

## Next Phase Preview

**Phase 2: Advanced Media Features**
- 3D model viewer integration
- Advanced image editing tools
- Real-time collaboration features
- Version control for assets

---

## Appendices

### A. Entity Subtype Constants
```python
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
```

### B. API Endpoint Summary
```
POST   /api/universes/{id}/world-config
GET    /api/universes/{id}/world-config
PUT    /api/universes/{id}/world-config

GET    /api/entity-types/{type}/traits
POST   /api/elements/{id}/traits
PUT    /api/elements/{id}/traits/{trait_id}
DELETE /api/elements/{id}/traits/{trait_id}

POST   /api/universes/{id}/timeline
GET    /api/universes/{id}/timeline
PUT    /api/timeline/{id}
DELETE /api/timeline/{id}
GET    /api/timeline/{id}/participants
```

---

**Phase 1 Status**: Ready to begin implementation
**First Task**: Create database migration for world-building schema
**Blockers**: None
**Questions**: None
