# UnifiedMediaAssetManager - Testing Guide

## Phase 3 Features (Video & Audio Generation) - READY FOR TESTING

This guide will help you test the newly implemented Phase 3 video and audio generation features.

## What's Been Implemented

### ✅ Completed Features

1. **Database Schema**
   - `video_jobs` table for tracking video generation requests
   - `audio_jobs` table for tracking audio processing requests
   - `media_assets` table for cataloging generated media
   - All tables properly indexed and with foreign key relationships

2. **Video Generation System**
   - `VideoStrategyAgent` - Analyzes prompts and generates creative strategies
   - `VideoGenerationAgent` - Handles video creation via multiple providers
   - `VideoStorageService` - Manages local video storage with thumbnail generation
   - Mock provider for testing without API keys

3. **Audio Processing System**
   - `AudioAgent` - Handles transcription, TTS, and audio analysis
   - Support for multiple providers (Whisper, ElevenLabs, etc.)
   - Mock provider for testing without API keys

4. **API Endpoints**
   - `POST /api/video/generate` - Create video generation job
   - `GET /api/video/jobs` - List all video jobs
   - `GET /api/video/jobs/{job_id}` - Get job status and result
   - `POST /api/video/strategy` - Generate strategy without creating job
   - `POST /api/audio/transcribe` - Transcribe audio to text
   - `POST /api/audio/tts` - Convert text to speech
   - `POST /api/audio/analyze` - Analyze audio characteristics

## Setup Instructions

### Option 1: Docker (Recommended)

1. **Ensure Docker is running**
   ```bash
   docker --version
   docker ps
   ```

2. **Start the services**
   ```bash
   cd UnifiedMediaAssetManager
   docker-compose up -d
   ```

   This starts:
   - Redis (port 6379)
   - Backend API (port 8000)
   - Celery Worker
   - Flower monitoring (port 5555)

3. **Check service health**
   ```bash
   docker-compose ps
   docker-compose logs backend
   ```

4. **Access the services**
   - API Documentation: http://localhost:8000/docs
   - Flower (Celery monitoring): http://localhost:5555

### Option 2: Manual Setup (If Docker has issues)

1. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Start Redis (required)**
   ```bash
   redis-server
   ```

4. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Start Celery worker (in separate terminal)**
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```

## Testing the Video Generation API

### 1. Generate Video Strategy

First, test the strategy generation to see creative variations:

```bash
curl -X POST http://localhost:8000/api/video/strategy \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene mountain landscape at sunset",
    "mood": 70,
    "platform": "youtube",
    "num_variations": 3
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "mood_category": "uplifting",
  "variations": [
    {
      "mood_category": "uplifting",
      "camera_movement": "slow pan right",
      "enriched_prompt": "A serene mountain landscape at sunset with warm golden light...",
      "rationale": "Slow pan enhances the peaceful atmosphere..."
    }
  ]
}
```

### 2. Generate Video

Create a video generation job:

```bash
curl -X POST http://localhost:8000/api/video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene mountain landscape at sunset",
    "mood": 70,
    "aspect_ratio": "16:9",
    "duration": 5
  }'
```

**Expected Response:**
```json
{
  "job_id": "abc123...",
  "status": "processing",
  "provider_job_id": "mock_video_abc123",
  "strategy": {
    "mood_category": "uplifting",
    "camera_movement": "slow pan right",
    "enriched_prompt": "..."
  }
}
```

### 3. Check Video Job Status

```bash
curl http://localhost:8000/api/video/jobs/{job_id}
```

**Expected Response (Processing):**
```json
{
  "id": "abc123...",
  "status": "processing",
  "provider": "mock",
  "prompt": "...",
  "created_at": "2026-01-04T14:00:00"
}
```

**Expected Response (Completed):**
```json
{
  "id": "abc123...",
  "status": "completed",
  "output_video_url": "/media/videos/default/abc123.mp4",
  "prompt": "...",
  "mood_category": "uplifting",
  "camera_movement": "slow pan right",
  "completed_at": "2026-01-04T14:00:05"
}
```

### 4. List All Video Jobs

```bash
curl http://localhost:8000/api/video/jobs
```

## Testing the Audio Processing API

### 1. Text-to-Speech

```bash
curl -X POST http://localhost:8000/api/audio/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the text to speech system.",
    "voice": "default",
    "provider": "mock"
  }'
