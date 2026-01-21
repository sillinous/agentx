"""Scheduler Agent - Manage scheduled and recurring tasks."""

import logging
from datetime import datetime
from typing import Any, Dict, List

from built_in_agents.base import (
    AgentCapability, AgentContext, AgentMessage, AgentResponse, BaseAgent, Protocol,
)

logger = logging.getLogger(__name__)


class SchedulerAgent(BaseAgent):
    """Agent for scheduling and managing recurring tasks."""

    def __init__(self):
        super().__init__(
            agent_id="scheduler-agent",
            name="Scheduler Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP, Protocol.MCP],
        )
        self._schedules: Dict[str, Dict] = {}

    def _register_default_capabilities(self) -> None:
        self.register_capability(AgentCapability(
            name="create_schedule",
            description="Create a new scheduled task",
            parameters={
                "name": {"type": "string"},
                "cron": {"type": "string", "description": "Cron expression"},
                "agent_id": {"type": "string", "description": "Agent to invoke"},
                "capability": {"type": "string"},
                "payload": {"type": "object"},
            },
            returns={"schedule_id": {"type": "string"}},
        ))

        self.register_capability(AgentCapability(
            name="list_schedules",
            description="List all scheduled tasks",
            returns={"schedules": {"type": "array"}},
        ))

        self.register_capability(AgentCapability(
            name="delete_schedule",
            description="Delete a scheduled task",
            parameters={"schedule_id": {"type": "string"}},
            returns={"deleted": {"type": "boolean"}},
        ))

        self.register_capability(AgentCapability(
            name="pause_schedule",
            description="Pause a scheduled task",
            parameters={"schedule_id": {"type": "string"}},
            returns={"paused": {"type": "boolean"}},
        ))

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "create_schedule":
            schedule_id = f"sched_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
            self._schedules[schedule_id] = {
                "id": schedule_id,
                "name": payload.get("name", "Unnamed"),
                "cron": payload.get("cron", "0 * * * *"),
                "agent_id": payload.get("agent_id"),
                "capability": payload.get("capability"),
                "payload": payload.get("payload", {}),
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "last_run": None,
                "next_run": None,
            }
            return AgentResponse.success_response({"schedule_id": schedule_id})

        elif capability == "list_schedules":
            return AgentResponse.success_response({
                "schedules": list(self._schedules.values())
            })

        elif capability == "delete_schedule":
            schedule_id = payload.get("schedule_id")
            if schedule_id in self._schedules:
                del self._schedules[schedule_id]
                return AgentResponse.success_response({"deleted": True})
            return AgentResponse.success_response({"deleted": False})

        elif capability == "pause_schedule":
            schedule_id = payload.get("schedule_id")
            if schedule_id in self._schedules:
                self._schedules[schedule_id]["status"] = "paused"
                return AgentResponse.success_response({"paused": True})
            return AgentResponse.success_response({"paused": False})

        return AgentResponse.error_response(f"Unknown capability: {capability}")
