"""Provider health check and status endpoints."""

import os
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/health", response_model=Dict[str, Any])
async def check_all_providers() -> Dict[str, Any]:
    """
    Check health status of all configured providers.

    Returns status for video, audio TTS, and audio transcription providers.
    """
    results: Dict[str, Any] = {
        "status": "ok",
        "providers": {}
    }

    # Check Runway ML (Video)
    runway_key = os.environ.get("RUNWAY_API_KEY", "")
    runway_configured = bool(runway_key and runway_key != "your-runway-api-key-here")
    if runway_configured:
        try:
            from app.providers.runway import RunwayProvider
            provider = RunwayProvider(api_key=runway_key)
            health = await provider.health_check()
            results["providers"]["runway"] = health
            await provider.close()
        except Exception as e:
            results["providers"]["runway"] = {
                "status": "error",
                "message": str(e)
            }
    else:
        results["providers"]["runway"] = {
            "status": "not_configured",
            "message": "RUNWAY_API_KEY not set"
        }

    # Check ElevenLabs (TTS)
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    elevenlabs_configured = bool(
        elevenlabs_key and elevenlabs_key != "your-elevenlabs-api-key-here"
    )
    if elevenlabs_configured:
        try:
            from app.providers.elevenlabs import ElevenLabsProvider
            provider = ElevenLabsProvider(api_key=elevenlabs_key)
            health = await provider.health_check()
            results["providers"]["elevenlabs"] = health
            await provider.close()
        except Exception as e:
            results["providers"]["elevenlabs"] = {
                "status": "error",
                "message": str(e)
            }
    else:
        results["providers"]["elevenlabs"] = {
            "status": "not_configured",
            "message": "ELEVENLABS_API_KEY not set"
        }

    # Check OpenAI Whisper (Transcription)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    openai_configured = bool(openai_key and openai_key != "your-openai-api-key-here")
    if openai_configured:
        try:
            from app.providers.openai_whisper import OpenAIWhisperProvider
            provider = OpenAIWhisperProvider(api_key=openai_key)
            health = await provider.health_check()
            results["providers"]["openai_whisper"] = health
            await provider.close()
        except Exception as e:
            results["providers"]["openai_whisper"] = {
                "status": "error",
                "message": str(e)
            }
    else:
        results["providers"]["openai_whisper"] = {
            "status": "not_configured",
            "message": "OPENAI_API_KEY not set"
        }

    # Check LTX-2 (Video)
    ltx_key = os.environ.get("LTX_API_KEY", "")
    ltx_configured = bool(ltx_key and ltx_key != "your-ltx-api-key-here")
    if ltx_configured:
        try:
            from app.providers.ltx_provider import LTXProvider
            provider = LTXProvider(api_key=ltx_key)
            health = await provider.health_check()
            results["providers"]["ltx"] = health
            await provider.close()
        except Exception as e:
            results["providers"]["ltx"] = {
                "status": "error",
                "message": str(e)
            }
    else:
        results["providers"]["ltx"] = {
            "status": "not_configured",
            "message": "LTX_API_KEY not set"
        }

    # Set overall status
    statuses = [p.get("status") for p in results["providers"].values()]
    if all(s == "not_configured" for s in statuses):
        results["status"] = "no_providers_configured"
    elif any(s == "error" for s in statuses):
        results["status"] = "partial"

    return results


