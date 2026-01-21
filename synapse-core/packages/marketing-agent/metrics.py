"""
Synapse Core - Prometheus Metrics
Provides application metrics for monitoring and alerting.
"""

import time
from functools import wraps
from typing import Callable, Optional

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
        multiprocess,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes if prometheus_client is not installed
    class DummyMetric:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def info(self, *args, **kwargs):
            pass

    Counter = Histogram = Gauge = Info = lambda *args, **kwargs: DummyMetric()
    CollectorRegistry = lambda: None
    generate_latest = lambda *args: b""
    CONTENT_TYPE_LATEST = "text/plain"


# =============================================================================
# Metrics Registry
# =============================================================================

# Use default registry unless in multiprocess mode
REGISTRY = CollectorRegistry() if PROMETHEUS_AVAILABLE else None


# =============================================================================
# Application Metrics
# =============================================================================

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["method", "endpoint"],
)

# Agent Metrics
agent_invoke_total = Counter(
    "agent_invoke_total",
    "Total agent invocations",
    ["agent", "status"],
)

agent_invoke_duration_seconds = Histogram(
    "agent_invoke_duration_seconds",
    "Agent invocation duration in seconds",
    ["agent"],
    buckets=(0.5, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0),
)

agent_tokens_used = Counter(
    "agent_tokens_used_total",
    "Total tokens used by agents",
    ["agent", "token_type"],  # token_type: prompt, completion
)

# Authentication Metrics
auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total authentication attempts",
    ["type", "status"],  # type: login, register, verify; status: success, failure
)

active_sessions = Gauge(
    "active_sessions",
    "Number of active user sessions",
)

# Rate Limiting Metrics
rate_limit_exceeded_total = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit exceeded events",
    ["endpoint", "client_ip"],
)

# Database Metrics
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# Application Info
app_info = Info(
    "synapse_core",
    "Synapse Core application information",
)


# =============================================================================
# Metric Helpers
# =============================================================================

def init_app_info(version: str = "1.0.0", environment: str = "development"):
    """Initialize application info metric."""
    if PROMETHEUS_AVAILABLE:
        app_info.info({
            "version": version,
            "environment": environment,
            "agents": "scribe,architect,sentry",
        })


def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Track HTTP request metrics."""
    http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_agent_invocation(agent: str, status: str, duration: float, tokens_prompt: int = 0, tokens_completion: int = 0):
    """Track agent invocation metrics."""
    agent_invoke_total.labels(agent=agent, status=status).inc()
    agent_invoke_duration_seconds.labels(agent=agent).observe(duration)

    if tokens_prompt > 0:
        agent_tokens_used.labels(agent=agent, token_type="prompt").inc(tokens_prompt)
    if tokens_completion > 0:
        agent_tokens_used.labels(agent=agent, token_type="completion").inc(tokens_completion)


def track_auth_attempt(auth_type: str, success: bool):
    """Track authentication attempt."""
    status = "success" if success else "failure"
    auth_attempts_total.labels(type=auth_type, status=status).inc()


def track_rate_limit_exceeded(endpoint: str, client_ip: str):
    """Track rate limit exceeded event."""
    rate_limit_exceeded_total.labels(endpoint=endpoint, client_ip=client_ip).inc()


def track_db_query(operation: str, table: str, duration: float):
    """Track database query metrics."""
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


# =============================================================================
# Decorator for Automatic Metrics
# =============================================================================

def metrics_endpoint(endpoint_name: str):
    """Decorator to automatically track endpoint metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            method = "POST"  # Default, could be extracted from request

            http_requests_in_progress.labels(method=method, endpoint=endpoint_name).inc()

            try:
                result = await func(*args, **kwargs)
                status_code = getattr(result, "status_code", 200)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                http_requests_in_progress.labels(method=method, endpoint=endpoint_name).dec()
                track_request_metrics(method, endpoint_name, status_code, duration)

        return wrapper
    return decorator


def agent_metrics(agent_name: str):
    """Decorator to automatically track agent invocation metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                track_agent_invocation(agent_name, status, duration)

        return wrapper
    return decorator


# =============================================================================
# Metrics Endpoint
# =============================================================================

def get_metrics() -> tuple[bytes, str]:
    """Generate metrics in Prometheus format."""
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus client not installed\n", "text/plain"

    return generate_latest(), CONTENT_TYPE_LATEST


# =============================================================================
# FastAPI Middleware
# =============================================================================

class PrometheusMiddleware:
    """Middleware to track HTTP request metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope.get("method", "GET")
        path = scope.get("path", "/")

        # Normalize endpoint for metrics (avoid high cardinality)
        endpoint = self._normalize_endpoint(path)

        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        status_code = 500  # Default in case of unhandled exception

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            track_request_metrics(method, endpoint, status_code, duration)

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path to avoid high cardinality."""
        # Replace UUIDs and numeric IDs
        import re
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        return path
