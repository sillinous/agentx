"""Video storage service for managing generated video files."""
import os
import logging
import hashlib
import uuid
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import requests
import httpx

logger = logging.getLogger(__name__)

class VideoStorageService:
    """Manages local storage and retrieval of video files."""

    def __init__(self, base_path: str = "./media/videos"):
        self.base_path = Path(base_path)
        self.thumbnails_path = self.base_path / "thumbnails"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"VideoStorageService initialized: {self.base_path}")

    def generate_path(self, universe_id: str, video_id: str, extension: str = "mp4") -> Path:
        """Generate organized storage path: media/videos/{universe_id}/{video_id}.mp4"""
        universe_dir = self.base_path / universe_id
        universe_dir.mkdir(parents=True, exist_ok=True)
        return universe_dir / f"{video_id}.{extension}"

    async def download_from_url(self, url: str, universe_id: str, video_id: str) -> Dict[str, Any]:
        """Download video from external URL and save locally."""
        try:
            logger.info(f"Downloading video from: {url}")

            # Download with httpx for async support
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                video_data = response.content

            # Save video
            result = self.save_video(video_data, universe_id, video_id)

            if result["success"]:
                # Generate thumbnail
                thumbnail_path = self.generate_thumbnail(result["file_path"], video_id)
                if thumbnail_path:
                    result["thumbnail_path"] = str(thumbnail_path)
                    result["thumbnail_url"] = f"/media/videos/thumbnails/{Path(thumbnail_path).name}"

                # Get video metadata
                metadata = self.get_video_metadata(result["file_path"])
                result.update(metadata)

            return result

        except Exception as e:
            logger.error(f"Failed to download video from {url}: {e}")
            return {"success": False, "error": str(e)}

    def save_video(self, video_data: bytes, universe_id: str, video_id: str) -> Dict[str, Any]:
        """Save video file and return metadata."""
        try:
            file_path = self.generate_path(universe_id, video_id)

            # Write video data
            with open(file_path, 'wb') as f:
                f.write(video_data)

            # Calculate file info
            file_size = os.path.getsize(file_path)
            checksum = hashlib.md5(video_data).hexdigest()

            logger.info(f"Saved video: {file_path} ({file_size} bytes)")

            return {
                "success": True,
                "file_path": str(file_path),
                "file_size": file_size,
                "checksum": checksum,
                "public_url": f"/media/videos/{universe_id}/{video_id}.mp4",
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to save video: {e}")
            return {"success": False, "error": str(e)}

    def generate_thumbnail(self, video_path: str, video_id: str) -> Optional[str]:
        """Generate thumbnail image from video using ffmpeg."""
        try:
            thumbnail_path = self.thumbnails_path / f"{video_id}.jpg"

            # Use ffmpeg to extract frame at 1 second
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-ss", "00:00:01.000",
                "-vframes", "1",
                "-y",  # Overwrite output file
                str(thumbnail_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and thumbnail_path.exists():
                logger.info(f"Generated thumbnail: {thumbnail_path}")
                return str(thumbnail_path)
            else:
                logger.warning(f"ffmpeg failed: {result.stderr}")
                return None

        except FileNotFoundError:
            logger.warning("ffmpeg not found - thumbnails disabled")
            return None
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract video metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration,size:stream=width,height,codec_name",
                "-of", "json",
                str(video_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)

                # Extract relevant metadata
                metadata = {}
                if "format" in data:
                    metadata["duration"] = float(data["format"].get("duration", 0))
                if "streams" in data and len(data["streams"]) > 0:
                    stream = data["streams"][0]
                    metadata["width"] = stream.get("width")
                    metadata["height"] = stream.get("height")
                    metadata["codec"] = stream.get("codec_name")

                return metadata
        except Exception as e:
            logger.warning(f"Failed to get video metadata: {e}")

        return {}

    def get_video_path(self, universe_id: str, video_id: str) -> Optional[Path]:
        """Get path to video file if it exists."""
        file_path = self.generate_path(universe_id, video_id)
        return file_path if file_path.exists() else None

    def delete_video(self, universe_id: str, video_id: str) -> bool:
        """Delete video file and thumbnail."""
        try:
            # Delete video
            file_path = self.generate_path(universe_id, video_id)
            deleted = False
            if file_path.exists():
                os.remove(file_path)
                logger.info(f"Deleted video: {file_path}")
                deleted = True

            # Delete thumbnail
            thumbnail_path = self.thumbnails_path / f"{video_id}.jpg"
            if thumbnail_path.exists():
                os.remove(thumbnail_path)
                logger.info(f"Deleted thumbnail: {thumbnail_path}")

            return deleted
        except Exception as e:
            logger.error(f"Failed to delete video: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_size = 0
        file_count = 0

        for path in self.base_path.rglob("*.mp4"):
            total_size += os.path.getsize(path)
            file_count += 1

        return {
            "total_files": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "base_path": str(self.base_path)
        }


# Global instance
_video_storage = None

def get_video_storage() -> VideoStorageService:
    """Get singleton instance of VideoStorageService."""
    global _video_storage
    if _video_storage is None:
        _video_storage = VideoStorageService()
    return _video_storage
