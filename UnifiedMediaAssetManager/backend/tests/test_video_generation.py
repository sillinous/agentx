"""Integration tests for Video Generation API endpoints."""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)


class TestVideoStrategy:
    """Test video strategy generation endpoint."""

    def test_generate_strategy_success(self):
        """Test successful strategy generation."""
        response = client.post(
            "/api/video/strategy",
            json={
                "prompt": "A serene mountain landscape at sunset",
                "mood": 70,
                "platform": "youtube",
                "num_variations": 3
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "mood_category" in data
        assert "variations" in data
        assert len(data["variations"]) <= 3

        # Check variation structure
        variation = data["variations"][0]
        assert "mood_category" in variation
        assert "camera_movement" in variation
        assert "enriched_prompt" in variation
        assert "rationale" in variation

    def test_generate_strategy_minimal(self):
        """Test strategy generation with minimal parameters."""
        response = client.post(
            "/api/video/strategy",
            json={
                "prompt": "Test prompt",
                "mood": 50
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestVideoGeneration:
    """Test video generation endpoint."""

    def test_generate_video_success(self):
        """Test successful video generation job creation."""
        response = client.post(
            "/api/video/generate",
            json={
                "prompt": "A serene mountain landscape at sunset",
                "mood": 70,
                "aspect_ratio": "16:9",
                "duration": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert data["status"] in ["pending", "processing"]
        assert "strategy" in data

        # Store job_id for next test
        return data["job_id"]

    def test_generate_video_with_universe(self):
        """Test video generation linked to a universe."""
        # First create a universe
        universe_response = client.post(
            "/api/universes",
            json={
                "name": "Test Universe for Video",
                "description": "Test universe"
            }
        )
        universe_id = universe_response.json()["id"]

        # Generate video for this universe
        response = client.post(
            "/api/video/generate",
            json={
                "universe_id": universe_id,
                "prompt": "Landscape from Test Universe",
                "mood": 50
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_get_video_job_status(self):
        """Test retrieving video job status."""
        # First create a job
        create_response = client.post(
            "/api/video/generate",
            json={
                "prompt": "Test video",
                "mood": 50
            }
        )
        job_id = create_response.json()["job_id"]

        # Get job status
        response = client.get(f"/api/video/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == job_id
        assert "status" in data
        assert "prompt" in data
        assert "created_at" in data

    def test_list_video_jobs(self):
        """Test listing all video jobs."""
        response = client.get("/api/video/jobs")

        assert response.status_code == 200
        data = response.json()

        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)

    def test_list_video_jobs_filtered(self):
        """Test listing video jobs with filters."""
        response = client.get(
            "/api/video/jobs",
            params={
                "status": "completed",
                "limit": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data


class TestVideoJobManagement:
    """Test video job management operations."""

    def test_video_job_lifecycle(self):
        """Test complete video job lifecycle."""
        # 1. Create job
        create_response = client.post(
            "/api/video/generate",
            json={
                "prompt": "Lifecycle test video",
                "mood": 60,
                "duration": 3
            }
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # 2. Check initial status
        status_response = client.get(f"/api/video/jobs/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] in ["pending", "processing", "completed"]

        # 3. Verify job appears in list
        list_response = client.get("/api/video/jobs")
        job_ids = [job["id"] for job in list_response.json()["jobs"]]
        assert job_id in job_ids


class TestVideoValidation:
    """Test input validation for video endpoints."""

    def test_generate_video_missing_prompt(self):
        """Test video generation fails without prompt."""
        response = client.post(
            "/api/video/generate",
            json={
                "mood": 50
            }
        )

        assert response.status_code == 422  # Validation error

    def test_generate_video_invalid_mood(self):
        """Test video generation with out-of-range mood."""
        response = client.post(
            "/api/video/generate",
            json={
                "prompt": "Test",
                "mood": 150  # Should be 0-100
            }
        )

        # Should either validate or accept and clamp
        assert response.status_code in [200, 422]

    def test_get_nonexistent_job(self):
        """Test getting status of non-existent job."""
        response = client.get("/api/video/jobs/nonexistent_job_id")

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
