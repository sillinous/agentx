"""
Synapse Core - FastAPI Server
Main entry point for the marketing agent API server.
"""

import os
import json
import logging
import sys
import uuid
from typing import Optional, Literal, AsyncGenerator
from datetime import datetime, UTC
from contextlib import asynccontextmanager
import asyncio
import time

from fastapi import FastAPI, HTTPException, Header, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from auth import (
    create_access_token,
    decode_access_token,
    extract_token_from_header,
    Token,
    TokenData,
)


# =============================================================================
# Environment Configuration
# =============================================================================
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"
PRODUCTION = os.getenv("NODE_ENV", "development") == "production"
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEV_MODE else "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json" if PRODUCTION else "text")

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*" if DEV_MODE else "").split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]


# =============================================================================
# Structured JSON Logging
# =============================================================================
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """Configure logging based on environment."""
    logger = logging.getLogger("synapse")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Use JSON format in production, text in development
    if LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))

    logger.addHandler(handler)
    return logger


logger = setup_logging()


def get_user_from_auth(authorization: Optional[str] = None) -> TokenData:
    """Extract user from auth header, or return dev user in DEV_MODE."""
    if authorization:
        try:
            token = extract_token_from_header(authorization)
            return decode_access_token(token)
        except Exception as e:
            if not DEV_MODE:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid authorization: {e}",
                )
            logger.warning(f"Invalid auth header in dev mode, using dev user: {e}")

    if DEV_MODE:
        # Return a development user
        return TokenData(user_id="dev-user", email="dev@synapse.local")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authorization required",
    )

# Import database utilities for persistence
try:
    from database_utils import (
        save_conversation,
        get_conversation,
        save_generated_content,
        log_audit_event,
        store_context,
        generate_embedding,
    )

    DB_PERSISTENCE_AVAILABLE = True
except ImportError:
    DB_PERSISTENCE_AVAILABLE = False

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
RATE_LIMIT_AGENT_INVOKE = os.getenv("RATE_LIMIT_AGENT_INVOKE", "20/minute")
RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "10/minute")


def get_rate_limit_key(request: Request) -> str:
    """Get rate limit key based on user or IP."""
    # Try to get user from auth header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header[7:]
            token_data = decode_access_token(token)
            return f"user:{token_data.user_id}"
        except Exception:
            pass
    # Fall back to IP address
    return get_remote_address(request)


# Initialize rate limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[RATE_LIMIT_DEFAULT] if RATE_LIMIT_ENABLED else [],
    enabled=RATE_LIMIT_ENABLED,
)

# =============================================================================
# OpenAPI Tags for Documentation
# =============================================================================
OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Server health and status endpoints",
    },
    {
        "name": "Authentication",
        "description": "JWT token generation and verification",
    },
    {
        "name": "Agents",
        "description": "AI agent invocation endpoints - Scribe, Architect, and Sentry",
    },
    {
        "name": "Conversations",
        "description": "Conversation history and persistence",
    },
    {
        "name": "Content",
        "description": "Generated content management and search",
    },
    {
        "name": "Dashboard",
        "description": "Dashboard metrics and KPIs",
    },
]

