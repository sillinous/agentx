# Agent Infrastructure Testing Guide

## Overview

This guide provides step-by-step instructions for testing the AI Agent Infrastructure implemented in Phase 2.

## Prerequisites

1. **Environment Variables**: Ensure the following are set in your `.env` file:
   ```bash
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/umam

   # Celery / Redis
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0

   # AI Agent
   ANTHROPIC_API_KEY=your-anthropic-api-key-here

   # JWT (for API authentication)
   JWT_SECRET=your-secret-key
   ```

2. **Services Running**: Start all services with Docker Compose:
   ```bash
   cd UnifiedMediaAssetManager
   docker-compose up -d
   ```

3. **Database Migration**: Apply the agent infrastructure migration:
   ```bash
   cd backend
   alembic upgrade head
   ```

## Service Health Checks

### 1. Check Redis
```bash
docker-compose exec redis redis-cli ping
# Expected: PONG
```

### 2. Check Celery Worker
```bash
docker-compose logs celery_worker
# Expected: Look for "ready" message and no errors
```

### 3. Check Flower (Celery Monitoring)
Open browser to: http://localhost:5555
- Should see Celery dashboard
- Workers should be shown as online

### 4. Check API Server
```bash
curl http://localhost:8000/
# Expected: {"message":"Welcome to the Unified Media Asset Manager API"}
```

## API Testing

### Step 1: Get Authentication Token

```bash
# Get development token
curl -X POST http://localhost:8000/auth/dev-token
# Response: {"token":"eyJ0eXAiOiJKV1QiLCJhbGc..."}

# Save token for subsequent requests
export TOKEN="your-token-here"
```

### Step 2: Create a Test Universe (Optional)

```bash
curl -X POST http://localhost:8000/universes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-universe-001",
    "name": "Test Sci-Fi Universe",
    "description": "A cyberpunk universe for testing",
    "elements": []
  }'
```

### Step 3: Test Narrative Agent

#### Create Narrative Job
```bash
curl -X POST http://localhost:8000/agents/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "narrative",
    "universe_id": "test-universe-001",
    "input_data": {
      "prompt": "A hacker discovers a hidden digital world",
      "world_config": {
        "genre": "Cyberpunk",
        "tone": "Dark and gritty",
        "tech_level": "High-tech future"
      },
      "characters": [
        {
          "name": "Alex Chen",
          "description": "A skilled hacker with a mysterious past"
        }
      ],
      "type": "narrative"
    }
  }'
```

Expected Response:
```json
{
  "job_id": "uuid-here",
  "status": "pending",
  "agent_type": "narrative",
  "created_at": "2026-01-03T..."
}
```

Save the job_id for checking status.

#### Check Job Status
```bash
export JOB_ID="job-id-from-previous-step"

curl -X GET http://localhost:8000/agents/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

Expected Response (when completed):
```json
{
  "job_id": "uuid",
  "universe_id": "test-universe-001",
  "agent_type": "narrative",
  "status": "completed",
  "input_data": {...},
  "output_data": {
    "type": "narrative",
    "content": "Generated narrative scene here...",
    "model": "claude-3-haiku-20240307",
    "tokens_used": 450
  },
  "confidence_score": 0.9,
  "human_review_required": false,
  "error_message": null,
  "created_at": "...",
  "started_at": "...",
  "completed_at": "..."
}
```

### Step 4: Test Spatial Agent

```bash
curl -X POST http://localhost:8000/agents/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "spatial",
    "input_data": {
      "location_name": "Neo-Tokyo District 7",
      "world_config": {
        "genre": "Cyberpunk",
        "tone": "Dark and gritty",
        "tech_level": "High-tech future",
        "physics": "Realistic"
      },
      "type": "city",
      "details": "A sprawling urban district dominated by megacorporations"
    }
  }'
```

### Step 5: Test Consistency Agent

```bash
curl -X POST http://localhost:8000/agents/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "consistency",
    "input_data": {
      "content": "The wizard cast a spell using his smartphone to summon a dragon.",
      "world_config": {
        "genre": "Medieval Fantasy",
        "tone": "Epic",
        "tech_level": "Medieval",
        "magic_system": "Arcane spells and rituals"
      },
      "content_type": "narrative"
    }
  }'
