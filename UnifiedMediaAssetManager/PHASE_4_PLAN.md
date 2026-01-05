# Phase 4 Implementation Plan - Advanced Features

**Status**: IN PROGRESS (Core UI Complete)
**Start Date**: January 5, 2026
**Updated**: January 5, 2026
**Target**: Advanced UI features and real provider integrations

---

## Overview

Phase 4 focuses on enhancing the user experience with advanced visualization features and connecting to real AI/media providers. This builds on the solid foundation from Phases 1-3.

---

## Features to Implement

### 1. 3D Model Viewer (Priority: HIGH)
**Source**: REQ-SD-005 from REQUIREMENTS_ROADMAP.md

A React Three Fiber component for previewing GLTF/GLB 3D models within the application.

**Requirements**:
- React Three Fiber integration
- GLTF/GLB format support
- Orbit controls (rotate, zoom, pan)
- Auto-rotation toggle
- Stage lighting
- Loading state with suspense fallback
- Responsive canvas sizing

**Dependencies**:
```bash
npm install three @react-three/fiber @react-three/drei
```

**Files to Create**:
- `frontend/src/components/ModelViewer.tsx` - Main 3D viewer component
- `frontend/src/app/universes/[universeId]/elements/[elementId]/model/page.tsx` - Model viewer page

---

### 2. Video Generation UI (Priority: HIGH)

Frontend components to interact with the Phase 3 video generation API.

**Requirements**:
- Video job creation form
- Job status monitoring with polling
- Video playback component
- Strategy preview/selection
- Thumbnail display

**Files to Create**:
- `frontend/src/components/VideoGenerator.tsx` - Video generation form
- `frontend/src/components/VideoPlayer.tsx` - Video playback component
- `frontend/src/components/JobStatusMonitor.tsx` - Job status tracker
- `frontend/src/app/universes/[universeId]/video/page.tsx` - Video generation page

---

### 3. Audio Processing UI (Priority: MEDIUM)

Frontend components for audio transcription, TTS, and analysis.

**Requirements**:
- Text-to-speech form with voice selection
- Audio upload for transcription
- Waveform visualization
- Audio playback with controls

**Files to Create**:
- `frontend/src/components/AudioProcessor.tsx` - Audio processing form
- `frontend/src/components/AudioPlayer.tsx` - Audio playback component
- `frontend/src/app/universes/[universeId]/audio/page.tsx` - Audio tools page

---

### 4. Real Provider Integration (Priority: MEDIUM)

Replace mock providers with real API integrations.

**Providers to Integrate**:
- **Video**: Runway ML, Kling AI (optional)
- **Audio**: ElevenLabs TTS, OpenAI Whisper
- **AI**: Anthropic Claude (already configured)

**Files to Modify**:
- `backend/app/agents/video_generation_agent.py` - Add real Runway integration
- `backend/app/agents/audio_agent.py` - Add ElevenLabs/Whisper integration

---

## Implementation Order

1. **3D Model Viewer** - Standalone component, no backend changes needed
2. **Video Generation UI** - Uses existing Phase 3 API
3. **Audio Processing UI** - Uses existing Phase 3 API
4. **Real Provider Integration** - Enhances existing agents

---

## Task Breakdown

### Task 4.1: 3D Model Viewer Component - COMPLETE
- [x] Install Three.js dependencies (three, @react-three/fiber, @react-three/drei)
- [x] Create ModelViewer component with Canvas
- [x] Add GLTF loader with useGLTF hook
- [x] Implement orbit controls
- [x] Add stage lighting and environment
- [x] Create loading fallback
- [x] Add auto-rotation toggle
- [x] Integrate into element detail page (inline viewer for GLTF/GLB)

### Task 4.2: Video Generation UI - COMPLETE
- [x] Create VideoGenerator form component
- [x] Add mood/strategy selection with slider
- [x] Implement strategy preview with variations
- [x] Implement job submission
- [x] Create JobStatusMonitor with polling
- [x] Add VideoPlayer component
- [x] Create video page route (`/universes/[id]/video`)
- [x] Add navigation to universe page