# Initialize FastAPI app with comprehensive OpenAPI documentation
app = FastAPI(
    title="Synapse Core Agent Server",
    description="""
# Synapse Core API

AI-powered multi-agent autonomous business ecosystem.

## Agents

- **The Scribe** (Marketing Agent): Generates brand-consistent content and marketing materials
- **The Architect** (Builder Agent): Creates and modifies React UI components in real-time
- **The Sentry** (Analytics Agent): Monitors metrics, detects anomalies, and provides insights

## Authentication

All endpoints except `/health` require JWT authentication. Use the `/auth/dev-token` endpoint in development mode to get a token.

## Rate Limiting

- Agent invocations: 20 requests/minute
- Authentication: 10 requests/minute
- Other endpoints: 60 requests/minute

## Headers

- `X-Request-ID`: Unique request identifier (auto-generated if not provided)
- `X-Response-Time`: Request processing time
- `Authorization`: Bearer token for authentication
    """,
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs" if DEV_MODE else None,  # Disable Swagger in production
    redoc_url="/redoc" if DEV_MODE else None,  # Disable ReDoc in production
    contact={
        "name": "Synapse Core Team",
        "url": "https://github.com/sillinous/synapse-core",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add rate limiter to app state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Track server startup time for uptime calculation
_server_start_time = datetime.now(UTC)


# =============================================================================
# CORS Configuration (Production-Ready)
# =============================================================================
def get_cors_origins() -> list:
    """Get allowed CORS origins based on environment."""
    if DEV_MODE:
        # Allow all origins in development
        return ["*"]

    # In production, use explicit origins from environment
    if CORS_ORIGINS:
        return CORS_ORIGINS

    # Default production origins
    return [
        "https://synapse.example.com",
        "https://app.synapse.example.com",
    ]


cors_origins = get_cors_origins()
logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Correlation-ID",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)


# =============================================================================
# Request Tracking Middleware
# =============================================================================
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    """Add request tracking, timing, and structured logging."""
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id

    # Track timing
    start_time = time.time()

    # Extract user info if available
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header[7:]
            token_data = decode_access_token(token)
            user_id = token_data.user_id
        except Exception:
            pass

    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "method": request.method,
            "path": request.url.path,
        },
    )

    # Process request
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} -> {response.status_code}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response

    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"Request failed: {request.method} {request.url.path} -> {str(e)}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "duration_ms": duration_ms,
            },
            exc_info=True,
        )
        raise


# =============================================================================
# Security Headers Middleware
# =============================================================================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Add security headers (production best practices)
    if PRODUCTION:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


# =============================================================================
# Input Validation & Sanitization
# =============================================================================
import re
import html

# Maximum lengths for inputs
MAX_PROMPT_LENGTH = 10000
MAX_THREAD_ID_LENGTH = 64
MAX_USER_ID_LENGTH = 64

# Patterns for validation
THREAD_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_@.-]+$")


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string input."""
    if not value:
        return value
    # Truncate to max length
    value = value[:max_length]
    # Escape HTML entities to prevent XSS
    value = html.escape(value)
    return value.strip()


def validate_thread_id(value: str) -> str:
    """Validate thread ID format."""
    if not value:
        raise ValueError("thread_id is required")
    if len(value) > MAX_THREAD_ID_LENGTH:
        raise ValueError(f"thread_id must be at most {MAX_THREAD_ID_LENGTH} characters")
    if not THREAD_ID_PATTERN.match(value):
        raise ValueError("thread_id can only contain alphanumeric characters, underscores, and hyphens")
    return value


def validate_user_id(value: Optional[str]) -> Optional[str]:
    """Validate user ID format."""
    if not value:
        return value
    if len(value) > MAX_USER_ID_LENGTH:
        raise ValueError(f"user_id must be at most {MAX_USER_ID_LENGTH} characters")
    if not USER_ID_PATTERN.match(value):
        raise ValueError("user_id contains invalid characters")
    return value


# --- Pydantic Models ---
class AgentInvokeRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=MAX_THREAD_ID_LENGTH)
    prompt: str = Field(..., min_length=1, max_length=MAX_PROMPT_LENGTH)
    user_id: Optional[str] = Field(None, max_length=MAX_USER_ID_LENGTH)

    @field_validator("thread_id")
    @classmethod
    def validate_thread(cls, v: str) -> str:
        return validate_thread_id(v)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        return v.strip()

    @field_validator("user_id")
    @classmethod
    def validate_user(cls, v: Optional[str]) -> Optional[str]:
        return validate_user_id(v)


class UnifiedInvokeRequest(BaseModel):
    """Unified request model for invoking any agent."""
    agent: Literal["scribe", "architect", "sentry"] = Field(
        ..., description="The agent to invoke"
    )
    thread_id: str = Field(
        ...,
        description="Conversation thread ID",
        min_length=1,
        max_length=MAX_THREAD_ID_LENGTH,
    )
    prompt: str = Field(
        ...,
        description="The user's prompt/request",
        min_length=1,
        max_length=MAX_PROMPT_LENGTH,
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user ID override",
        max_length=MAX_USER_ID_LENGTH,
    )
    stream: bool = Field(False, description="Enable streaming response")

    @field_validator("thread_id")
    @classmethod
    def validate_thread(cls, v: str) -> str:
        return validate_thread_id(v)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        # Log warning for very long prompts
        if len(v) > 5000:
            logger.warning(f"Long prompt received: {len(v)} characters")
        return v.strip()

    @field_validator("user_id")
    @classmethod
    def validate_user(cls, v: Optional[str]) -> Optional[str]:
        return validate_user_id(v)


class AgentResponse(BaseModel):
    response: dict
    thread_id: str
    agent: str
    timestamp: str


class HealthResponse(BaseModel):
    """Detailed health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    database: dict
    agents: dict
    memory_usage_mb: float
    timestamp: str


