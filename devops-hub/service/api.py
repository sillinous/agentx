"""
Agent Library Service API - FastAPI REST endpoints.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from factory.agent_factory import AgentFactory
from factory.agent_registry import AgentMetadata
from service.agent_loader import get_loader, AgentLoader
from service.workflow_engine import get_workflow_engine, WorkflowStatus, WorkflowDefinition, WorkflowStep, StepType
from service.message_bus import get_message_bus, Event
from core.auth import (
    APIKey, get_api_key, get_api_key_manager, configure_auth,
    require_read, require_write, require_execute, require_admin,
)
from core.database import get_database, get_event_repository


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


def create_app() -> FastAPI:
    app = FastAPI(title="Agent Library Service", version="1.0.0",
                  description="REST API for agent discovery and execution")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health():
        return HealthResponse(status="healthy", timestamp=datetime.now().isoformat(), version="1.0.0")

    @app.get("/agents", response_model=List[AgentSummary], tags=["Agents"])
    async def list_agents(status: Optional[str] = Query(None)):
        factory = get_factory()
        agents = factory.registry.list_all()
        if status:
            agents = [a for a in agents if a.status.value == status]
        return [agent_to_summary(a) for a in agents]

    @app.get("/agents/discover", response_model=DiscoverResponse, tags=["Agents"])
    async def discover(domain: Optional[str] = None, capability: Optional[str] = None,
                       status: Optional[str] = "production", agent_type: Optional[str] = None):
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
    async def execute(agent_id: str, req: ExecutionRequest):
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
    async def execute_workflow(workflow_id: str, input_data: Dict[str, Any] = None):
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

    # ============ Startup Event ============

    @app.on_event("startup")
    async def startup():
        """Initialize database and check for bootstrap key."""
        # Initialize database
        get_database()

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

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
