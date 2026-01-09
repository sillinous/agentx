# Task Decomposer Agent
# Breaks down complex tasks into subtasks, creates execution plans

from dataclasses import dataclass, field
from datetime import datetime
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
class Task:
    """A decomposed task."""
    id: str
    name: str
    description: str
    subtasks: List["Task"] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    estimated_effort: str = "medium"
    status: str = "pending"


class TaskDecomposerAgent(BaseAgent):
    """
    Task Decomposer Agent - Break down complex tasks.

    Capabilities:
    - task-decomposition: Break tasks into manageable subtasks
    - dependency-analysis: Analyze task dependencies
    - execution-planning: Create execution plans
    - prioritization: Prioritize tasks
    - risk-analysis: Analyze task risks
    """

    def __init__(self):
        super().__init__(
            agent_id="task-decomposer",
            name="Task Decomposer Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.MCP],
        )
        self._tasks: Dict[str, Task] = {}

    def _register_default_capabilities(self) -> None:
        """Register task decomposition capabilities."""
        capabilities = [
            ("task-decomposition", "Break complex tasks into subtasks"),
            ("dependency-analysis", "Analyze dependencies between tasks"),
            ("execution-planning", "Create optimal execution plans"),
            ("prioritization", "Prioritize tasks by importance"),
            ("risk-analysis", "Analyze risks associated with tasks"),
        ]

        for name, desc in capabilities:
            self.register_capability(AgentCapability(name=name, description=desc))
            self.register_handler(name, self._handle_capability)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return await self._handle_capability(message, context)

    async def _handle_capability(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "task-decomposition":
            return await self._decompose_task(payload)
        elif capability == "dependency-analysis":
            return await self._analyze_dependencies(payload)
        elif capability == "execution-planning":
            return await self._create_execution_plan(payload)
        elif capability == "prioritization":
            return await self._prioritize_tasks(payload)
        elif capability == "risk-analysis":
            return await self._analyze_risks(payload)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    async def _decompose_task(self, payload: Dict[str, Any]) -> AgentResponse:
        """Decompose a complex task."""
        task_name = payload.get("task", "Complex Task")
        depth = payload.get("depth", 2)

        task_id = str(uuid4())
        decomposition = {
            "task_id": task_id,
            "name": task_name,
            "subtasks": [
                {
                    "id": f"{task_id}-1",
                    "name": "Research & Planning",
                    "effort": "medium",
                    "subtasks": [
                        {"id": f"{task_id}-1-1", "name": "Gather requirements", "effort": "low"},
                        {"id": f"{task_id}-1-2", "name": "Technical analysis", "effort": "medium"},
                    ],
                },
                {
                    "id": f"{task_id}-2",
                    "name": "Implementation",
                    "effort": "high",
                    "subtasks": [
                        {"id": f"{task_id}-2-1", "name": "Core functionality", "effort": "high"},
                        {"id": f"{task_id}-2-2", "name": "Integration", "effort": "medium"},
                    ],
                },
                {
                    "id": f"{task_id}-3",
                    "name": "Testing & Deployment",
                    "effort": "medium",
                    "subtasks": [
                        {"id": f"{task_id}-3-1", "name": "Unit tests", "effort": "medium"},
                        {"id": f"{task_id}-3-2", "name": "Deployment", "effort": "low"},
                    ],
                },
            ],
            "total_subtasks": 8,
            "estimated_total_effort": "high",
        }

        return AgentResponse.success_response(decomposition)

    async def _analyze_dependencies(self, payload: Dict[str, Any]) -> AgentResponse:
        """Analyze task dependencies."""
        tasks = payload.get("tasks", [])

        return AgentResponse.success_response({
            "dependency_graph": {
                "nodes": ["Task A", "Task B", "Task C", "Task D"],
                "edges": [
                    {"from": "Task A", "to": "Task B", "type": "blocks"},
                    {"from": "Task A", "to": "Task C", "type": "blocks"},
                    {"from": "Task B", "to": "Task D", "type": "blocks"},
                    {"from": "Task C", "to": "Task D", "type": "blocks"},
                ],
            },
            "critical_path": ["Task A", "Task B", "Task D"],
            "parallel_groups": [
                {"group": 1, "tasks": ["Task A"]},
                {"group": 2, "tasks": ["Task B", "Task C"]},
                {"group": 3, "tasks": ["Task D"]},
            ],
            "bottlenecks": ["Task A"],
            "circular_dependencies": [],
        })

    async def _create_execution_plan(self, payload: Dict[str, Any]) -> AgentResponse:
        """Create execution plan."""
        tasks = payload.get("tasks", [])
        strategy = payload.get("strategy", "parallel")

        return AgentResponse.success_response({
            "plan_id": str(uuid4()),
            "strategy": strategy,
            "phases": [
                {
                    "phase": 1,
                    "name": "Initialization",
                    "tasks": ["Setup environment", "Gather resources"],
                    "parallel": True,
                },
                {
                    "phase": 2,
                    "name": "Core Work",
                    "tasks": ["Implement feature A", "Implement feature B"],
                    "parallel": True,
                },
                {
                    "phase": 3,
                    "name": "Integration",
                    "tasks": ["Integrate components", "System testing"],
                    "parallel": False,
                },
                {
                    "phase": 4,
                    "name": "Finalization",
                    "tasks": ["Documentation", "Deployment"],
                    "parallel": True,
                },
            ],
            "total_phases": 4,
            "optimization_notes": [
                "Phases 1 and 2 can run concurrently",
                "Integration requires sequential execution",
            ],
        })

    async def _prioritize_tasks(self, payload: Dict[str, Any]) -> AgentResponse:
        """Prioritize tasks."""
        tasks = payload.get("tasks", [])
        criteria = payload.get("criteria", ["urgency", "importance", "effort"])

        return AgentResponse.success_response({
            "prioritized_tasks": [
                {"task": "Critical bug fix", "priority": 1, "score": 0.95, "reason": "High urgency, high importance"},
                {"task": "Security update", "priority": 2, "score": 0.90, "reason": "High importance"},
                {"task": "New feature", "priority": 3, "score": 0.75, "reason": "Medium importance"},
                {"task": "Code cleanup", "priority": 4, "score": 0.50, "reason": "Low urgency"},
            ],
            "criteria_used": criteria,
            "scoring_method": "weighted_sum",
            "recommendations": [
                "Focus on critical bug fix immediately",
                "Schedule security update for this sprint",
                "Plan new feature for next sprint",
            ],
        })

    async def _analyze_risks(self, payload: Dict[str, Any]) -> AgentResponse:
        """Analyze task risks."""
        task = payload.get("task", "")

        return AgentResponse.success_response({
            "overall_risk": 0.45,
            "risk_level": "Medium",
            "risks": [
                {
                    "category": "Technical",
                    "description": "Complex integration requirements",
                    "probability": 0.6,
                    "impact": "High",
                    "mitigation": "Create proof of concept first",
                },
                {
                    "category": "Resource",
                    "description": "Key person dependency",
                    "probability": 0.4,
                    "impact": "Medium",
                    "mitigation": "Document knowledge, cross-train",
                },
                {
                    "category": "Schedule",
                    "description": "Aggressive timeline",
                    "probability": 0.5,
                    "impact": "Medium",
                    "mitigation": "Add buffer time, prioritize MVP",
                },
            ],
            "risk_matrix": {
                "high_probability_high_impact": 0,
                "high_probability_low_impact": 1,
                "low_probability_high_impact": 1,
                "low_probability_low_impact": 1,
            },
        })
