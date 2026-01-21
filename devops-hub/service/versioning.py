"""
API Versioning support for DevOps Hub.

Provides version negotiation via URL path or headers.
"""

import re
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Current stable version
CURRENT_VERSION = 1

# All supported versions
SUPPORTED_VERSIONS = [1]

# Deprecated but still functional versions
DEPRECATED_VERSIONS: list = []

# Sunset versions (return 410 Gone)
SUNSET_VERSIONS: list = []

# Sunset dates for deprecated versions
SUNSET_DATES = {
    # 0: "2027-01-01T00:00:00Z",  # Example: v0 sunsets on Jan 1, 2027
}


class APIVersionError(Exception):
    """Raised when an unsupported API version is requested."""

    def __init__(self, version: int, message: str):
        self.version = version
        self.message = message
        super().__init__(message)


def parse_version_from_path(path: str) -> Optional[int]:
    """Extract version number from URL path like /api/v1/..."""
    match = re.search(r"/v(\d+)(?:/|$)", path)
    if match:
        return int(match.group(1))
    return None


def parse_version_from_accept(accept_header: str) -> Optional[int]:
    """
    Extract version from Accept header.

    Supports: application/vnd.devops-hub.v1+json
    """
    match = re.search(r"vnd\.devops-hub\.v(\d+)", accept_header)
    if match:
        return int(match.group(1))
    return None


def get_api_version(request: Request) -> int:
    """
    Determine the requested API version from the request.

    Priority:
    1. URL path (/api/v1/...)
    2. Accept header (application/vnd.devops-hub.v1+json)
    3. X-API-Version header
    4. Default to current version
    """
    # Check URL path first
    path_version = parse_version_from_path(request.url.path)
    if path_version is not None:
        return path_version

    # Check Accept header
    accept = request.headers.get("Accept", "")
    accept_version = parse_version_from_accept(accept)
    if accept_version is not None:
        return accept_version

    # Check X-API-Version header
    version_header = request.headers.get("X-API-Version")
    if version_header:
        try:
            return int(version_header)
        except ValueError:
            pass

    # Default to current version
    return CURRENT_VERSION


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API version handling.

    - Validates requested version is supported
    - Adds version headers to responses
    - Adds deprecation warnings for deprecated versions
    - Returns 410 Gone for sunset versions
    """

    async def dispatch(self, request: Request, call_next):
        # Skip versioning for non-API paths
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        # Parse requested version
        version = get_api_version(request)

        # Check if version is sunset (no longer available)
        if version in SUNSET_VERSIONS:
            return JSONResponse(
                status_code=410,
                content={
                    "error": "Gone",
                    "message": f"API version {version} is no longer available",
                    "current_version": CURRENT_VERSION,
                    "documentation": "/docs"
                },
                headers={
                    "X-API-Version": str(CURRENT_VERSION),
                    "X-Deprecated-Version": str(version)
                }
            )

        # Check if version is supported
        if version not in SUPPORTED_VERSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Unsupported API version",
                    "message": f"API version {version} is not supported",
                    "supported_versions": SUPPORTED_VERSIONS,
                    "current_version": CURRENT_VERSION
                },
                headers={"X-API-Version": str(CURRENT_VERSION)}
            )

        # Store version in request state for handlers to access
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version header to response
        response.headers["X-API-Version"] = str(version)

        # Add deprecation headers if version is deprecated
        if version in DEPRECATED_VERSIONS:
            response.headers["Deprecation"] = "true"

            if version in SUNSET_DATES:
                response.headers["Sunset"] = SUNSET_DATES[version]

            response.headers["X-Deprecation-Notice"] = (
                f"API version {version} is deprecated. "
                f"Please migrate to version {CURRENT_VERSION}. "
                f"See /docs for migration guide."
            )

            # Add Link header to successor version
            response.headers["Link"] = (
                f'</api/v{CURRENT_VERSION}>; rel="successor-version"'
            )

        return response


def version_required(min_version: int = 1, max_version: Optional[int] = None):
    """
    Decorator to require a specific API version range.

    Usage:
        @version_required(min_version=2)
        async def v2_only_endpoint():
            ...

        @version_required(min_version=1, max_version=1)
        async def v1_only_endpoint():
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            version = getattr(request.state, "api_version", CURRENT_VERSION)

            if version < min_version:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Version too low",
                        "message": f"This endpoint requires API version {min_version} or higher",
                        "requested_version": version
                    }
                )

            if max_version is not None and version > max_version:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Version too high",
                        "message": f"This endpoint is only available in API version {max_version} or lower",
                        "requested_version": version
                    }
                )

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator


def get_version_info() -> dict:
    """Get information about available API versions."""
    return {
        "current_version": CURRENT_VERSION,
        "supported_versions": SUPPORTED_VERSIONS,
        "deprecated_versions": DEPRECATED_VERSIONS,
        "sunset_versions": SUNSET_VERSIONS,
        "sunset_dates": SUNSET_DATES
    }
