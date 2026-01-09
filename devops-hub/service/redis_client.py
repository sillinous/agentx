"""
Redis Client - Connection management, caching, and pub/sub integration.

Provides Redis integration with graceful fallback when Redis is unavailable.
The system operates normally without Redis, using it as an optional enhancement.
"""

import asyncio
import functools
import hashlib
import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

# Type variable for generic cache decorator
T = TypeVar("T")

# Try to import redis - make it optional
try:
    import redis.asyncio as aioredis
    from redis.asyncio import ConnectionPool, Redis
    from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    ConnectionPool = None
    Redis = None
    RedisConnectionError = Exception
    RedisTimeoutError = Exception


@dataclass
class RedisConfig:
    """Redis connection configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    max_connections: int = 10
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    decode_responses: bool = True

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            db=int(os.environ.get("REDIS_DB", "0")),
            password=os.environ.get("REDIS_PASSWORD"),
            socket_timeout=float(os.environ.get("REDIS_SOCKET_TIMEOUT", "5.0")),
            socket_connect_timeout=float(os.environ.get("REDIS_CONNECT_TIMEOUT", "5.0")),
            max_connections=int(os.environ.get("REDIS_MAX_CONNECTIONS", "10")),
        )


@dataclass
class RedisHealth:
    """Redis health check result."""
    available: bool
    latency_ms: Optional[float] = None
    version: Optional[str] = None
    connected_clients: Optional[int] = None
    used_memory: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "latency_ms": self.latency_ms,
            "version": self.version,
            "connected_clients": self.connected_clients,
            "used_memory": self.used_memory,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class RedisClient:
    """
    Redis client with connection pooling and graceful fallback.

    Features:
    - Connection pooling for efficient resource usage
    - Automatic reconnection on connection failures
    - Graceful degradation when Redis is unavailable
    - Health check functionality
    - Caching with TTL support
    - Pub/sub integration with message bus
    """

    def __init__(self, config: Optional[RedisConfig] = None):
        self._config = config or RedisConfig.from_env()
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._connected = False
        self._last_health_check: Optional[RedisHealth] = None
        self._lock = asyncio.Lock()
        self._pubsub_handlers: Dict[str, List[Callable]] = {}
        self._pubsub_task: Optional[asyncio.Task] = None

    @property
    def is_available(self) -> bool:
        """Check if Redis is available and connected."""
        return REDIS_AVAILABLE and self._connected

    async def connect(self) -> bool:
        """
        Establish connection to Redis.

        Returns True if connection successful, False otherwise.
        Does not raise exceptions - designed for optional Redis usage.
        """
        if not REDIS_AVAILABLE:
            logger.info("Redis package not installed - running without Redis")
            return False

        async with self._lock:
            if self._connected and self._client:
                return True

            try:
                self._pool = ConnectionPool(
                    host=self._config.host,
                    port=self._config.port,
                    db=self._config.db,
                    password=self._config.password,
                    socket_timeout=self._config.socket_timeout,
                    socket_connect_timeout=self._config.socket_connect_timeout,
                    max_connections=self._config.max_connections,
                    retry_on_timeout=self._config.retry_on_timeout,
                    health_check_interval=self._config.health_check_interval,
                    decode_responses=self._config.decode_responses,
                )

                self._client = Redis(connection_pool=self._pool)

                # Test connection with ping
                await self._client.ping()
                self._connected = True
                logger.info(f"Connected to Redis at {self._config.host}:{self._config.port}")
                return True

            except (RedisConnectionError, RedisTimeoutError, OSError) as e:
                logger.warning(f"Failed to connect to Redis: {e} - running without Redis")
                self._connected = False
                self._client = None
                self._pool = None
                return False
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {e}")
                self._connected = False
                self._client = None
                self._pool = None
                return False

    async def disconnect(self) -> None:
        """Close Redis connection and cleanup resources."""
        async with self._lock:
            # Cancel pubsub listener if running
            if self._pubsub_task and not self._pubsub_task.done():
                self._pubsub_task.cancel()
                try:
                    await self._pubsub_task
                except asyncio.CancelledError:
                    pass

            if self._client:
                await self._client.close()
                self._client = None

            if self._pool:
                await self._pool.disconnect()
                self._pool = None

            self._connected = False
            logger.info("Disconnected from Redis")

    async def health_check(self) -> RedisHealth:
        """
        Perform a health check on the Redis connection.

        Returns a RedisHealth object with connection status and metrics.
        """
        if not REDIS_AVAILABLE:
            return RedisHealth(
                available=False,
                error="Redis package not installed",
            )

        if not self._connected or not self._client:
            # Try to connect if not connected
            connected = await self.connect()
            if not connected:
                return RedisHealth(
                    available=False,
                    error="Not connected to Redis",
                )

        try:
            start = datetime.utcnow()
            await self._client.ping()
            latency = (datetime.utcnow() - start).total_seconds() * 1000

            # Get server info
            info = await self._client.info()

            health = RedisHealth(
                available=True,
                latency_ms=round(latency, 2),
                version=info.get("redis_version"),
                connected_clients=info.get("connected_clients"),
                used_memory=info.get("used_memory_human"),
            )
            self._last_health_check = health
            return health

        except (RedisConnectionError, RedisTimeoutError) as e:
            self._connected = False
            return RedisHealth(
                available=False,
                error=str(e),
            )
        except Exception as e:
            return RedisHealth(
                available=False,
                error=f"Health check failed: {e}",
            )

    # ============ Caching Methods ============

    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        if not self.is_available:
            return None

        try:
            return await self._client.get(key)
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis get failed for key {key}: {e}")
            self._connected = False
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds
            nx: Only set if key does not exist
            xx: Only set if key exists

        Returns True if set was successful.
        """
        if not self.is_available:
            return False

        try:
            result = await self._client.set(key, value, ex=ttl, nx=nx, xx=xx)
            return result is not None and result is not False
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis set failed for key {key}: {e}")
            self._connected = False
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns number of keys deleted."""
        if not self.is_available or not keys:
            return 0

        try:
            return await self._client.delete(*keys)
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis delete failed: {e}")
            self._connected = False
            return 0

    async def exists(self, *keys: str) -> int:
        """Check if keys exist. Returns count of existing keys."""
        if not self.is_available or not keys:
            return 0

        try:
            return await self._client.exists(*keys)
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis exists check failed: {e}")
            self._connected = False
            return 0

    async def get_json(self, key: str) -> Optional[Any]:
        """Get and deserialize a JSON value from cache."""
        value = await self.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Serialize and set a JSON value in cache."""
        try:
            json_str = json.dumps(value, default=str)
            return await self.set(key, json_str, ttl=ttl)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize value for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter. Returns new value or None on failure."""
        if not self.is_available:
            return None

        try:
            return await self._client.incrby(key, amount)
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis increment failed for key {key}: {e}")
            self._connected = False
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on an existing key."""
        if not self.is_available:
            return False

        try:
            return await self._client.expire(key, ttl)
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis expire failed for key {key}: {e}")
            self._connected = False
            return False

    async def ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL of a key in seconds. Returns None if key doesn't exist or has no TTL."""
        if not self.is_available:
            return None

        try:
            result = await self._client.ttl(key)
            return result if result >= 0 else None
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis TTL check failed for key {key}: {e}")
            self._connected = False
            return None

    # ============ Pub/Sub Methods ============

    async def publish(self, channel: str, message: Union[str, Dict[str, Any]]) -> int:
        """
        Publish a message to a channel.

        Args:
            channel: Channel name to publish to
            message: Message string or dict (will be JSON serialized)

        Returns number of subscribers that received the message.
        """
        if not self.is_available:
            return 0

        try:
            if isinstance(message, dict):
                message = json.dumps(message, default=str)
            return await self._client.publish(channel, message)
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.warning(f"Redis publish failed on channel {channel}: {e}")
            self._connected = False
            return 0

    async def subscribe(
        self,
        channel: str,
        handler: Callable[[str, str], None],
    ) -> bool:
        """
        Subscribe to a channel with a message handler.

        Args:
            channel: Channel name or pattern (use * for wildcard)
            handler: Callback function(channel, message) called for each message

        Returns True if subscription was successful.
        """
        if not REDIS_AVAILABLE:
            return False

        if channel not in self._pubsub_handlers:
            self._pubsub_handlers[channel] = []
        self._pubsub_handlers[channel].append(handler)

        # Start listener task if not running
        if self._pubsub_task is None or self._pubsub_task.done():
            self._pubsub_task = asyncio.create_task(self._pubsub_listener())

        return True

    async def unsubscribe(self, channel: str, handler: Optional[Callable] = None) -> bool:
        """
        Unsubscribe from a channel.

        If handler is provided, only remove that handler.
        If handler is None, remove all handlers for the channel.
        """
        if channel not in self._pubsub_handlers:
            return False

        if handler is None:
            del self._pubsub_handlers[channel]
        else:
            try:
                self._pubsub_handlers[channel].remove(handler)
                if not self._pubsub_handlers[channel]:
                    del self._pubsub_handlers[channel]
            except ValueError:
                return False

        return True

    async def _pubsub_listener(self) -> None:
        """Background task that listens for pub/sub messages."""
        if not REDIS_AVAILABLE or not self._connected:
            return

        pubsub = self._client.pubsub()

        try:
            while self._pubsub_handlers:
                # Subscribe to all registered channels
                channels = list(self._pubsub_handlers.keys())
                if not channels:
                    await asyncio.sleep(1)
                    continue

                try:
                    # Subscribe to channels (patterns if they contain *)
                    for channel in channels:
                        if "*" in channel:
                            await pubsub.psubscribe(channel)
                        else:
                            await pubsub.subscribe(channel)

                    # Listen for messages
                    async for message in pubsub.listen():
                        if message["type"] in ("message", "pmessage"):
                            channel = message.get("channel", message.get("pattern", ""))
                            data = message["data"]

                            # Find matching handlers
                            for pattern, handlers in list(self._pubsub_handlers.items()):
                                if self._channel_matches(channel, pattern):
                                    for handler in handlers:
                                        try:
                                            if asyncio.iscoroutinefunction(handler):
                                                await handler(channel, data)
                                            else:
                                                handler(channel, data)
                                        except Exception as e:
                                            logger.error(f"Error in pubsub handler: {e}")

                except (RedisConnectionError, RedisTimeoutError) as e:
                    logger.warning(f"Redis pubsub connection lost: {e}")
                    self._connected = False
                    await asyncio.sleep(5)  # Wait before retry
                    await self.connect()

        except asyncio.CancelledError:
            pass
        finally:
            try:
                await pubsub.unsubscribe()
                await pubsub.punsubscribe()
                await pubsub.close()
            except Exception:
                pass

    def _channel_matches(self, channel: str, pattern: str) -> bool:
        """Check if a channel matches a pattern (supports * wildcard)."""
        if pattern == channel:
            return True
        if "*" not in pattern:
            return False

        # Simple wildcard matching
        import fnmatch
        return fnmatch.fnmatch(channel, pattern)