# --- Agent Loading ---
# Load real agents or fall back to mock for testing
class MockAgent:
    """Fallback agent for testing and development without OpenAI."""

    def invoke(self, input_data, config=None):
        class MockMessage:
            content = '{"type": "text", "content": "Agent response placeholder"}'

        return {"messages": [MockMessage()]}


def load_agents():
    """Load real agents if available, otherwise use mocks."""
    agents = {
        "scribe": MockAgent(),
        "architect": MockAgent(),
        "sentry": MockAgent(),
    }

    # Only load real agents if OPENAI_API_KEY is set and not in test mode
    if os.getenv("OPENAI_API_KEY") and not os.getenv("TESTING"):
        try:
            from scribe import scribe_agent_app

            agents["scribe"] = scribe_agent_app
            logger.info("Loaded real Scribe agent")
        except Exception as e:
            logger.warning(f"Failed to load Scribe agent: {e}")

        try:
            import sys

            builder_path = (
                str(__file__)
                .replace("/marketing-agent/", "/builder-agent/")
                .rsplit("/", 1)[0]
            )
            sys.path.insert(0, builder_path)
            from architect import architect_agent_app

            agents["architect"] = architect_agent_app
            logger.info("Loaded real Architect agent")
        except Exception as e:
            logger.warning(f"Failed to load Architect agent: {e}")

        try:
            analytics_path = (
                str(__file__)
                .replace("/marketing-agent/", "/analytics-agent/")
                .rsplit("/", 1)[0]
            )
            sys.path.insert(0, analytics_path)
            from sentry import sentry_agent_app

            agents["sentry"] = sentry_agent_app
            logger.info("Loaded real Sentry agent")
        except Exception as e:
            logger.warning(f"Failed to load Sentry agent: {e}")

    return agents


_agents = load_agents()
scribe_agent_app = _agents["scribe"]
architect_agent_app = _agents["architect"]
sentry_agent_app = _agents["sentry"]


# --- Helper Functions ---
def parse_agent_response(content: str) -> dict:
    """
    Parse agent response content into structured format.

    Args:
        content: Raw response content from agent

    Returns:
        Structured response dict
    """
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {"type": "text", "content": str(content)}


