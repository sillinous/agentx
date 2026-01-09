"""
Agent Validator - Validates agents against 8 Architectural Principles.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Type
import inspect


class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    principle: str
    severity: ValidationSeverity
    message: str
    suggestion: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    agent_id: str
    issues: List[ValidationIssue] = field(default_factory=list)
    score: float = 0.0

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def to_dict(self) -> Dict[str, Any]:
        return {"is_valid": self.is_valid, "agent_id": self.agent_id, "score": self.score,
                "error_count": len(self.errors), "warning_count": len(self.warnings),
                "issues": [{"principle": i.principle, "severity": i.severity.value,
                           "message": i.message, "suggestion": i.suggestion} for i in self.issues]}


class AgentValidator:
    REQUIRED_METHODS = ["initialize", "shutdown", "execute", "health_check", "get_capabilities"]
    REQUIRED_PROTOCOLS = ["a2a", "a2p", "acp", "anp", "mcp"]

    def __init__(self, strict: bool = False):
        self.strict = strict

    def validate_class(self, agent_class: Type) -> ValidationResult:
        issues: List[ValidationIssue] = []
        agent_id = getattr(agent_class, "__name__", "unknown")
        for method in self.REQUIRED_METHODS:
            if not hasattr(agent_class, method):
                issues.append(ValidationIssue("Standardized", ValidationSeverity.ERROR,
                    f"Missing required method: {method}()", f"Implement {method}() from BaseAgent"))
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        score = max(0, 100 - (error_count * 12.5) - (warning_count * 2.5))
        is_valid = error_count == 0 if not self.strict else (error_count == 0 and warning_count == 0)
        return ValidationResult(is_valid=is_valid, agent_id=agent_id, issues=issues, score=score)

    def validate_metadata(self, metadata: Dict[str, Any]) -> ValidationResult:
        issues: List[ValidationIssue] = []
        agent_id = metadata.get("id", "unknown")
        for field in ["id", "name", "version", "capabilities", "protocols"]:
            if field not in metadata:
                issues.append(ValidationIssue("Standardized", ValidationSeverity.ERROR,
                    f"Missing required field: {field}", f"Add '{field}' to metadata"))
        protocols = metadata.get("protocols", [])
        proto_names = [p.split("/")[0].lower() for p in protocols]
        for req in self.REQUIRED_PROTOCOLS:
            if req not in proto_names:
                issues.append(ValidationIssue("Interoperable", ValidationSeverity.WARNING,
                    f"Missing protocol: {req}", f"Add '{req}/1.0' to protocols"))
        if not metadata.get("capabilities"):
            issues.append(ValidationIssue("Composable", ValidationSeverity.ERROR,
                "No capabilities defined", "Define at least one capability"))
        if not metadata.get("implementations"):
            issues.append(ValidationIssue("Redeployable", ValidationSeverity.WARNING,
                "No implementation paths", "Add implementation paths"))
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
        score = max(0, 100 - (error_count * 12.5) - (warning_count * 2.5))
        is_valid = error_count == 0 if not self.strict else (error_count == 0 and warning_count == 0)
        return ValidationResult(is_valid=is_valid, agent_id=agent_id, issues=issues, score=score)

    def get_principles(self) -> List[Dict[str, str]]:
        return [
            {"id": "standardized", "name": "Standardized", "description": "Uses BaseAgent + dataclass config"},
            {"id": "interoperable", "name": "Interoperable", "description": "Implements 5 protocols"},
            {"id": "redeployable", "name": "Redeployable", "description": "Environment config support"},
            {"id": "reusable", "name": "Reusable", "description": "No embedded assumptions"},
            {"id": "atomic", "name": "Atomic", "description": "Single responsibility"},
            {"id": "composable", "name": "Composable", "description": "Schema-based I/O"},
            {"id": "orchestratable", "name": "Orchestratable", "description": "Coordination protocol support"},
            {"id": "vendor_agnostic", "name": "Vendor Agnostic", "description": "No proprietary dependencies"},
        ]
