"""
Agent Factory - Central hub for agent registration, validation, and lifecycle management.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from .agent_registry import AgentMetadata, AgentRegistry, AgentStatus
from .agent_validator import AgentValidator, ValidationResult


class AgentFactory:
    def __init__(self, registry_path: Optional[Path] = None, strict_validation: bool = False,
                 auto_load_registry: bool = True):
        self.registry = AgentRegistry(registry_path)
        self.validator = AgentValidator(strict=strict_validation)
        self._agent_classes: Dict[str, Type] = {}
        self._pre_register_hooks: List[Callable] = []
        self._post_register_hooks: List[Callable] = []

    def register_agent(self, metadata: AgentMetadata, agent_class: Optional[Type] = None,
                       skip_validation: bool = False) -> str:
        for hook in self._pre_register_hooks:
            hook(metadata)
        if not skip_validation:
            result = self.validator.validate_metadata(metadata.to_dict())
            if not result.is_valid:
                raise ValueError(f"Validation failed: {'; '.join([e.message for e in result.errors])}")
        if agent_class:
            self._agent_classes[metadata.id] = agent_class
        agent_id = self.registry.register(metadata)
        for hook in self._post_register_hooks:
            hook(metadata)
        return agent_id

    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        return self.registry.get(agent_id)

    def discover_agents(self, domain: Optional[str] = None, capability: Optional[str] = None,
                        status: str = "production", agent_type: Optional[str] = None) -> List[AgentMetadata]:
        return self.registry.discover(domain=domain, capability=capability, status=status, agent_type=agent_type)

    def validate_agent(self, agent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
        if agent_id:
            m = self.registry.get(agent_id)
            if m:
                return self.validator.validate_metadata(m.to_dict())
            raise KeyError(f"Agent {agent_id} not found")
        if metadata:
            return self.validator.validate_metadata(metadata)
        raise ValueError("Must provide agent_id or metadata")

    def promote_to_production(self, agent_id: str) -> None:
        m = self.registry.get(agent_id)
        if not m:
            raise KeyError(f"Agent {agent_id} not found")
        m.status = AgentStatus.PRODUCTION
        self.registry.update(m)

    def deprecate_agent(self, agent_id: str) -> None:
        m = self.registry.get(agent_id)
        if not m:
            raise KeyError(f"Agent {agent_id} not found")
        m.status = AgentStatus.DEPRECATED
        self.registry.update(m)

    def get_statistics(self) -> Dict[str, Any]:
        agents = self.registry.list_all()
        stats = {"total_agents": len(agents), "by_status": {}, "by_domain": {}, "by_type": {},
                 "capabilities": len(self.registry.get_capabilities()), "apqc_processes": 0}
        for a in agents:
            stats["by_status"][a.status.value] = stats["by_status"].get(a.status.value, 0) + 1
            stats["by_domain"][a.domain.value] = stats["by_domain"].get(a.domain.value, 0) + 1
            stats["by_type"][a.agent_type.value] = stats["by_type"].get(a.agent_type.value, 0) + 1
        return stats

    def import_existing_registry(self, json_path: Path) -> int:
        return self.registry.import_from_json(json_path)


def create_factory(base_path: Optional[Path] = None) -> AgentFactory:
    if base_path is None:
        base_path = Path(__file__).parent.parent
    registry_path = base_path / "factory" / "registry.json"
    return AgentFactory(registry_path=registry_path, strict_validation=False)


_default_factory: Optional[AgentFactory] = None


def get_factory() -> AgentFactory:
    global _default_factory
    if _default_factory is None:
        _default_factory = create_factory()
    return _default_factory
