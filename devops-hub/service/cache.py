"""
Response caching for DevOps Hub API.

Provides in-memory and Redis-backed caching for API responses.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False


@dataclass
class CacheEntry:
    """Cached value with metadata."""
    value: Any
    expires_at: float
    created_at: float

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float:
        return max(0, self.expires_at - time.time())


class InMemoryCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache."""
        ttl = ttl or self._default_ttl
        async with self._lock:
            # Evict expired entries if at capacity
            if len(self._cache) >= self._max_size:
                await self._evict_expired()

            # If still at capacity, evict oldest entries
            if len(self._cache) >= self._max_size:
                await self._evict_oldest(len(self._cache) - self._max_size + 1)

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.time() + ttl,
                created_at=time.time()
            )

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._cache.clear()

    async def _evict_expired(self) -> int:
        """Remove expired entries. Returns count evicted."""
        now = time.time()
        expired = [k for k, v in self._cache.items() if v.expires_at < now]
        for key in expired:
            del self._cache[key]
        return len(expired)

    async def _evict_oldest(self, count: int) -> None:
        """Evict oldest entries."""
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        for key in sorted_keys[:count]:
            del self._cache[key]

    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "type": "memory",
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }


class RedisCache:
    """Redis-backed cache."""

    def __init__(
        self,
        redis_url: str,
        default_ttl: int = 300,
        key_prefix: str = "devops_hub:"
    ):
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        self._key_prefix = key_prefix
        self._client: Optional[Any] = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - using memory cache")
            return False

        try:
            self._client = aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._client.ping()
            self._connected = True
            logger.info("Redis cache connected")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._connected = False

    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self._connected:
            return None
        try:
            value = await self._client.get(self._make_key(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache."""
        if not self._connected:
            return
        try:
            ttl = ttl or self._default_ttl
            await self._client.setex(
                self._make_key(key),
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.warning(f"Redis set error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self._connected:
            return False
        try:
            result = await self._client.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
            return False

    async def clear(self) -> None:
        """Clear all entries with our prefix."""
        if not self._connected:
            return
        try:
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(
                    cursor,
                    match=f"{self._key_prefix}*",
                    count=100
                )
                if keys:
                    await self._client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Redis clear error: {e}")

    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "type": "redis",
            "connected": self._connected,
            "url": self._redis_url.split("@")[-1] if "@" in self._redis_url else self._redis_url
        }


class CacheManager:
    """
    Unified cache manager with fallback.

    Uses Redis if available, falls back to in-memory cache.
    """

    def __init__(self):
        self._memory_cache = InMemoryCache()
        self._redis_cache: Optional[RedisCache] = None
        self._use_redis = False

    async def initialize(self) -> None:
        """Initialize cache backends."""
        redis_url = os.getenv("REDIS_URL")
        if redis_url and REDIS_AVAILABLE:
            self._redis_cache = RedisCache(redis_url)
            self._use_redis = await self._redis_cache.connect()

        if not self._use_redis:
            logger.info("Using in-memory cache")

    async def shutdown(self) -> None:
        """Shutdown cache backends."""
        if self._redis_cache:
            await self._redis_cache.disconnect()

    @property
    def cache(self) -> Union[InMemoryCache, RedisCache]:
        """Get the active cache backend."""
        if self._use_redis and self._redis_cache:
            return self._redis_cache
        return self._memory_cache

    async def get(self, key: str) -> Optional[Any]:
        return await self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        await self.cache.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        return await self.cache.delete(key)

    async def clear(self) -> None:
        await self.cache.clear()

    @property
    def stats(self) -> Dict[str, Any]:
        return self.cache.stats


# Global cache manager
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get the global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.initialize()
    return _cache_manager


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl=60)
        async def get_agents():
            ...

        @cached(ttl=300, key_prefix="agent")
        async def get_agent(agent_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = await get_cache_manager()

            # Generate cache key
            func_key = f"{key_prefix or func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = await cache.get(func_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(func_key, result, ttl)
            return result

        return wrapper
    return decorator


def invalidate_cache(key_pattern: str = ""):
    """
    Decorator to invalidate cache after function execution.

    Usage:
        @invalidate_cache(key_pattern="agents")
        async def create_agent(agent_data):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Clear cache entries matching pattern
            cache = await get_cache_manager()
            # For now, just clear all - a more sophisticated implementation
            # would support pattern matching
            if key_pattern:
                await cache.delete(key_pattern)

            return result
        return wrapper
    return decorator
