"""
Security utilities for DevOps Hub API.

Provides:
- Security headers middleware
- Input validation and sanitization
- Rate limiting helpers
- Security audit logging
"""

import hashlib
import hmac
import logging
import re
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# =============================================================================
# Security Headers
# =============================================================================

SECURITY_HEADERS = {
    # Prevent MIME type sniffing
    "X-Content-Type-Options": "nosniff",

    # Prevent clickjacking
    "X-Frame-Options": "DENY",

    # Enable XSS filter
    "X-XSS-Protection": "1; mode=block",

    # Referrer policy
    "Referrer-Policy": "strict-origin-when-cross-origin",

    # Permissions policy (restrict browser features)
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",

    # Cache control for API responses
    "Cache-Control": "no-store, no-cache, must-revalidate, private",

    # Prevent caching of sensitive data
    "Pragma": "no-cache",
}

# Content Security Policy for API responses
CSP_POLICY = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app, include_csp: bool = True):
        super().__init__(app)
        self.include_csp = include_csp

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add CSP for API endpoints
        if self.include_csp and request.url.path.startswith("/api"):
            response.headers["Content-Security-Policy"] = CSP_POLICY

        # Add HSTS for HTTPS connections
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


# =============================================================================
# Input Validation
# =============================================================================

# Patterns for dangerous input
DANGEROUS_PATTERNS = [
    r"<script[^>]*>",  # Script tags
    r"javascript:",    # JavaScript URLs
    r"on\w+\s*=",      # Event handlers
    r"data:\s*text/html",  # Data URLs with HTML
    r"\{\{.*\}\}",     # Template injection
    r"\$\{.*\}",       # Template literals
    r"<!--.*-->",      # HTML comments
]

# Compiled patterns for efficiency
_DANGEROUS_REGEX = re.compile(
    "|".join(DANGEROUS_PATTERNS),
    re.IGNORECASE | re.DOTALL
)

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\s",
    r"--\s*$",         # SQL comments
    r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
    r"'\s*(OR|AND)\s*'?\d*'?\s*=",  # OR/AND injection
]

_SQL_INJECTION_REGEX = re.compile(
    "|".join(SQL_INJECTION_PATTERNS),
    re.IGNORECASE
)

# Maximum input lengths
MAX_STRING_LENGTH = 10000
MAX_ID_LENGTH = 255
MAX_NAME_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000


class InputValidationError(HTTPException):
    """Raised when input validation fails."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """
    Sanitize a string input.

    - Strips whitespace
    - Truncates to max length
    - Removes null bytes
    """
    if not isinstance(value, str):
        return str(value)

    # Remove null bytes
    value = value.replace("\x00", "")

    # Strip whitespace
    value = value.strip()

    # Truncate
    if len(value) > max_length:
        value = value[:max_length]

    return value


def validate_id(value: str, field_name: str = "id") -> str:
    """
    Validate an ID field.

    IDs must be:
    - Non-empty
    - Max 255 characters
    - Alphanumeric with hyphens/underscores
    """
    value = sanitize_string(value, MAX_ID_LENGTH)

    if not value:
        raise InputValidationError(f"{field_name} is required")

    if not re.match(r"^[a-zA-Z0-9_-]+$", value):
        raise InputValidationError(
            f"{field_name} must contain only alphanumeric characters, "
            "hyphens, and underscores"
        )

    return value


def validate_name(value: str, field_name: str = "name") -> str:
    """Validate a name field."""
    value = sanitize_string(value, MAX_NAME_LENGTH)

    if not value:
        raise InputValidationError(f"{field_name} is required")

    # Check for dangerous patterns
    if _DANGEROUS_REGEX.search(value):
        raise InputValidationError(f"{field_name} contains invalid characters")

    return value


def validate_description(value: Optional[str], field_name: str = "description") -> Optional[str]:
    """Validate a description field."""
    if value is None:
        return None

    value = sanitize_string(value, MAX_DESCRIPTION_LENGTH)

    # Check for dangerous patterns
    if _DANGEROUS_REGEX.search(value):
        raise InputValidationError(f"{field_name} contains invalid content")

    return value


def check_sql_injection(value: str) -> bool:
    """Check if a string contains potential SQL injection."""
    return bool(_SQL_INJECTION_REGEX.search(value))


def validate_no_sql_injection(value: str, field_name: str = "input") -> str:
    """Validate that input doesn't contain SQL injection attempts."""
    if check_sql_injection(value):
        logger.warning(f"Potential SQL injection detected in {field_name}")
        raise InputValidationError(f"Invalid characters in {field_name}")
    return value


