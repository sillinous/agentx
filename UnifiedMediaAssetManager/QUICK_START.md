# UnifiedMediaAssetManager - Quick Start

## ✅ Current Status
- **Phase 3**: 100% Complete
- **Services**: Starting up
- **Disk Space**: 3.6GB free (sufficient)
- **Ready for**: API Testing

---

## Services Running

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

**Ports:**
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Flower (Celery): http://localhost:5555 (when started)

---

## Quick API Test

Once the backend finishes starting (look for "Uvicorn running" in logs):

### Test 1: Health Check
```bash
curl http://localhost:8000/
```

### Test 2: Video Strategy
```bash
curl -X POST http://localhost:8000/api/video/strategy \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Mountain landscape at sunset",
    "mood": 70,
    "num_variations": 2
  }'
```

### Test 3: Generate Video
```bash
curl -X POST http://localhost:8000/api/video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Mountain landscape at sunset",
    "mood": 70,
    "duration": 5
  }'
```

### Test 4: Audio TTS
```bash
curl -X POST http://localhost:8000/api/audio/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from the Unified Media Asset Manager!",
    "voice": "default",
    "provider": "mock"
  }'
```

---

## What to Expect (Mock Providers)

All responses will be **instant** and **simulated** because we're using mock providers:

✅ **Video Strategy**: Returns creative suggestions immediately
✅ **Video Generation**: Creates job instantly (status: "processing" → "completed")
✅ **Audio TTS**: Returns mock audio URL immediately
✅ **Audio Transcription**: Returns sample transcription

---

## View API Documentation

Once backend is running, visit:
**http://localhost:8000/docs**

This provides:
- Interactive API explorer
- Request/response schemas
- Try-it-out functionality
- Full endpoint documentation

---

## Next Steps After Testing

1. ✅ Verify all endpoints work
2. Run integration tests: `cd backend && pytest tests/ -v`
3. Start Celery worker for async jobs: `docker-compose up -d celery_worker`
4. Start Flower for monitoring: `docker-compose up -d flower`
5. Integrate with frontend
6. Add real provider API keys

---

## Troubleshooting

**Backend won't start**:
```bash
docker-compose logs backend
```

**Database issues**:
```bash
docker-compose exec backend alembic current
docker-compose exec backend alembic upgrade head
```

**Reset everything**:
```bash
docker-compose down -v
rm backend/sql_app.db
docker-compose up -d
```

---

For detailed testing guide, see `TESTING_GUIDE.md`