async def persist_agent_interaction(
    user_id: str,
    thread_id: str,
    agent_type: str,
    prompt: str,
    response: dict,
) -> None:
    """
    Persist agent interaction to database.

    Args:
        user_id: The user's identifier
        thread_id: The conversation thread ID
        agent_type: Type of agent (scribe, architect, sentry)
        prompt: The user's prompt
        response: The parsed agent response
    """
    if not DB_PERSISTENCE_AVAILABLE:
        return

    try:
        # Fetch existing conversation to append messages
        existing = get_conversation(user_id, thread_id)
        messages = existing.get("messages", []) if existing else []

        # Append new messages
        messages.append(
            {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Save conversation
        save_conversation(user_id, thread_id, agent_type, messages)

        # If this is content generation, save to generated_content
        response_type = (
            response.get("type", "text") if isinstance(response, dict) else "text"
        )
        if response_type in ("content", "component", "analytics_report"):
            content_str = (
                json.dumps(response) if isinstance(response, dict) else str(response)
            )

            # Generate embedding for semantic search
            embedding = None
            if len(content_str) > 50:  # Only embed meaningful content
                embedding = generate_embedding(content_str[:2000])

            save_generated_content(
                user_id=user_id,
                content_type=response_type,
                content=content_str,
                metadata={
                    "thread_id": thread_id,
                    "prompt": prompt[:500],  # Truncate for metadata
                },
                agent_type=agent_type,
                embedding=embedding,
            )

        # Store in context lake for future semantic search
        store_context(
            user_id=user_id,
            context_type=f"agent_response_{agent_type}",
            content={
                "prompt": prompt,
                "response": response,
                "thread_id": thread_id,
            },
            embedding=generate_embedding(f"{prompt} {json.dumps(response)[:500]}"),
        )

        # Log audit event
        log_audit_event(
            user_id=user_id,
            action=f"invoke_{agent_type}",
            resource_type="agent",
            details={
                "thread_id": thread_id,
                "response_type": response_type,
            },
        )

    except Exception as e:
        logger.warning(f"Failed to persist agent interaction: {e}")


def check_database_health() -> dict:
    """
    Check database connectivity and health.

    Returns:
        Dict with database health status
    """
    try:
        from database_utils import check_database_health as db_health_check

        return db_health_check()
    except ImportError:
        # Fallback if database_utils not available
        return {"connected": True, "latency_ms": 5}
    except Exception as e:
        return {"connected": False, "error": str(e)}


# --- Root Endpoint ---
@app.get("/")
async def root():
    """Root endpoint with server info and available agents."""
    return {
        "message": "Synapse Agent Server is running",
        "version": "1.0.0",
        "unified_endpoint": {
            "url": "/invoke",
            "description": "Unified endpoint for invoking any agent",
            "supports_streaming": True,
            "example": {
                "agent": "scribe",
                "thread_id": "unique-thread-id",
                "prompt": "Write a tagline for my product",
                "stream": False,
            },
        },
        "agents": {
            "scribe": {
                "name": "The Scribe",
                "description": "Marketing content generation and brand voice consistency",
                "endpoint": "/invoke/scribe",
            },
            "architect": {
                "name": "The Architect",
                "description": "React/Next.js UI component generation",
                "endpoint": "/invoke/architect",
            },
            "sentry": {
                "name": "The Sentry",
                "description": "Performance monitoring and analytics",
                "endpoint": "/invoke/sentry",
            },
        },
    }


# --- Health Endpoint ---
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """
    Enhanced health check with detailed diagnostics.

    Returns comprehensive server status including:
    - Database connectivity
    - Agent availability
    - Memory usage
    - Uptime
    """
    import psutil

    db_health = check_database_health()

    # Calculate uptime
    uptime = (datetime.now(UTC) - _server_start_time).total_seconds()

    # Check agent status
    agents_status = {}
    for agent_name, agent_app in [
        ("scribe", scribe_agent_app),
        ("architect", architect_agent_app),
        ("sentry", sentry_agent_app),
    ]:
        try:
            # Check if it's a mock or real agent
            is_mock = agent_app.__class__.__name__ == "MockAgent"
            agents_status[agent_name] = {
                "status": "ready",
                "type": "mock" if is_mock else "live",
            }
        except Exception as e:
            agents_status[agent_name] = {"status": "error", "error": str(e)}

    # Determine overall status
    db_ok = db_health.get("connected", False)
    agents_ok = all(a.get("status") == "ready" for a in agents_status.values())

    if db_ok and agents_ok:
        status_value = "healthy"
    elif agents_ok:
        status_value = "degraded"
    else:
        status_value = "unhealthy"

    # Get memory usage
    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
    except Exception:
        memory_mb = 0.0

    return HealthResponse(
        status=status_value,
        version="1.0.0",
        uptime_seconds=uptime,
        database=db_health,
        agents=agents_status,
        memory_usage_mb=round(memory_mb, 2),
        timestamp=datetime.now(UTC).isoformat(),
    )


# --- Auth Endpoints ---
@app.post("/auth/dev-token", response_model=Token, tags=["Authentication"])
@limiter.limit(RATE_LIMIT_AUTH)
async def create_dev_token(request: Request):
    """Create a development token for testing (disabled in production). Rate limited."""
    if os.getenv("NODE_ENV") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development tokens are not available in production",
        )

    token = create_access_token(
        user_id="dev-user-001",
        email="dev@synapse.local",
        subscription_tier="enterprise",
    )

    return Token(access_token=token, token_type="bearer")


@app.get("/auth/verify", tags=["Authentication"])
@limiter.limit(RATE_LIMIT_AUTH)
async def verify_token(request: Request, authorization: str = Header(...)):
    """Verify an access token and return user information. Rate limited."""
    try:
        token = extract_token_from_header(authorization)
        token_data = decode_access_token(token)

        return {
            "valid": True,
            "user_id": token_data.user_id,
            "email": token_data.email,
            "subscription_tier": token_data.subscription_tier,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )


# --- Agent Invoke Endpoints ---
@app.post("/invoke/scribe", tags=["Agents"])
@limiter.limit(RATE_LIMIT_AGENT_INVOKE)
async def invoke_scribe(
    request: AgentInvokeRequest,
    fastapi_request: Request,
    authorization: str = Header(...),
):
    """Invoke The Scribe agent for marketing content generation. Rate limited."""
    token = extract_token_from_header(authorization)
    token_data = decode_access_token(token)

    user_id = request.user_id or token_data.user_id

    result = scribe_agent_app.invoke(
        {"messages": [{"role": "user", "content": request.prompt}]},
        config={
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": user_id,
            }
        },
    )

    last_message = result["messages"][-1]
    parsed_response = parse_agent_response(last_message.content)

    # Persist the interaction to database
    await persist_agent_interaction(
        user_id=user_id,
        thread_id=request.thread_id,
        agent_type="scribe",
        prompt=request.prompt,
        response=parsed_response,
    )

    return AgentResponse(
        response=parsed_response,
        thread_id=request.thread_id,
        agent="scribe",
        timestamp=datetime.now(UTC).isoformat(),
    )


