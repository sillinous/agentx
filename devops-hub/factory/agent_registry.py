"""
Agent Registry - Centralized agent discovery and metadata management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class AgentStatus(Enum):
    DRAFT = "draft"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class AgentDomain(Enum):
    SYSTEM = "system"
    BUSINESS = "business"
    UTILITY = "utility"


class AgentType(Enum):
    SUPERVISOR = "supervisor"
    COORDINATOR = "coordinator"
    WORKER = "worker"
    ANALYST = "analyst"


@dataclass
class PerformanceMetrics:
    max_concurrent_requests: int = 100
    average_latency_ms: int = 500
    uptime_percent: float = 99.9


@dataclass
class AgentMetadata:
    id: str
    name: str
    version: str
    status: AgentStatus
    domain: AgentDomain
    agent_type: AgentType
    description: str
    capabilities: List[str]
    protocols: List[str]
    implementations: Dict[str, str] = field(default_factory=dict)
    documentation: str = ""
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "version": self.version,
            "status": self.status.value, "domain": self.domain.value,
            "type": self.agent_type.value, "description": self.description,
            "capabilities": self.capabilities, "protocols": self.protocols,
            "implementations": self.implementations, "documentation": self.documentation,
            "performance": {"max_concurrent_requests": self.performance.max_concurrent_requests,
                          "average_latency_ms": self.performance.average_latency_ms,
                          "uptime_percent": self.performance.uptime_percent},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMetadata":
        perf = data.get("performance", {})
        return cls(
            id=data["id"], name=data["name"], version=data.get("version", "1.0.0"),
            status=AgentStatus(data.get("status", "production")),
            domain=AgentDomain(data.get("domain", "utility")),
            agent_type=AgentType(data.get("type", "worker")),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            protocols=data.get("protocols", []),
            implementations=data.get("implementations", {}),
            documentation=data.get("documentation", ""),
            performance=PerformanceMetrics(
                max_concurrent_requests=perf.get("max_concurrent_requests", 100),
                average_latency_ms=perf.get("average_latency_ms", 500),
                uptime_percent=perf.get("uptime_percent", 99.9)),
        )


class AgentRegistry:
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path
        self.agents: Dict[str, AgentMetadata] = {}
        self._index_by_domain: Dict[str, List[str]] = {}
        self._index_by_capability: Dict[str, List[str]] = {}
        self._index_by_status: Dict[str, List[str]] = {}
        self._index_by_type: Dict[str, List[str]] = {}
        if registry_path and registry_path.exists():
            self._load_from_file()

    def register(self, metadata: AgentMetadata) -> str:
        if metadata.id in self.agents:
            raise ValueError(f"Agent {metadata.id} already registered")
        self.agents[metadata.id] = metadata
        self._add_to_indexes(metadata)
        if self.registry_path:
            self._save_to_file()
        return metadata.id

    def update(self, metadata: AgentMetadata) -> None:
        if metadata.id not in self.agents:
            raise KeyError(f"Agent {metadata.id} not found")
        self._remove_from_indexes(self.agents[metadata.id])
        metadata.updated_at = datetime.now()
        self.agents[metadata.id] = metadata
        self._add_to_indexes(metadata)

    def get(self, agent_id: str) -> Optional[AgentMetadata]:
        return self.agents.get(agent_id)

    def list_all(self) -> List[AgentMetadata]:
        return list(self.agents.values())

    def count(self) -> int:
        return len(self.agents)

    def discover(self, domain: Optional[str] = None, capability: Optional[str] = None,
                 status: Optional[str] = None, agent_type: Optional[str] = None) -> List[AgentMetadata]:
        candidates = set(self.agents.keys())
        if domain:
            candidates &= set(self._index_by_domain.get(domain, []))
        if capability:
            candidates &= set(self._index_by_capability.get(capability, []))
        if status:
            candidates &= set(self._index_by_status.get(status, []))
        if agent_type:
            candidates &= set(self._index_by_type.get(agent_type, []))
        return [self.agents[aid] for aid in candidates]

    def get_capabilities(self) -> List[str]:
        return list(self._index_by_capability.keys())

    def get_domains(self) -> List[str]:
        return list(self._index_by_domain.keys())

    def _add_to_indexes(self, m: AgentMetadata) -> None:
        d, s, t = m.domain.value, m.status.value, m.agent_type.value
        self._index_by_domain.setdefault(d, []).append(m.id)
        self._index_by_status.setdefault(s, []).append(m.id)
        self._index_by_type.setdefault(t, []).append(m.id)
        for cap in m.capabilities:
            self._index_by_capability.setdefault(cap, []).append(m.id)

    def _remove_from_indexes(self, m: AgentMetadata) -> None:
        d, s, t = m.domain.value, m.status.value, m.agent_type.value
        if d in self._index_by_domain:
            self._index_by_domain[d] = [x for x in self._index_by_domain[d] if x != m.id]
        if s in self._index_by_status:
            self._index_by_status[s] = [x for x in self._index_by_status[s] if x != m.id]
        if t in self._index_by_type:
            self._index_by_type[t] = [x for x in self._index_by_type[t] if x != m.id]
        for cap in m.capabilities:
            if cap in self._index_by_capability:
                self._index_by_capability[cap] = [x for x in self._index_by_capability[cap] if x != m.id]

    def _load_from_file(self) -> None:
        with open(self.registry_path, "r") as f:
            for agent in json.load(f).get("agents", []):
                m = AgentMetadata.from_dict(agent)
                self.agents[m.id] = m
                self._add_to_indexes(m)

    def _save_to_file(self) -> None:
        if not self.registry_path:
            return
        data = {"version": "1.0.0", "last_updated": datetime.now().isoformat(),
                "total_agents": len(self.agents),
                "agents": [a.to_dict() for a in self.agents.values()]}
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_from_json(self, json_path: Path) -> int:
        with open(json_path, "r") as f:
            data = json.load(f)
        count = 0
        for agent in data.get("agents", []):
            try:
                m = AgentMetadata.from_dict(agent)
                if m.id not in self.agents:
                    self.register(m)
                    count += 1
            except Exception:
                pass
        return count
    
    def reload(self) -> int:
        """
        Reload agent registry from file.
        
        Clears current state and reloads from registry_path.
        Returns number of agents loaded.
        """
        if not self.registry_path or not self.registry_path.exists():
            return 0
        
        # Clear current state
        self.agents.clear()
        self._index_by_domain.clear()
        self._index_by_capability.clear()
        self._index_by_status.clear()
        self._index_by_type.clear()
        
        # Reload from file
        self._load_from_file()
        
        return len(self.agents)
