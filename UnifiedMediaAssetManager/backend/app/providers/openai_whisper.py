"""OpenAI Whisper provider for audio transcription."""

import httpx
import logging
import tempfile
import os
from typing import Any, Dict, Optional

from .base import BaseProvider, ProviderError

logger = logging.getLogger(__name__)


class OpenAIWhisperProvider(BaseProvider):
    """
    OpenAI Whisper API client for audio transcription.

    Supports:
    - Audio file transcription
    - Multiple audio formats (mp3, mp4, wav, webm, etc.)
    - Multiple languages (auto-detected or specified)

    API Documentation: https://platform.openai.com/docs/api-reference/audio
    """

    provider_name = "openai"
    BASE_URL = "https://api.openai.com/v1"

    # Supported audio formats
    SUPPORTED_FORMATS = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                },
                timeout=300.0,  # Transcription can take time
            )
        return self._client

    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity."""
        if not self.is_configured:
            return {"status": "error", "message": "API key not configured"}

        try:
            client = await self._get_client()
            # List models to verify API key
            response = await client.get("/models")
            if response.status_code == 200:
                return {"status": "ok", "provider": self.provider_name}
            elif response.status_code == 401:
                return {"status": "error", "message": "Invalid API key"}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def transcribe(
        self,
        audio_url: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "verbose_json",
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using OpenAI Whisper API.

        Args:
            audio_url: URL of the audio file to transcribe
            language: ISO 639-1 language code (optional, auto-detected if not provided)
            prompt: Optional prompt to guide transcription
            response_format: Output format (json, text, srt, verbose_json, vtt)
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Dict with transcription text, language, duration, and segments
        """
        self.validate_config()

        try:
            # Download audio file
            logger.info(f"Downloading audio from: {audio_url}")
            async with httpx.AsyncClient(timeout=120.0) as download_client:
                response = await download_client.get(audio_url)
                response.raise_for_status()
                audio_data = response.content

            # Check file size
            if len(audio_data) > self.MAX_FILE_SIZE:
                raise ProviderError(
                    f"Audio file too large ({len(audio_data)} bytes). Max: {self.MAX_FILE_SIZE} bytes",
                    self.provider_name
                )

            # Determine file extension from URL or default to mp3
            ext = audio_url.split(".")[-1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                ext = "mp3"

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                # Prepare form data
                files = {
                    "file": (f"audio.{ext}", open(temp_path, "rb"), f"audio/{ext}"),
                }
                data = {
                    "model": "whisper-1",
                    "response_format": response_format,
                    "temperature": str(temperature),
                }
                if language:
                    data["language"] = language
                if prompt:
                    data["prompt"] = prompt

                client = await self._get_client()
                logger.info("Sending transcription request to OpenAI...")

                response = await client.post(
                    "/audio/transcriptions",
                    files=files,
                    data=data,
                )

                if response.status_code == 200:
                    result = response.json()

                    return {
                        "success": True,
                        "provider": self.provider_name,
                        "text": result.get("text", ""),
                        "language": result.get("language", language or "auto"),
                        "duration": result.get("duration", 0),
                        "segments": result.get("segments", []),
                        "words": result.get("words", []),
                    }
                elif response.status_code == 401:
                    raise ProviderError("Invalid API key", self.provider_name)
                elif response.status_code == 413:
                    raise ProviderError("Audio file too large", self.provider_name)
                else:
                    error_data = response.json() if response.content else {}
                    raise ProviderError(
                        f"Transcription failed: {error_data.get('error', {}).get('message', response.status_code)}",
                        self.provider_name
                    )

            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except ProviderError:
            raise
        except Exception as e:
            self._handle_error(e, "transcribe audio")

    async def translate(
        self,
        audio_url: str,
        prompt: Optional[str] = None,
        response_format: str = "verbose_json",
    ) -> Dict[str, Any]:
        """
        Translate audio to English using OpenAI Whisper API.

        Args:
            audio_url: URL of the audio file to translate
            prompt: Optional prompt to guide translation
            response_format: Output format

        Returns:
            Dict with translated text in English
        """
        self.validate_config()

        try:
            # Download audio file
            async with httpx.AsyncClient(timeout=120.0) as download_client:
                response = await download_client.get(audio_url)
                response.raise_for_status()
                audio_data = response.content

            ext = audio_url.split(".")[-1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                ext = "mp3"

            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                files = {
                    "file": (f"audio.{ext}", open(temp_path, "rb"), f"audio/{ext}"),
                }
                data = {
                    "model": "whisper-1",
                    "response_format": response_format,
                }
                if prompt:
                    data["prompt"] = prompt

                client = await self._get_client()

                response = await client.post(
                    "/audio/translations",
                    files=files,
                    data=data,
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "provider": self.provider_name,
                        "text": result.get("text", ""),
                        "language": "en",  # Translations are always to English
                        "duration": result.get("duration", 0),
                    }
                else:
                    error_data = response.json() if response.content else {}
                    raise ProviderError(
                        f"Translation failed: {error_data.get('error', {}).get('message', response.status_code)}",
                        self.provider_name
                    )

            finally:
                os.unlink(temp_path)

        except ProviderError:
            raise
        except Exception as e:
            self._handle_error(e, "translate audio")

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
