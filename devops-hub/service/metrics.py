"""
Prometheus metrics module for DevOps Hub.

Provides HTTP request tracking, custom counters, and a /metrics endpoint.
"""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)


# ============ HTTP Metrics ============

HTTP_REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


# ============ Agent Metrics ============

ACTIVE_AGENTS = Gauge(
    "active_agents_count",
    "Number of currently active agents",
)

AGENT_EXECUTIONS = Counter(
    "agent_executions_total",
    "Total number of agent executions",
    ["agent_id", "capability", "status"],
)


# ============ Workflow Metrics ============

WORKFLOW_EXECUTIONS = Counter(
    "workflow_executions_total",
    "Total number of workflow executions",
    ["workflow_id", "status"],
)

WORKFLOW_DURATION = Histogram(
    "workflow_execution_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)


# ============ Event Bus Metrics ============

EVENT_BUS_MESSAGES = Counter(
    "event_bus_messages_total",
    "Total number of messages published to the event bus",
    ["event_type", "source"],
)


# ============ WebSocket Metrics ============

WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections_count",
    "Number of active WebSocket connections",
)


# ============ Helper Functions ============

def track_request(method: str, path: str, status: int, duration: float) -> None:
    """Track an HTTP request with its metrics."""
    # Normalize path to avoid high cardinality (remove IDs)
    normalized_path = _normalize_path(path)
    HTTP_REQUEST_COUNT.labels(method=method, path=normalized_path, status=str(status)).inc()
    HTTP_REQUEST_LATENCY.labels(method=method, path=normalized_path).observe(duration)


def track_agent_execution(agent_id: str, capability: str, success: bool) -> None:
    """Track an agent execution."""
    status = "success" if success else "error"
    AGENT_EXECUTIONS.labels(agent_id=agent_id, capability=capability, status=status).inc()


def track_workflow_execution(workflow_id: str, status: str, duration: float) -> None:
    """Track a workflow execution."""
    WORKFLOW_EXECUTIONS.labels(workflow_id=workflow_id, status=status).inc()
    WORKFLOW_DURATION.labels(workflow_id=workflow_id).observe(duration)


def track_event_published(event_type: str, source: str) -> None:
    """Track an event published to the event bus."""
    EVENT_BUS_MESSAGES.labels(event_type=event_type, source=source).inc()


def set_active_agents(count: int) -> None:
    """Set the current number of active agents."""
    ACTIVE_AGENTS.set(count)


def increment_websocket_connections() -> None:
    """Increment WebSocket connection count."""
    WEBSOCKET_CONNECTIONS.inc()


def decrement_websocket_connections() -> None:
    """Decrement WebSocket connection count."""
    WEBSOCKET_CONNECTIONS.dec()


def _normalize_path(path: str) -> str:
    """
    Normalize URL path to reduce cardinality.

    Replaces dynamic segments (UUIDs, IDs) with placeholders.
    """
    import re

    # Replace UUIDs
    path = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "{id}",
        path,
        flags=re.IGNORECASE,
    )

    # Replace numeric IDs in path segments
    path = re.sub(r"/\d+(/|$)", r"/{id}\1", path)

    return path


# ============ Middleware ============

class MetricsMiddleware:
    """
    ASGI middleware for tracking HTTP request metrics.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Skip metrics endpoint to avoid recursion
        path = scope.get("path", "")
        if path == "/metrics":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        start_time = time.perf_counter()
        status_code = 500  # Default in case of error

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start_time
            track_request(method, path, status_code, duration)


def add_metrics_middleware(app: FastAPI) -> None:
    """Add the metrics middleware to a FastAPI application."""
    app.add_middleware(MetricsMiddleware)


# ============ Metrics Endpoint ============

async def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint handler.

    Returns metrics in Prometheus text format.
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


def add_metrics_route(app: FastAPI) -> None:
    """Add the /metrics endpoint to a FastAPI application."""
    app.add_api_route(
        "/metrics",
        metrics_endpoint,
        methods=["GET"],
        tags=["Monitoring"],
        summary="Prometheus metrics",
        description="Returns metrics in Prometheus text format for scraping.",
    )


def setup_metrics(app: FastAPI) -> None:
    """
    Complete metrics setup for a FastAPI application.

    Adds both the middleware and the /metrics endpoint.

    Usage:
        from service.metrics import setup_metrics

        app = FastAPI()
        setup_metrics(app)
    """
    add_metrics_middleware(app)
    add_metrics_route(app)
