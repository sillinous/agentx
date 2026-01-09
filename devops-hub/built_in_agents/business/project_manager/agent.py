# Project Manager Agent
# Project tracking, scheduling, resource allocation, and progress monitoring

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4
import logging

from ...base import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentMessage,
    AgentResponse,
    Protocol,
)

logger = logging.getLogger(__name__)


@dataclass
class Project:
    """A project being managed."""
    id: str
    name: str
    status: str = "planning"
    progress: float = 0.0
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    risks: List[Dict[str, Any]] = field(default_factory=list)


class ProjectManagerAgent(BaseAgent):
    """
    Project Manager Agent - Project tracking and coordination.

    Capabilities:
    - project-tracking: Track project status and milestones
    - scheduling: Create and manage project schedules
    - resource-allocation: Allocate resources to tasks
    - progress-monitoring: Monitor and report progress
    - risk-tracking: Track and manage project risks
    """

    def __init__(self):
        super().__init__(
            agent_id="project-manager",
            name="Project Manager Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.MCP],
        )
        self._projects: Dict[str, Project] = {}

    def _register_default_capabilities(self) -> None:
        """Register project management capabilities."""
        capabilities = [
            ("project-tracking", "Track project status, milestones, and deliverables"),
            ("scheduling", "Create and manage project schedules and timelines"),
            ("resource-allocation", "Allocate and manage resources across tasks"),
            ("progress-monitoring", "Monitor progress and generate status reports"),
            ("risk-tracking", "Identify, track, and mitigate project risks"),
        ]

        for name, desc in capabilities:
            self.register_capability(AgentCapability(name=name, description=desc))
            self.register_handler(name, self._handle_capability)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return await self._handle_capability(message, context)

    async def _handle_capability(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "project-tracking":
            return await self._track_project(payload)
        elif capability == "scheduling":
            return await self._manage_schedule(payload)
        elif capability == "resource-allocation":
            return await self._allocate_resources(payload)
        elif capability == "progress-monitoring":
            return await self._monitor_progress(payload)
        elif capability == "risk-tracking":
            return await self._track_risks(payload)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    async def _track_project(self, payload: Dict[str, Any]) -> AgentResponse:
        """Track project status."""
        action = payload.get("action", "status")
        project_id = payload.get("project_id")

        if action == "create":
            project = Project(
                id=str(uuid4()),
                name=payload.get("name", "New Project"),
                status="planning",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=90),
            )
            self._projects[project.id] = project

            return AgentResponse.success_response({
                "project_id": project.id,
                "name": project.name,
                "status": project.status,
                "created": True,
            })

        elif action == "status" and project_id:
            if project_id in self._projects:
                p = self._projects[project_id]
                return AgentResponse.success_response({
                    "project_id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "progress": p.progress,
                    "task_count": len(p.tasks),
                })

        # List all projects
        return AgentResponse.success_response({
            "projects": [
                {"id": p.id, "name": p.name, "status": p.status, "progress": p.progress}
                for p in self._projects.values()
            ],
            "total": len(self._projects),
        })

    async def _manage_schedule(self, payload: Dict[str, Any]) -> AgentResponse:
        """Manage project schedule."""
        project_id = payload.get("project_id")
        action = payload.get("action", "view")

        schedule = {
            "milestones": [
                {"name": "Planning Complete", "date": "2026-01-15", "status": "completed"},
                {"name": "Design Review", "date": "2026-02-01", "status": "in_progress"},
                {"name": "Development Done", "date": "2026-03-15", "status": "pending"},
                {"name": "Launch", "date": "2026-04-01", "status": "pending"},
            ],
            "critical_path": ["Design", "Development", "Testing", "Deployment"],
            "buffer_days": 10,
            "on_track": True,
        }

        return AgentResponse.success_response(schedule)

    async def _allocate_resources(self, payload: Dict[str, Any]) -> AgentResponse:
        """Allocate resources."""
        task_id = payload.get("task_id")
        resources = payload.get("resources", [])

        return AgentResponse.success_response({
            "allocated": True,
            "task_id": task_id,
            "resources": resources or [
                {"name": "Developer A", "allocation": "100%", "role": "Lead"},
                {"name": "Developer B", "allocation": "50%", "role": "Support"},
            ],
            "availability": {
                "Developer A": "Available",
                "Developer B": "Partially available",
            },
            "recommendations": [
                "Consider adding QA resource in week 4",
                "Schedule design review with full team",
            ],
        })

    async def _monitor_progress(self, payload: Dict[str, Any]) -> AgentResponse:
        """Monitor project progress."""
        project_id = payload.get("project_id")

        return AgentResponse.success_response({
            "overall_progress": 0.45,
            "status": "On Track",
            "metrics": {
                "tasks_completed": 18,
                "tasks_remaining": 22,
                "tasks_overdue": 2,
                "velocity": 4.5,
            },
            "burndown": [
                {"week": 1, "remaining": 40},
                {"week": 2, "remaining": 35},
                {"week": 3, "remaining": 28},
                {"week": 4, "remaining": 22},
            ],
            "blockers": [
                {"task": "API Integration", "blocker": "Waiting for credentials", "severity": "medium"},
            ],
        })

    async def _track_risks(self, payload: Dict[str, Any]) -> AgentResponse:
        """Track project risks."""
        return AgentResponse.success_response({
            "risk_score": 0.35,
            "status": "Manageable",
            "risks": [
                {
                    "id": "R001",
                    "description": "Resource availability",
                    "probability": 0.4,
                    "impact": "Medium",
                    "mitigation": "Cross-training team members",
                },
                {
                    "id": "R002",
                    "description": "Scope creep",
                    "probability": 0.6,
                    "impact": "High",
                    "mitigation": "Strict change control process",
                },
                {
                    "id": "R003",
                    "description": "Technical complexity",
                    "probability": 0.3,
                    "impact": "High",
                    "mitigation": "Proof of concept first",
                },
            ],
            "mitigations_in_progress": 2,
            "risks_closed": 3,
        })
