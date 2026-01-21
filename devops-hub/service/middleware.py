"""
API Middleware - Request processing middleware for FastAPI.

Provides:
- Request ID tracking for distributed tracing
- Request logging with timing
- Error handling standardization
"""

import time
import logging
from uuid import uuid4
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from service.logging_config import set_request_id, clear_request_id, get_request_id

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to each request.

    The request ID is:
    - Read from X-Request-ID header if provided
    - Generated if not provided
    - Added to response headers
    - Available throughout the request lifecycle via context var
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid4())

        # Set in context for logging
        set_request_id(request_id)

        # Store in request state for access in handlers
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_request_id()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request/response details with timing.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
            }
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                f"Request completed: {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )

            # Add timing header
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} -> {type(e).__name__}: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True
            )
            raise
