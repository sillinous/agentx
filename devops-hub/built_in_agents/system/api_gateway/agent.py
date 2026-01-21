"""API Gateway Agent - Route and manage external API calls."""

import logging
from datetime import datetime
from typing import Any, Dict

from built_in_agents.base import (
    AgentCapability, AgentContext, AgentMessage, AgentResponse, BaseAgent, Protocol,
)

logger = logging.getLogger(__name__)


class APIGatewayAgent(BaseAgent):
    """Agent for managing external API integrations."""

    def __init__(self):
        super().__init__(
            agent_id="api-gateway-agent",
            name="API Gateway Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP, Protocol.MCP],
        )
        self._endpoints: Dict[str, Dict] = {}

    def _register_default_capabilities(self) -> None:
        self.register_capability(AgentCapability(
            name="register_endpoint",
            description="Register an external API endpoint",
            parameters={
                "name": {"type": "string"},
                "url": {"type": "string"},
                "method": {"type": "string"},
                "headers": {"type": "object"},
                "auth_type": {"type": "string"},
            },
            returns={"endpoint_id": {"type": "string"}},
        ))

        self.register_capability(AgentCapability(
            name="call_endpoint",
            description="Call a registered endpoint",
            parameters={
                "endpoint_id": {"type": "string"},
                "payload": {"type": "object"},
            },
            returns={"status_code": {"type": "integer"}, "response": {"type": "object"}},
        ))

        self.register_capability(AgentCapability(
            name="list_endpoints",
            description="List all registered endpoints",
            returns={"endpoints": {"type": "array"}},
        ))

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "register_endpoint":
            endpoint_id = f"ep_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
            self._endpoints[endpoint_id] = {
                "id": endpoint_id,
                "name": payload.get("name"),
                "url": payload.get("url"),
                "method": payload.get("method", "GET"),
                "headers": payload.get("headers", {}),
                "auth_type": payload.get("auth_type", "none"),
                "created_at": datetime.utcnow().isoformat(),
            }
            return AgentResponse.success_response({"endpoint_id": endpoint_id})

        elif capability == "call_endpoint":
            endpoint_id = payload.get("endpoint_id")
            if endpoint_id not in self._endpoints:
                return AgentResponse.error_response("Endpoint not found")
            endpoint = self._endpoints[endpoint_id]
            # In production, make actual HTTP request
            logger.info(f"Calling endpoint: {endpoint['url']}")
            return AgentResponse.success_response({
                "status_code": 200,
                "response": {"message": "Simulated response"},
                "endpoint": endpoint["name"],
            })

        elif capability == "list_endpoints":
            return AgentResponse.success_response({
                "endpoints": list(self._endpoints.values())
            })

        return AgentResponse.error_response(f"Unknown capability: {capability}")