```

**Expected Response:**
```json
{
  "job_id": "audio123...",
  "status": "completed",
  "result": {
    "success": true,
    "audio_url": "/media/audio/audio123.mp3",
    "duration": 3.5,
    "provider": "mock"
  }
}
```

### 2. Audio Transcription

```bash
curl -X POST http://localhost:8000/api/audio/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/sample.mp3",
    "provider": "mock"
  }'
```

**Expected Response:**
```json
{
  "job_id": "trans123...",
  "status": "completed",
  "result": {
    "success": true,
    "text": "Transcribed text content...",
    "confidence": 0.95,
    "language": "en"
  }
}
```

### 3. Audio Analysis

```bash
curl -X POST http://localhost:8000/api/audio/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/sample.mp3",
    "provider": "mock"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "duration": 45.3,
  "sample_rate": 44100,
  "channels": 2,
  "format": "mp3",
  "loudness": -12.5,
  "tempo": 120
}
```

## Testing with Real Providers

To test with real API providers instead of mocks:

1. **Add API keys to .env:**
   ```bash
   ANTHROPIC_API_KEY=your_key_here
   RUNWAY_API_KEY=your_runway_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   ```

2. **Modify request to specify provider:**
   ```json
   {
     "prompt": "...",
     "provider": "runway"  // or "minimax", "klingai", "suno", etc.
   }
   ```

## Integration Testing

A comprehensive test suite is available:

```bash
cd backend
pytest tests/test_video_generation.py -v
pytest tests/test_audio_processing.py -v
```

## Monitoring & Debugging

### View API Logs
```bash
docker-compose logs -f backend
```

### View Celery Worker Logs
```bash
docker-compose logs -f celery_worker
```

### Access Flower (Celery Monitoring)
http://localhost:5555

### Check Database
```bash
docker-compose exec backend sqlite3 sql_app.db
.tables
SELECT * FROM video_jobs ORDER BY created_at DESC LIMIT 5;
```

## Common Issues

### Issue: "No such table" error
**Solution:** Run migrations: `alembic upgrade head`

### Issue: Video jobs stay in "processing" status
**Solution:** Check Celery worker is running and connected to Redis

### Issue: Thumbnails not generating
**Solution:** Ensure ffmpeg is installed in the Docker container (already configured)

### Issue: Mock videos don't download
**Solution:** This is expected - mock provider returns placeholder URLs. Use real providers for actual videos.

## Next Steps

Once basic testing is complete:

1. ✅ Verify all endpoints return expected responses
2. ✅ Test error handling (invalid inputs, missing parameters)
3. ⏭️ Integrate with frontend UI
4. ⏭️ Implement Phase 1 features (story design tools)
5. ⏭️ Add real provider integrations (Runway, Minimax, etc.)
6. ⏭️ Set up production deployment (Kubernetes)

## Success Criteria

The system is ready for user testing when:

- ✅ Database migrations complete without errors
- ✅ API server starts and responds to health checks
- ✅ Video generation endpoint creates jobs successfully
- ✅ Audio processing endpoints return mock results
- ✅ Job status can be queried and returns correct state
- ⏭️ Frontend can communicate with backend API
- ⏭️ Real provider integrations work (when API keys provided)

---

**Status:** Phase 3 backend implementation is **COMPLETE** and ready for API testing.

**Date:** 2026-01-04

**Next:** Frontend integration and user acceptance testing.