```

This should detect inconsistency (smartphone in medieval setting).

Expected output_data:
```json
{
  "is_consistent": false,
  "violations": [
    "Use of modern technology (smartphone) in medieval setting"
  ],
  "explanation": "...",
  "suggestions": [
    "Replace smartphone with period-appropriate item like spellbook or staff"
  ]
}
```

### Step 6: List All Jobs

```bash
# List all jobs
curl -X GET "http://localhost:8000/agents/jobs?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Filter by agent type
curl -X GET "http://localhost:8000/agents/jobs?agent_type=narrative" \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl -X GET "http://localhost:8000/agents/jobs?status=completed" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 7: View Agent Statistics

```bash
curl -X GET http://localhost:8000/agents/stats \
  -H "Authorization: Bearer $TOKEN"
```

Expected Response:
```json
{
  "status_counts": {
    "completed": 3,
    "pending": 0,
    "processing": 0,
    "failed": 0
  },
  "agent_type_counts": {
    "narrative": 1,
    "spatial": 1,
    "consistency": 1
  },
  "avg_confidence_by_type": {
    "narrative": 0.9,
    "spatial": 0.85,
    "consistency": 0.8
  },
  "human_review_required": 0,
  "total_jobs": 3
}
```

### Step 8: Test Job Retry (Optional)

First, create a job that will fail (e.g., by providing invalid input or removing ANTHROPIC_API_KEY temporarily).

```bash
# Check the failed job
curl -X GET http://localhost:8000/agents/jobs/$FAILED_JOB_ID \
  -H "Authorization: Bearer $TOKEN"

# Retry the job
curl -X POST http://localhost:8000/agents/jobs/$FAILED_JOB_ID/retry \
  -H "Authorization: Bearer $TOKEN"
```

## Database Verification

### Check Job Records
```bash
# Connect to database
docker-compose exec db psql -U umam_user -d umam_db

# Query agent jobs
SELECT id, agent_type, status, confidence_score, human_review_required, created_at
FROM agent_jobs
ORDER BY created_at DESC
LIMIT 10;

# Check for specific job
SELECT * FROM agent_jobs WHERE id = 'job-id-here';
```

## Monitoring with Flower

1. Open http://localhost:5555 in your browser
2. View active workers and tasks
3. Monitor task execution times
4. Check for failed tasks

## Common Issues & Troubleshooting

### Issue: Jobs stuck in "pending" status
**Solution**: Check if Celery worker is running
```bash
docker-compose logs celery_worker
docker-compose restart celery_worker
```

### Issue: "No API key" error
**Solution**: Verify ANTHROPIC_API_KEY is set
```bash
docker-compose exec api env | grep ANTHROPIC
```

### Issue: Database connection errors
**Solution**: Check database is running and migration is applied
```bash
docker-compose ps db
cd backend && alembic current
```

### Issue: Import errors in Celery worker
**Solution**: Rebuild the container
```bash
docker-compose down
docker-compose build celery_worker
docker-compose up -d
```

## Performance Testing

### Concurrent Job Processing
```bash
# Submit 10 jobs simultaneously
for i in {1..10}; do
  curl -X POST http://localhost:8000/agents/jobs \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"agent_type\": \"narrative\",
      \"input_data\": {
        \"prompt\": \"Test narrative $i\",
        \"world_config\": {\"genre\": \"Fantasy\"}
      }
    }" &
done
wait

# Check stats to see if they're being processed
curl -X GET http://localhost:8000/agents/stats \
  -H "Authorization: Bearer $TOKEN"
```

## Success Criteria

- ✅ All services start without errors
- ✅ Redis accepts connections
- ✅ Celery worker is online and accepting tasks
- ✅ Flower dashboard is accessible
- ✅ API endpoints respond correctly
- ✅ Jobs transition through states: pending → processing → completed
- ✅ Narrative agent generates coherent content
- ✅ Spatial agent creates detailed location descriptions
- ✅ Consistency agent correctly identifies violations
- ✅ Confidence scores are calculated
- ✅ Human review flags work correctly
- ✅ Job retry mechanism works
- ✅ Statistics endpoint returns accurate data

## Next Steps After Testing

Once all tests pass:
1. Document any issues found and their resolutions
2. Consider adding automated integration tests
3. Set up monitoring/alerting for production
4. Proceed to Phase 3: Video Generation Integration
