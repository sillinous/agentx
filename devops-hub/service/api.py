"""
Agent Library Service API - FastAPI REST endpoints.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from factory.agent_factory import AgentFactory
from factory.agent_registry import AgentMetadata
from service.agent_loader import get_loader, AgentLoader
from service.workflow_engine import get_workflow_engine, WorkflowStatus, WorkflowDefinition, WorkflowStep, StepType
from service.message_bus import get_message_bus, Event
from service.websocket import router as websocket_router
from core.auth import (
    APIKey, get_api_key, get_api_key_manager, configure_auth,
    require_read, require_write, require_execute, require_admin,
)
from core.database import get_database, get_event_repository
from service.rate_limiter import rate_limit_general, rate_limit_execute
from service.hitl_service import get_hitl_service
from service.logging_config import configure_logging, get_logger
from service.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from service.responses import paginate_list, create_error_response, APIException
from service.integrations_api import router as integrations_router, settings_router

# Configure logging on module import
configure_logging()
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class AgentSummary(BaseModel):
    id: str
    name: str
    version: str
    status: str
    domain: str
    type: str
    description: str
    capabilities: List[str]


class AgentDetail(AgentSummary):
    protocols: List[str]
    implementations: Dict[str, str]
    documentation: str
    performance: Dict[str, Any]


class ExecutionRequest(BaseModel):
    capability: str = Field(..., description="The capability to execute")
    input_data: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


class ExecutionResponse(BaseModel):
    agent_id: str
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float
    timestamp: str


class ValidationResponse(BaseModel):
    is_valid: bool
    agent_id: str
    score: float
    error_count: int
    warning_count: int
    issues: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    total_agents: int
    by_status: Dict[str, int]
    by_domain: Dict[str, int]
    by_type: Dict[str, int]
    capabilities_count: int
    apqc_processes_count: int


class DiscoverResponse(BaseModel):
    agents: List[AgentSummary]
    total: int
    filters_applied: Dict[str, Any]


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., description="Name for the API key")
    scopes: List[str] = Field(default=["read"], description="Scopes for the key")
    expires_in_days: Optional[int] = Field(None, description="Days until expiration")


class APIKeyResponse(BaseModel):
    id: str
    name: str
    scopes: List[str]
    is_active: bool
    created_at: Optional[str]
    last_used_at: Optional[str]
    expires_at: Optional[str]


class CreateAPIKeyResponse(BaseModel):
    key: str
    id: str
    name: str
    scopes: List[str]
    message: str = "Store this key securely. It will not be shown again."


class CreateHITLRequest(BaseModel):
    agent_id: str
    request_type: str
    title: str
    description: str
    required_fields: Dict[str, str] = Field(default_factory=dict)
    priority: str = "medium"
    workflow_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class FulfillHITLRequest(BaseModel):
    fulfilled_by: str
    response_data: Dict[str, Any]
    notes: Optional[str] = None


class RejectHITLRequest(BaseModel):
    rejected_by: str
    reason: str


class HITLRequestResponse(BaseModel):
    id: str
    request_type: str
    title: str
    description: str
    agent_id: str
    priority: str
    status: str
    workflow_id: Optional[str]
    context: Dict[str, Any]
    required_fields: Dict[str, str]
    response_data: Optional[Dict[str, Any]]
    created_at: str
    fulfilled_at: Optional[str]
    fulfilled_by: Optional[str]
    notes: Optional[str]


_factory: Optional[AgentFactory] = None


def get_factory() -> AgentFactory:
    global _factory
    if _factory is None:
        base_path = Path(__file__).parent.parent
        registry_path = base_path / "factory" / "registry.json"
        _factory = AgentFactory(registry_path=registry_path, strict_validation=False)
        existing = base_path / "AGENT_REGISTRY.json"
        if existing.exists() and _factory.registry.count() == 0:
            _factory.import_existing_registry(existing)
    return _factory


def agent_to_summary(m: AgentMetadata) -> AgentSummary:
    return AgentSummary(id=m.id, name=m.name, version=m.version, status=m.status.value,
                        domain=m.domain.value, type=m.agent_type.value,
                        description=m.description, capabilities=m.capabilities)


def agent_to_detail(m: AgentMetadata) -> AgentDetail:
    return AgentDetail(id=m.id, name=m.name, version=m.version, status=m.status.value,
                       domain=m.domain.value, type=m.agent_type.value, description=m.description,
                       capabilities=m.capabilities, protocols=m.protocols,
                       implementations=m.implementations, documentation=m.documentation,
                       performance={"max_concurrent_requests": m.performance.max_concurrent_requests,
                                   "average_latency_ms": m.performance.average_latency_ms,
                                   "uptime_percent": m.performance.uptime_percent})


def get_cors_origins() -> List[str]:
    """Get CORS origins from environment variable."""
    origins_str = os.environ.get("CORS_ORIGINS", "")
    if not origins_str or origins_str == "*":
        # Default: allow all in development, but log a warning
        return ["*"]
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Library Service", version="1.0.0",
                  description="REST API for agent discovery and execution")

    # Add request ID middleware (first, so it's available to all other middleware)
    app.add_middleware(RequestIDMiddleware)

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Configure CORS - use CORS_ORIGINS env var for production security
    cors_origins = get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("Application middleware configured")

    # Exception handlers for standardized error responses
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        request_id = getattr(request.state, 'request_id', None)
        return create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            code=exc.code,
            details=exc.details,
            request_id=request_id,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, 'request_id', None)
        return create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            request_id=request_id,
        )

    # Include WebSocket router for real-time event streaming
    app.include_router(websocket_router)

    # Include integration and settings routers
    app.include_router(integrations_router)
    app.include_router(settings_router)

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health():
        return HealthResponse(status="healthy", timestamp=datetime.now().isoformat(), version="1.0.0")

    @app.get("/health/live", tags=["System"])
    async def health_live():
        """Kubernetes liveness probe - returns 200 if service is running."""
        return {"status": "alive", "timestamp": datetime.now().isoformat()}

    @app.get("/health/ready", tags=["System"])
    async def health_ready():
        """Kubernetes readiness probe - checks dependencies."""
        dependencies = {"database": "unknown", "redis": "unknown"}
        overall_status = "ready"

        # Check database
        try:
            db = get_database()
            db.execute("SELECT 1")
            dependencies["database"] = "healthy"
        except Exception as e:
            dependencies["database"] = f"unhealthy: {str(e)}"
            overall_status = "not_ready"

        # Check Redis (optional)
        try:
            from service.redis_client import get_redis_client
            redis = get_redis_client()
            dependencies["redis"] = "healthy" if redis.is_available else "not_configured"
        except Exception:
            dependencies["redis"] = "unavailable"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "dependencies": dependencies,
        }


    @app.get("/agents", response_model=List[AgentSummary], tags=["Agents"])
    async def list_agents(
        status: Optional[str] = Query(None, description="Filter by agent status"),
        _rate_limit: None = Depends(rate_limit_general),
    ):
        """List all registered agents."""
        factory = get_factory()
        agents = factory.registry.list_all()
        if status:
            agents = [a for a in agents if a.status.value == status]
        return [agent_to_summary(a) for a in agents]

    @app.get("/agents/paginated", tags=["Agents"])
    async def list_agents_paginated(
        status: Optional[str] = Query(None, description="Filter by agent status"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        _rate_limit: None = Depends(rate_limit_general),
    ):
        """
        List all registered agents with pagination.

        Returns paginated response with metadata.
        """
        factory = get_factory()
        agents = factory.registry.list_all()
        if status:
            agents = [a for a in agents if a.status.value == status]

        agent_summaries = [agent_to_summary(a) for a in agents]
        return paginate_list(agent_summaries, page=page, page_size=page_size)

    @app.get("/agents/discover", response_model=DiscoverResponse, tags=["Agents"])
    async def discover(
        domain: Optional[str] = None,
        capability: Optional[str] = None,
        status: Optional[str] = "production",
        agent_type: Optional[str] = None,
        _rate_limit: None = Depends(rate_limit_general),
    ):
        factory = get_factory()
        agents = factory.discover_agents(domain=domain, capability=capability, status=status, agent_type=agent_type)
        return DiscoverResponse(agents=[agent_to_summary(a) for a in agents], total=len(agents),
                                filters_applied={"domain": domain, "capability": capability,
                                                "status": status, "agent_type": agent_type})

    @app.get("/agents/{agent_id}", response_model=AgentDetail, tags=["Agents"])
    async def get_agent(agent_id: str):
        factory = get_factory()
        m = factory.get_agent(agent_id)
        if not m:
            raise HTTPException(404, f"Agent {agent_id} not found")
        return agent_to_detail(m)

    @app.get("/agents/{agent_id}/capabilities", tags=["Agents"])
    async def get_capabilities(agent_id: str):
        factory = get_factory()
        m = factory.get_agent(agent_id)
        if not m:
            raise HTTPException(404, f"Agent {agent_id} not found")
        return {"agent_id": agent_id, "capabilities": m.capabilities, "capability_details": []}

    @app.post("/agents/{agent_id}/execute", response_model=ExecutionResponse, tags=["Execution"])
    async def execute(
        agent_id: str,
        req: ExecutionRequest,
        _rate_limit: None = Depends(rate_limit_execute),
    ):
        factory = get_factory()
        m = factory.get_agent(agent_id)
        if not m:
            raise HTTPException(404, f"Agent {agent_id} not found")

        # Validate capability
        if req.capability not in m.capabilities:
            raise HTTPException(400, f"Agent {agent_id} does not have capability: {req.capability}")

        # Execute using agent loader
        loader = get_loader()
        start = datetime.now()
        response = await loader.execute_agent(
            agent_id=agent_id,
            capability=req.capability,
            payload=req.input_data,
        )
        execution_time = (datetime.now() - start).total_seconds() * 1000

        return ExecutionResponse(
            agent_id=agent_id,
            status="success" if response.success else "error",
            output=response.data if response.success else None,
            error=response.error if not response.success else None,
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat(),
        )

    @app.get("/agents/{agent_id}/health", tags=["Agents"])
    async def get_agent_health(agent_id: str):
        """Get runtime health of an agent instance."""
        loader = get_loader()
        health = loader.get_agent_health(agent_id)
        if not health:
            raise HTTPException(404, f"Agent {agent_id} not found or not loaded")
        return {"agent_id": agent_id, "health": health}

    @app.get("/agents/{agent_id}/runtime-capabilities", tags=["Agents"])
    async def get_runtime_capabilities(agent_id: str):
        """Get runtime capabilities from the actual agent instance."""
        loader = get_loader()
        agent = loader.get_agent(agent_id)
        if not agent:
            raise HTTPException(404, f"Agent {agent_id} not found")
        capabilities = [c.to_dict() for c in agent.get_capabilities()]
        return {"agent_id": agent_id, "capabilities": capabilities}

    @app.post("/agents/{agent_id}/validate", response_model=ValidationResponse, tags=["Validation"])
    async def validate(agent_id: str):
        factory = get_factory()
        m = factory.get_agent(agent_id)
        if not m:
            raise HTTPException(404, f"Agent {agent_id} not found")
        result = factory.validate_agent(metadata=m.to_dict())
        return ValidationResponse(is_valid=result.is_valid, agent_id=result.agent_id, score=result.score,
                                  error_count=len(result.errors), warning_count=len(result.warnings),
                                  issues=[{"principle": i.principle, "severity": i.severity.value,
                                          "message": i.message, "suggestion": i.suggestion} for i in result.issues])

    @app.get("/statistics", response_model=StatisticsResponse, tags=["System"])
    async def statistics():
        factory = get_factory()
        stats = factory.get_statistics()
        return StatisticsResponse(total_agents=stats["total_agents"], by_status=stats["by_status"],
                                  by_domain=stats["by_domain"], by_type=stats["by_type"],
                                  capabilities_count=stats["capabilities"], apqc_processes_count=stats["apqc_processes"])

    @app.get("/capabilities", tags=["Discovery"])
    async def list_capabilities():
        return {"capabilities": get_factory().registry.get_capabilities()}

    @app.get("/domains", tags=["Discovery"])
    async def list_domains():
        return {"domains": get_factory().registry.get_domains()}

    # ============ Workflow Endpoints ============

    @app.get("/workflows", tags=["Workflows"])
    async def list_workflows():
        """List all available workflow templates."""
        engine = get_workflow_engine()
        return {"workflows": engine.list_workflows()}

    @app.get("/workflows/{workflow_id}", tags=["Workflows"])
    async def get_workflow(workflow_id: str):
        """Get workflow definition details."""
        engine = get_workflow_engine()
        workflow = engine.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(404, f"Workflow not found: {workflow_id}")
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "steps": [
                {
                    "name": s.name,
                    "type": s.type.value,
                    "agent_id": s.agent_id,
                    "capability": s.capability,
                }
                for s in workflow.steps
            ],
        }

    @app.post("/workflows/{workflow_id}/execute", tags=["Workflows"])
    async def execute_workflow(
        workflow_id: str,
        input_data: Dict[str, Any] = None,
        _rate_limit: None = Depends(rate_limit_execute),
    ):
        """Execute a workflow with the given input data."""
        engine = get_workflow_engine()
        workflow = engine.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(404, f"Workflow not found: {workflow_id}")

        execution = await engine.execute_workflow(workflow_id, input_data or {})
        return execution.to_dict()

    @app.get("/workflow-executions", tags=["Workflows"])
    async def list_executions(workflow_id: Optional[str] = None, status: Optional[str] = None):
        """List workflow executions with optional filters."""
        engine = get_workflow_engine()
        status_enum = WorkflowStatus(status) if status else None
        return {"executions": engine.list_executions(workflow_id, status_enum)}

    @app.get("/workflow-executions/{execution_id}", tags=["Workflows"])
    async def get_execution(execution_id: str):
        """Get details of a specific workflow execution."""
        engine = get_workflow_engine()
        execution = engine.get_execution(execution_id)
        if not execution:
            raise HTTPException(404, f"Execution not found: {execution_id}")
        return execution.to_dict()

    @app.post("/workflows", tags=["Workflows"])
    async def create_workflow(workflow_def: Dict[str, Any]):
        """Create a custom workflow definition."""
        engine = get_workflow_engine()

        # Parse steps
        steps = []
        for step_data in workflow_def.get("steps", []):
            step = WorkflowStep(
                name=step_data.get("name", ""),
                type=StepType(step_data.get("type", "agent")),
                agent_id=step_data.get("agent_id"),
                capability=step_data.get("capability"),
                input_mapping=step_data.get("input_mapping", {}),
                output_key=step_data.get("output_key"),
            )
            steps.append(step)

        workflow = WorkflowDefinition(
            name=workflow_def.get("name", "Custom Workflow"),
            description=workflow_def.get("description", ""),
            version=workflow_def.get("version", "1.0.0"),
            steps=steps,
        )

        workflow_id = engine.register_workflow(workflow)
        return {"workflow_id": workflow_id, "name": workflow.name, "steps_count": len(steps)}

    # ============ Event Bus Endpoints ============

    @app.get("/events", tags=["Events"])
    async def get_events(event_type: Optional[str] = None, source: Optional[str] = None, limit: int = 100):
        """Get event history."""
        bus = get_message_bus()
        events = bus.get_history(event_type=event_type, source=source, limit=limit)
        return {"events": [e.to_dict() for e in events], "total": len(events)}

    @app.post("/events", tags=["Events"])
    async def publish_event(event_data: Dict[str, Any]):
        """Publish a custom event."""
        bus = get_message_bus()
        event = Event(
            type=event_data.get("type", "custom"),
            source=event_data.get("source", "api"),
            data=event_data.get("data", {}),
            correlation_id=event_data.get("correlation_id"),
        )
        await bus.publish(event)
        return {"published": True, "event_id": event.id}

    @app.get("/events/subscriptions", tags=["Events"])
    async def get_subscriptions():
        """Get current event subscriptions."""
        bus = get_message_bus()
        return {"subscriptions": bus.get_subscriptions()}

    # ============ Authentication Endpoints ============

    @app.get("/auth/me", tags=["Authentication"])
    async def get_current_user(key: Optional[APIKey] = Depends(get_api_key)):
        """Get information about the current API key."""
        if key is None:
            return {"authenticated": False, "message": "No API key provided"}
        return {
            "authenticated": True,
            "key_id": key.id,
            "name": key.name,
            "scopes": key.scopes,
        }

    @app.get("/auth/keys", response_model=List[APIKeyResponse], tags=["Authentication"])
    async def list_api_keys(_: APIKey = Depends(require_admin())):
        """List all API keys (admin only)."""
        manager = get_api_key_manager()
        keys = manager.list_keys()
        return [
            APIKeyResponse(
                id=k.id,
                name=k.name,
                scopes=k.scopes,
                is_active=k.is_active,
                created_at=k.created_at.isoformat() if k.created_at else None,
                last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
                expires_at=k.expires_at.isoformat() if k.expires_at else None,
            )
            for k in keys
        ]

    @app.post("/auth/keys", response_model=CreateAPIKeyResponse, tags=["Authentication"])
    async def create_api_key(
        req: CreateAPIKeyRequest,
        _: APIKey = Depends(require_admin()),
    ):
        """Create a new API key (admin only)."""
        manager = get_api_key_manager()
        try:
            raw_key, key = manager.create_key(
                name=req.name,
                scopes=req.scopes,
                expires_in_days=req.expires_in_days,
            )
            return CreateAPIKeyResponse(
                key=raw_key,
                id=key.id,
                name=key.name,
                scopes=key.scopes,
            )
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.delete("/auth/keys/{key_id}", tags=["Authentication"])
    async def revoke_api_key(key_id: str, _: APIKey = Depends(require_admin())):
        """Revoke an API key (admin only)."""
        manager = get_api_key_manager()
        if manager.revoke_key(key_id):
            return {"revoked": True, "key_id": key_id}
        raise HTTPException(404, f"Key not found: {key_id}")

    # ============ Documentation Endpoints ============

    @app.get("/docs/handbook", tags=["Documentation"])
    async def get_handbook():
        """Get the complete handbook structure with table of contents."""
        from service.documentation_service import get_documentation_service
        docs_service = get_documentation_service(get_factory())
        return docs_service.get_handbook_structure()

    @app.get("/docs/guides", tags=["Documentation"])
    async def list_guides(category: Optional[str] = None):
        """List all documentation guides."""
        from core.database import get_documentation_repository
        repo = get_documentation_repository()
        guides = repo.list_all(category)
        return {"guides": guides, "total": len(guides)}

    @app.get("/docs/guides/{slug:path}", tags=["Documentation"])
    async def get_guide(slug: str):
        """Get a specific guide by slug."""
        from core.database import get_documentation_repository
        repo = get_documentation_repository()
        guide = repo.get_by_slug(slug)
        if not guide:
            raise HTTPException(404, f"Guide not found: {slug}")
        return guide

    @app.get("/docs/examples", tags=["Documentation"])
    async def list_examples(category: Optional[str] = None, agent_id: Optional[str] = None, tag: Optional[str] = None):
        """List documentation examples with optional filters."""
        from core.database import get_example_repository
        repo = get_example_repository()
        if agent_id:
            examples = repo.find_by_agent(agent_id)
        elif tag:
            examples = repo.find_by_tag(tag)
        else:
            examples = repo.list_all(category)
        return {"examples": examples, "total": len(examples)}

    @app.get("/docs/examples/{example_id}", tags=["Documentation"])
    async def get_example(example_id: str):
        """Get a specific example by ID."""
        from core.database import get_example_repository
        repo = get_example_repository()
        example = repo.get(example_id)
        if not example:
            raise HTTPException(404, f"Example not found: {example_id}")
        return example

    @app.get("/docs/agents/{agent_id}", tags=["Documentation"])
    async def get_agent_documentation(agent_id: str):
        """Get auto-generated documentation for a specific agent."""
        from service.documentation_service import get_documentation_service
        docs_service = get_documentation_service(get_factory())
        doc = docs_service.generate_agent_documentation(agent_id)
        if not doc:
            raise HTTPException(404, f"Agent not found: {agent_id}")
        return doc

    @app.get("/docs/agents", tags=["Documentation"])
    async def get_all_agent_documentation():
        """Get auto-generated documentation for all agents."""
        from service.documentation_service import get_documentation_service
        docs_service = get_documentation_service(get_factory())
        docs = docs_service.generate_all_agent_docs()
        return {"agents": docs, "total": len(docs)}

    @app.post("/docs/guides", tags=["Documentation"])
    async def create_or_update_guide(guide: Dict[str, Any]):
        """Create or update a documentation guide."""
        from core.database import get_documentation_repository
        import uuid
        repo = get_documentation_repository()
        if "id" not in guide:
            guide["id"] = str(uuid.uuid4())
        if "slug" not in guide:
            guide["slug"] = guide.get("title", "").lower().replace(" ", "-")
        repo.save(guide)
        return {"id": guide["id"], "slug": guide["slug"], "title": guide.get("title")}

    @app.post("/docs/examples", tags=["Documentation"])
    async def create_or_update_example(example: Dict[str, Any]):
        """Create or update a documentation example."""
        from core.database import get_example_repository
        import uuid
        repo = get_example_repository()
        if "id" not in example:
            example["id"] = str(uuid.uuid4())
        repo.save(example)
        return {"id": example["id"], "title": example.get("title")}

    @app.delete("/docs/guides/{guide_id}", tags=["Documentation"])
    async def delete_guide(guide_id: str):
        """Delete a documentation guide."""
        from core.database import get_documentation_repository
        repo = get_documentation_repository()
        if repo.delete(guide_id):
            return {"deleted": True, "id": guide_id}
        raise HTTPException(404, f"Guide not found: {guide_id}")

    @app.delete("/docs/examples/{example_id}", tags=["Documentation"])
    async def delete_example(example_id: str):
        """Delete a documentation example."""
        from core.database import get_example_repository
        repo = get_example_repository()
        if repo.delete(example_id):
            return {"deleted": True, "id": example_id}
        raise HTTPException(404, f"Example not found: {example_id}")

    @app.post("/docs/initialize", tags=["Documentation"])
    async def initialize_documentation():
        """Initialize default documentation content."""
        from service.documentation_service import get_documentation_service
        docs_service = get_documentation_service(get_factory())
        stats = docs_service.initialize_default_content()
        return {"initialized": True, "stats": stats}

    # ============ Portfolio Endpoints ============

    @app.get("/portfolio/summary", tags=["Portfolio"])
    async def get_portfolio_summary():
        """Get high-level portfolio summary with monetization insights (cached)."""
        from service.portfolio_analyzer import ProjectAnalyzer
        analyzer = ProjectAnalyzer(Path.cwd(), use_cache=True)
        return await analyzer.get_portfolio_summary_async()

    @app.get("/portfolio/projects", tags=["Portfolio"])
    async def get_all_projects():
        """Get detailed analysis of all projects (cached, parallel scanning)."""
        from service.portfolio_analyzer import ProjectAnalyzer
        analyzer = ProjectAnalyzer(Path.cwd(), use_cache=True)
        projects = await analyzer.scan_all_projects_async()
        return {"projects": projects, "total": len(projects)}

    @app.get("/portfolio/projects/{project_name}", tags=["Portfolio"])
    async def get_project_details(project_name: str):
        """Get detailed analysis of a specific project (cached)."""
        from service.portfolio_analyzer import ProjectAnalyzer
        analyzer = ProjectAnalyzer(Path.cwd(), use_cache=True)
        project_path = Path.cwd().parent / project_name
        if not project_path.exists():
            raise HTTPException(404, f"Project not found: {project_name}")
        project_data = await analyzer.analyze_project_async(project_path)
        return project_data

    @app.get("/portfolio/recommendations", tags=["Portfolio"])
    async def get_top_recommendations():
        """Get top revenue-generating recommendations across all projects (cached)."""
        from service.portfolio_analyzer import ProjectAnalyzer
        analyzer = ProjectAnalyzer(Path.cwd(), use_cache=True)
        projects = await analyzer.scan_all_projects_async()
        
        all_recommendations = []
        for project in projects:
            for rec in project["recommendations"]:
                all_recommendations.append({
                    **rec,
                    "project": project["name"],
                    "monetization_score": project["monetization"]["score"],
                })
        
        # Sort by revenue recommendations first, then by type priority
        priority_order = {"revenue": 0, "critical": 1, "high": 2, "medium": 3, "low": 4}
        all_recommendations.sort(
            key=lambda x: (priority_order.get(x["type"], 5), -x["monetization_score"])
        )
        
        return {
            "recommendations": all_recommendations[:20],
            "total": len(all_recommendations),
            "revenue_opportunities": sum(1 for r in all_recommendations if r["type"] == "revenue"),
        }

    @app.get("/portfolio/dashboard", tags=["Portfolio"])
    async def get_dashboard_data():
        """Get portfolio data formatted for public dashboard (optimized for frontend display)."""
        from service.portfolio_analyzer import ProjectAnalyzer
        from service.dashboard_formatter import format_for_dashboard
        
        analyzer = ProjectAnalyzer(Path.cwd(), use_cache=True)
        
        # Fetch both projects and summary in parallel
        projects_task = analyzer.scan_all_projects_async()
        summary_task = analyzer.get_portfolio_summary_async()
        
        projects, summary = await asyncio.gather(projects_task, summary_task)
        
        # Format for dashboard
        dashboard_data = format_for_dashboard(projects, summary)
        
        return dashboard_data

    @app.get("/portfolio/health", tags=["Portfolio"])
    async def get_portfolio_health():
        """
        Get comprehensive portfolio health report.

        Includes metadata coverage, blocker analysis, status breakdown,
        and actionable insights for developers and stakeholders.
        """
        from service.portfolio_analyzer import ProjectAnalyzer

        analyzer = ProjectAnalyzer(Path.cwd(), use_cache=True)
        projects = await analyzer.scan_all_projects_async()

        # Calculate metadata coverage
        with_metadata = [p for p in projects if p.get("has_metadata")]
        without_metadata = [p for p in projects if not p.get("has_metadata")]

        # Status breakdown
        status_counts = {"planning": 0, "in_progress": 0, "ready": 0, "launched": 0, "archived": 0}
        for p in with_metadata:
            status = p.get("project_status", "in_progress")
            if status in status_counts:
                status_counts[status] += 1

        # Priority breakdown
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for p in with_metadata:
            priority = p.get("priority", 5)
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Blocker analysis
        all_blockers = []
        for p in projects:
            for blocker in p.get("blockers", []):
                all_blockers.append({
                    "project": p.get("display_name", p["name"]),
                    "title": blocker["title"],
                    "severity": blocker.get("severity", "medium"),
                    "description": blocker.get("description", ""),
                })

        critical_blockers = [b for b in all_blockers if b["severity"] == "critical"]
        high_blockers = [b for b in all_blockers if b["severity"] == "high"]

        # Ready to launch projects
        ready_projects = [
            {
                "name": p.get("display_name", p["name"]),
                "completion": p.get("completion", 0),
                "time_to_launch": p.get("time_to_launch", "Unknown"),
                "blocker_count": p.get("blocker_count", 0),
                "mrr_potential": p.get("revenue_metadata", {}).get("mrr_potential", "Unknown"),
            }
            for p in projects
            if p.get("project_status") == "ready"
        ]

        # High potential without metadata (opportunities to document)
        undocumented_high_value = [
            {
                "name": p["name"],
                "monetization_score": p["monetization"]["score"],
                "revenue_streams": p["monetization"]["revenue_streams"],
            }
            for p in without_metadata
            if p["monetization"]["score"] >= 70
        ][:10]

        return {
            "total_projects": len(projects),
            "metadata_coverage": {
                "with_metadata": len(with_metadata),
                "without_metadata": len(without_metadata),
                "percentage": round(len(with_metadata) / len(projects) * 100, 1) if projects else 0,
            },
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "blockers": {
                "total": len(all_blockers),
                "critical": len(critical_blockers),
                "high": len(high_blockers),
                "critical_items": critical_blockers,
                "high_items": high_blockers[:5],
            },
            "ready_to_launch": ready_projects,
            "undocumented_high_value": undocumented_high_value,
            "insights": {
                "metadata_recommendation": f"Add PROJECT_META.json to {len(undocumented_high_value)} high-value projects",
                "launch_candidates": len(ready_projects),
                "critical_attention_needed": len(critical_blockers),
            },
            "updated_at": datetime.now().isoformat(),
        }

    # ============ Cache Management Endpoints ============
    
    @app.get("/portfolio/cache/stats", tags=["Portfolio"])
    async def get_cache_stats():
        """Get portfolio cache statistics."""
        from service.portfolio_cache import get_portfolio_cache
        cache = get_portfolio_cache()
        return await cache.get_cache_stats()
    
    @app.post("/portfolio/cache/invalidate", tags=["Portfolio"])
    async def invalidate_portfolio_cache(project_name: Optional[str] = None):
        """
        Invalidate portfolio cache.
        
        If project_name is provided, only that project's cache is cleared.
        Otherwise, all portfolio cache is cleared.
        """
        from service.portfolio_cache import get_portfolio_cache
        cache = get_portfolio_cache()
        
        if project_name:
            count = await cache.invalidate_project(project_name)
            return {
                "invalidated": count,
                "scope": "project",
                "project": project_name,
            }
        else:
            count = await cache.invalidate_all_projects()
            return {
                "invalidated": count,
                "scope": "all",
            }
    
    @app.post("/portfolio/cache/warm", tags=["Portfolio"])
    async def warm_portfolio_cache():
        """Pre-populate portfolio cache with fresh data."""
        from service.portfolio_analyzer import ProjectAnalyzer
        from service.portfolio_cache import get_portfolio_cache
        
        analyzer = ProjectAnalyzer(Path.cwd(), use_cache=False)
        cache = get_portfolio_cache()
        
        if not cache.is_available:
            raise HTTPException(503, "Cache not available")
        
        results = await cache.warm_cache(analyzer)
        return {
            "warming_complete": True,
            "results": results,
        }

    # ============ Revenue Automation Endpoints ============

    @app.get("/automation/actions", tags=["Automation"])
    async def get_executable_actions():
        """Get list of actions that can be executed autonomously."""
        from service.revenue_automation import RevenueActionExecutor
        executor = RevenueActionExecutor(Path.cwd())
        actions = executor.get_executable_actions()
        return {"actions": actions, "total": len(actions)}

    @app.post("/automation/actions/{action_id}/execute", tags=["Automation"])
    async def execute_action(action_id: str, dry_run: bool = True):
        """Execute a specific automation action."""
        from service.revenue_automation import RevenueActionExecutor
        executor = RevenueActionExecutor(Path.cwd())
        result = executor.execute_action(action_id, dry_run=dry_run)
        return result

    @app.post("/automation/workflows/{workflow_type}/execute", tags=["Automation"])
    async def execute_workflow(
        workflow_type: str,
        target_projects: Optional[List[str]] = None
    ):
        """Execute a revenue-generating workflow."""
        from service.revenue_automation import RevenueActionExecutor
        executor = RevenueActionExecutor(Path.cwd())
        result = executor.execute_revenue_workflow(workflow_type, target_projects)
        return result

    @app.get("/automation/workflows", tags=["Automation"])
    async def list_workflows():
        """List available automation workflows."""
        return {
            "workflows": [
                {
                    "type": "sync_all",
                    "name": "Sync All Projects",
                    "description": "Commit and push all pending changes across projects",
                    "risk": "low",
                    "auto_executable": True,
                },
                {
                    "type": "prepare_top_projects",
                    "name": "Prepare Top Projects",
                    "description": "Prepare top 5 monetization projects for launch",
                    "risk": "low",
                    "auto_executable": True,
                },
                {
                    "type": "revenue_push",
                    "name": "Revenue Push",
                    "description": "Identify and prepare high-revenue projects for monetization",
                    "risk": "medium",
                    "auto_executable": False,
                },
            ]
        }

    # ============ HITL (Human-in-the-Loop) Endpoints ============

    @app.get("/hitl/requests", response_model=List[HITLRequestResponse], tags=["HITL"])
    async def list_hitl_requests(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        _rate_limit: None = Depends(rate_limit_general),
    ):
        """List human action requests with optional filters."""
        hitl_service = get_hitl_service()
        requests = hitl_service.list_requests(
            status=status,
            priority=priority,
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )
        return [
            HITLRequestResponse(
                id=r.id,
                request_type=r.request_type,
                title=r.title,
                description=r.description,
                agent_id=r.agent_id,
                priority=r.priority,
                status=r.status,
                workflow_id=r.workflow_id,
                context=r.context,
                required_fields=r.required_fields,
                response_data=r.response_data,
                created_at=r.created_at,
                fulfilled_at=r.fulfilled_at,
                fulfilled_by=r.fulfilled_by,
                notes=r.notes,
            )
            for r in requests
        ]

    @app.post("/hitl/requests", response_model=HITLRequestResponse, tags=["HITL"])
    async def create_hitl_request(
        req: CreateHITLRequest,
        _rate_limit: None = Depends(rate_limit_general),
    ):
        """Create a new human action request."""
        hitl_service = get_hitl_service()
        request = hitl_service.create_request(
            agent_id=req.agent_id,
            request_type=req.request_type,
            title=req.title,
            description=req.description,
            required_fields=req.required_fields,
            priority=req.priority,
            workflow_id=req.workflow_id,
            context=req.context,
        )
        
        # Publish event for real-time notifications
        bus = get_message_bus()
        await bus.publish(Event(
            type="hitl.request.created",
            source="hitl_service",
            data={
                "request_id": request.id,
                "agent_id": request.agent_id,
                "request_type": request.request_type,
                "title": request.title,
                "priority": request.priority,
            },
        ))
        
        return HITLRequestResponse(
            id=request.id,
            request_type=request.request_type,
            title=request.title,
            description=request.description,
            agent_id=request.agent_id,
            priority=request.priority,
            status=request.status,
            workflow_id=request.workflow_id,
            context=request.context,
            required_fields=request.required_fields,
            response_data=request.response_data,
            created_at=request.created_at,
            fulfilled_at=request.fulfilled_at,
            fulfilled_by=request.fulfilled_by,
            notes=request.notes,
        )

    @app.get("/hitl/requests/{request_id}", response_model=HITLRequestResponse, tags=["HITL"])
    async def get_hitl_request(request_id: str):
        """Get details of a specific human action request."""
        hitl_service = get_hitl_service()
        request = hitl_service.get_request(request_id)
        if not request:
            raise HTTPException(404, f"HITL request not found: {request_id}")
        
        return HITLRequestResponse(
            id=request.id,
            request_type=request.request_type,
            title=request.title,
            description=request.description,
            agent_id=request.agent_id,
            priority=request.priority,
            status=request.status,
            workflow_id=request.workflow_id,
            context=request.context,
            required_fields=request.required_fields,
            response_data=request.response_data,
            created_at=request.created_at,
            fulfilled_at=request.fulfilled_at,
            fulfilled_by=request.fulfilled_by,
            notes=request.notes,
        )

    @app.post("/hitl/requests/{request_id}/fulfill", response_model=HITLRequestResponse, tags=["HITL"])
    async def fulfill_hitl_request(
        request_id: str,
        req: FulfillHITLRequest,
    ):
        """Fulfill a human action request."""
        hitl_service = get_hitl_service()
        request = hitl_service.fulfill_request(
            request_id=request_id,
            fulfilled_by=req.fulfilled_by,
            response_data=req.response_data,
            notes=req.notes,
        )
        if not request:
            raise HTTPException(404, f"HITL request not found: {request_id}")
        
        # Publish event for real-time notifications
        bus = get_message_bus()
        await bus.publish(Event(
            type="hitl.request.fulfilled",
            source="hitl_service",
            data={
                "request_id": request.id,
                "agent_id": request.agent_id,
                "workflow_id": request.workflow_id,
                "fulfilled_by": request.fulfilled_by,
            },
        ))
        
        return HITLRequestResponse(
            id=request.id,
            request_type=request.request_type,
            title=request.title,
            description=request.description,
            agent_id=request.agent_id,
            priority=request.priority,
            status=request.status,
            workflow_id=request.workflow_id,
            context=request.context,
            required_fields=request.required_fields,
            response_data=request.response_data,
            created_at=request.created_at,
            fulfilled_at=request.fulfilled_at,
            fulfilled_by=request.fulfilled_by,
            notes=request.notes,
        )

    @app.post("/hitl/requests/{request_id}/reject", response_model=HITLRequestResponse, tags=["HITL"])
    async def reject_hitl_request(
        request_id: str,
        req: RejectHITLRequest,
    ):
        """Reject a human action request."""
        hitl_service = get_hitl_service()
        request = hitl_service.reject_request(
            request_id=request_id,
            rejected_by=req.rejected_by,
            reason=req.reason,
        )
        if not request:
            raise HTTPException(404, f"HITL request not found: {request_id}")
        
        # Publish event for real-time notifications
        bus = get_message_bus()
        await bus.publish(Event(
            type="hitl.request.rejected",
            source="hitl_service",
            data={
                "request_id": request.id,
                "agent_id": request.agent_id,
                "workflow_id": request.workflow_id,
                "rejected_by": request.rejected_by,
                "reason": req.reason,
            },
        ))
        
        return HITLRequestResponse(
            id=request.id,
            request_type=request.request_type,
            title=request.title,
            description=request.description,
            agent_id=request.agent_id,
            priority=request.priority,
            status=request.status,
            workflow_id=request.workflow_id,
            context=request.context,
            required_fields=request.required_fields,
            response_data=request.response_data,
            created_at=request.created_at,
            fulfilled_at=request.fulfilled_at,
            fulfilled_by=request.fulfilled_by,
            notes=request.notes,
        )

    @app.get("/hitl/statistics", tags=["HITL"])
    async def get_hitl_statistics():
        """Get HITL request statistics."""
        hitl_service = get_hitl_service()
        return hitl_service.get_statistics()

    # ============ Startup Event ============

    @app.on_event("startup")
    async def startup():
        """Initialize database and check for bootstrap key."""
        # Initialize database
        get_database()

        # Initialize HITL database
        hitl_service = get_hitl_service()
        print("HITL database initialized")

        # Initialize default documentation
        from service.documentation_service import get_documentation_service
        docs_service = get_documentation_service(get_factory())
        docs_service.initialize_default_content()

        # Configure auth based on environment
        auth_enabled = os.environ.get("AUTH_ENABLED", "true").lower() == "true"
        allow_anon_read = os.environ.get("ALLOW_ANONYMOUS_READ", "true").lower() == "true"
        configure_auth(enabled=auth_enabled, allow_anonymous_read=allow_anon_read)

        # Create bootstrap admin key if none exist
        manager = get_api_key_manager()
        if len(manager.list_keys()) == 0:
            raw_key, key = manager.create_key(
                name="bootstrap-admin",
                scopes=["admin"],
            )
            print(f"\n{'='*60}")
            print("BOOTSTRAP ADMIN KEY CREATED")
            print(f"Key: {raw_key}")
            print("Store this key securely. It will not be shown again.")
            print(f"{'='*60}\n")
        
        # Initialize Redis connection
        try:
            from service.redis_client import init_redis
            redis = await init_redis()
            if redis.is_available:
                logger.info("Redis connection established")
                
                # Warm portfolio cache on startup
                try:
                    from service.portfolio_analyzer import ProjectAnalyzer
                    from service.portfolio_cache import get_portfolio_cache
                    
                    analyzer = ProjectAnalyzer(Path.cwd(), use_cache=False)
                    cache = get_portfolio_cache()
                    await cache.warm_cache(analyzer)
                    logger.info("Portfolio cache warmed successfully")
                except Exception as e:
                    logger.warning(f"Failed to warm cache: {e}")
            else:
                logger.info("Redis not available - running without caching")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
        
        # Start registry hot-reloading watcher
        try:
            from service.registry_watcher import start_registry_watching
            
            def reload_registry():
                """Callback to reload agent registry."""
                global _factory
                if _factory:
                    try:
                        _factory.registry.reload()
                        logger.info("Agent registry reloaded successfully")
                    except Exception as e:
                        logger.error(f"Failed to reload registry: {e}")
            
            base_path = Path(__file__).parent.parent
            registry_path = base_path / "factory" / "registry.json"
            start_registry_watching(registry_path, reload_registry)
            logger.info("Registry hot-reloading enabled")
        except Exception as e:
            logger.warning(f"Registry watcher initialization failed: {e}")
    
    @app.on_event("shutdown")
    async def shutdown():
        """Clean up resources on shutdown."""
        # Close Redis connection
        try:
            from service.redis_client import close_redis
            await close_redis()
            logger.info("Redis connection closed")
        except Exception:
            pass
        
        # Stop registry watcher
        try:
            from service.registry_watcher import stop_registry_watching
            await stop_registry_watching()
            logger.info("Registry watcher stopped")
        except Exception:
            pass

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
