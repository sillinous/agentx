# Phase 3: Video & Audio Generation - Implementation Plan

**Status**: 🚧 **IN PROGRESS**
**Start Date**: January 4, 2026
**Estimated Duration**: 2-3 weeks
**Phase**: 3 of 6

---

## Executive Summary

Phase 3 extends the agent infrastructure built in Phase 2 to support video and audio generation. This phase integrates capabilities from HiggsVideoDirectorApp, CineLyric, SunoToHiggsBridge, and other media repositories to provide comprehensive multimedia content creation.

### Key Objectives

1. **Video Generation**: Text-to-video and image-to-video using external APIs
2. **Video Strategy**: Mood-based parameter generation (camera movements, lighting)
3. **Audio Generation**: Music and voice synthesis
4. **Media Storage**: Video/audio file storage and streaming
5. **Pipeline Integration**: Combine agents for multi-modal content creation

---

## Architecture Overview

### Video Generation Flow

```
User Request → VideoStrategyAgent → VideoGenerationAgent → External API → Storage → User
                    ↓                       ↓
              (Mood Classification)   (API Integration)
              (Camera Parameters)     (Kling/Runway/Pika)
              (Prompt Enrichment)     (Job Tracking)
```

### Agent Types (Phase 3)

1. **VideoStrategyAgent**: Translates user intent into video parameters
   - Mood classification (0-100 slider → categories)
   - Camera movement selection
   - Prompt enrichment with cinematic terms
   - Platform optimization (TikTok, YouTube, Instagram)

2. **VideoGenerationAgent**: Executes video generation
   - Text-to-video generation
   - Image-to-video generation
   - API integration (Kling, Runway, Pika, etc.)
   - Job status polling and webhook handling

3. **AudioAgent**: Generates music and voice
   - Text-to-music (Suno API)
   - Text-to-speech (ElevenLabs, Coqui)
   - Audio transcription (Whisper)
   - Audio stem separation (Demucs)

---

## Database Schema

### New Tables

#### video_jobs
```sql
CREATE TABLE video_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID REFERENCES universes(id) ON DELETE CASCADE,
    agent_job_id UUID REFERENCES agent_jobs(id),

    -- Request parameters
    generation_type VARCHAR(50) NOT NULL,  -- 'text_to_video', 'image_to_video'
    prompt TEXT NOT NULL,
    negative_prompt TEXT,

    -- Strategy parameters (from VideoStrategyAgent)
    mood_category VARCHAR(50),  -- 'high_energy', 'luxury_reveal', etc.
    camera_movement VARCHAR(100),
    aspect_ratio VARCHAR(10) DEFAULT '16:9',
    duration INTEGER DEFAULT 5,  -- seconds

    -- External API details
    provider VARCHAR(50),  -- 'kling', 'runway', 'pika', 'luma'
    provider_job_id VARCHAR(255),
    provider_status VARCHAR(50),

    -- Generated content
    video_url TEXT,
    thumbnail_url TEXT,
    local_path TEXT,
    file_size BIGINT,

    -- Metadata
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    INDEX idx_video_jobs_universe (universe_id),
    INDEX idx_video_jobs_status (status),
    INDEX idx_video_jobs_provider (provider, provider_job_id)
);
```

#### audio_jobs
```sql
CREATE TABLE audio_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID REFERENCES universes(id) ON DELETE CASCADE,
    agent_job_id UUID REFERENCES agent_jobs(id),

    -- Request parameters
    generation_type VARCHAR(50) NOT NULL,  -- 'text_to_music', 'text_to_speech', 'transcription'
    prompt TEXT,
    audio_input_path TEXT,  -- For transcription/stem separation

    -- Generation parameters
    duration INTEGER,
    voice_id VARCHAR(255),  -- For TTS
    language VARCHAR(10),

    -- External API details
    provider VARCHAR(50),  -- 'suno', 'elevenlabs', 'coqui'
    provider_job_id VARCHAR(255),

    -- Generated content
    audio_url TEXT,
    local_path TEXT,
    file_size BIGINT,
    transcription JSON,  -- For transcription jobs

    -- Metadata
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    INDEX idx_audio_jobs_universe (universe_id),
    INDEX idx_audio_jobs_status (status)
);
```

