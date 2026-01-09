"""VideoGenerationAgent - Handles video generation via external APIs."""
import logging
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VideoProviderBase:
    """Base class for video generation providers."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def generate_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    async def check_status(self, job_id: str) -> Dict[str, Any]:
        raise NotImplementedError


class MockVideoProvider(VideoProviderBase):
    """Mock provider for testing."""
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.jobs: Dict[str, Dict[str, Any]] = {}

    async def generate_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        job_id = f"mock_{uuid.uuid4().hex[:12]}"
        self.jobs[job_id] = {"status": "processing", "progress": 0}
        return {"job_id": job_id, "status": "processing"}

    async def check_status(self, job_id: str) -> Dict[str, Any]:
        if job_id not in self.jobs:
            return {"status": "failed", "error": "Job not found"}
        job = self.jobs[job_id]
        job["progress"] = min(job["progress"] + 25, 100)
        if job["progress"] >= 100:
            return {
                "status": "completed",
                "video_url": f"https://mock-cdn.example.com/{job_id}.mp4",
                "thumbnail_url": f"https://mock-cdn.example.com/{job_id}.jpg",
                "duration": 5.0,
                "file_size": 2500000
            }
        return {"status": "processing", "progress": job["progress"]}


class RunwayVideoProvider(VideoProviderBase):
    """Runway ML provider wrapper for video generation."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._provider = None

    def _get_provider(self):
        """Lazy-load Runway provider."""
        if self._provider is None:
            from app.providers.runway import RunwayProvider
            self._provider = RunwayProvider(api_key=self.api_key)
        return self._provider

    async def generate_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        provider = self._get_provider()
        result = await provider.generate_video(
            prompt=params.get("prompt", ""),
            duration=params.get("duration", 5),
            aspect_ratio=params.get("aspect_ratio", "16:9"),
            seed=params.get("seed"),
            reference_image_url=params.get("reference_image_url"),
        )
        return {
            "job_id": result.get("job_id"),
            "status": result.get("status", "processing"),
        }

    async def check_status(self, job_id: str) -> Dict[str, Any]:
        provider = self._get_provider()
        result = await provider.get_job_status(job_id)
        return {
            "status": result.get("status"),
            "progress": result.get("progress", 0),
            "video_url": result.get("video_url"),
            "error": result.get("error"),
        }


class VideoGenerationAgent(BaseAgent):
    """Agent for managing video generation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_type="video_generation")
        self.config = config or {}

        # Determine provider mode from environment
        provider_mode = os.environ.get("VIDEO_PROVIDER", "mock").lower()

        # Initialize providers
        self.providers: Dict[str, VideoProviderBase] = {
            "mock": MockVideoProvider(),
        }

        # Add real provider if configured
        runway_key = os.environ.get("RUNWAY_API_KEY")
        if runway_key and runway_key != "your-runway-api-key-here":
            self.providers["runway"] = RunwayVideoProvider(api_key=runway_key)
            logger.info("Runway ML provider initialized")

        # Set default provider based on mode and availability
        if provider_mode == "real" and "runway" in self.providers:
            self.default_provider = "runway"
        else:
            self.default_provider = "mock"

        logger.info(f"VideoGenerationAgent using provider: {self.default_provider}")

    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate video using configured provider."""
        try:
            provider_name = inputs.get("provider", self.default_provider)
            provider = self.providers.get(provider_name, self.providers["mock"])

            result = await provider.generate_video(inputs)
            return {
                "success": True,
                "provider": provider_name,
                "provider_job_id": result["job_id"],
                "status": result["status"]
            }
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def check_job_status(self, provider: str, job_id: str) -> Dict[str, Any]:
        """Check status of a video generation job."""
        try:
            prov = self.providers.get(provider, self.providers["mock"])
            return await prov.check_status(job_id)
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def get_available_providers(self) -> list:
        """Return list of available provider names."""
        return list(self.providers.keys())
