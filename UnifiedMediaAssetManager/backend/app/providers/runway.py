"""Runway ML provider for AI video generation."""

import asyncio
import httpx
import logging
from typing import Any, Dict, Optional

from .base import BaseProvider, ProviderError

logger = logging.getLogger(__name__)


class RunwayProvider(BaseProvider):
    """
    Runway ML API client for video generation.

    Supports:
    - Text-to-video generation (Gen-3 Alpha)
    - Image-to-video generation
    - Job status polling

    API Documentation: https://docs.runwayml.com/
    """

    provider_name = "runway"
    BASE_URL = "https://api.runwayml.com/v1"

    # Generation parameters
    DEFAULT_DURATION = 5  # seconds
    DEFAULT_ASPECT_RATIO = "16:9"
    SUPPORTED_ASPECT_RATIOS = ["16:9", "9:16", "1:1"]

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
                    "Content-Type": "application/json",
                    "X-Runway-Version": "2024-11-06",
                },
                timeout=60.0,
            )
        return self._client

    async def health_check(self) -> Dict[str, Any]:
        """Check Runway API connectivity."""
        if not self.is_configured:
            return {"status": "error", "message": "API key not configured"}

        try:
            client = await self._get_client()
            # Use a lightweight endpoint to verify connectivity
            response = await client.get("/tasks")
            if response.status_code == 200:
                return {"status": "ok", "provider": self.provider_name}
            elif response.status_code == 401:
                return {"status": "error", "message": "Invalid API key"}
            else:
                return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def generate_video(
        self,
        prompt: str,
        duration: int = DEFAULT_DURATION,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        seed: Optional[int] = None,
        reference_image_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a video using Runway Gen-3 Alpha.

        Args:
            prompt: Text description of the video to generate
            duration: Video duration in seconds (5 or 10)
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)
            seed: Optional seed for reproducibility
            reference_image_url: Optional image URL for image-to-video

        Returns:
            Dict with job_id and initial status
        """
        self.validate_config()

        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            raise ProviderError(
                f"Unsupported aspect ratio: {aspect_ratio}. "
                f"Supported: {self.SUPPORTED_ASPECT_RATIOS}",
                self.provider_name
            )

        try:
            client = await self._get_client()

            # Build request payload
            payload = {
                "promptText": prompt,
                "model": "gen3a_turbo",  # Gen-3 Alpha Turbo
                "duration": duration,
                "ratio": aspect_ratio.replace(":", "_"),  # Convert 16:9 to 16_9
                "watermark": False,
            }

            if seed is not None:
                payload["seed"] = seed

            if reference_image_url:
                payload["promptImage"] = reference_image_url

            logger.info(f"Starting Runway video generation: {prompt[:50]}...")

            response = await client.post("/image_to_video", json=payload)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "provider": self.provider_name,
                    "job_id": data.get("id"),
                    "status": "processing",
                }
            elif response.status_code == 402:
                raise ProviderError(
                    "Insufficient credits. Please add credits to your Runway account.",
                    self.provider_name
                )
            else:
                error_data = response.json() if response.content else {}
                raise ProviderError(
                    f"Generation failed: {error_data.get('error', response.status_code)}",
                    self.provider_name,
                    {"status_code": response.status_code, "response": error_data}
                )

        except ProviderError:
            raise
        except Exception as e:
            self._handle_error(e, "generate video")

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation job.

        Args:
            job_id: The Runway task ID

        Returns:
            Dict with status, progress, and output URL if completed
        """
        self.validate_config()

        try:
            client = await self._get_client()
            response = await client.get(f"/tasks/{job_id}")

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")

                result = {
                    "job_id": job_id,
                    "status": status,
                    "progress": data.get("progress", 0),
                }

                if status == "SUCCEEDED":
                    result["status"] = "completed"
                    result["video_url"] = data.get("output", [None])[0]
                elif status == "FAILED":
                    result["status"] = "failed"
                    result["error"] = data.get("failure", "Unknown error")
                elif status == "RUNNING":
                    result["status"] = "processing"

                return result
            else:
                raise ProviderError(
                    f"Failed to get job status: HTTP {response.status_code}",
                    self.provider_name
                )

        except ProviderError:
            raise
        except Exception as e:
            self._handle_error(e, "get job status")

    async def wait_for_completion(
        self,
        job_id: str,
        poll_interval: float = 5.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Wait for a video generation job to complete.

        Args:
            job_id: The Runway task ID
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait

        Returns:
            Final job status with video URL if successful
        """
        elapsed = 0.0

        while elapsed < timeout:
            status = await self.get_job_status(job_id)

            if status["status"] in ("completed", "failed"):
                return status

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            logger.debug(f"Runway job {job_id}: {status.get('progress', 0)}% complete")

        raise ProviderError(
            f"Job {job_id} timed out after {timeout} seconds",
            self.provider_name
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
