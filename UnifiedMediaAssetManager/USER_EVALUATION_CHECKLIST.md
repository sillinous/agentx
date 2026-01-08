# User Evaluation Testing Checklist

**Date:** 2026-01-08
**Version:** 1.0
**Status:** Ready for User Testing

---

## Quick Start

### 1. Start the Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Access the Application
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Test User Credentials

Use the "Seed Test Users" feature or these pre-configured accounts:

| Username | Password | Roles |
|----------|----------|-------|
| test_admin | TestAdmin123! | admin, editor, viewer |
| test_editor | TestEditor123! | editor, viewer |
| test_viewer | TestViewer123! | viewer |
| test_creator | TestCreator123! | creator, viewer |

To seed test users:
```bash
curl -X POST http://localhost:8000/auth/seed-test-users
```

---

## Feature Testing Checklist

### Authentication (Priority: High)
- [ ] Register a new user account
- [ ] Login with registered account
- [ ] Login with test user (use quick-fill buttons)
- [ ] View user menu (shows username, roles)
- [ ] Logout successfully
- [ ] Session persists on page refresh

### Universe Management (Priority: High)
- [ ] View list of universes on home page
- [ ] Create a new universe with name and description
- [ ] Click into universe detail page
- [ ] See universe info and element list

### Element Management (Priority: High)
- [ ] Add a new element (character, location, prop, etc.)
- [ ] View element detail page
- [ ] Add text component to element
- [ ] Add image component (with URL)
- [ ] Add attribute component
- [ ] View all component types rendered correctly

### World Configuration (Priority: Medium)
- [ ] Navigate to World Config page from universe
- [ ] Select genre from dropdown (12 options)
- [ ] Select physics system
- [ ] Select magic system
- [ ] Select tech level
- [ ] Select tone/atmosphere
- [ ] Set color palette (primary, secondary, accent)
- [ ] Add art style notes
- [ ] Save configuration
- [ ] View saved configuration

### Entity Traits (Priority: Medium)
- [ ] Navigate to Traits page for an element
- [ ] View trait templates based on entity type
- [ ] Add trait using template quick-fill
- [ ] Add custom trait manually
- [ ] Edit existing trait
- [ ] Delete trait
- [ ] Filter traits by category

### Timeline Events (Priority: Medium)
- [ ] Navigate to Timeline page
- [ ] View timeline visualization (dots on line)
- [ ] Create new event with title and timestamp
- [ ] Add event description, type, significance
- [ ] Add participants to event
- [ ] Edit existing event
- [ ] Delete event
- [ ] Filter events by type/significance

### Video Generation (Priority: High)
- [ ] Navigate to Video page for universe
- [ ] Enter video prompt text
- [ ] Adjust mood slider (0-100)
- [ ] Select aspect ratio (16:9, 9:16, 1:1)
- [ ] Select duration (3, 5, 10 seconds)
- [ ] Click "Generate Strategy" to preview
- [ ] View 3 strategy variations
- [ ] Generate video job
- [ ] View job status and progress
- [ ] See video URL when complete (mock)

### Audio Processing (Priority: High)
- [ ] Navigate to Audio page for universe
- [ ] **TTS Tab:**
  - [ ] Enter text to convert
  - [ ] Select voice from dropdown
  - [ ] Generate speech
  - [ ] View audio URL result
- [ ] **Transcription Tab:**
  - [ ] Enter audio URL
  - [ ] Select language (optional)
  - [ ] Transcribe audio
  - [ ] View transcription text
- [ ] **Analysis Tab:**
  - [ ] Enter audio URL
  - [ ] Analyze audio
  - [ ] View technical details (duration, format, etc.)

### 3D Model Viewer (Priority: Low)
- [ ] Add 3D model component to element (GLTF/GLB URL)
- [ ] View model loads in viewer
- [ ] Drag to rotate model
- [ ] Scroll to zoom
- [ ] Toggle auto-rotation

---

## API Endpoint Testing (Optional)

For advanced testers, verify backend directly:

```bash
# Health check
curl http://localhost:8000/

# Provider status
curl http://localhost:8000/api/providers/status

# Create universe
curl -X POST http://localhost:8000/universes \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Universe", "description": "Testing"}'

# Video strategy
curl -X POST http://localhost:8000/api/video/strategy \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A sunset over mountains", "mood": 50}'
```

---

## Known Limitations

1. **Mock Providers:** Video/audio generation uses mock responses (no actual AI generation without API keys)
2. **3D Viewer:** Requires GLTF/GLB format models
3. **File Upload:** Currently URL-based only (no direct file upload)
4. **Real-time Collaboration:** Not yet implemented

---

## Reporting Issues

When reporting issues, please include:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Browser and version
5. Console errors (if any)

---

## Success Criteria

User testing is successful if:
- [ ] All High priority features work without errors
- [ ] 80%+ of Medium priority features work
- [ ] No blocking issues prevent core workflows
- [ ] UI is intuitive and responsive
- [ ] Error messages are clear and helpful

---

**Document Version:** 1.0
**Prepared By:** Claude Opus 4.5
**For:** User Evaluation Testers