class RedisPubSubBridge:
    """
    Bridge between Redis pub/sub and the local MessageBus.

    Allows events to be propagated across multiple service instances
    via Redis pub/sub while maintaining local message bus functionality.
    """

    def __init__(self, redis_client: RedisClient, channel_prefix: str = "devops-hub:events"):
        self._redis = redis_client
        self._channel_prefix = channel_prefix
        self._message_bus = None
        self._local_event_ids: set = set()  # Track events we published to avoid echo

    async def connect_to_message_bus(self, message_bus) -> None:
        """
        Connect to a MessageBus instance and bridge events to Redis.

        Args:
            message_bus: The MessageBus instance to bridge
        """
        from service.message_bus import Event

        self._message_bus = message_bus

        # Subscribe to all local events and forward to Redis
        async def forward_to_redis(event: Event):
            if event.id in self._local_event_ids:
                # This event came from Redis, don't echo back
                return

            channel = f"{self._channel_prefix}:{event.type}"
            await self._redis.publish(channel, event.to_dict())

        message_bus.subscribe("*", forward_to_redis)

        # Subscribe to Redis events and forward to local bus
        await self._redis.subscribe(
            f"{self._channel_prefix}:*",
            self._handle_redis_event,
        )

        logger.info("Redis pub/sub bridge connected to message bus")

    async def _handle_redis_event(self, channel: str, message: str) -> None:
        """Handle events received from Redis and forward to local bus."""
        if self._message_bus is None:
            return

        try:
            from service.message_bus import Event

            data = json.loads(message) if isinstance(message, str) else message

            # Mark this event as coming from Redis
            event = Event(
                id=data.get("id"),
                type=data.get("type", ""),
                source=data.get("source", ""),
                data=data.get("data", {}),
                correlation_id=data.get("correlation_id"),
                metadata=data.get("metadata", {}),
            )

            # Track to avoid echo
            self._local_event_ids.add(event.id)

            # Clean up old event IDs (keep last 1000)
            if len(self._local_event_ids) > 1000:
                self._local_event_ids = set(list(self._local_event_ids)[-500:])

            # Publish to local bus
            await self._message_bus.publish(event)

        except Exception as e:
            logger.error(f"Error handling Redis event: {e}")