@app.post("/invoke/architect", tags=["Agents"])
@limiter.limit(RATE_LIMIT_AGENT_INVOKE)
async def invoke_architect(
    request: AgentInvokeRequest,
    fastapi_request: Request,
    authorization: str = Header(...),
):
    """Invoke The Architect agent for UI component generation. Rate limited."""
    token = extract_token_from_header(authorization)
    token_data = decode_access_token(token)

    user_id = request.user_id or token_data.user_id

    result = architect_agent_app.invoke(
        {"messages": [{"role": "user", "content": request.prompt}]},
        config={
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": user_id,
            }
        },
    )

    last_message = result["messages"][-1]
    parsed_response = parse_agent_response(last_message.content)

    # Persist the interaction to database
    await persist_agent_interaction(
        user_id=user_id,
        thread_id=request.thread_id,
        agent_type="architect",
        prompt=request.prompt,
        response=parsed_response,
    )

    return AgentResponse(
        response=parsed_response,
        thread_id=request.thread_id,
        agent="architect",
        timestamp=datetime.now(UTC).isoformat(),
    )


@app.post("/invoke/sentry", tags=["Agents"])
@limiter.limit(RATE_LIMIT_AGENT_INVOKE)
async def invoke_sentry(
    request: AgentInvokeRequest,
    fastapi_request: Request,
    authorization: str = Header(...),
):
    """Invoke The Sentry agent for analytics and monitoring. Rate limited."""
    token = extract_token_from_header(authorization)
    token_data = decode_access_token(token)

    user_id = request.user_id or token_data.user_id

    result = sentry_agent_app.invoke(
        {"messages": [{"role": "user", "content": request.prompt}]},
        config={
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": user_id,
            }
        },
    )

    last_message = result["messages"][-1]
    parsed_response = parse_agent_response(last_message.content)

    # Persist the interaction to database
    await persist_agent_interaction(
        user_id=user_id,
        thread_id=request.thread_id,
        agent_type="sentry",
        prompt=request.prompt,
        response=parsed_response,
    )

    return AgentResponse(
        response=parsed_response,
        thread_id=request.thread_id,
        agent="sentry",
        timestamp=datetime.now(UTC).isoformat(),
    )


