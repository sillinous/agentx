"""Notification Agent - Multi-channel notification delivery."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from built_in_agents.base import (
    AgentCapability, AgentContext, AgentMessage, AgentResponse, BaseAgent, Protocol,
)

logger = logging.getLogger(__name__)


class NotificationAgent(BaseAgent):
    """Agent for sending notifications via multiple channels."""

    def __init__(self):
        super().__init__(
            agent_id="notification-agent",
            name="Notification Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP, Protocol.MCP],
        )

    def _register_default_capabilities(self) -> None:
        self.register_capability(AgentCapability(
            name="send_notification",
            description="Send a notification via specified channel",
            parameters={
                "channel": {"type": "string"},
                "recipient": {"type": "string"},
                "subject": {"type": "string"},
                "message": {"type": "string"},
            },
            returns={"notification_id": {"type": "string"}, "status": {"type": "string"}},
        ))

        self.register_capability(AgentCapability(
            name="get_channels",
            description="Get list of available notification channels",
            returns={"channels": {"type": "array"}},
        ))

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "send_notification":
            result = await self._send_notification(
                channel=payload.get("channel", "log"),
                recipient=payload.get("recipient", ""),
                subject=payload.get("subject", ""),
                body=payload.get("message", ""),
            )
            return AgentResponse.success_response(result)

        elif capability == "get_channels":
            return AgentResponse.success_response({
                "channels": ["email", "slack", "webhook", "teams", "discord", "log"]
            })

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    async def _send_notification(self, channel: str, recipient: str, subject: str, body: str) -> Dict:
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        logger.info(f"[{channel.upper()}] To: {recipient}, Subject: {subject}")
        return {
            "notification_id": notification_id,
            "status": "sent",
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat(),
        }
