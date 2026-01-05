"""Integration tests for Audio Processing API endpoints."""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)


class TestTextToSpeech:
    """Test text-to-speech endpoint."""

    def test_tts_success(self):
        """Test successful TTS conversion."""
        response = client.post(
            "/api/audio/tts",
            json={
                "text": "Hello, this is a test of the text to speech system.",
                "voice": "default",
                "provider": "mock"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert "result" in data

        result = data["result"]
        assert result["success"] is True
        assert "audio_url" in result or "error" in result

    def test_tts_different_voices(self):
        """Test TTS with different voice options."""
        voices = ["default", "male", "female", "child"]

        for voice in voices:
            response = client.post(
                "/api/audio/tts",
                json={
                    "text": f"Testing {voice} voice",
                    "voice": voice,
                    "provider": "mock"
                }
            )

            assert response.status_code == 200

    def test_tts_with_universe(self):
        """Test TTS linked to a universe."""
        # Create universe first
        universe_response = client.post(
            "/api/universes",
            json={
                "name": "Audio Test Universe",
                "description": "For audio testing"
            }
        )
        universe_id = universe_response.json()["id"]

        # Generate TTS
        response = client.post(
            "/api/audio/tts",
            json={
                "universe_id": universe_id,
                "text": "Audio for test universe",
                "voice": "default",
                "provider": "mock"
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] in ["processing", "completed"]


class TestAudioTranscription:
    """Test audio transcription endpoint."""

    def test_transcribe_success(self):
        """Test successful audio transcription."""
        response = client.post(
            "/api/audio/transcribe",
            json={
                "audio_url": "https://example.com/sample.mp3",
                "provider": "mock"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert "result" in data

        result = data["result"]
        assert result["success"] is True
        assert "text" in result or "error" in result

    def test_transcribe_with_universe(self):
        """Test transcription linked to a universe."""
        # Create universe
        universe_response = client.post(
            "/api/universes",
            json={
                "name": "Transcription Test Universe",
                "description": "For transcription testing"
            }
        )
        universe_id = universe_response.json()["id"]

        # Transcribe audio
        response = client.post(
            "/api/audio/transcribe",
            json={
                "universe_id": universe_id,
                "audio_url": "https://example.com/test.mp3",
                "provider": "mock"
            }
        )

        assert response.status_code == 200


class TestAudioAnalysis:
    """Test audio analysis endpoint."""

    def test_analyze_success(self):
        """Test successful audio analysis."""
        response = client.post(
            "/api/audio/analyze",
            json={
                "audio_url": "https://example.com/sample.mp3",
                "provider": "mock"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        # Mock should return sample analysis data
        assert "duration" in data or "error" in data

    def test_analyze_different_formats(self):
        """Test audio analysis with different file formats."""
        formats = ["mp3", "wav", "flac", "m4a"]

        for fmt in formats:
            response = client.post(
                "/api/audio/analyze",
                json={
                    "audio_url": f"https://example.com/sample.{fmt}",
                    "provider": "mock"
                }
            )

            assert response.status_code == 200


class TestAudioValidation:
    """Test input validation for audio endpoints."""

    def test_tts_missing_text(self):
        """Test TTS fails without text."""
        response = client.post(
            "/api/audio/tts",
            json={
                "voice": "default",
                "provider": "mock"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_transcribe_missing_url(self):
        """Test transcription fails without audio URL."""
        response = client.post(
            "/api/audio/transcribe",
            json={
                "provider": "mock"
            }
        )

        assert response.status_code == 422

    def test_analyze_invalid_url(self):
        """Test analysis with invalid URL format."""
        response = client.post(
            "/api/audio/analyze",
            json={
                "audio_url": "not-a-valid-url",
                "provider": "mock"
            }
        )

        # Should either validate URL or accept and fail gracefully
        assert response.status_code in [200, 422]


class TestAudioProviders:
    """Test different audio provider options."""

    def test_mock_provider(self):
        """Test mock provider for all operations."""
        # TTS
        tts_response = client.post(
            "/api/audio/tts",
            json={"text": "Test", "provider": "mock"}
        )
        assert tts_response.status_code == 200

        # Transcribe
        transcribe_response = client.post(
            "/api/audio/transcribe",
            json={"audio_url": "https://example.com/test.mp3", "provider": "mock"}
        )
        assert transcribe_response.status_code == 200

        # Analyze
        analyze_response = client.post(
            "/api/audio/analyze",
            json={"audio_url": "https://example.com/test.mp3", "provider": "mock"}
        )
        assert analyze_response.status_code == 200


class TestAudioJobLifecycle:
    """Test complete audio job lifecycle."""

    def test_tts_job_lifecycle(self):
        """Test TTS job from creation to completion."""
        # 1. Create TTS job
        create_response = client.post(
            "/api/audio/tts",
            json={
                "text": "Lifecycle test audio",
                "voice": "default",
                "provider": "mock"
            }
        )

        assert create_response.status_code == 200
        data = create_response.json()

        # 2. Verify job was created
        assert "job_id" in data
        job_id = data["job_id"]

        # 3. Check result
        assert "result" in data
        result = data["result"]
        assert result["success"] is True

    def test_transcription_job_lifecycle(self):
        """Test transcription job from creation to completion."""
        # 1. Create transcription job
        create_response = client.post(
            "/api/audio/transcribe",
            json={
                "audio_url": "https://example.com/lifecycle-test.mp3",
                "provider": "mock"
            }
        )

        assert create_response.status_code == 200
        data = create_response.json()

        # 2. Verify job completion
        assert data["status"] in ["processing", "completed"]
        assert "result" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