### Task 4.3: Audio Processing UI - COMPLETE
- [x] Create AudioProcessor component with tabs
- [x] Add TTS form with voice options (7 voices)
- [x] Add transcription form with URL input
- [x] Add analysis form with results display
- [x] Create audio page route (`/universes/[id]/audio`)
- [x] Add navigation to universe page

### Task 4.4: Provider Integration - COMPLETE
- [x] Add Runway ML client (`backend/app/providers/runway.py`)
- [x] Implement video generation with Runway Gen-3 Alpha
- [x] Add ElevenLabs client (`backend/app/providers/elevenlabs.py`)
- [x] Implement TTS with ElevenLabs
- [x] Update environment variables (`.env.example`)
- [x] Add base provider class with error handling
- [x] Configure Whisper for transcription (`backend/app/providers/openai_whisper.py`)
- [x] Add provider health check endpoints (`backend/app/api/providers.py`)
- [x] Wire providers into existing agents (VideoGenerationAgent, AudioAgent)

---

## Success Criteria

- [x] 3D models can be viewed and rotated in browser
- [x] Videos can be generated from the UI
- [x] Audio can be processed from the UI
- [x] At least one real provider is integrated per category
  - Video: Runway ML Gen-3 Alpha
  - Audio TTS: ElevenLabs
  - Audio Transcription: OpenAI Whisper API
- [x] All new UI components are responsive
- [x] Loading states and error handling implemented
- [x] Provider health check endpoints available

## Files Created (This Session)

### Frontend Components
- `frontend/src/components/ModelViewer.tsx` - 3D GLTF viewer (~120 lines)
- `frontend/src/components/VideoGenerator.tsx` - Video generation UI (~350 lines)
- `frontend/src/components/AudioProcessor.tsx` - Audio processing UI (~320 lines)

### Frontend Pages
- `frontend/src/app/universes/[universeId]/video/page.tsx` - Video page (~100 lines)
- `frontend/src/app/universes/[universeId]/audio/page.tsx` - Audio page (~90 lines)

### Frontend API Extensions
- `frontend/src/services/api.ts` - Added video/audio API functions (~230 lines)

### Backend Providers (Phase 4.4)
- `backend/app/providers/base.py` - Base provider class with error handling (~90 lines)
- `backend/app/providers/runway.py` - Runway ML Gen-3 Alpha client (~230 lines)
- `backend/app/providers/elevenlabs.py` - ElevenLabs TTS client (~260 lines)
- `backend/app/providers/openai_whisper.py` - OpenAI Whisper API client (~200 lines)
- `backend/app/api/providers.py` - Health check endpoints (~200 lines)

### Backend Agent Updates
- `backend/app/agents/video_generation_agent.py` - Integrated RunwayProvider
- `backend/app/agents/audio_agent.py` - Integrated ElevenLabs and OpenAI Whisper

### Updated Files
- `frontend/package.json` - Added Three.js dependencies
- `frontend/src/app/universes/[universeId]/page.tsx` - Added media generation links
- `frontend/src/app/universes/[universeId]/elements/[elementId]/page.tsx` - Integrated 3D viewer
- `backend/.env.example` - Added provider API key templates

**Total New Code**: ~2,200+ lines

---

## Technical Notes

### Three.js Integration
- Use dynamic imports to avoid SSR issues
- Canvas must be wrapped in client component
- Environment maps improve visual quality

### Job Polling Strategy
- Poll every 2 seconds while job is processing
- Stop polling on completion or failure
- Show progress indicator during processing

### Provider API Keys
- Store in environment variables
- Never expose in frontend
- Validate before job submission

---

**Prepared by**: Claude Opus 4.5
**Date**: January 5, 2026