#### media_assets
```sql
CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    universe_id UUID REFERENCES universes(id) ON DELETE CASCADE,
    element_id UUID REFERENCES elements(id) ON DELETE SET NULL,

    -- Asset details
    asset_type VARCHAR(20) NOT NULL,  -- 'video', 'audio', 'image'
    title VARCHAR(255),
    description TEXT,

    -- File details
    file_path TEXT NOT NULL,
    public_url TEXT,
    file_size BIGINT,
    mime_type VARCHAR(100),
    duration REAL,  -- For video/audio (seconds)
    dimensions JSON,  -- For video/image: {"width": 1920, "height": 1080}

    -- Source tracking
    source_job_id UUID,  -- References video_jobs or audio_jobs
    source_type VARCHAR(50),  -- 'generated', 'uploaded', 'imported'

    -- Metadata
    tags TEXT[],
    metadata JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_media_assets_universe (universe_id),
    INDEX idx_media_assets_type (asset_type),
    INDEX idx_media_assets_element (element_id)
);
```

---

## Implementation Tasks

### Task 1: Database Migration ✅
Create Alembic migration for new tables.

**File**: `backend/alembic/versions/c3d4e5f6g7h8_add_video_audio_infrastructure.py`

### Task 2: VideoStrategyAgent Implementation
Translates user intent into video parameters based on mood.

**File**: `backend/app/agents/video_strategy_agent.py`

**Key Features**:
- Mood classification (0-100 slider → 4 categories)
- Camera movement matrix per mood
- Prompt enrichment with cinematic vocabulary
- Platform-specific optimization

**Mood Matrix**:
```python
MOOD_MATRIX = {
    "high_energy": {
        "range": (75, 100),
        "cameras": ["fpv_drone", "crash_zoom_in", "whip_pan_right"],
        "lighting": ["high_contrast", "neon_glow"],
        "keywords": ["dynamic", "explosive", "intense"]
    },
    "luxury_reveal": {
        "range": (50, 75),
        "cameras": ["dolly_slow", "crane_up", "pan_slow"],
        "lighting": ["golden_hour", "soft_key"],
        "keywords": ["elegant", "sophisticated", "premium"]
    },
    "intimate_story": {
        "range": (25, 50),
        "cameras": ["static_focus", "handheld_subtle", "dolly_zoom"],
        "lighting": ["natural", "warm_ambient"],
        "keywords": ["personal", "emotional", "authentic"]
    },
    "surreal_trip": {
        "range": (0, 25),
        "cameras": ["bullet_time", "spiral_zoom", "through_object"],
        "lighting": ["neon_noir", "volumetric"],
        "keywords": ["dreamlike", "abstract", "otherworldly"]
    }
}
```

### Task 3: VideoGenerationAgent Implementation
Integrates with external video generation APIs.

**File**: `backend/app/agents/video_generation_agent.py`

**Supported Providers** (Phase 3.1 - Start with Mock/Placeholder):
- **Mock Provider**: Returns placeholder videos for testing
- **Future Providers** (Phase 3.2+):
  - Kling AI (text-to-video, image-to-video)
  - Runway ML (Gen-3 Alpha)
  - Pika Labs
  - Luma Dream Machine
  - Stability AI (Stable Video Diffusion)

**API Pattern**:
```python
class VideoGenerationAgent(BaseAgent):
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        generation_type = input_data.get('generation_type')  # 'text_to_video' or 'image_to_video'
        prompt = input_data.get('prompt')
        provider = input_data.get('provider', 'mock')

        # Get provider client
        client = self._get_provider_client(provider)

        # Submit job
        provider_job = await client.generate_video(
            prompt=prompt,
            **input_data.get('parameters', {})
        )

        # Store job info
        video_job = await self._create_video_job(
            provider=provider,
            provider_job_id=provider_job['id'],
            input_data=input_data
        )

        # Poll for completion (async task)
        await self._poll_until_complete(video_job.id, client, provider_job['id'])

        return {
            "video_job_id": video_job.id,
            "status": "processing",
            "provider": provider
        }
```

### Task 4: Video Storage Service
Handles video file storage, streaming, and CDN integration.

**File**: `backend/app/services/video_storage.py`

**Features**:
- Download videos from provider URLs
- Store in local filesystem or S3
- Generate thumbnails
- Create streaming-optimized formats
- Serve videos with range request support

### Task 5: AudioAgent Implementation
Music and voice generation capabilities.

**File**: `backend/app/agents/audio_agent.py`

**Capabilities**:
- Text-to-music (Suno API - placeholder)
- Text-to-speech (ElevenLabs - placeholder)
- Audio transcription (OpenAI Whisper)
- Stem separation (Demucs)

### Task 6: API Endpoints

**New Endpoints**:

