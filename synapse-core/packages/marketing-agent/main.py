"""
Synapse Core - FastAPI Server
Main entry point for the marketing agent API server.
"""

import os
import json
import logging
from typing import Optional, Literal, AsyncGenerator
from datetime import datetime, UTC
import asyncio

from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import (
    create_access_token,
    decode_access_token,
    extract_token_from_header,
    Token,
    TokenData,
)

# Development mode - allows unauthenticated access for local testing
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"


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

# Track server startup time for uptime calculation
_server_start_time = datetime.now(UTC)

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


class UnifiedInvokeRequest(BaseModel):
    """Unified request model for invoking any agent."""
    agent: Literal["scribe", "architect", "sentry"] = Field(
        ..., description="The agent to invoke"
    )
    thread_id: str = Field(..., description="Conversation thread ID")
    prompt: str = Field(..., description="The user's prompt/request")
    user_id: Optional[str] = Field(None, description="Optional user ID override")
    stream: bool = Field(False, description="Enable streaming response")


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
@app.get("/health", response_model=HealthResponse)
async def health():
    """Enhanced health check with detailed diagnostics."""
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


@app.post("/invoke")
async def unified_invoke(
    request: UnifiedInvokeRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Unified endpoint to invoke any agent.

    This endpoint routes requests to the appropriate agent based on the
    'agent' parameter. Supports both regular and streaming responses.
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
@app.get("/conversations/{thread_id}")
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


@app.get("/conversations")
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


@app.get("/content")
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


@app.post("/content/search")
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


# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