@router.get("/health/{provider_name}", response_model=Dict[str, Any])
async def check_provider(provider_name: str) -> Dict[str, Any]:
    """
    Check health status of a specific provider.

    Args:
        provider_name: Provider to check (runway, elevenlabs, openai_whisper)
    """
    provider_map = {
        "runway": ("RUNWAY_API_KEY", "app.providers.runway", "RunwayProvider"),
        "ltx": ("LTX_API_KEY", "app.providers.ltx_provider", "LTXProvider"),
        "elevenlabs": ("ELEVENLABS_API_KEY", "app.providers.elevenlabs", "ElevenLabsProvider"),
        "openai_whisper": ("OPENAI_API_KEY", "app.providers.openai_whisper", "OpenAIWhisperProvider"),
    }

    if provider_name not in provider_map:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown provider: {provider_name}. "
                   f"Available: {list(provider_map.keys())}"
        )

    env_var, module_path, class_name = provider_map[provider_name]
    api_key = os.environ.get(env_var, "")

    if not api_key or api_key.startswith("your-"):
        return {
            "provider": provider_name,
            "status": "not_configured",
            "message": f"{env_var} not set"
        }

    try:
        import importlib
        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)
        provider = provider_class(api_key=api_key)
        health = await provider.health_check()
        await provider.close()
        return {
            "provider": provider_name,
            **health
        }
    except Exception as e:
        return {
            "provider": provider_name,
            "status": "error",
            "message": str(e)
        }


@router.get("/status", response_model=Dict[str, Any])
async def get_provider_status() -> Dict[str, Any]:
    """
    Get current provider configuration status.

    Returns which providers are configured and their modes (mock/real).
    """
    video_mode = os.environ.get("VIDEO_PROVIDER", "mock")
    tts_mode = os.environ.get("AUDIO_TTS_PROVIDER", "mock")
    transcribe_mode = os.environ.get("AUDIO_TRANSCRIBE_PROVIDER", "mock")

    runway_key = os.environ.get("RUNWAY_API_KEY", "")
    ltx_key = os.environ.get("LTX_API_KEY", "")
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    # Determine active video provider
    video_provider = video_mode
    if video_mode == "real":
        # Auto-select best available
        if ltx_key and not ltx_key.startswith("your-"):
            video_provider = "ltx"
        elif runway_key and not runway_key.startswith("your-"):
            video_provider = "runway"
        else:
            video_provider = "mock"

    return {
        "video": {
            "mode": video_mode,
            "active_provider": video_provider,
            "providers": {
                "runway": {
                    "configured": bool(runway_key and not runway_key.startswith("your-")),
                },
                "ltx": {
                    "configured": bool(ltx_key and not ltx_key.startswith("your-")),
                },
            },
        },
        "audio_tts": {
            "mode": tts_mode,
            "provider": "elevenlabs" if tts_mode == "elevenlabs" else "mock",
            "configured": bool(elevenlabs_key and not elevenlabs_key.startswith("your-")),
        },
        "audio_transcribe": {
            "mode": transcribe_mode,
            "provider": "whisper" if transcribe_mode == "whisper" else "mock",
            "configured": bool(openai_key and not openai_key.startswith("your-")),
        },
    }


@router.get("/voices", response_model=Dict[str, Any])
async def list_available_voices() -> Dict[str, Any]:
    """
    List available TTS voices.

    Returns ElevenLabs voices if configured, otherwise mock voice list.
    """
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")

    if elevenlabs_key and not elevenlabs_key.startswith("your-"):
        try:
            from app.providers.elevenlabs import ElevenLabsProvider
            provider = ElevenLabsProvider(api_key=elevenlabs_key)
            voices = await provider.list_voices()
            await provider.close()
            return {"voices": voices, "provider": "elevenlabs"}
        except Exception as e:
            logger.warning(f"Failed to fetch voices from ElevenLabs: {e}")

    # Return mock voices
    return {
        "voices": [
            {"id": "default", "name": "Default", "category": "mock"},
            {"id": "alloy", "name": "Alloy", "category": "mock"},
            {"id": "echo", "name": "Echo", "category": "mock"},
            {"id": "fable", "name": "Fable", "category": "mock"},
            {"id": "onyx", "name": "Onyx", "category": "mock"},
            {"id": "nova", "name": "Nova", "category": "mock"},
            {"id": "shimmer", "name": "Shimmer", "category": "mock"},
        ],
        "provider": "mock"
    }
