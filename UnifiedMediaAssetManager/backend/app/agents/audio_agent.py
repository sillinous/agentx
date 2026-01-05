"""AudioAgent - Handles audio processing (transcription, TTS, analysis)."""
import logging
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AudioProviderBase:
    """Base class for audio processing providers."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def transcribe(self, audio_url: str) -> Dict[str, Any]:
        """Transcribe audio to text."""
        raise NotImplementedError

    async def text_to_speech(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """Convert text to speech."""
        raise NotImplementedError

    async def analyze_audio(self, audio_url: str) -> Dict[str, Any]:
        """Analyze audio characteristics."""
        raise NotImplementedError


class MockAudioProvider(AudioProviderBase):
    """Mock provider for testing audio operations."""

    async def transcribe(self, audio_url: str) -> Dict[str, Any]:
        """Mock transcription - returns sample text."""
        logger.info(f"Mock transcription of: {audio_url}")
        return {
            "success": True,
            "text": "This is a mock transcription of the audio file. "
                    "In production, this would contain the actual transcribed "
                    "text from Whisper or another service.",
            "language": "en",
            "duration": 30.5,
            "words": [
                {"word": "This", "start": 0.0, "end": 0.2, "confidence": 0.95},
                {"word": "is", "start": 0.2, "end": 0.35, "confidence": 0.98},
                {"word": "a", "start": 0.35, "end": 0.45, "confidence": 0.92},
                {"word": "mock", "start": 0.45, "end": 0.75, "confidence": 0.88}
            ],
            "confidence": 0.93
        }

    async def text_to_speech(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """Mock TTS - returns sample audio URL."""
        logger.info(f"Mock TTS for text: {text[:50]}... with voice: {voice}")
        audio_id = uuid.uuid4().hex[:12]
        return {
            "success": True,
            "audio_url": f"https://mock-cdn.example.com/tts/{audio_id}.mp3",
            "duration": len(text) * 0.05,  # Rough estimate: 0.05s per character
            "voice": voice,
            "format": "mp3",
            "sample_rate": 24000,
            "file_size": len(text) * 1000  # Rough estimate
        }

    async def analyze_audio(self, audio_url: str) -> Dict[str, Any]:
        """Mock audio analysis."""
        logger.info(f"Mock audio analysis of: {audio_url}")
        return {
            "success": True,
            "duration": 45.3,
            "sample_rate": 44100,
            "channels": 2,
            "format": "mp3",
            "bitrate": 320000,
            "tempo": 120,
            "key": "C major",
            "loudness": -14.5,
            "speech_ratio": 0.8,  # 80% speech, 20% music/silence
            "language": "en"
        }


class ElevenLabsTTSProvider(AudioProviderBase):
    """ElevenLabs provider wrapper for text-to-speech."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._provider = None

    def _get_provider(self):
        """Lazy-load ElevenLabs provider."""
        if self._provider is None:
            from app.providers.elevenlabs import ElevenLabsProvider
            self._provider = ElevenLabsProvider(api_key=self.api_key)
        return self._provider

    async def transcribe(self, audio_url: str) -> Dict[str, Any]:
        """ElevenLabs doesn't support transcription, fall back to mock."""
        mock = MockAudioProvider()
        return await mock.transcribe(audio_url)

    async def text_to_speech(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """Generate TTS using ElevenLabs."""
        try:
            provider = self._get_provider()
            result = await provider.text_to_speech(
                text=text,
                voice=voice,
            )

            # Save audio data to a file or return base64
            # For now, we'll return metadata and indicate success
            if result.get("success"):
                audio_id = uuid.uuid4().hex[:12]
                return {
                    "success": True,
                    "audio_data": result.get("audio_data"),  # Raw bytes
                    "audio_url": f"/media/audio/tts/{audio_id}.mp3",
                    "duration": result.get("duration", 0),
                    "voice": result.get("voice_id"),
                    "format": "mp3",
                    "character_count": result.get("character_count", len(text)),
                }
            return result

        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_audio(self, audio_url: str) -> Dict[str, Any]:
        """Use mock for audio analysis."""
        mock = MockAudioProvider()
        return await mock.analyze_audio(audio_url)


class OpenAIWhisperAPIProvider(AudioProviderBase):
    """OpenAI Whisper API provider for transcription."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._provider = None

    def _get_provider(self):
        """Lazy-load OpenAI Whisper provider."""
        if self._provider is None:
            from app.providers.openai_whisper import OpenAIWhisperProvider
            self._provider = OpenAIWhisperProvider(api_key=self.api_key)
        return self._provider

    async def transcribe(self, audio_url: str) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API."""
        try:
            provider = self._get_provider()
            result = await provider.transcribe(audio_url=audio_url)
            return result
        except Exception as e:
            logger.error(f"OpenAI Whisper transcription failed: {e}")
            return {"success": False, "error": str(e)}

    async def text_to_speech(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """Whisper API doesn't support TTS, fall back to mock."""
        mock = MockAudioProvider()
        return await mock.text_to_speech(text, voice)

    async def analyze_audio(self, audio_url: str) -> Dict[str, Any]:
        """Use mock for audio analysis."""
        mock = MockAudioProvider()
        return await mock.analyze_audio(audio_url)


class WhisperProvider(AudioProviderBase):
    """Provider for local Whisper transcription (requires whisper package)."""

    async def transcribe(self, audio_url: str) -> Dict[str, Any]:
        """Transcribe using local Whisper model."""
        try:
            import whisper
            import tempfile
            import httpx

            logger.info(f"Transcribing with local Whisper: {audio_url}")

            # Download audio file
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(audio_url)
                response.raise_for_status()

                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(response.content)
                    temp_path = f.name

            # Load Whisper model (use base or small for speed)
            model = whisper.load_model("base")

            # Transcribe
            result = model.transcribe(temp_path)

            # Clean up temp file
            os.unlink(temp_path)

            return {
                "success": True,
                "text": result["text"],
                "language": result["language"],
                "segments": result.get("segments", []),
                "duration": result.get("duration", 0)
            }

        except ImportError:
            logger.warning("Local Whisper not installed, falling back to mock")
            mock = MockAudioProvider()
            return await mock.transcribe(audio_url)
        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            return {"success": False, "error": str(e)}

    async def text_to_speech(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """Whisper doesn't support TTS, use mock."""
        mock = MockAudioProvider()
        return await mock.text_to_speech(text, voice)

    async def analyze_audio(self, audio_url: str) -> Dict[str, Any]:
        """Basic audio analysis."""
        mock = MockAudioProvider()
        return await mock.analyze_audio(audio_url)


class AudioAgent(BaseAgent):
    """Agent for managing audio processing tasks."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="AudioAgent",
            model_name="whisper-base",
            config=config or {}
        )

        # Determine provider modes from environment
        tts_mode = os.environ.get("AUDIO_TTS_PROVIDER", "mock").lower()
        transcribe_mode = os.environ.get("AUDIO_TRANSCRIBE_PROVIDER", "mock").lower()

        # Initialize base providers
        self.providers: Dict[str, AudioProviderBase] = {
            "mock": MockAudioProvider(),
            "whisper": WhisperProvider(),  # Local Whisper
        }

        # Add ElevenLabs TTS provider if configured
        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
        if elevenlabs_key and elevenlabs_key != "your-elevenlabs-api-key-here":
            self.providers["elevenlabs"] = ElevenLabsTTSProvider(api_key=elevenlabs_key)
            logger.info("ElevenLabs TTS provider initialized")

        # Add OpenAI Whisper API provider if configured
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key and openai_key != "your-openai-api-key-here":
            self.providers["openai_whisper"] = OpenAIWhisperAPIProvider(api_key=openai_key)
            logger.info("OpenAI Whisper API provider initialized")

        # Set default providers based on mode and availability
        if tts_mode == "real" and "elevenlabs" in self.providers:
            self.default_tts_provider = "elevenlabs"
        else:
            self.default_tts_provider = "mock"

        if transcribe_mode == "real" and "openai_whisper" in self.providers:
            self.default_transcribe_provider = "openai_whisper"
        else:
            self.default_transcribe_provider = "mock"

        # Legacy default provider (for backwards compatibility)
        self.default_provider = config.get("default_provider", "mock") if config else "mock"

        logger.info(f"AudioAgent - TTS: {self.default_tts_provider}, "
                    f"Transcribe: {self.default_transcribe_provider}")

    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process audio-related tasks.

        Args:
            inputs: {
                "task": "transcribe" | "tts" | "analyze",
                "audio_url": str (for transcribe/analyze),
                "text": str (for tts),
                "voice": str (optional, for tts),
                "provider": str (optional, override default)
            }
        """
        try:
            task = inputs.get("task")

            if task == "transcribe":
                # Use transcription-specific default provider
                provider_name = inputs.get("provider", self.default_transcribe_provider)
                provider = self.providers.get(provider_name, self.providers["mock"])

                audio_url = inputs.get("audio_url")
                if not audio_url:
                    return {"success": False, "error": "audio_url required for transcription"}

                result = await provider.transcribe(audio_url)
                result["task"] = "transcribe"
                result["provider"] = provider_name
                return result

            elif task == "tts":
                # Use TTS-specific default provider
                provider_name = inputs.get("provider", self.default_tts_provider)
                provider = self.providers.get(provider_name, self.providers["mock"])

                text = inputs.get("text")
                if not text:
                    return {"success": False, "error": "text required for TTS"}

                voice = inputs.get("voice", "default")
                result = await provider.text_to_speech(text, voice)
                result["task"] = "tts"
                result["provider"] = provider_name
                return result

            elif task == "analyze":
                # Analysis uses mock for now
                provider_name = inputs.get("provider", "mock")
                provider = self.providers.get(provider_name, self.providers["mock"])

                audio_url = inputs.get("audio_url")
                if not audio_url:
                    return {"success": False, "error": "audio_url required for analysis"}

                result = await provider.analyze_audio(audio_url)
                result["task"] = "analyze"
                result["provider"] = provider_name
                return result

            else:
                return {
                    "success": False,
                    "error": f"Unknown task: {task}. Supported: transcribe, tts, analyze"
                }

        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return {"success": False, "error": str(e)}

    def get_available_providers(self) -> Dict[str, list]:
        """Return available providers by task type."""
        return {
            "tts": [p for p in self.providers.keys()
                    if p in ("mock", "elevenlabs")],
            "transcribe": [p for p in self.providers.keys()
                           if p in ("mock", "whisper", "openai_whisper")],
            "analyze": ["mock"],
        }

    def get_confidence(self, result: Dict[str, Any]) -> float:
        """Extract confidence score from result."""
        if not result.get("success"):
            return 0.0

        # For transcription, use transcription confidence
        if result.get("task") == "transcribe":
            return result.get("confidence", 0.9)

        # For TTS and analysis, high confidence since they're generation tasks
        return 0.95
