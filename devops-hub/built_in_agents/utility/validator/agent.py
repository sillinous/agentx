"""Validator Agent - Validate data against schemas and rules."""

import logging
import re
from typing import Any, Dict, List

from built_in_agents.base import (
    AgentCapability, AgentContext, AgentMessage, AgentResponse, BaseAgent, Protocol,
)

logger = logging.getLogger(__name__)


class ValidatorAgent(BaseAgent):
    """Agent for validating data against schemas and rules."""

    def __init__(self):
        super().__init__(
            agent_id="validator-agent",
            name="Validator Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP, Protocol.MCP],
        )

    def _register_default_capabilities(self) -> None:
        self.register_capability(AgentCapability(
            name="validate_schema",
            description="Validate data against a JSON schema",
            parameters={
                "data": {"type": "object", "description": "Data to validate"},
                "schema": {"type": "object", "description": "JSON schema"},
            },
            returns={"valid": {"type": "boolean"}, "errors": {"type": "array"}},
        ))

        self.register_capability(AgentCapability(
            name="validate_email",
            description="Validate email address format",
            parameters={"email": {"type": "string"}},
            returns={"valid": {"type": "boolean"}},
        ))

        self.register_capability(AgentCapability(
            name="validate_url",
            description="Validate URL format",
            parameters={"url": {"type": "string"}},
            returns={"valid": {"type": "boolean"}},
        ))

        self.register_capability(AgentCapability(
            name="validate_required_fields",
            description="Check if required fields are present",
            parameters={
                "data": {"type": "object"},
                "required_fields": {"type": "array"},
            },
            returns={"valid": {"type": "boolean"}, "missing_fields": {"type": "array"}},
        ))

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "validate_schema":
            result = self._validate_schema(payload.get("data", {}), payload.get("schema", {}))
            return AgentResponse.success_response(result)

        elif capability == "validate_email":
            email = payload.get("email", "")
            valid = bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email))
            return AgentResponse.success_response({"valid": valid, "email": email})

        elif capability == "validate_url":
            url = payload.get("url", "")
            valid = bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", url))
            return AgentResponse.success_response({"valid": valid, "url": url})

        elif capability == "validate_required_fields":
            result = self._validate_required_fields(
                payload.get("data", {}),
                payload.get("required_fields", [])
            )
            return AgentResponse.success_response(result)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    def _validate_schema(self, data: Dict, schema: Dict) -> Dict:
        """Simple schema validation."""
        errors = []
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        for field, rules in properties.items():
            if field in data:
                value = data[field]
                expected_type = rules.get("type")
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field {field} must be a string")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} must be a number")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field {field} must be an array")

        return {"valid": len(errors) == 0, "errors": errors}

    def _validate_required_fields(self, data: Dict, required: List[str]) -> Dict:
        """Check for required fields."""
        missing = [f for f in required if f not in data or data[f] is None]
        return {"valid": len(missing) == 0, "missing_fields": missing}