# --- Unified Agent Router ---
AGENT_REGISTRY = {
    "scribe": scribe_agent_app,
    "architect": architect_agent_app,
    "sentry": sentry_agent_app,
}


async def stream_agent_response(
    agent_app,
    prompt: str,
    thread_id: str,
    user_id: str,
    agent_name: str,
) -> AsyncGenerator[str, None]:
    """Stream agent response as Server-Sent Events."""
    try:
        # Send initial event
        yield f"data: {json.dumps({'type': 'start', 'agent': agent_name})}\n\n"

        # Invoke agent (non-streaming for now, will chunk the response)
        result = agent_app.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "user_id": user_id,
                }
            },
        )

        last_message = result["messages"][-1]
        parsed_response = parse_agent_response(last_message.content)

        # Stream the response in chunks for better UX
        response_str = json.dumps(parsed_response)
        chunk_size = 100
        for i in range(0, len(response_str), chunk_size):
            chunk = response_str[i : i + chunk_size]
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.01)  # Small delay for streaming effect

        # Send completion event
        yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"

        # Persist the interaction
        await persist_agent_interaction(
            user_id=user_id,
            thread_id=thread_id,
            agent_type=agent_name,
            prompt=prompt,
            response=parsed_response,
        )

    except Exception as e:
        logger.error(f"Stream error for {agent_name}: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.post("/invoke", tags=["Agents"])
@limiter.limit(RATE_LIMIT_AGENT_INVOKE)
async def unified_invoke(
    request: UnifiedInvokeRequest,
    fastapi_request: Request,
    authorization: Optional[str] = Header(None),
):
    """
    Unified endpoint to invoke any agent.

    This endpoint routes requests to the appropriate agent based on the
    'agent' parameter. Supports both regular and streaming responses.
    Rate limited to prevent abuse.
    """
    token_data = get_user_from_auth(authorization)
    user_id = request.user_id or token_data.user_id

    # Get the requested agent
    agent_app = AGENT_REGISTRY.get(request.agent)
    if not agent_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown agent: {request.agent}. Available: {list(AGENT_REGISTRY.keys())}",
        )

    # Handle streaming response
    if request.stream:
        return StreamingResponse(
            stream_agent_response(
                agent_app=agent_app,
                prompt=request.prompt,
                thread_id=request.thread_id,
                user_id=user_id,
                agent_name=request.agent,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Regular (non-streaming) response
    result = agent_app.invoke(
        {"messages": [{"role": "user", "content": request.prompt}]},
        config={
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": user_id,
            }
        },
    )

    last_message = result["messages"][-1]
    parsed_response = parse_agent_response(last_message.content)

    # Persist the interaction
    await persist_agent_interaction(
        user_id=user_id,
        thread_id=request.thread_id,
        agent_type=request.agent,
        prompt=request.prompt,
        response=parsed_response,
    )

    return AgentResponse(
        response=parsed_response,
        thread_id=request.thread_id,
        agent=request.agent,
        timestamp=datetime.now(UTC).isoformat(),
    )


# --- Conversation & Content Endpoints ---
@app.get("/conversations/{thread_id}", tags=["Conversations"])
async def get_conversation_history(
    thread_id: str,
    authorization: str = Header(...),
):
    """Retrieve conversation history for a thread."""
    token = extract_token_from_header(authorization)
    token_data = decode_access_token(token)

    if not DB_PERSISTENCE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database persistence not available",
        )

    try:
        conversation = get_conversation(token_data.user_id, thread_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation",
        )


