"""
Rate Limiter - API rate limiting with Redis backend and in-memory fallback.

Provides configurable rate limiting for API endpoints with graceful degradation
when Redis is unavailable.
"""

import os
import time
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = False
    requests_per_window: int = 100
    window_seconds: int = 60
    execute_requests_per_window: int = 20
    execute_window_seconds: int = 60

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """Create configuration from environment variables."""
        return cls(
            enabled=os.environ.get("RATE_LIMIT_ENABLED", "false").lower() == "true",
            requests_per_window=int(os.environ.get("RATE_LIMIT_REQUESTS", "100")),
            window_seconds=int(os.environ.get("RATE_LIMIT_WINDOW", "60")),
            execute_requests_per_window=int(os.environ.get("RATE_LIMIT_EXECUTE_REQUESTS", "20")),
            execute_window_seconds=int(os.environ.get("RATE_LIMIT_EXECUTE_WINDOW", "60")),
        )


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    Used as fallback when Redis is unavailable or for single-instance deployments.
    Note: This doesn't share state across multiple workers/instances.
    """

    def __init__(self):
        # Structure: {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)

    def _cleanup_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests outside the current window."""
        cutoff = time.time() - window_seconds
        self._requests[key] = [
            (ts, count) for ts, count in self._requests[key]
            if ts > cutoff
        ]

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if the request is within rate limits.

        Returns:
            Tuple of (allowed, current_count, remaining)
        """
        now = time.time()
        self._cleanup_old_requests(key, window_seconds)

        current_count = sum(count for _, count in self._requests[key])

        if current_count >= max_requests:
            return False, current_count, 0

        self._requests[key].append((now, 1))
        return True, current_count + 1, max_requests - current_count - 1

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        self._requests.pop(key, None)


class RateLimiter:
    """
    Rate limiter with Redis support and in-memory fallback.

    Uses Redis when available for distributed rate limiting across multiple
    instances. Falls back to in-memory limiting for single-instance deployments.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig.from_env()
        self._memory_limiter = InMemoryRateLimiter()
        self._redis_client = None

    def _get_client_identifier(self, request: Request) -> str:
        """Extract client identifier from request for rate limiting."""
        # Try to get real IP from proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    async def _check_redis_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """Check rate limit using Redis."""
        try:
            from service.redis_client import get_redis_client
            redis = get_redis_client()

            if not redis.is_available:
                return await self._check_memory_limit(key, max_requests, window_seconds)

            # Use Redis INCR with expiry for atomic rate limiting
            current = await redis.get(key)
            if current is not None:
                count = int(current)
                if count >= max_requests:
                    return False, count, 0

            new_count = await redis.increment(key)
            if new_count == 1:
                await redis.expire(key, window_seconds)

            remaining = max(0, max_requests - new_count)
            return True, new_count, remaining

        except Exception as e:
            logger.warning(f"Redis rate limit check failed, using memory: {e}")
            return await self._check_memory_limit(key, max_requests, window_seconds)

    async def _check_memory_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """Check rate limit using in-memory limiter."""
        return self._memory_limiter.check_rate_limit(key, max_requests, window_seconds)

    async def check_limit(
        self,
        request: Request,
        endpoint_type: str = "general"
    ) -> None:
        """
        Check rate limit for a request.

        Args:
            request: FastAPI request object
            endpoint_type: "general" or "execute" for different limits

        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        if not self.config.enabled:
            return

        client_id = self._get_client_identifier(request)

        # Determine limits based on endpoint type
        if endpoint_type == "execute":
            max_requests = self.config.execute_requests_per_window
            window_seconds = self.config.execute_window_seconds
        else:
            max_requests = self.config.requests_per_window
            window_seconds = self.config.window_seconds

        key = f"ratelimit:{endpoint_type}:{client_id}"

        allowed, count, remaining = await self._check_redis_limit(
            key, max_requests, window_seconds
        )

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id} on {endpoint_type}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": max_requests,
                    "window_seconds": window_seconds,
                    "retry_after": window_seconds,
                },
                headers={
                    "Retry-After": str(window_seconds),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + window_seconds),
                }
            )


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# FastAPI dependency functions
async def rate_limit_general(request: Request) -> None:
    """FastAPI dependency for general endpoint rate limiting."""
    limiter = get_rate_limiter()
    await limiter.check_limit(request, "general")


async def rate_limit_execute(request: Request) -> None:
    """FastAPI dependency for execution endpoint rate limiting."""
    limiter = get_rate_limiter()
    await limiter.check_limit(request, "execute")