def cache(
    ttl: int = 300,
    key_prefix: str = "",
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Caching decorator for async functions.

    Uses Redis when available, falls back to no caching when Redis is unavailable.

    Args:
        ttl: Time-to-live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
        key_builder: Optional function to build cache key from args/kwargs

    Example:
        @cache(ttl=60, key_prefix="user")
        async def get_user(user_id: str) -> dict:
            return await fetch_user_from_db(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            redis_client = get_redis_client()

            if not redis_client.is_available:
                # Redis not available, just call the function
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key builder using function name and args hash
                key_parts = [key_prefix, func.__module__, func.__name__]
                if args:
                    args_hash = hashlib.md5(str(args).encode()).hexdigest()[:8]
                    key_parts.append(args_hash)
                if kwargs:
                    kwargs_hash = hashlib.md5(str(sorted(kwargs.items())).encode()).hexdigest()[:8]
                    key_parts.append(kwargs_hash)
                cache_key = ":".join(filter(None, key_parts))

            # Try to get from cache
            cached = await redis_client.get_json(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached

            # Call function and cache result
            result = await func(*args, **kwargs)
            await redis_client.set_json(cache_key, result, ttl=ttl)
            logger.debug(f"Cached result for key: {cache_key}")

            return result

        # Add method to invalidate cache
        async def invalidate(*args, **kwargs):
            redis_client = get_redis_client()
            if not redis_client.is_available:
                return False

            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [key_prefix, func.__module__, func.__name__]
                if args:
                    args_hash = hashlib.md5(str(args).encode()).hexdigest()[:8]
                    key_parts.append(args_hash)
                if kwargs:
                    kwargs_hash = hashlib.md5(str(sorted(kwargs.items())).encode()).hexdigest()[:8]
                    key_parts.append(kwargs_hash)
                cache_key = ":".join(filter(None, key_parts))

            return await redis_client.delete(cache_key) > 0

        wrapper.invalidate = invalidate
        return wrapper

    return decorator


def rate_limit(
    max_requests: int,
    window_seconds: int = 60,
    key_func: Optional[Callable[..., str]] = None,
):
    """
    Rate limiting decorator using Redis.

    Falls back to allowing all requests when Redis is unavailable.

    Args:
        max_requests: Maximum number of requests allowed in the window
        window_seconds: Time window in seconds
        key_func: Function to extract rate limit key (e.g., user ID, IP)

    Example:
        @rate_limit(max_requests=100, window_seconds=60, key_func=lambda req: req.client.host)
        async def api_endpoint(request):
            return {"message": "Hello"}
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            redis_client = get_redis_client()

            if not redis_client.is_available:
                # Redis not available, allow request
                return await func(*args, **kwargs)

            # Build rate limit key
            if key_func:
                identifier = key_func(*args, **kwargs)
            else:
                identifier = "global"

            rate_key = f"ratelimit:{func.__name__}:{identifier}"

            # Check current count
            current = await redis_client.get(rate_key)
            if current is not None:
                count = int(current)
                if count >= max_requests:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds"
                    )

            # Increment counter
            new_count = await redis_client.increment(rate_key)
            if new_count == 1:
                # First request in window, set expiry
                await redis_client.expire(rate_key, window_seconds)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


# ============ Global Redis Client Instance ============

_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get the global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


async def init_redis(config: Optional[RedisConfig] = None) -> RedisClient:
    """
    Initialize the global Redis client and establish connection.

    Should be called during application startup.
    """
    global _redis_client
    _redis_client = RedisClient(config)
    await _redis_client.connect()
    return _redis_client


async def close_redis() -> None:
    """
    Close the global Redis client connection.

    Should be called during application shutdown.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.disconnect()
        _redis_client = None


@asynccontextmanager
async def redis_context(config: Optional[RedisConfig] = None):
    """
    Context manager for Redis client lifecycle.

    Example:
        async with redis_context() as redis:
            await redis.set("key", "value")
    """
    client = await init_redis(config)
    try:
        yield client
    finally:
        await close_redis()
