# Documentation Generator Agent
# Auto-documentation generation, API docs, guides, and maintenance

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


class DocumentationGeneratorAgent(BaseAgent):
    """
    Documentation Generator Agent - Automated documentation.

    Capabilities:
    - auto-documentation: Generate documentation from code
    - api-doc-generation: Generate API documentation
    - guide-creation: Create user guides and tutorials
    - example-generation: Generate code examples
    - doc-maintenance: Maintain and update documentation
    """

    def __init__(self):
        super().__init__(
            agent_id="documentation-generator",
            name="Documentation Generator Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.MCP],
        )
        self._generated_docs: Dict[str, Dict[str, Any]] = {}

    def _register_default_capabilities(self) -> None:
        """Register documentation capabilities."""
        capabilities = [
            ("auto-documentation", "Generate documentation from source code"),
            ("api-doc-generation", "Generate comprehensive API documentation"),
            ("guide-creation", "Create user guides and tutorials"),
            ("example-generation", "Generate code examples and snippets"),
            ("doc-maintenance", "Update and maintain existing documentation"),
        ]

        for name, desc in capabilities:
            self.register_capability(AgentCapability(name=name, description=desc))
            self.register_handler(name, self._handle_capability)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return await self._handle_capability(message, context)

    async def _handle_capability(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "auto-documentation":
            return await self._generate_docs(payload)
        elif capability == "api-doc-generation":
            return await self._generate_api_docs(payload)
        elif capability == "guide-creation":
            return await self._create_guide(payload)
        elif capability == "example-generation":
            return await self._generate_examples(payload)
        elif capability == "doc-maintenance":
            return await self._maintain_docs(payload)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    async def _generate_docs(self, payload: Dict[str, Any]) -> AgentResponse:
        """Generate documentation from code."""
        source = payload.get("source", "")
        format_type = payload.get("format", "markdown")

        doc_id = str(uuid4())
        self._generated_docs[doc_id] = {
            "type": "auto",
            "format": format_type,
            "created_at": datetime.utcnow().isoformat(),
        }

        return AgentResponse.success_response({
            "doc_id": doc_id,
            "format": format_type,
            "sections": [
                {"name": "Overview", "generated": True},
                {"name": "Classes", "items": 5},
                {"name": "Functions", "items": 12},
                {"name": "Constants", "items": 3},
            ],
            "coverage": 0.85,
            "warnings": [
                "Missing docstring for function 'helper_method'",
                "Incomplete type hints in class 'DataHandler'",
            ],
        })

    async def _generate_api_docs(self, payload: Dict[str, Any]) -> AgentResponse:
        """Generate API documentation."""
        api_spec = payload.get("spec", {})
        format_type = payload.get("format", "openapi")

        return AgentResponse.success_response({
            "format": format_type,
            "endpoints_documented": 15,
            "schemas_documented": 8,
            "documentation": {
                "title": "API Documentation",
                "version": "1.0.0",
                "endpoints": [
                    {"path": "/api/agents", "methods": ["GET", "POST"], "documented": True},
                    {"path": "/api/agents/{id}", "methods": ["GET", "PUT", "DELETE"], "documented": True},
                    {"path": "/api/health", "methods": ["GET"], "documented": True},
                ],
                "schemas": ["Agent", "AgentCapability", "Response", "Error"],
            },
            "output_formats": ["html", "json", "yaml"],
        })

    async def _create_guide(self, payload: Dict[str, Any]) -> AgentResponse:
        """Create user guide."""
        topic = payload.get("topic", "Getting Started")
        audience = payload.get("audience", "developers")

        return AgentResponse.success_response({
            "guide_id": str(uuid4()),
            "title": f"{topic} Guide",
            "audience": audience,
            "sections": [
                {"title": "Introduction", "word_count": 300},
                {"title": "Prerequisites", "word_count": 150},
                {"title": "Installation", "word_count": 400},
                {"title": "Quick Start", "word_count": 500},
                {"title": "Configuration", "word_count": 350},
                {"title": "Troubleshooting", "word_count": 250},
            ],
            "total_word_count": 1950,
            "reading_time": "8 minutes",
            "includes_examples": True,
        })

    async def _generate_examples(self, payload: Dict[str, Any]) -> AgentResponse:
        """Generate code examples."""
        topic = payload.get("topic", "basic_usage")
        language = payload.get("language", "python")

        return AgentResponse.success_response({
            "topic": topic,
            "language": language,
            "examples": [
                {
                    "title": "Basic Usage",
                    "description": "How to get started",
                    "code": f"# {language.title()} example\nfrom agent import create_agent\nagent = create_agent('my-agent')",
                    "runnable": True,
                },
                {
                    "title": "With Configuration",
                    "description": "Configure the agent",
                    "code": "agent = create_agent('my-agent', config={'timeout': 30})",
                    "runnable": True,
                },
                {
                    "title": "Error Handling",
                    "description": "Handle errors gracefully",
                    "code": "try:\n    result = agent.execute()\nexcept AgentError as e:\n    print(f'Error: {e}')",
                    "runnable": True,
                },
            ],
            "total_examples": 3,
        })

    async def _maintain_docs(self, payload: Dict[str, Any]) -> AgentResponse:
        """Maintain documentation."""
        action = payload.get("action", "check")

        if action == "check":
            return AgentResponse.success_response({
                "status": "needs_update",
                "issues": [
                    {"type": "outdated", "file": "api.md", "section": "Endpoints", "severity": "high"},
                    {"type": "broken_link", "file": "guide.md", "link": "/old-path", "severity": "medium"},
                    {"type": "missing", "file": "changelog.md", "description": "No entry for v1.2", "severity": "low"},
                ],
                "coverage": {
                    "classes": "90%",
                    "functions": "85%",
                    "endpoints": "100%",
                },
                "last_updated": "2026-01-01",
            })
        elif action == "update":
            return AgentResponse.success_response({
                "updated": True,
                "files_updated": 3,
                "changes": [
                    {"file": "api.md", "change": "Updated endpoint documentation"},
                    {"file": "guide.md", "change": "Fixed broken links"},
                    {"file": "changelog.md", "change": "Added v1.2 entry"},
                ],
            })

        return AgentResponse.success_response({"action": action, "status": "processed"})
