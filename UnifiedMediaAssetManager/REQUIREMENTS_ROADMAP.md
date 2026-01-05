# UnifiedMediaAssetManager - Integration Requirements Roadmap
## Comprehensive Requirements for Feature Parity with Source Repositories

**Document Version:** 1.0
**Created:** 2026-01-03
**Status:** Planning
**Target Completion:** Q2 2026

---

## Document Purpose

This document provides a comprehensive, actionable roadmap for integrating all media-related functionality from source repositories into UnifiedMediaAssetManager (UMAM). Each requirement is traceable to source repositories and includes implementation guidance.

---

## Table of Contents

1. [Story Design & Worldbuilding Requirements](#1-story-design--worldbuilding-requirements)
2. [Agent System Requirements](#2-agent-system-requirements)
3. [Video Generation Requirements](#3-video-generation-requirements)
4. [Audio Processing Requirements](#4-audio-processing-requirements)
5. [Image Generation & Editing Requirements](#5-image-generation--editing-requirements)
6. [Production Workflow Requirements](#6-production-workflow-requirements)
7. [Infrastructure Requirements](#7-infrastructure-requirements)
8. [Security & Authentication Requirements](#8-security--authentication-requirements)
9. [Testing Requirements](#9-testing-requirements)
10. [Documentation Requirements](#10-documentation-requirements)

---

## 1. Story Design & Worldbuilding Requirements

### REQ-SD-001: World Configuration System
**Priority:** HIGH
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need to define the fundamental parameters of my story world (genre, physics, magic, tech level, tone) so that AI agents can generate consistent content.

**Acceptance Criteria:**
- [ ] User can select genre from predefined list (Cyberpunk, Fantasy, Sci-Fi, Historical, etc.)
- [ ] User can define physics system (Standard, Alternative, Hybrid)
- [ ] User can configure magic system (None, Traditional, Digital Surrealism, Elemental, etc.)
- [ ] User can set tech level (Stone Age, Medieval, Modern, Post-Scarcity, etc.)
- [ ] User can choose tone (Gritty, Neon, Melancholy, Hopeful, Dark, etc.)
- [ ] Configuration is stored per universe in database
- [ ] Configuration is retrievable by AI agents for context
- [ ] Frontend UI provides intuitive dropdowns/selectors

**Technical Implementation:**
```sql
CREATE TABLE world_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID UNIQUE REFERENCES universes(id) ON DELETE CASCADE,
    genre VARCHAR(100) NOT NULL,
    physics VARCHAR(100),
    magic_system VARCHAR(100),
    tech_level VARCHAR(100),
    tone VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**
- `POST /api/universes/{id}/world-config` - Create configuration
- `GET /api/universes/{id}/world-config` - Retrieve configuration
- `PUT /api/universes/{id}/world-config` - Update configuration

**Reference Files:**
- StoryBiblePortfolioApp: `/frontend/src/types.ts` (TypeScript definitions)
- StoryBiblePortfolioApp: `/frontend/src/components/StoryBibleEditor.tsx` (UI component)

---

### REQ-SD-002: Extended Entity Type System
**Priority:** HIGH
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need 8 specialized entity types (Character, Location, Item, Faction, Event, Concept, Species, Technology) with type-specific traits so I can organize my story world effectively.

**Acceptance Criteria:**
- [ ] System supports 8 entity types with distinct schemas
- [ ] Each entity type has specialized trait templates
- [ ] Traits are customizable per entity instance
- [ ] Entity type determines available trait suggestions
- [ ] Frontend displays appropriate forms based on entity type
- [ ] Database enforces entity type constraints

**Entity Types:**
1. **Character** - Traits: personality, backstory, relationships, motivations
2. **Location** - Traits: geography, climate, population, landmarks
3. **Item** - Traits: properties, history, powers, materials
4. **Faction** - Traits: goals, structure, members, resources
5. **Event** - Traits: causes, consequences, participants, timeline
6. **Concept** - Traits: philosophy, implications, adherents
7. **Species** - Traits: biology, culture, abilities, origins
8. **Technology** - Traits: function, limitations, inventors, impact

**Technical Implementation:**
```sql
ALTER TABLE elements
ADD COLUMN entity_subtype VARCHAR(50) CHECK (
    entity_subtype IN ('character', 'location', 'item', 'faction',
                       'event', 'concept', 'species', 'technology')
);

CREATE TABLE entity_traits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    element_id UUID REFERENCES elements(id) ON DELETE CASCADE,
    trait_key VARCHAR(100) NOT NULL,
    trait_value TEXT,
    trait_type VARCHAR(50),  -- 'text', 'number', 'boolean', 'list'
    created_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**
- `GET /api/entity-types/{type}/traits` - Get trait templates
- `POST /api/elements/{id}/traits` - Add trait
- `PUT /api/elements/{id}/traits/{trait_id}` - Update trait
- `DELETE /api/elements/{id}/traits/{trait_id}` - Remove trait

**Reference Files:**
- StoryBiblePortfolioApp: `/frontend/src/types.ts` (AbstractEntity, EntityInstance types)
- StoryBiblePortfolioApp: `/frontend/src/components/EntityEditor.tsx`

---

### REQ-SD-003: Timeline Event Management
**Priority:** MEDIUM
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need to create a chronological timeline of events with participants so I can track narrative progression and maintain story consistency.

**Acceptance Criteria:**
- [ ] User can create timeline events with title, description, timestamp
- [ ] Events can be associated with participant entities
- [ ] Events are automatically sorted chronologically
- [ ] Timeline is visualized on frontend
- [ ] Events can be filtered by date range
- [ ] Events can be linked to specific story elements

**Technical Implementation:**
```sql
CREATE TABLE timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID REFERENCES universes(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_timestamp TIMESTAMP,
    participants JSONB,  -- Array of element IDs: ["uuid1", "uuid2"]
    event_type VARCHAR(50),  -- 'battle', 'discovery', 'meeting', etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_timeline_universe ON timeline_events(universe_id);
CREATE INDEX idx_timeline_timestamp ON timeline_events(event_timestamp);
```

**API Endpoints:**
- `POST /api/universes/{id}/timeline` - Create event
- `GET /api/universes/{id}/timeline` - List events (sorted chronologically)
- `PUT /api/timeline/{id}` - Update event
- `DELETE /api/timeline/{id}` - Delete event
- `GET /api/timeline/{id}/participants` - Get participant details

**Frontend Component:**
```tsx
// TimelineView.tsx - Visual timeline with draggable events
interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  timestamp: Date;
  participants: string[];  // Element IDs
}
```

**Reference Files:**
- StoryBiblePortfolioApp: `/frontend/src/types.ts` (TimelineEvent type)
- StoryBiblePortfolioApp: `/frontend/src/components/StoryBibleEditor.tsx`

---

### REQ-SD-004: Style Guide System
**Priority:** LOW
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need to define visual style guidelines (art style, color palette, mood, lighting) so that generated media maintains consistent aesthetics.

**Acceptance Criteria:**
- [ ] User can define art style preferences
- [ ] User can specify color palette (hex codes + names)
- [ ] User can set mood descriptors
- [ ] User can configure lighting preferences
- [ ] User can attach reference images
- [ ] Style guide is used by image/video generation agents

**Technical Implementation:**
```sql
CREATE TABLE style_guides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID UNIQUE REFERENCES universes(id) ON DELETE CASCADE,
    art_style VARCHAR(255),
    color_palette JSONB,  -- [{"name": "Primary", "hex": "#FF5733"}, ...]
    mood VARCHAR(255),
    lighting VARCHAR(255),
    reference_images JSONB,  -- Array of image URLs
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**
- `POST /api/universes/{id}/style-guide` - Create style guide
- `GET /api/universes/{id}/style-guide` - Retrieve style guide
- `PUT /api/universes/{id}/style-guide` - Update style guide

---

### REQ-SD-005: 3D Model Viewer
**Priority:** MEDIUM
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need to preview 3D models (GLTF format) within the application with interactive controls so I can visualize story assets.

**Acceptance Criteria:**
- [ ] React Three Fiber integration
- [ ] GLTF/GLB format support
- [ ] Orbit controls (rotate, zoom, pan)
- [ ] Auto-rotation toggle
- [ ] Stage lighting
- [ ] Loading state with suspense fallback
- [ ] Responsive canvas sizing

**Technical Implementation:**
```bash
# Frontend dependencies
npm install three @react-three/fiber @react-three/drei
```

**Frontend Component:**
```tsx
// ModelViewer.tsx
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage } from '@react-three/drei';
import { useGLTF } from '@react-three/drei';

export function ModelViewer({ url }: { url: string }) {
  return (
    <Canvas>
      <Suspense fallback={<Loader />}>
        <Stage environment="city" intensity={0.6}>
          <Model url={url} />
        </Stage>
        <OrbitControls autoRotate />
      </Suspense>
    </Canvas>
  );
}
```

**Reference Files:**
- StoryBiblePortfolioApp: `/frontend/src/components/ModelViewer.tsx`

---

## 2. Agent System Requirements

### REQ-AG-001: Multi-Agent Infrastructure
**Priority:** CRITICAL
**Sources:** StoryBiblePortfolioApp, synapse-core, cinematic-stream
**User Story:** As a system, I need a robust multi-agent orchestration framework to manage asynchronous AI-powered tasks with job tracking, status updates, and result persistence.

**Acceptance Criteria:**
- [ ] Celery + Redis integration for task queue
- [ ] Agent base class with standard interface
- [ ] Job status tracking (pending, processing, completed, failed)
- [ ] Confidence scoring for all agent outputs
- [ ] Human review flagging for low-confidence results
- [ ] Thread-based conversation management
- [ ] Result persistence in database
- [ ] Real-time status polling

**Technical Implementation:**
```python
# backend/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, agent_id: str, user_id: str):
        self.agent_id = agent_id
        self.user_id = user_id
        self.llm = self._init_llm()

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent task and return result"""
        pass

    def _calculate_confidence(self, result: Any) -> float:
        """Calculate confidence score (0.0-1.0)"""
        # Override in subclasses
        return 0.9

    async def execute_job(self, job_id: str, input_data: Dict[str, Any]):
        """Execute job with tracking"""
        # Update status to 'processing'
        # Call process()
        # Calculate confidence
        # Store result
        # Update status to 'completed'
        pass
```

**Database Schema:**
```sql
CREATE TABLE agent_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID REFERENCES universes(id),
    agent_type VARCHAR(50) NOT NULL,  -- 'narrative', 'spatial', 'consistency', etc.
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    input_data JSONB NOT NULL,
    output_data JSONB,
    confidence_score FLOAT,
    human_review_required BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_agent_jobs_universe ON agent_jobs(universe_id);
CREATE INDEX idx_agent_jobs_status ON agent_jobs(status);
CREATE INDEX idx_agent_jobs_type ON agent_jobs(agent_type);
```

**Celery Tasks:**
```python
# backend/tasks/agent_tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def process_agent_job(self, job_id: str):
    """Process agent job asynchronously"""
    try:
        # Retrieve job from database
        # Instantiate appropriate agent
        # Execute agent.execute_job()
        # Handle errors and retries
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

**API Endpoints:**
- `POST /api/agents/jobs` - Create new agent job
- `GET /api/agents/jobs` - List jobs with filters
- `GET /api/agents/jobs/{id}` - Get job status and result
- `POST /api/agents/jobs/{id}/retry` - Retry failed job
- `POST /api/agents/jobs/{id}/approve` - Approve job pending review

**Reference Files:**
- StoryBiblePortfolioApp: `/backend/src/agents.js`
- synapse-core: `/packages/marketing-agent/scribe.py`
- cinematic-stream: `/backend/src/agents.py`

---

### REQ-AG-002: Narrative Generation Agent
**Priority:** CRITICAL
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need an AI agent that generates compelling narrative scenes based on my story context so I can accelerate content creation.

**Acceptance Criteria:**
- [ ] Accepts prompt + world context + character info
- [ ] Generates narrative text (300-1000 words)
- [ ] Maintains consistency with world configuration
- [ ] Outputs structured JSON with scene details
- [ ] Uses Claude 3 Haiku (fast, cost-effective)
- [ ] Confidence scoring based on context adherence
- [ ] Handles both narrative text and video prompt requests

**Technical Implementation:**
```python
# backend/agents/narrative_agent.py
from .base_agent import BaseAgent
from anthropic import Anthropic

class NarrativeAgent(BaseAgent):
    """Generates narrative scenes and video prompts"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = input_data.get('prompt')
        world_config = input_data.get('world_config')
        characters = input_data.get('characters', [])
        request_type = input_data.get('type', 'narrative')  # or 'video_prompt'

        # Build context from world config
        context = self._build_context(world_config, characters)

        # Generate content with Claude
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"{context}\n\nGenerate: {prompt}"
            }]
        )

        return {
            "type": request_type,
            "content": response.content[0].text,
            "model": "claude-3-haiku",
            "tokens_used": response.usage.total_tokens
        }
```

**API Endpoints:**
- `POST /api/agents/narrative/generate` - Generate narrative scene

**Reference Files:**
- StoryBiblePortfolioApp: `/backend/src/agents.js` (NarrativeAgent class)

---

### REQ-AG-003: Spatial/Location Agent
**Priority:** HIGH
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need an AI agent that generates detailed location descriptions and environmental designs so I can build rich story worlds.

**Acceptance Criteria:**
- [ ] Generates location descriptions (geography, landmarks, atmosphere)
- [ ] Creates map-worthy environmental specifications
- [ ] Maintains world configuration consistency
- [ ] Outputs structured location data
- [ ] Uses Claude 3 Haiku

**Technical Implementation:**
```python
# backend/agents/spatial_agent.py
class SpatialAgent(BaseAgent):
    """Generates location and environment descriptions"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        location_name = input_data.get('location_name')
        world_config = input_data.get('world_config')
        location_type = input_data.get('type', 'city')  # city, wilderness, structure

        # Generate with Claude
        # Return structured location data
        return {
            "location_name": location_name,
            "description": "...",
            "landmarks": [],
            "atmosphere": "...",
            "map_layout": "..."
        }
```

---

### REQ-AG-004: Consistency Validator Agent
**Priority:** HIGH
**Source:** StoryBiblePortfolioApp
**User Story:** As a story designer, I need an AI agent that validates generated content against my world rules to prevent inconsistencies.

**Acceptance Criteria:**
- [ ] Checks content against world configuration
- [ ] Validates genre consistency
- [ ] Validates tone adherence
- [ ] Validates tech level appropriateness
- [ ] Validates magic/physics rule compliance
- [ ] Returns "Consistent" or "Inconsistent" with explanations
- [ ] Flags violations for review

**Technical Implementation:**
```python
# backend/agents/consistency_agent.py
class ConsistencyAgent(BaseAgent):
    """Validates content consistency with world rules"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        content = input_data.get('content')
        world_config = input_data.get('world_config')

        # Analyze content for rule violations
        # Return validation result
        return {
            "is_consistent": True/False,
            "violations": [],
            "explanation": "...",
            "confidence": 0.95
        }
```

---

### REQ-AG-005: Video Strategy Agent
**Priority:** HIGH
**Source:** HiggsVideoDirectorApp, cinematic-stream
**User Story:** As a video creator, I need an AI agent that translates my creative intent into video generation parameters (mood, camera movements, lighting) so I can produce professional videos.

**Acceptance Criteria:**
- [ ] Accepts prompt + mood slider (0-100)
- [ ] Classifies mood into categories (High Energy, Luxury, Intimate, Surreal)
- [ ] Generates 3 camera movement variations per mood
- [ ] Enriches prompts with cinematic parameters
- [ ] Learns user preferences via MemoryAgent
- [ ] Supports multi-platform optimization (aspect ratios)

**Technical Implementation:**
```python
# backend/agents/video_strategy_agent.py
class VideoStrategyAgent(BaseAgent):
    """Develops video generation strategies"""

    MOOD_MATRIX = {
        "high_energy": {"range": (75, 100), "cameras": ["fpv_drone", "crash_zoom", "whip_pan"]},
        "luxury_reveal": {"range": (50, 75), "cameras": ["dolly_slow", "pan_slow", "crane_up"]},
        "intimate_story": {"range": (25, 50), "cameras": ["static_focus", "dolly_zoom", "handheld_subtle"]},
        "surreal_trip": {"range": (0, 25), "cameras": ["bullet_time", "through_object", "spiral_zoom"]}
    }

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = input_data.get('prompt')
        mood_slider = input_data.get('mood_slider', 50)
        aspect_ratio = input_data.get('aspect_ratio', '16:9')

        # Classify mood
        mood_category = self._classify_mood(mood_slider)

        # Generate 3 variations
        variations = []
        for camera in self.MOOD_MATRIX[mood_category]["cameras"][:3]:
            enriched_prompt = self._enrich_prompt(prompt, mood_category, camera)
            variations.append({
                "prompt": enriched_prompt,
                "camera_move": camera,
                "aspect_ratio": aspect_ratio,
                "mood": mood_category
            })

        return {"variations": variations}
```

**Reference Files:**
- HiggsVideoDirectorApp: `/higgs_video_director_app/agents/strategy_agent.py`
- cinematic-stream: `/backend/src/agents.py` (StrategyAgent)

---

### REQ-AG-006: Content Generation Agent (Scribe)
**Priority:** MEDIUM
**Source:** synapse-core
**User Story:** As a marketer, I need an AI agent that generates marketing content (emails, landing pages, social posts) aligned with my brand voice.

**Acceptance Criteria:**
- [ ] Generates email sequences
- [ ] Generates landing page copy
- [ ] Generates social media posts
- [ ] Retrieves brand DNA from database
- [ ] Performs sentiment analysis
- [ ] Provides SEO optimization
- [ ] Multi-step workflow (Draft → Verify → Refine)

**Technical Implementation:**
```python
# backend/agents/scribe_agent.py
class ScribeAgent(BaseAgent):
    """Content generation with brand voice"""

    tools = [
        "retrieve_brand_voice",
        "sentiment_analyzer",
        "seo_optimizer"
    ]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        content_type = input_data.get('type')  # email, landing_page, social
        prompt = input_data.get('prompt')
        user_id = input_data.get('user_id')

        # Retrieve brand DNA
        brand_voice = await self._retrieve_brand_voice(user_id)

        # Generate content with GPT-4
        # Analyze sentiment
        # Optimize for SEO

        return {
            "content_type": content_type,
            "content": "...",
            "sentiment": "positive",
            "seo_score": 85
        }
```

**Reference Files:**
- synapse-core: `/packages/marketing-agent/scribe.py`

---

## 3. Video Generation Requirements

### REQ-VG-001: Text-to-Video with Remotion
**Priority:** HIGH
**Source:** video-studio
**User Story:** As a video creator, I need to generate animated videos from natural language descriptions so I can create professional animations without coding.

**Acceptance Criteria:**
- [ ] Accepts text description of desired animation
- [ ] Uses AI (Claude/GPT-4) to generate React/TSX code
- [ ] Validates generated code for Remotion compatibility
- [ ] Bundles code with Remotion bundler
- [ ] Renders video with Chromium + FFmpeg
- [ ] Outputs MP4 file (H.264 codec)
- [ ] Supports customizable duration and dimensions
- [ ] Real-time preview of generated code

**Technical Implementation:**
```python
# backend/services/remotion_service.py
import subprocess
import tempfile
from anthropic import Anthropic

class RemotionVideoService:
    """Generate videos using Remotion and AI"""

    async def generate_video(
        self,
        description: str,
        duration: int = 30,  # frames
        width: int = 1920,
        height: int = 1080
    ) -> str:
        # Generate React/TSX code with Claude
        tsx_code = await self._generate_tsx_code(description, duration)

        # Validate code
        if not self._validate_tsx(tsx_code):
            raise ValueError("Generated code is not valid Remotion component")

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.tsx', delete=False) as f:
            f.write(tsx_code.encode())
            tsx_path = f.name

        # Bundle with Remotion
        bundle_path = await self._bundle_remotion(tsx_path)

        # Render video
        video_path = await self._render_video(bundle_path, duration, width, height)

        return video_path

    async def _generate_tsx_code(self, description: str, duration: int) -> str:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        prompt = f"""Generate a Remotion React component for this animation:
{description}

Duration: {duration} frames at 30fps

Requirements:
- Use Remotion hooks (useCurrentFrame, useVideoConfig)
- Use interpolate() for animations
- Export as default function
- Return valid JSX
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract code from markdown
        code = self._extract_code(response.content[0].text)
        return code

    async def _render_video(self, bundle_path: str, duration: int, width: int, height: int) -> str:
        output_path = f"/tmp/video_{uuid.uuid4()}.mp4"

        cmd = [
            "npx", "remotion", "render",
            bundle_path,
            "MyVideo",
            output_path,
            "--frames", str(duration),
            "--width", str(width),
            "--height", str(height)
        ]

        subprocess.run(cmd, check=True)
        return output_path
```

**Frontend Dependencies:**
```bash
npm install remotion @remotion/cli
```

**API Endpoints:**
- `POST /api/video/generate/animation` - Generate animation from text
- `GET /api/video/render/{id}` - Get render status
- `GET /api/video/download/{id}` - Download rendered video

**Reference Files:**
- video-studio: `/src/server/ai-client.ts`
- video-studio: `/src/server/index.ts`

---

### REQ-VG-002: Audio-to-Video Pipeline
**Priority:** HIGH
**Sources:** CineLyric, wanVideo2.2, HunyuanVideoAvatar
**User Story:** As a content creator, I need to generate videos synchronized with audio input so I can create music videos and talking avatars.

**Acceptance Criteria:**
- [ ] Accepts audio file (MP3, WAV, OGG)
- [ ] Transcribes audio with timestamps (Whisper)
- [ ] Extracts lyrics and timing
- [ ] Generates visual prompts from lyrics
- [ ] Creates AI video clips for each scene
- [ ] Assembles clips with original audio
- [ ] Adds synchronized lyric overlays
- [ ] Outputs MP4 with AAC audio

**Technical Implementation:**
```python
# backend/services/audio_video_service.py
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

class AudioToVideoService:
    """Generate videos from audio input"""

    def __init__(self):
        self.whisper_model = whisper.load_model("tiny")

    async def create_music_video(
        self,
        audio_path: str,
        visual_style: str = "cinematic"
    ) -> str:
        # Step 1: Transcribe audio
        segments = await self._transcribe_audio(audio_path)

        # Step 2: Generate visual prompts
        scene_prompts = await self._lyrics_to_scenes(segments, visual_style)

        # Step 3: Generate video clips
        video_clips = await self._generate_video_clips(scene_prompts)

        # Step 4: Assemble with audio
        final_video = await self._assemble_video(video_clips, audio_path, segments)

        return final_video

    async def _transcribe_audio(self, audio_path: str) -> List[Dict]:
        result = self.whisper_model.transcribe(audio_path)
        return result["segments"]

    async def _lyrics_to_scenes(self, segments: List[Dict], style: str) -> List[Dict]:
        # Use AI to convert lyrics to visual prompts
        # Group segments into scenes (~50 words per scene)
        scenes = []
        current_scene = []

        for seg in segments:
            current_scene.append(seg)
            if len(' '.join([s['text'] for s in current_scene]).split()) >= 50:
                prompt = await self._generate_visual_prompt(current_scene, style)
                scenes.append({
                    "prompt": prompt,
                    "start": current_scene[0]['start'],
                    "end": current_scene[-1]['end']
                })
                current_scene = []

        return scenes

    async def _assemble_video(
        self,
        clips: List[str],
        audio_path: str,
        segments: List[Dict]
    ) -> str:
        # Load clips
        video_clips = [VideoFileClip(c) for c in clips]

        # Concatenate
        final = concatenate_videoclips(video_clips)

        # Add audio
        audio = AudioFileClip(audio_path)
        final = final.set_audio(audio)

        # Add subtitles
        final = self._add_subtitles(final, segments)

        # Write output
        output_path = f"/tmp/music_video_{uuid.uuid4()}.mp4"
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')

        return output_path
```

**Dependencies:**
```bash
pip install openai-whisper moviepy ffmpeg-python pydub librosa
```

**API Endpoints:**
- `POST /api/video/generate/music-video` - Upload audio, generate video
- `GET /api/video/music-video/{id}/status` - Poll generation status

**Reference Files:**
- CineLyric: `/cinelyric/core/audio.py`
- CineLyric: `/cinelyric/core/assembly.py`
- wanVideo2.2: `/wan/speech2video.py`

---

### REQ-VG-003: Music-to-Video with Suno + Higgsfield
**Priority:** MEDIUM
**Source:** SunoToHiggsBridge
**User Story:** As a content creator, I need to generate music from text prompts and automatically create synchronized music videos.

**Acceptance Criteria:**
- [ ] Accepts text prompt for music generation
- [ ] Generates music via Suno API
- [ ] Evaluates generated tracks with CriticAgent
- [ ] Selects best track
- [ ] Splits lyrics into scenes
- [ ] Generates video clips via Higgsfield API
- [ ] Compiles final music video
- [ ] Stores in S3 with public URL

**Technical Implementation:**
```python
# backend/services/suno_higgs_service.py
from suno_api import SunoClient
from higgsfield_client import HiggsfieldClient

class MusicVideoService:
    """Generate music videos via Suno + Higgsfield"""

    def __init__(self):
        self.suno = SunoClient(cookie=os.getenv('SUNO_COOKIE'))
        self.higgs = HiggsfieldClient(
            api_id=os.getenv('HIGGSFIELD_ID'),
            api_secret=os.getenv('HIGGSFIELD_SECRET')
        )

    async def generate_music_video(
        self,
        prompt: str,
        music_style: str,
        video_style: str
    ) -> Dict[str, str]:
        # Generate music
        tracks = await self.suno.generate(prompt)

        # Critic evaluates tracks
        best_track = await self._select_best_track(tracks)

        # Split lyrics to scenes
        scenes = await self._lyric_to_scenes(best_track['lyrics'])

        # Generate video clips
        video_clips = []
        for scene in scenes:
            task = await self.higgs.submit(
                task_type='text-to-video',
                prompt=f"{scene['visual_prompt']} | {video_style}",
                aspect_ratio='16:9',
                audio_sync=True
            )
            video_url = await self._wait_for_completion(task['task_id'])
            video_clips.append(video_url)

        # Compile video
        final_video = await self._compile_video(video_clips, best_track['audio_url'])

        return {
            "audio_url": best_track['audio_url'],
            "video_url": final_video,
            "lyrics": best_track['lyrics']
        }
```

**API Endpoints:**
- `POST /api/music-video/generate` - Create music video from prompt
- `GET /api/music-video/{id}/status` - Poll status

**Reference Files:**
- SunoToHiggsBridge: `/backend/src/agents.py`
- SunoToHiggsBridge: `/backend/src/clients.py`

---

### REQ-VG-004: Multi-Platform Video Optimization
**Priority:** MEDIUM
**Source:** cinematic-stream
**User Story:** As a content creator, I need to generate platform-optimized videos (TikTok, YouTube, Instagram) with appropriate aspect ratios and mood adjustments.

**Acceptance Criteria:**
- [ ] Supports TikTok (9:16), YouTube (16:9), Instagram (4:5)
- [ ] Adjusts mood parameters per platform
- [ ] Generates platform-specific briefs
- [ ] Batch generation for multiple platforms
- [ ] Real-time status tracking

**Technical Implementation:**
```python
# backend/services/platform_optimizer.py
class PlatformOptimizerService:
    """Optimize videos for multiple platforms"""

    PLATFORM_CONFIGS = {
        "tiktok": {"aspect_ratio": "9:16", "mood_boost": 20},
        "youtube": {"aspect_ratio": "16:9", "mood_boost": 0},
        "instagram": {"aspect_ratio": "4:5", "mood_boost": 10}
    }

    async def optimize_for_platforms(
        self,
        prompt: str,
        mood: int,
        platforms: List[str]
    ) -> Dict[str, str]:
        results = {}

        for platform in platforms:
            config = self.PLATFORM_CONFIGS[platform]
            adjusted_mood = min(100, mood + config["mood_boost"])

            video_url = await self._generate_video(
                prompt=prompt,
                mood=adjusted_mood,
                aspect_ratio=config["aspect_ratio"]
            )

            results[platform] = video_url

        return results
```

**Reference Files:**
- cinematic-stream: `/backend/src/agents.py` (CampaignManager)

---

## 4. Audio Processing Requirements

### REQ-AU-001: Audio Transcription Service
**Priority:** HIGH
**Sources:** CineLyric, SunoToHiggsBridge
**User Story:** As a content creator, I need to transcribe audio files with precise timestamps so I can create synchronized subtitles and captions.

**Acceptance Criteria:**
- [ ] Supports MP3, WAV, OGG, M4A formats
- [ ] Uses OpenAI Whisper (tiny, base, or small models)
- [ ] Returns word-level timestamps
- [ ] Returns sentence/segment timestamps
- [ ] Handles multiple languages
- [ ] Confidence scores for each segment

**Technical Implementation:**
```python
# backend/services/audio_service.py
import whisper

class AudioTranscriptionService:
    """Transcribe audio with timestamps"""

    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)

    async def transcribe(self, audio_path: str) -> Dict[str, Any]:
        result = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            language=None  # Auto-detect
        )

        return {
            "text": result["text"],
            "language": result["language"],
            "segments": [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "words": seg.get("words", [])
                }
                for seg in result["segments"]
            ]
        }
```

**API Endpoints:**
- `POST /api/audio/transcribe` - Upload and transcribe audio

**Dependencies:**
```bash
pip install openai-whisper
```

---

### REQ-AU-002: Audio Stem Separation
**Priority:** MEDIUM
**Source:** CineLyric
**User Story:** As an audio producer, I need to separate audio into stems (vocals, drums, bass, instruments) so I can isolate and manipulate individual elements.

**Acceptance Criteria:**
- [ ] Separates audio into 4 stems (vocals, drums, bass, other)
- [ ] Uses demucs library
- [ ] Outputs WAV files for each stem
- [ ] Maintains audio quality
- [ ] Supports batch processing

**Technical Implementation:**
```python
# backend/services/audio_service.py
import demucs.separate

class AudioStemService:
    """Separate audio into stems"""

    async def separate_stems(self, audio_path: str) -> Dict[str, str]:
        output_dir = f"/tmp/stems_{uuid.uuid4()}"
        os.makedirs(output_dir, exist_ok=True)

        # Run demucs
        demucs.separate.main([
            "--two-stems", "vocals",
            "-n", "htdemucs",
            "-o", output_dir,
            audio_path
        ])

        return {
            "vocals": f"{output_dir}/htdemucs/vocals.wav",
            "drums": f"{output_dir}/htdemucs/drums.wav",
            "bass": f"{output_dir}/htdemucs/bass.wav",
            "other": f"{output_dir}/htdemucs/other.wav"
        }
```

**Dependencies:**
```bash
pip install demucs
```

---

## 5. Image Generation & Editing Requirements

### REQ-IG-001: OmniGen2 Integration
**Priority:** MEDIUM
**Source:** OmniGen2
**User Story:** As a designer, I need unified image generation capabilities (text-to-image, image editing, subject-driven generation) in one system.

**Acceptance Criteria:**
- [ ] Text-to-image generation
- [ ] Image-to-text (captioning)
- [ ] Instruction-based image editing
- [ ] Subject-driven generation (reference images)
- [ ] Support for multiple reference images
- [ ] Negative prompts
- [ ] Guidance scale configuration

**Technical Implementation:**
```python
# backend/services/omnigen_service.py
from OmniGen import OmniGenPipeline

class OmniGenService:
    """Unified image generation and editing"""

    def __init__(self):
        self.pipeline = OmniGenPipeline.from_pretrained("Shitao/OmniGen-v1")

    async def text_to_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        guidance_scale: float = 3.0,
        num_steps: int = 50
    ) -> str:
        images = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            guidance_scale=guidance_scale,
            num_inference_steps=num_steps
        )

        # Save and return path
        output_path = f"/tmp/image_{uuid.uuid4()}.png"
        images[0].save(output_path)
        return output_path

    async def edit_image(
        self,
        image_path: str,
        instruction: str,
        guidance_scale: float = 2.0
    ) -> str:
        images = self.pipeline(
            prompt=instruction,
            input_images=[image_path],
            guidance_scale=guidance_scale
        )

        output_path = f"/tmp/edited_{uuid.uuid4()}.png"
        images[0].save(output_path)
        return output_path
```

**API Endpoints:**
- `POST /api/images/generate` - Text-to-image
- `POST /api/images/edit` - Edit image with instruction
- `POST /api/images/caption` - Generate caption from image

---

## 6. Production Workflow Requirements

### REQ-PW-001: Multi-Project Orchestration
**Priority:** MEDIUM
**Source:** NexusProductions
**User Story:** As a production manager, I need to manage multiple video projects simultaneously with automated workflows.

**Acceptance Criteria:**
- [ ] Create production projects with metadata
- [ ] Track project status (draft, in_progress, rendering, completed)
- [ ] Assign agents to projects
- [ ] Monitor rendering progress
- [ ] Manage asset libraries per project
- [ ] Revenue tracking and monetization

**Technical Implementation:**
```sql
CREATE TABLE production_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(50),  -- 'feature', 'series', 'short', 'music_video'
    status VARCHAR(20) DEFAULT 'draft',
    owner_id UUID REFERENCES users(id),
    metadata JSONB,
    revenue_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 7. Infrastructure Requirements

### REQ-IN-001: Celery + Redis Setup
**Priority:** CRITICAL
**User Story:** As a system, I need asynchronous task processing for long-running operations like video generation.

**Acceptance Criteria:**
- [ ] Redis running on port 6379
- [ ] Celery workers configured
- [ ] Task monitoring (Flower)
- [ ] Automatic retries with exponential backoff
- [ ] Task result persistence
- [ ] Dead letter queue for failed tasks

**Docker Compose:**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  flower:
    build: ./backend
    command: celery -A app.tasks flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - celery_worker
```

---

### REQ-IN-002: GPU Support (Optional)
**Priority:** LOW
**User Story:** As a system, I may need GPU acceleration for video rendering and AI model inference.

**Acceptance Criteria:**
- [ ] NVIDIA GPU detection
- [ ] CUDA support
- [ ] Docker GPU runtime configuration
- [ ] Graceful fallback to CPU

---

## 8. Security & Authentication Requirements

### REQ-SEC-001: Enhanced Authentication
**Priority:** MEDIUM
**User Story:** As a platform, I need robust authentication with role-based access control.

**Acceptance Criteria:**
- [ ] Email/password registration
- [ ] JWT token refresh mechanism
- [ ] Role-based permissions (admin, creator, viewer)
- [ ] API key management for external services
- [ ] Audit logging for sensitive operations

---

## 9. Testing Requirements

### REQ-TEST-001: Comprehensive Test Suite
**Priority:** HIGH
**User Story:** As a developer, I need automated tests to ensure reliability.

**Acceptance Criteria:**
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests for agents
- [ ] E2E tests with Playwright
- [ ] Performance tests for video generation
- [ ] Load tests for concurrent users

---

## 10. Documentation Requirements

### REQ-DOC-001: User Guides
**Priority:** MEDIUM
**Acceptance Criteria:**
- [ ] Story design workflow tutorial
- [ ] Video generation guide
- [ ] Agent usage best practices
- [ ] API documentation (OpenAPI/Swagger)

---

## Appendix A: Technology Stack Summary

### Backend:
```
fastapi
uvicorn
sqlalchemy
alembic
celery[redis]
redis
openai-whisper
demucs
librosa
pydub
moviepy
ffmpeg-python
anthropic
openai
replicate
higgsfield-client
suno-api
pillow
boto3 (S3)
```

### Frontend:
```
next@16
react@19
three
@react-three/fiber
@react-three/drei
react-player
wavesurfer.js
remotion
```

### Infrastructure:
```
docker
docker-compose
postgresql
redis
nginx
```

---

## Appendix B: Estimated Effort

| Phase | Weeks | Developer-Weeks |
|-------|-------|-----------------|
| Phase 1: Story Features | 2 | 4 |
| Phase 2: Agent Infrastructure | 2 | 6 |
| Phase 3: Video Generation | 3 | 9 |
| Phase 4: Audio Processing | 1 | 2 |
| Phase 5: Advanced Features | 2 | 4 |
| Phase 6: Production Workflow | 2 | 4 |
| **Total** | **12** | **29** |

**Team Size:** 2-3 developers recommended
**Timeline:** 3-4 months with full-time team

---

**END OF REQUIREMENTS DOCUMENT**
