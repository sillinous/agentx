import os
import uuid
from pathlib import Path
from typing import Tuple

import requests
from PIL import Image
from io import BytesIO

ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = ROOT / "media"
IMAGES_DIR = MEDIA_DIR / "images"

# Storage backend selection: 'local' (default) or 's3'
MEDIA_STORAGE = os.environ.get("MEDIA_STORAGE", "local").lower()

# S3 configuration (for MEDIA_STORAGE=s3)
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT")  # optional, for S3-compatible services
S3_PUBLIC_URL_BASE = os.environ.get("S3_PUBLIC_URL_BASE")  # optional override for public URLs


def ensure_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _s3_client():
    try:
        import boto3
    except Exception:
        raise RuntimeError("boto3 is required for S3 storage backend")
    client_kwargs = {}
    if S3_ENDPOINT:
        client_kwargs["endpoint_url"] = S3_ENDPOINT
    return boto3.client("s3", region_name=S3_REGION, **client_kwargs)


def _s3_public_url_for_key(key: str) -> str:
    if S3_PUBLIC_URL_BASE:
        return f"{S3_PUBLIC_URL_BASE.rstrip('/')}/{key}"
    if S3_ENDPOINT:
        base = S3_ENDPOINT.rstrip('/')
        return f"{base}/{S3_BUCKET}/{key}"
    # Default AWS S3 URL
    return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"


def _upload_bytes_to_s3(data: bytes, key: str, content_type: str = "image/png") -> str:
    client = _s3_client()
    extra_args = {"ACL": "public-read", "ContentType": content_type}
    client.put_object(Bucket=S3_BUCKET, Key=key, Body=data, **extra_args)
    return _s3_public_url_for_key(key)


def save_image_bytes(data: bytes, filename: str) -> Path:
    """Save image bytes using configured backend. Returns filesystem path for local, or a Path-like for compatibility."""
    if MEDIA_STORAGE == "s3":
        # upload to s3 under images/<filename>
        key = f"images/{filename}"
        # attempt to infer content type
        content_type = "image/png"
        if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
            content_type = "image/jpeg"
        public_url = _upload_bytes_to_s3(data, key, content_type=content_type)
        return Path(public_url)

    # local filesystem
    ensure_dirs()
    out_path = IMAGES_DIR / filename
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path


def download_and_save(url: str) -> Tuple[Path, str]:
    """Download an image from `url`, save it (local or S3), return (path, public_url)."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    # Determine file extension from content-type or url
    content_type = resp.headers.get("content-type", "image/png")
    if "jpeg" in content_type:
        ext = "jpg"
    elif "png" in content_type:
        ext = "png"
    else:
        ext = url.split(".")[-1].split("?")[0] or "png"

    filename = f"generated-{uuid.uuid4()}.{ext}"

    if MEDIA_STORAGE == "s3":
        key = f"images/{filename}"
        public_url = _upload_bytes_to_s3(resp.content, key, content_type=content_type)
        return Path(public_url), public_url

    # Local storage path
    out_path = save_image_bytes(resp.content, filename)

    # Optionally create a small thumbnail for UI
    try:
        img = Image.open(BytesIO(resp.content))
        img.thumbnail((256, 256))
        thumb_name = f"thumb-{out_path.name}"
        thumb_path = IMAGES_DIR / thumb_name
        img.save(thumb_path)
    except Exception:
        thumb_path = None

    # Return the filesystem path and the relative URL path to be served by StaticFiles
    relative_url = f"/media/images/{out_path.name}"
    return out_path, relative_url


def save_uploaded_file(upload_bytes: bytes, filename: str = None) -> Tuple[Path, str]:
    """Save raw bytes from an upload to media/images and return (path, relative_url)."""
    ensure_dirs()
    if not filename:
        filename = f"uploaded-{uuid.uuid4()}.png"
    out_path = save_image_bytes(upload_bytes, filename)

    # create thumbnail
    try:
        img = Image.open(BytesIO(upload_bytes))
        img.thumbnail((256, 256))
        thumb_name = f"thumb-{out_path.name}"
        thumb_path = IMAGES_DIR / thumb_name
        img.save(thumb_path)
    except Exception:
        thumb_path = None

    relative_url = f"/media/images/{out_path.name}"
    return out_path, relative_url
