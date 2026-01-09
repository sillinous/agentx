# Supervisor Agent
# Orchestrates the agent ecosystem, coordinates workflows, manages agent lifecycle

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import asyncio
import logging

from ...base import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentMessage,
    AgentResponse,
    AgentState,
    MessageType,
    Protocol,
)

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    """Represents an orchestrated workflow."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    status: str = "pending"
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class ManagedAgent:
    """Tracks an agent managed by the supervisor."""
    agent_id: str
    name: str
    status: str = "unknown"
    capabilities: List[str] = field(default_factory=list)
    last_heartbeat: Optional[datetime] = None
    task_count: int = 0
    error_count: int = 0


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent - The central orchestrator of the agent ecosystem.

    Capabilities:
    - orchestration: Execute multi-agent workflows
    - monitoring: Track agent health and performance
    - routing: Direct tasks to appropriate agents
    - agent-lifecycle-management: Start, stop, pause agents
    - workflow-coordination: Manage complex multi-step processes
    """

    def __init__(self):
        super().__init__(
            agent_id="supervisor-agent",
            name="Supervisor Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP, Protocol.MCP],
        )

        self._managed_agents: Dict[str, ManagedAgent] = {}
        self._workflows: Dict[str, Workflow] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._active_tasks: Set[str] = set()

    def _register_default_capabilities(self) -> None:
        """Register supervisor capabilities."""
        self.register_capability(AgentCapability(
            name="orchestration",
            description="Execute multi-agent workflows with dependency management",
            parameters={
                "workflow": {"type": "object", "description": "Workflow definition"},
                "context": {"type": "object", "description": "Execution context"},
            },
            returns={"type": "object", "properties": {"workflow_id": "string", "status": "string"}},
        ))

        self.register_capability(AgentCapability(
            name="monitoring",
            description="Monitor and track agent health across the ecosystem",
            parameters={
                "agent_ids": {"type": "array", "description": "List of agent IDs to monitor"},
            },
            returns={"type": "object", "properties": {"agents": "array", "summary": "object"}},
        ))

        self.register_capability(AgentCapability(
            name="routing",
            description="Route tasks to the most appropriate agent",
            parameters={
                "task": {"type": "object", "description": "Task to route"},
                "requirements": {"type": "array", "description": "Required capabilities"},
            },
            returns={"type": "object", "properties": {"agent_id": "string", "confidence": "number"}},
        ))

        self.register_capability(AgentCapability(
            name="agent-lifecycle-management",
            description="Manage agent lifecycle (start, stop, pause, resume)",
            parameters={
                "agent_id": {"type": "string", "description": "Target agent ID"},
                "action": {"type": "string", "enum": ["start", "stop", "pause", "resume"]},
            },
            returns={"type": "object", "properties": {"success": "boolean", "state": "string"}},
        ))

        self.register_capability(AgentCapability(
            name="workflow-coordination",
            description="Coordinate complex multi-step workflows",
            parameters={
                "workflow_id": {"type": "string", "description": "Workflow to coordinate"},
                "action": {"type": "string", "enum": ["start", "pause", "resume", "cancel", "status"]},
            },
            returns={"type": "object", "properties": {"workflow": "object"}},
        ))

        # Register handlers
        self.register_handler("orchestration", self._handle_orchestration)
        self.register_handler("monitoring", self._handle_monitoring)
        self.register_handler("routing", self._handle_routing)
        self.register_handler("agent-lifecycle-management", self._handle_lifecycle)
        self.register_handler("workflow-coordination", self._handle_workflow_coordination)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Process incoming messages."""
        capability = message.capability

        if capability in self._message_handlers:
            handler = self._message_handlers[capability]
            return await handler(message, context)

        return AgentResponse.error_response(
            f"Unknown capability: {capability}",
            error_code="UNKNOWN_CAPABILITY",
            correlation_id=message.id,
        )

    # Capability Handlers

    async def _handle_orchestration(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle workflow orchestration requests."""
        payload = message.payload
        workflow_def = payload.get("workflow", {})
        workflow_context = payload.get("context", {})

        # Create workflow
        workflow = Workflow(
            name=workflow_def.get("name", "unnamed"),
            steps=workflow_def.get("steps", []),
            context=workflow_context,
        )

        self._workflows[workflow.id] = workflow

        # Start execution
        asyncio.create_task(self._execute_workflow(workflow))

        return AgentResponse.success_response({
            "workflow_id": workflow.id,
            "status": "started",
            "steps_count": len(workflow.steps),
        })

    async def _handle_monitoring(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle monitoring requests."""
        payload = message.payload
        agent_ids = payload.get("agent_ids", list(self._managed_agents.keys()))

        agents_status = []
        healthy = 0
        unhealthy = 0

        for agent_id in agent_ids:
            if agent_id in self._managed_agents:
                agent = self._managed_agents[agent_id]
                status = {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "status": agent.status,
                    "capabilities": agent.capabilities,
                    "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
                    "task_count": agent.task_count,
                    "error_count": agent.error_count,
                }
                agents_status.append(status)

                if agent.status == "healthy":
                    healthy += 1
                else:
                    unhealthy += 1

        return AgentResponse.success_response({
            "agents": agents_status,
            "summary": {
                "total": len(agents_status),
                "healthy": healthy,
                "unhealthy": unhealthy,
            },
        })

    async def _handle_routing(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle task routing requests."""
        payload = message.payload
        task = payload.get("task", {})
        requirements = payload.get("requirements", [])

        # Find best matching agent
        best_match = None
        best_score = 0

        for agent_id, agent in self._managed_agents.items():
            if agent.status != "healthy":
                continue

            # Calculate match score
            matching_caps = set(agent.capabilities) & set(requirements)
            score = len(matching_caps) / max(len(requirements), 1)

            # Factor in load
            load_factor = 1 / (1 + agent.task_count)
            score *= load_factor

            if score > best_score:
                best_score = score
                best_match = agent_id

        if best_match:
            return AgentResponse.success_response({
                "agent_id": best_match,
                "confidence": best_score,
                "requirements_met": list(set(self._managed_agents[best_match].capabilities) & set(requirements)),
            })
        else:
            return AgentResponse.error_response(
                "No suitable agent found",
                error_code="NO_AGENT_AVAILABLE",
            )

    async def _handle_lifecycle(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle agent lifecycle management requests."""
        payload = message.payload
        agent_id = payload.get("agent_id")
        action = payload.get("action")

        if not agent_id:
            return AgentResponse.error_response(
                "agent_id is required",
                error_code="MISSING_PARAMETER",
            )

        if action == "register":
            # Register a new agent
            self._managed_agents[agent_id] = ManagedAgent(
                agent_id=agent_id,
                name=payload.get("name", agent_id),
                status="healthy",
                capabilities=payload.get("capabilities", []),
                last_heartbeat=datetime.utcnow(),
            )
            return AgentResponse.success_response({
                "success": True,
                "state": "registered",
                "agent_id": agent_id,
            })

        elif action == "unregister":
            if agent_id in self._managed_agents:
                del self._managed_agents[agent_id]
            return AgentResponse.success_response({
                "success": True,
                "state": "unregistered",
            })

        elif action == "heartbeat":
            if agent_id in self._managed_agents:
                self._managed_agents[agent_id].last_heartbeat = datetime.utcnow()
                self._managed_agents[agent_id].status = payload.get("status", "healthy")
            return AgentResponse.success_response({
                "success": True,
                "state": "acknowledged",
            })

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    async def _handle_workflow_coordination(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle workflow coordination requests."""
        payload = message.payload
        workflow_id = payload.get("workflow_id")
        action = payload.get("action", "status")

        if workflow_id and workflow_id not in self._workflows:
            return AgentResponse.error_response(
                f"Workflow not found: {workflow_id}",
                error_code="WORKFLOW_NOT_FOUND",
            )

        if action == "list":
            workflows = [
                {
                    "id": w.id,
                    "name": w.name,
                    "status": w.status,
                    "current_step": w.current_step,
                    "total_steps": len(w.steps),
                    "created_at": w.created_at.isoformat(),
                }
                for w in self._workflows.values()
            ]
            return AgentResponse.success_response({"workflows": workflows})

        if action == "status":
            workflow = self._workflows[workflow_id]
            return AgentResponse.success_response({
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "status": workflow.status,
                    "current_step": workflow.current_step,
                    "total_steps": len(workflow.steps),
                    "results": workflow.results,
                    "error": workflow.error,
                    "created_at": workflow.created_at.isoformat(),
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                }
            })

        elif action == "cancel":
            workflow = self._workflows[workflow_id]
            workflow.status = "cancelled"
            return AgentResponse.success_response({
                "workflow_id": workflow_id,
                "status": "cancelled",
            })

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    async def _execute_workflow(self, workflow: Workflow) -> None:
        """Execute a workflow's steps."""
        workflow.status = "running"
        workflow.started_at = datetime.utcnow()

        try:
            for i, step in enumerate(workflow.steps):
                workflow.current_step = i
                step_name = step.get("name", f"step_{i}")

                logger.info(f"Executing workflow step: {step_name}")

                # Execute step (simplified - would delegate to appropriate agent)
                step_result = await self._execute_step(step, workflow.context)
                workflow.results[step_name] = step_result

                # Check for failure
                if not step_result.get("success", True):
                    workflow.status = "failed"
                    workflow.error = step_result.get("error", "Step failed")
                    return

            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()

        except Exception as e:
            workflow.status = "failed"
            workflow.error = str(e)
            logger.exception(f"Workflow {workflow.id} failed")

    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        step_type = step.get("type", "task")
        agent_id = step.get("agent")
        capability = step.get("capability")
        params = step.get("parameters", {})

        # Merge context into params
        params = {**context, **params}

        # For now, simulate execution
        await asyncio.sleep(0.1)

        return {
            "success": True,
            "agent": agent_id,
            "capability": capability,
            "result": f"Executed {step.get('name', 'step')}",
        }

    # Public API

    def register_agent(self, agent_id: str, name: str, capabilities: List[str]) -> None:
        """Register an agent with the supervisor."""
        self._managed_agents[agent_id] = ManagedAgent(
            agent_id=agent_id,
            name=name,
            status="healthy",
            capabilities=capabilities,
            last_heartbeat=datetime.utcnow(),
        )

    def get_managed_agents(self) -> List[Dict[str, Any]]:
        """Get all managed agents."""
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "status": a.status,
                "capabilities": a.capabilities,
            }
            for a in self._managed_agents.values()
        ]

    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows."""
        return [
            {
                "id": w.id,
                "name": w.name,
                "status": w.status,
                "current_step": w.current_step,
                "total_steps": len(w.steps),
            }
            for w in self._workflows.values()
        ]