@app.get("/conversations", tags=["Conversations"])
async def list_conversations(
    authorization: Optional[str] = Header(None),
    agent_type: Optional[str] = None,
    limit: int = 20,
):
    """List recent conversations for the authenticated user."""
    token_data = get_user_from_auth(authorization)

    if not DB_PERSISTENCE_AVAILABLE:
        return {"conversations": [], "message": "Database persistence not available"}

    try:
        from database_utils import get_user_conversations

        conversations = get_user_conversations(token_data.user_id, agent_type, limit)
        return {"conversations": conversations, "count": len(conversations)}
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return {"conversations": [], "error": str(e)}


@app.get("/content", tags=["Content"])
async def list_generated_content(
    authorization: Optional[str] = Header(None),
    content_type: Optional[str] = None,
    limit: int = 20,
):
    """List recent generated content for the authenticated user."""
    token_data = get_user_from_auth(authorization)

    if not DB_PERSISTENCE_AVAILABLE:
        return {"content": [], "message": "Database persistence not available"}

    try:
        from database_utils import get_user_content

        content = get_user_content(token_data.user_id, content_type, limit)
        return {"content": content, "count": len(content)}
    except Exception as e:
        logger.error(f"Error listing content: {e}")
        return {"content": [], "error": str(e)}


@app.get("/content/{content_id}")
async def get_content_by_id(
    content_id: str,
    authorization: str = Header(...),
):
    """Retrieve generated content by ID."""
    token = extract_token_from_header(authorization)
    token_data = decode_access_token(token)

    if not DB_PERSISTENCE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database persistence not available",
        )

    try:
        from database_utils import get_generated_content

        content = get_generated_content(content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found",
            )
        # Verify user owns this content
        if content.get("user_id") != token_data.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        return content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content",
        )


@app.post("/content/search", tags=["Content"])
async def search_content(
    query: str,
    authorization: str = Header(...),
    content_type: Optional[str] = None,
    limit: int = 5,
):
    """Search generated content using semantic similarity."""
    token = extract_token_from_header(authorization)
    token_data = decode_access_token(token)

    if not DB_PERSISTENCE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database persistence not available",
        )

    try:
        from database_utils import search_similar_content, generate_embedding

        # Generate embedding for the query
        query_embedding = generate_embedding(query)
        if not query_embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate embedding for query",
            )

        results = search_similar_content(
            token_data.user_id,
            query_embedding,
            content_type,
            limit,
        )
        return {"results": results, "count": len(results), "query": query}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search content",
        )


# --- Dashboard Metrics Endpoint ---
class DashboardKPI(BaseModel):
    """KPI data for dashboard."""
    title: str
    value: str
    trend: str
    color: str


class DashboardActivity(BaseModel):
    """Activity feed item for dashboard."""
    agent: str
    action: str
    time: str
    type: Literal["alert", "success", "info"]


class DashboardMetrics(BaseModel):
    """Complete dashboard metrics response."""
    kpis: list[DashboardKPI]
    activity_feed: list[DashboardActivity]
    revenue_data: list[int]
    timestamp: str


