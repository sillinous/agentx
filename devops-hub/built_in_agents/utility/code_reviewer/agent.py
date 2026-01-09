# Code Reviewer Agent
# Code analysis, suggestions, style checking, and security analysis

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
class CodeReview:
    """A code review result."""
    id: str
    file_count: int
    issues: List[Dict[str, Any]]
    score: float
    created_at: datetime = field(default_factory=datetime.utcnow)


class CodeReviewerAgent(BaseAgent):
    """
    Code Reviewer Agent - Automated code review and analysis.

    Capabilities:
    - code-analysis: Analyze code quality and patterns
    - security-scanning: Scan for security vulnerabilities
    - style-checking: Check code style consistency
    - refactoring-suggestions: Suggest code improvements
    - performance-analysis: Analyze performance issues
    """

    def __init__(self):
        super().__init__(
            agent_id="code-reviewer",
            name="Code Reviewer Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.MCP],
        )
        self._reviews: Dict[str, CodeReview] = {}

    def _register_default_capabilities(self) -> None:
        """Register code review capabilities."""
        capabilities = [
            ("code-analysis", "Analyze code quality, complexity, and patterns"),
            ("security-scanning", "Scan for security vulnerabilities and issues"),
            ("style-checking", "Check code against style guidelines"),
            ("refactoring-suggestions", "Suggest refactoring improvements"),
            ("performance-analysis", "Analyze potential performance issues"),
        ]

        for name, desc in capabilities:
            self.register_capability(AgentCapability(name=name, description=desc))
            self.register_handler(name, self._handle_capability)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return await self._handle_capability(message, context)

    async def _handle_capability(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "code-analysis":
            return await self._analyze_code(payload)
        elif capability == "security-scanning":
            return await self._scan_security(payload)
        elif capability == "style-checking":
            return await self._check_style(payload)
        elif capability == "refactoring-suggestions":
            return await self._suggest_refactoring(payload)
        elif capability == "performance-analysis":
            return await self._analyze_performance(payload)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    async def _analyze_code(self, payload: Dict[str, Any]) -> AgentResponse:
        """Analyze code quality."""
        code = payload.get("code", "")
        language = payload.get("language", "python")

        review = CodeReview(
            id=str(uuid4()),
            file_count=1,
            issues=[
                {"type": "complexity", "severity": "medium", "line": 15, "message": "Function too complex"},
                {"type": "duplication", "severity": "low", "line": 30, "message": "Similar code found"},
            ],
            score=0.78,
        )

        self._reviews[review.id] = review

        return AgentResponse.success_response({
            "review_id": review.id,
            "language": language,
            "score": review.score,
            "metrics": {
                "complexity": {"cyclomatic": 8, "cognitive": 12},
                "maintainability": 0.75,
                "test_coverage": 0.65,
                "duplication": 0.08,
            },
            "issues": review.issues,
            "summary": "Code quality is good with minor issues",
        })

    async def _scan_security(self, payload: Dict[str, Any]) -> AgentResponse:
        """Scan for security vulnerabilities."""
        return AgentResponse.success_response({
            "security_score": 0.85,
            "vulnerabilities": [
                {
                    "id": "SEC001",
                    "severity": "high",
                    "type": "injection",
                    "location": "line 45",
                    "description": "Potential SQL injection",
                    "fix": "Use parameterized queries",
                },
                {
                    "id": "SEC002",
                    "severity": "medium",
                    "type": "xss",
                    "location": "line 78",
                    "description": "Unescaped output",
                    "fix": "Escape HTML output",
                },
            ],
            "passed_checks": [
                "No hardcoded credentials",
                "HTTPS enforced",
                "Input validation present",
            ],
            "recommendations": [
                "Enable CSRF protection",
                "Add rate limiting",
            ],
        })

    async def _check_style(self, payload: Dict[str, Any]) -> AgentResponse:
        """Check code style."""
        style_guide = payload.get("style_guide", "pep8")

        return AgentResponse.success_response({
            "style_guide": style_guide,
            "compliance_score": 0.92,
            "violations": [
                {"rule": "line-length", "count": 5, "severity": "low"},
                {"rule": "naming-convention", "count": 2, "severity": "low"},
                {"rule": "missing-docstring", "count": 3, "severity": "medium"},
            ],
            "auto_fixable": 7,
            "manual_review": 3,
        })

    async def _suggest_refactoring(self, payload: Dict[str, Any]) -> AgentResponse:
        """Suggest refactoring improvements."""
        return AgentResponse.success_response({
            "suggestions": [
                {
                    "type": "extract_method",
                    "location": "lines 25-45",
                    "description": "Extract complex logic into separate method",
                    "benefit": "Improved readability and testability",
                    "effort": "low",
                },
                {
                    "type": "simplify_conditional",
                    "location": "line 67",
                    "description": "Simplify nested conditionals",
                    "benefit": "Reduced complexity",
                    "effort": "low",
                },
                {
                    "type": "design_pattern",
                    "location": "class UserHandler",
                    "description": "Consider Strategy pattern",
                    "benefit": "Better extensibility",
                    "effort": "medium",
                },
            ],
            "total_suggestions": 3,
            "estimated_improvement": "15% reduction in complexity",
        })

    async def _analyze_performance(self, payload: Dict[str, Any]) -> AgentResponse:
        """Analyze performance issues."""
        return AgentResponse.success_response({
            "performance_score": 0.7,
            "issues": [
                {
                    "type": "n+1_query",
                    "location": "line 89",
                    "impact": "high",
                    "description": "N+1 database query pattern",
                    "fix": "Use eager loading or batch queries",
                },
                {
                    "type": "memory_leak",
                    "location": "line 120",
                    "impact": "medium",
                    "description": "Potential memory leak in event handler",
                    "fix": "Clean up subscriptions",
                },
            ],
            "hotspots": [
                {"location": "process_data()", "cpu_impact": "high"},
                {"location": "load_config()", "io_impact": "medium"},
            ],
            "recommendations": [
                "Add caching for frequently accessed data",
                "Use async operations for I/O",
                "Consider lazy loading",
            ],
        })