```python
# Video Generation
POST   /api/video/generate           # Create video generation job
GET    /api/video/jobs                # List video jobs
GET    /api/video/jobs/{id}           # Get video job status
GET    /api/video/jobs/{id}/download  # Download generated video
POST   /api/video/jobs/{id}/retry     # Retry failed job

# Video Strategy
POST   /api/video/strategy            # Generate video strategy variations

# Audio Generation
POST   /api/audio/generate            # Create audio generation job
GET    /api/audio/jobs                # List audio jobs
GET    /api/audio/jobs/{id}           # Get audio job status
POST   /api/audio/transcribe          # Transcribe audio file

# Media Assets
GET    /api/media/assets              # List all media assets
POST   /api/media/assets              # Upload new asset
GET    /api/media/assets/{id}         # Get asset details
DELETE /api/media/assets/{id}         # Delete asset
```

### Task 7: Celery Tasks

**File**: `backend/app/agents/video_tasks.py`

```python
@celery_app.task(bind=True, max_retries=5)
def poll_video_generation(self, video_job_id: str, provider: str):
    """Poll external API for video generation completion"""

@celery_app.task
def generate_video_thumbnail(video_path: str):
    """Generate thumbnail from video"""

@celery_app.task
def cleanup_old_videos(days: int = 30):
    """Clean up old video files from storage"""
```

---

## Phase 3 Milestones

### Milestone 3.1: Foundation (Week 1)
- ✅ Database schema and migration
- ✅ VideoStrategyAgent implementation
- ✅ VideoGenerationAgent (mock provider)
- ✅ Basic API endpoints
- ✅ Video storage service

**Success Criteria**:
- Can create video generation jobs
- VideoStrategyAgent generates mood-based parameters
- Mock videos are stored and retrievable
- API endpoints respond correctly

### Milestone 3.2: Audio Integration (Week 2)
- AudioAgent implementation
- Audio transcription (Whisper)
- Audio storage service
- Audio API endpoints

**Success Criteria**:
- Can transcribe uploaded audio files
- Transcription includes timestamps
- Audio files are stored and accessible

### Milestone 3.3: Production Readiness (Week 3)
- Real video generation provider integration (Kling or Runway)
- Webhook handling for async jobs
- Video streaming optimization
- End-to-end testing
- Documentation

**Success Criteria**:
- Can generate real videos from external APIs
- Videos are downloaded and stored locally
- Streaming works for large video files
- All endpoints tested

---

## Technology Stack

### Video Processing
- **FFmpeg**: Video manipulation, thumbnail generation
- **moviepy**: Python video editing
- **Pillow**: Image processing

### Audio Processing
- **Whisper**: Audio transcription
- **Demucs**: Audio stem separation
- **pydub**: Audio file manipulation
- **librosa**: Audio analysis

### External APIs (Planned)
- **Kling AI**: Text/image-to-video (future)
- **Runway ML**: Video generation (future)
- **Suno**: Music generation (future)
- **ElevenLabs**: Text-to-speech (future)

### Storage
- **Local Filesystem**: Development
- **S3**: Production (future)
- **CDN**: Video delivery (future)

---

## Dependencies to Add

```txt
# Video Processing
ffmpeg-python>=0.2.0
moviepy>=1.0.3
pillow>=10.0.0

# Audio Processing
openai-whisper>=20231117
demucs>=4.0.0
pydub>=0.25.1
librosa>=0.10.0

# HTTP Clients for External APIs
httpx>=0.25.0
aiohttp>=3.9.0
```

---

## Risk Mitigation

### Risk 1: External API Rate Limits
**Mitigation**: Implement job queuing, retry logic, and provider fallback

### Risk 2: Large File Storage
**Mitigation**: Implement cleanup jobs, S3 integration for production

### Risk 3: Video Processing Performance
**Mitigation**: Use Celery for async processing, optimize FFmpeg settings

### Risk 4: API Costs
**Mitigation**: Start with mock providers, add billing alerts, implement quotas

---

## Testing Strategy

### Unit Tests
- Agent logic (mood classification, parameter generation)
- Storage service (file operations)
- API request/response validation

### Integration Tests
- End-to-end video generation flow
- Mock provider integration
- Database operations

### Manual Tests
- Video playback in browser
- Audio transcription accuracy
- API endpoint usability

---

## Success Metrics

- ✅ VideoStrategyAgent generates valid parameters
- ✅ VideoGenerationAgent creates jobs successfully
- ✅ Videos are stored and retrievable
- ✅ API endpoints respond within 200ms
- ✅ Mock video generation completes in < 5 seconds
- ✅ Real video generation (when implemented) completes in < 2 minutes
- ✅ Audio transcription accuracy > 90%

---

## Next Phase Preview

**Phase 4: Advanced Features & UI Integration**
- Frontend components for video generation
- Real-time job status updates (WebSockets)
- Video editor integration
- Multi-clip assembly
- Advanced prompt engineering tools

---

**Phase 3 Status**: Ready to begin implementation
**First Task**: Create database migration for video/audio infrastructure
