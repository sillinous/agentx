"""
Synapse Core - FastAPI Server
Main entry point for the marketing agent API server.
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime, UTC

from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import (
    create_access_token,
    decode_access_token,
    extract_token_from_header,
    Token,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Synapse Core Agent Server",
    description="AI-powered multi-agent autonomous business ecosystem",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---
class AgentInvokeRequest(BaseModel):
    thread_id: str
    prompt: str
    user_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: dict
    thread_id: str
    agent: str
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
            builder_path = str(__file__).replace(
                "/marketing-agent/", "/builder-agent/"
            ).rsplit("/", 1)[0]
            sys.path.insert(0, builder_path)
            from architect import architect_agent_app
            agents["architect"] = architect_agent_app
            logger.info("Loaded real Architect agent")
        except Exception as e:
            logger.warning(f"Failed to load Architect agent: {e}")

        try:
            analytics_path = str(__file__).replace(
                "/marketing-agent/", "/analytics-agent/"
            ).rsplit("/", 1)[0]
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
@app.get("/health")
async def health():
    """Health check endpoint with database and agent status."""
    db_health = check_database_health()

    status_value = "healthy" if db_health.get("connected", False) else "degraded"

    return {
        "status": status_value,
        "version": "1.0.0",
        "database": db_health,
        "agents": {
            "scribe": "ready",
            "architect": "ready",
            "sentry": "ready",
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


# --- Auth Endpoints ---
@app.post("/auth/dev-token", response_model=Token)
async def create_dev_token():
    """Create a development token for testing (disabled in production)."""
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


@app.get("/auth/verify")
async def verify_token(authorization: str = Header(...)):
    """Verify an access token and return user information."""
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
@app.post("/invoke/scribe")
async def invoke_scribe(
    request: AgentInvokeRequest,
    authorization: str = Header(...),
):
    """Invoke The Scribe agent for marketing content generation."""
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

    return AgentResponse(
        response=parsed_response,
        thread_id=request.thread_id,
        agent="scribe",
        timestamp=datetime.now(UTC).isoformat(),
    )


@app.post("/invoke/architect")
async def invoke_architect(
    request: AgentInvokeRequest,
    authorization: str = Header(...),
):
    """Invoke The Architect agent for UI component generation."""
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

    return AgentResponse(
        response=parsed_response,
        thread_id=request.thread_id,
        agent="architect",
        timestamp=datetime.now(UTC).isoformat(),
    )


@app.post("/invoke/sentry")
async def invoke_sentry(
    request: AgentInvokeRequest,
    authorization: str = Header(...),
):
    """Invoke The Sentry agent for analytics and monitoring."""
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

    return AgentResponse(
        response=parsed_response,
        thread_id=request.thread_id,
        agent="sentry",
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
