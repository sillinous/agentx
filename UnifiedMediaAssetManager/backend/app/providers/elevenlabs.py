"""ElevenLabs provider for text-to-speech audio generation."""

import httpx
import logging
from typing import Any, Dict, List, Optional

from .base import BaseProvider, ProviderError

logger = logging.getLogger(__name__)


class ElevenLabsProvider(BaseProvider):
    """
    ElevenLabs API client for text-to-speech generation.

    Supports:
    - Text-to-speech with multiple voices
    - Voice listing and selection
    - Multiple audio formats (mp3, wav, ogg)

    API Documentation: https://elevenlabs.io/docs/api-reference
    """

    provider_name = "elevenlabs"
    BASE_URL = "https://api.elevenlabs.io/v1"

    # Default voice settings
    DEFAULT_MODEL = "eleven_multilingual_v2"
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel - default voice

    # Predefined voice mappings
    VOICE_MAPPING = {
        "default": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "alloy": "21m00Tcm4TlvDq8ikWAM",    # Map to Rachel
        "echo": "VR6AewLTigWG4xSOukaG",     # Arnold - male
        "fable": "jBpfuIE2acCO8z3wKNLl",    # Gigi - British
        "onyx": "ODq5zmih8GrVes37Dizd",     # Patrick - deep male
        "nova": "EXAVITQu4vr4xnSDxMaL",     # Bella - female
        "shimmer": "MF3mGyEYCl7XYWbV9V6O",  # Elli - soft female
    }

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self._client: Optional[httpx.AsyncClient] = None
        self._voices_cache: Optional[List[Dict]] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "xi-api-key": self._api_key,
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def health_check(self) -> Dict[str, Any]:
        """Check ElevenLabs API connectivity."""
        if not self.is_configured:
            return {"status": "error", "message": "API key not configured"}

        try:
            client = await self._get_client()
            response = await client.get("/user")
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok",
                    "provider": self.provider_name,
                    "subscription": data.get("subscription", {}).get("tier"),
                }
            elif response.status_code == 401:
                return {"status": "error", "message": "Invalid API key"}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def list_voices(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get available voices from ElevenLabs.

        Args:
            refresh: Force refresh the cache

        Returns:
            List of voice dictionaries with id, name, and labels
        """
        if self._voices_cache and not refresh:
            return self._voices_cache

        self.validate_config()

        try:
            client = await self._get_client()
            response = await client.get("/voices")

            if response.status_code == 200:
                data = response.json()
                self._voices_cache = [
                    {
                        "id": voice["voice_id"],
                        "name": voice["name"],
                        "category": voice.get("category", "custom"),
                        "labels": voice.get("labels", {}),
                        "preview_url": voice.get("preview_url"),
                    }
                    for voice in data.get("voices", [])
                ]
                return self._voices_cache
            else:
                raise ProviderError(
                    f"Failed to list voices: HTTP {response.status_code}",
                    self.provider_name
                )

        except ProviderError:
            raise
        except Exception as e:
            self._handle_error(e, "list voices")

    def _resolve_voice_id(self, voice: str) -> str:
        """Resolve voice name/alias to voice ID."""
        # Check if it's already a voice ID (usually 20+ chars)
        if len(voice) > 15:
            return voice

        # Check mapping
        voice_lower = voice.lower()
        if voice_lower in self.VOICE_MAPPING:
            return self.VOICE_MAPPING[voice_lower]

        # Default fallback
        logger.warning(f"Unknown voice '{voice}', using default")
        return self.DEFAULT_VOICE_ID

    async def text_to_speech(
        self,
        text: str,
        voice: str = "default",
        model: str = DEFAULT_MODEL,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        output_format: str = "mp3_44100_128",
    ) -> Dict[str, Any]:
        """
        Convert text to speech audio.

        Args:
            text: The text to convert to speech
            voice: Voice ID or alias (default, alloy, echo, etc.)
            model: TTS model to use
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice similarity boost (0.0-1.0)
            style: Style exaggeration (0.0-1.0)
            output_format: Audio format (mp3_44100_128, pcm_16000, etc.)

        Returns:
            Dict with audio_data (bytes), content_type, and duration estimate
        """
        self.validate_config()

        voice_id = self._resolve_voice_id(voice)

        try:
            client = await self._get_client()

            payload = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": True,
                }
            }

            logger.info(f"Generating TTS with voice {voice_id}: {text[:50]}...")

            response = await client.post(
                f"/text-to-speech/{voice_id}",
                json=payload,
                headers={"Accept": f"audio/{output_format.split('_')[0]}"},
            )

            if response.status_code == 200:
                audio_data = response.content
                content_type = response.headers.get("content-type", "audio/mpeg")

                # Estimate duration (rough: ~150 words per minute)
                word_count = len(text.split())
                estimated_duration = (word_count / 150) * 60

                return {
                    "success": True,
                    "provider": self.provider_name,
                    "audio_data": audio_data,
                    "content_type": content_type,
                    "duration": estimated_duration,
                    "voice_id": voice_id,
                    "character_count": len(text),
                }
            elif response.status_code == 401:
                raise ProviderError("Invalid API key", self.provider_name)
            elif response.status_code == 422:
                error_data = response.json()
                raise ProviderError(
                    f"Invalid request: {error_data.get('detail', 'Unknown error')}",
                    self.provider_name
                )
            else:
                raise ProviderError(
                    f"TTS generation failed: HTTP {response.status_code}",
                    self.provider_name
                )

        except ProviderError:
            raise
        except Exception as e:
            self._handle_error(e, "generate TTS")

    async def get_usage(self) -> Dict[str, Any]:
        """
        Get current API usage statistics.

        Returns:
            Dict with character usage and limits
        """
        self.validate_config()

        try:
            client = await self._get_client()
            response = await client.get("/user/subscription")

            if response.status_code == 200:
                data = response.json()
                return {
                    "character_count": data.get("character_count", 0),
                    "character_limit": data.get("character_limit", 0),
                    "tier": data.get("tier"),
                    "next_reset": data.get("next_character_count_reset_unix"),
                }
            else:
                raise ProviderError(
                    f"Failed to get usage: HTTP {response.status_code}",
                    self.provider_name
                )

        except ProviderError:
            raise
        except Exception as e:
            self._handle_error(e, "get usage")

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