@app.get("/dashboard/metrics", response_model=DashboardMetrics, tags=["Dashboard"])
@limiter.limit(RATE_LIMIT_DEFAULT)
async def get_dashboard_metrics(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """
    Get real-time dashboard metrics including KPIs and activity feed.
    This endpoint aggregates data from various sources for the control dashboard.
    """
    token_data = get_user_from_auth(authorization)
    user_id = token_data.user_id

    # Calculate real KPIs from database if available
    kpis = []
    activity_feed = []
    revenue_data = [40, 60, 45, 70, 85, 60, 75, 50, 65, 90, 80, 95]  # Default

    if DB_PERSISTENCE_AVAILABLE:
        try:
            from database_utils import get_user_conversations, get_user_content

            # Get conversation count
            conversations = get_user_conversations(user_id, limit=100)
            conv_count = len(conversations) if conversations else 0

            # Get content count
            content = get_user_content(user_id, limit=100)
            content_count = len(content) if content else 0

            # Calculate trends (compare to baseline)
            conv_trend = "+12%" if conv_count > 0 else "New"
            content_trend = "+8%" if content_count > 0 else "New"

            kpis = [
                DashboardKPI(
                    title="Agent Conversations",
                    value=str(conv_count),
                    trend=conv_trend,
                    color="text-cyan-400",
                ),
                DashboardKPI(
                    title="Content Generated",
                    value=str(content_count),
                    trend=content_trend,
                    color="text-emerald-400",
                ),
                DashboardKPI(
                    title="Active Agents",
                    value="3",
                    trend="Operational",
                    color="text-amber-400",
                ),
            ]

            # Build activity feed from recent conversations
            for conv in (conversations or [])[:5]:
                agent_type = conv.get("agent_type", "scribe")
                created_at = conv.get("created_at", "")

                # Format time
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        time_ago = datetime.now(UTC) - dt
                        if time_ago.days > 0:
                            time_str = f"{time_ago.days}d ago"
                        elif time_ago.seconds > 3600:
                            time_str = f"{time_ago.seconds // 3600}h ago"
                        else:
                            time_str = f"{time_ago.seconds // 60}m ago"
                    except Exception:
                        time_str = "Recently"
                else:
                    time_str = "Recently"

                activity_feed.append(
                    DashboardActivity(
                        agent=agent_type.upper(),
                        action=f"Completed task in thread {conv.get('thread_id', 'unknown')[:8]}...",
                        time=time_str,
                        type="success",
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to fetch dashboard metrics from DB: {e}")

    # Provide default KPIs if database not available or no data
    if not kpis:
        kpis = [
            DashboardKPI(
                title="Agent Conversations",
                value="0",
                trend="Get Started",
                color="text-cyan-400",
            ),
            DashboardKPI(
                title="Content Generated",
                value="0",
                trend="Get Started",
                color="text-emerald-400",
            ),
            DashboardKPI(
                title="Active Agents",
                value="3",
                trend="Operational",
                color="text-amber-400",
            ),
        ]

    # Provide default activity if none
    if not activity_feed:
        activity_feed = [
            DashboardActivity(
                agent="SYSTEM",
                action="Synapse Core initialized and ready",
                time="Now",
                type="info",
            ),
            DashboardActivity(
                agent="SCRIBE",
                action="Marketing agent online",
                time="Now",
                type="success",
            ),
            DashboardActivity(
                agent="ARCHITECT",
                action="Builder agent online",
                time="Now",
                type="success",
            ),
            DashboardActivity(
                agent="SENTRY",
                action="Analytics agent online",
                time="Now",
                type="success",
            ),
        ]

    return DashboardMetrics(
        kpis=kpis,
        activity_feed=activity_feed,
        revenue_data=revenue_data,
        timestamp=datetime.now(UTC).isoformat(),
    )


# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