# =============================================================================
# Rate Limiting Helpers
# =============================================================================

class RateLimitExceeded(HTTPException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )


class InMemoryRateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self._requests: Dict[str, List[float]] = {}

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try API key first
        api_key = request.headers.get("Authorization", "")
        if api_key.startswith("Bearer "):
            return f"key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def check_rate_limit(self, request: Request) -> bool:
        """
        Check if request is within rate limit.

        Returns True if allowed, raises RateLimitExceeded if not.
        """
        client_id = self._get_client_id(request)
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Get or create request list
        if client_id not in self._requests:
            self._requests[client_id] = []

        # Remove old requests
        self._requests[client_id] = [
            ts for ts in self._requests[client_id]
            if ts > window_start
        ]

        # Check limit
        if len(self._requests[client_id]) >= self.requests_per_minute:
            oldest = min(self._requests[client_id])
            retry_after = int(oldest + 60 - now) + 1
            raise RateLimitExceeded(retry_after=max(1, retry_after))

        # Record request
        self._requests[client_id].append(now)
        return True

    def cleanup(self):
        """Remove old entries to prevent memory growth."""
        now = time.time()
        window_start = now - 60

        for client_id in list(self._requests.keys()):
            self._requests[client_id] = [
                ts for ts in self._requests[client_id]
                if ts > window_start
            ]
            if not self._requests[client_id]:
                del self._requests[client_id]


# =============================================================================
# Security Audit Logging
# =============================================================================

class SecurityAuditLogger:
    """Log security-relevant events."""

    def __init__(self):
        self.logger = logging.getLogger("security.audit")

    def log_auth_success(self, request: Request, key_id: str):
        """Log successful authentication."""
        self.logger.info(
            "AUTH_SUCCESS",
            extra={
                "event": "auth_success",
                "key_id": key_id,
                "ip": self._get_ip(request),
                "path": request.url.path,
                "method": request.method,
            }
        )

    def log_auth_failure(self, request: Request, reason: str):
        """Log failed authentication."""
        self.logger.warning(
            "AUTH_FAILURE",
            extra={
                "event": "auth_failure",
                "reason": reason,
                "ip": self._get_ip(request),
                "path": request.url.path,
                "method": request.method,
            }
        )

    def log_rate_limit(self, request: Request):
        """Log rate limit hit."""
        self.logger.warning(
            "RATE_LIMIT",
            extra={
                "event": "rate_limit",
                "ip": self._get_ip(request),
                "path": request.url.path,
            }
        )

    def log_input_validation_failure(self, request: Request, field: str, reason: str):
        """Log input validation failure."""
        self.logger.warning(
            "INPUT_VALIDATION_FAILURE",
            extra={
                "event": "input_validation_failure",
                "field": field,
                "reason": reason,
                "ip": self._get_ip(request),
                "path": request.url.path,
            }
        )

    def log_suspicious_activity(self, request: Request, activity: str):
        """Log suspicious activity."""
        self.logger.error(
            "SUSPICIOUS_ACTIVITY",
            extra={
                "event": "suspicious_activity",
                "activity": activity,
                "ip": self._get_ip(request),
                "path": request.url.path,
                "user_agent": request.headers.get("User-Agent", ""),
            }
        )

    def _get_ip(self, request: Request) -> str:
        """Get client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# Global audit logger
audit_logger = SecurityAuditLogger()


# =============================================================================
# CSRF Protection (for future form support)
# =============================================================================

def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Verify a CSRF token using constant-time comparison."""
    return hmac.compare_digest(token, stored_token)


# =============================================================================
# Secure Random Generation
# =============================================================================

def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"dh_{secrets.token_urlsafe(32)}"


def generate_session_id() -> str:
    """Generate a secure session ID."""
    return secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


# =============================================================================
# Decorators
# =============================================================================

def require_https(func: Callable) -> Callable:
    """Decorator to require HTTPS connections."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if request.url.scheme != "https":
            # Check for proxy headers
            forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
            if forwarded_proto.lower() != "https":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="HTTPS required"
                )
        return await func(request, *args, **kwargs)
    return wrapper


def log_security_event(event_type: str):
    """Decorator to log security events."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                result = await func(request, *args, **kwargs)
                audit_logger.log_auth_success(request, event_type)
                return result
            except HTTPException as e:
                if e.status_code in (401, 403):
                    audit_logger.log_auth_failure(request, str(e.detail))
                raise
        return wrapper
    return decorator
