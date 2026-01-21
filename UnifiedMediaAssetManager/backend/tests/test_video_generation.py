"""Integration tests for Video Generation API endpoints."""
import pytest


class TestVideoStrategy:
    """Test video strategy generation endpoint."""

    def test_generate_strategy_success(self, client, auth_headers):
        """Test successful strategy generation."""
        response = client.post(
            "/api/video/strategy",
            json={
                "prompt": "A serene mountain landscape at sunset",
                "mood": 70,
                "platform": "youtube",
                "num_variations": 3
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "mood_category" in data
        assert "variations" in data
        assert len(data["variations"]) <= 3

        # Check variation structure
        variation = data["variations"][0]
        assert "mood_category" in variation
        assert "camera_movement" in variation
        # Variation contains prompt and rationale
        assert "prompt" in variation or "enriched_prompt" in variation
        assert "rationale" in variation or "metadata" in variation

    def test_generate_strategy_minimal(self, client, auth_headers):
        """Test strategy generation with minimal parameters."""
        response = client.post(
            "/api/video/strategy",
            json={
                "prompt": "Test prompt",
                "mood": 50
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "mood_category" in data
        assert "variations" in data


class TestVideoGeneration:
    """Test video generation endpoint."""

    def test_generate_video_success(self, client, auth_headers):
        """Test successful video generation job creation."""
        response = client.post(
            "/api/video/generate",
            json={
                "prompt": "A serene mountain landscape at sunset",
                "mood": 70,
                "aspect_ratio": "16:9",
                "duration": 5
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert data["status"] in ["pending", "processing", "completed"]

    def test_generate_video_with_universe(self, client, auth_headers, sample_universe_data):
        """Test video generation linked to a universe."""
        # First create a universe
        universe_response = client.post(
            "/universes",
            json=sample_universe_data,
            headers=auth_headers
        )
        assert universe_response.status_code == 201
        universe_id = universe_response.json()["id"]

        # Generate video for this universe
        response = client.post(
            "/api/video/generate",
            json={
                "universe_id": universe_id,
                "prompt": "Landscape from Test Universe",
                "mood": 50
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_get_video_job_status(self, client, auth_headers):
        """Test retrieving video job status."""
        # First create a job
        create_response = client.post(
            "/api/video/generate",
            json={
                "prompt": "Test video",
                "mood": 50
            },
            headers=auth_headers
        )
        job_id = create_response.json()["job_id"]

        # Get job status
        response = client.get(f"/api/video/jobs/{job_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == job_id
        assert "status" in data
        assert "prompt" in data
        assert "created_at" in data

    def test_list_video_jobs(self, client, auth_headers):
        """Test listing all video jobs."""
        response = client.get("/api/video/jobs", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)

    def test_list_video_jobs_filtered(self, client, auth_headers):
        """Test listing video jobs with filters."""
        response = client.get(
            "/api/video/jobs",
            params={
                "status": "completed",
                "limit": 5
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data


class TestVideoJobManagement:
    """Test video job management operations."""

    def test_video_job_lifecycle(self, client, auth_headers):
        """Test complete video job lifecycle."""
        # 1. Create job
        create_response = client.post(
            "/api/video/generate",
            json={
                "prompt": "Lifecycle test video",
                "mood": 60,
                "duration": 3
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # 2. Check initial status
        status_response = client.get(f"/api/video/jobs/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] in ["pending", "processing", "completed"]

        # 3. Verify job appears in list
        list_response = client.get("/api/video/jobs", headers=auth_headers)
        job_ids = [job["id"] for job in list_response.json()["jobs"]]
        assert job_id in job_ids


class TestVideoValidation:
    """Test input validation for video endpoints."""

    def test_generate_video_missing_prompt(self, client, auth_headers):
        """Test video generation fails without prompt."""
        response = client.post(
            "/api/video/generate",
            json={
                "mood": 50
            },
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_generate_video_invalid_mood(self, client, auth_headers):
        """Test video generation with out-of-range mood."""
        response = client.post(
            "/api/video/generate",
            json={
                "prompt": "Test",
                "mood": 150  # Should be 0-100
            },
            headers=auth_headers
        )

        # Should either validate or accept and clamp
        assert response.status_code in [200, 422]

    def test_get_nonexistent_job(self, client, auth_headers):
        """Test getting status of non-existent job."""
        response = client.get("/api/video/jobs/nonexistent_job_id", headers=auth_headers)

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
