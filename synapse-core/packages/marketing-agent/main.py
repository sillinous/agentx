"""
Synapse Agent Server - Main FastAPI Application
Provides API endpoints for interacting with the Synapse Agent Swarm.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# Add agent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "builder-agent"))
sys.path.insert(0, str(Path(__file__).parent.parent / "analytics-agent"))

from scribe import get_scribe_agent  # noqa: E402
from architect import get_architect_agent  # noqa: E402
from sentry import get_sentry_agent  # noqa: E402
from auth import (  # noqa: E402
    create_development_token,
    decode_access_token,
    extract_token_from_header,
    Token,
    TokenData,
)

# --- Logger Configuration ---
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI(
    title="Synapse Agent Server",
    description="An API server to interact with the Synapse Agent Swarm.",
    version="1.0.0",
)


# --- API Models ---
class AgentRequest(BaseModel):
    thread_id: str
    prompt: str


class ScribeRequest(BaseModel):
    thread_id: str
    user_id: Optional[str] = None
    prompt: str


class AgentResponse(BaseModel):
    response: dict


class VerifyResponse(BaseModel):
    valid: bool
    user_id: str
    email: Optional[str]
    subscription_tier: Optional[str]


# --- Agent Initialization ---
scribe_agent_app = get_scribe_agent()
architect_agent_app = get_architect_agent()
sentry_agent_app = get_sentry_agent()


# --- Helper Functions ---
def parse_agent_response(content: str) -> dict:
    """
    Parses agent response content. If JSON, parse it. Otherwise, wrap in text structure.
    """
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {"type": "text", "content": content}


def get_current_user(authorization: str = Header(...)) -> TokenData:
    """
    Dependency to extract and validate JWT token from Authorization header.
    """
    token = extract_token_from_header(authorization)
    return decode_access_token(token)


# --- Root Endpoint ---
@app.get("/")
def read_root():
    """Root endpoint with server info and available agents."""
    return {
        "message": "Synapse Agent Server is running. Visit /docs for API documentation.",
        "version": "1.0.0",
        "agents": {
            "scribe": {
                "name": "The Scribe",
                "description": "Marketing content generation agent",
                "endpoint": "/invoke/scribe",
            },
            "architect": {
                "name": "The Architect",
                "description": "React/Next.js component builder agent",
                "endpoint": "/invoke/architect",
            },
            "sentry": {
                "name": "The Sentry",
                "description": "Analytics and business intelligence agent",
                "endpoint": "/invoke/sentry",
            },
        },
    }


# --- Health Check Endpoint ---
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and orchestration."""
    from database_utils import check_database_health

    db_health = check_database_health()

    return {
        "status": "healthy" if db_health["connected"] else "degraded",
        "version": "1.0.0",
        "database": db_health,
        "agents": {
            "scribe": "ready",
            "architect": "ready",
            "sentry": "ready",
        },
    }


# --- Auth Endpoints ---
@app.post("/auth/dev-token", response_model=Token)
async def create_dev_token():
    """
    Creates a development token for testing purposes.
    Only available in non-production environments.
    """
    if os.getenv("NODE_ENV") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development tokens not available in production",
        )

    token = create_development_token()
    logger.info("Development token created")

    return Token(access_token=token, token_type="bearer")


@app.get("/auth/verify", response_model=VerifyResponse)
async def verify_token(authorization: str = Header(...)):
    """
    Verifies a JWT token and returns the decoded user information.
    """
    try:
        token_data = get_current_user(authorization)
        return VerifyResponse(
            valid=True,
            user_id=token_data.user_id,
            email=token_data.email,
            subscription_tier=token_data.subscription_tier,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# --- Agent Endpoints ---
@app.post("/invoke/scribe", response_model=AgentResponse)
async def invoke_scribe_agent(
    request: ScribeRequest,
    authorization: str = Header(...),
):
    """
    Invokes The Scribe agent with a given prompt.
    Requires JWT authentication.
    """
    token_data = get_current_user(authorization)
    user_id = request.user_id or token_data.user_id

    config = {"configurable": {"thread_id": request.thread_id, "user_id": user_id}}

    input_message = HumanMessage(content=request.prompt)

    logger.info(
        "Invoking Scribe agent",
        extra={"user_id": user_id, "thread_id": request.thread_id},
    )

    final_state = scribe_agent_app.invoke({"messages": [input_message]}, config=config)
    response_content = final_state["messages"][-1].content
    parsed_response = parse_agent_response(response_content)

    return AgentResponse(response=parsed_response)


@app.post("/invoke/architect", response_model=AgentResponse)
async def invoke_architect_agent(
    request: AgentRequest,
    authorization: str = Header(...),
):
    """
    Invokes The Architect agent to generate React/Next.js components.
    Requires JWT authentication.
    """
    token_data = get_current_user(authorization)

    config = {
        "configurable": {"thread_id": request.thread_id, "user_id": token_data.user_id}
    }

    input_message = HumanMessage(content=request.prompt)

    logger.info(
        "Invoking Architect agent",
        extra={"user_id": token_data.user_id, "thread_id": request.thread_id},
    )

    final_state = architect_agent_app.invoke(
        {"messages": [input_message]}, config=config
    )
    response_content = final_state["messages"][-1].content
    parsed_response = parse_agent_response(response_content)

    return AgentResponse(response=parsed_response)


@app.post("/invoke/sentry", response_model=AgentResponse)
async def invoke_sentry_agent(
    request: AgentRequest,
    authorization: str = Header(...),
):
    """
    Invokes The Sentry agent for analytics and business intelligence.
    Requires JWT authentication.
    """
    token_data = get_current_user(authorization)

    config = {
        "configurable": {"thread_id": request.thread_id, "user_id": token_data.user_id}
    }

    input_message = HumanMessage(content=request.prompt)

    logger.info(
        "Invoking Sentry agent",
        extra={"user_id": token_data.user_id, "thread_id": request.thread_id},
    )

    final_state = sentry_agent_app.invoke({"messages": [input_message]}, config=config)
    response_content = final_state["messages"][-1].content
    parsed_response = parse_agent_response(response_content)

    return AgentResponse(response=parsed_response)


# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn

    print("--- Starting Synapse Agent Server ---")
    print("API documentation will be available at http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
