# Router Agent
# Routes incoming requests to appropriate agents based on capability matching

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import logging
import re

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
class RouteEntry:
    """A routing table entry."""
    pattern: str
    agent_id: str
    capability: str
    priority: int = 0
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentEndpoint:
    """Represents an agent endpoint for routing."""
    agent_id: str
    capabilities: List[str]
    weight: float = 1.0
    healthy: bool = True
    current_load: int = 0
    max_load: int = 100


class RouterAgent(BaseAgent):
    """
    Router Agent - Intelligent request routing to appropriate agents.

    Capabilities:
    - request-routing: Route requests to best matching agent
    - agent-discovery: Discover available agents and capabilities
    - load-balancing: Distribute load across agent instances
    - capability-matching: Match requests to agent capabilities
    """

    def __init__(self):
        super().__init__(
            agent_id="router-agent",
            name="Router Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP, Protocol.MCP],
        )

        self._routing_table: List[RouteEntry] = []
        self._endpoints: Dict[str, AgentEndpoint] = {}
        self._capability_index: Dict[str, List[str]] = {}  # capability -> agent_ids

    def _register_default_capabilities(self) -> None:
        """Register router capabilities."""
        self.register_capability(AgentCapability(
            name="request-routing",
            description="Route a request to the most appropriate agent",
            parameters={
                "request": {"type": "object", "description": "Request to route"},
                "preferred_agent": {"type": "string", "description": "Preferred agent ID (optional)"},
            },
            returns={"type": "object", "properties": {"agent_id": "string", "endpoint": "string"}},
        ))

        self.register_capability(AgentCapability(
            name="agent-discovery",
            description="Discover available agents matching criteria",
            parameters={
                "capability": {"type": "string", "description": "Required capability"},
                "domain": {"type": "string", "description": "Agent domain filter"},
            },
            returns={"type": "array", "items": {"type": "object"}},
        ))

        self.register_capability(AgentCapability(
            name="load-balancing",
            description="Get load-balanced agent selection",
            parameters={
                "capability": {"type": "string", "description": "Required capability"},
                "strategy": {"type": "string", "enum": ["round-robin", "least-loaded", "weighted"]},
            },
            returns={"type": "object", "properties": {"agent_id": "string", "load": "number"}},
        ))

        self.register_capability(AgentCapability(
            name="capability-matching",
            description="Find agents matching capability requirements",
            parameters={
                "capabilities": {"type": "array", "description": "Required capabilities"},
                "match_mode": {"type": "string", "enum": ["all", "any"]},
            },
            returns={"type": "array", "items": {"type": "string"}},
        ))

        # Register handlers
        self.register_handler("request-routing", self._handle_routing)
        self.register_handler("agent-discovery", self._handle_discovery)
        self.register_handler("load-balancing", self._handle_load_balancing)
        self.register_handler("capability-matching", self._handle_capability_matching)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Process incoming messages."""
        if message.capability in self._message_handlers:
            return await self._message_handlers[message.capability](message, context)

        return AgentResponse.error_response(
            f"Unknown capability: {message.capability}",
            error_code="UNKNOWN_CAPABILITY",
        )

    async def _handle_routing(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle request routing."""
        payload = message.payload
        request = payload.get("request", {})
        preferred_agent = payload.get("preferred_agent")

        # Extract routing hints from request
        target_capability = request.get("capability")
        target_domain = request.get("domain")

        # Try preferred agent first
        if preferred_agent and preferred_agent in self._endpoints:
            endpoint = self._endpoints[preferred_agent]
            if endpoint.healthy and endpoint.current_load < endpoint.max_load:
                return AgentResponse.success_response({
                    "agent_id": preferred_agent,
                    "endpoint": f"/agents/{preferred_agent}",
                    "method": "preferred",
                })

        # Check routing table for pattern match
        request_path = request.get("path", "")
        for entry in sorted(self._routing_table, key=lambda e: -e.priority):
            if re.match(entry.pattern, request_path):
                if entry.agent_id in self._endpoints:
                    endpoint = self._endpoints[entry.agent_id]
                    if endpoint.healthy:
                        return AgentResponse.success_response({
                            "agent_id": entry.agent_id,
                            "endpoint": f"/agents/{entry.agent_id}",
                            "capability": entry.capability,
                            "method": "pattern_match",
                        })

        # Capability-based routing
        if target_capability and target_capability in self._capability_index:
            candidates = self._capability_index[target_capability]
            best_agent = self._select_best_agent(candidates)
            if best_agent:
                return AgentResponse.success_response({
                    "agent_id": best_agent,
                    "endpoint": f"/agents/{best_agent}",
                    "capability": target_capability,
                    "method": "capability_match",
                })

        return AgentResponse.error_response(
            "No suitable agent found for request",
            error_code="NO_ROUTE_FOUND",
        )

    async def _handle_discovery(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle agent discovery requests."""
        payload = message.payload
        capability = payload.get("capability")
        domain = payload.get("domain")

        results = []
        for agent_id, endpoint in self._endpoints.items():
            # Filter by capability
            if capability and capability not in endpoint.capabilities:
                continue

            results.append({
                "agent_id": agent_id,
                "capabilities": endpoint.capabilities,
                "healthy": endpoint.healthy,
                "load": endpoint.current_load,
                "max_load": endpoint.max_load,
            })

        return AgentResponse.success_response({
            "agents": results,
            "total": len(results),
        })

    async def _handle_load_balancing(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle load balancing requests."""
        payload = message.payload
        capability = payload.get("capability")
        strategy = payload.get("strategy", "least-loaded")

        # Get candidate agents
        if capability and capability in self._capability_index:
            candidates = self._capability_index[capability]
        else:
            candidates = list(self._endpoints.keys())

        # Filter to healthy agents
        healthy_candidates = [
            c for c in candidates
            if c in self._endpoints and self._endpoints[c].healthy
        ]

        if not healthy_candidates:
            return AgentResponse.error_response(
                "No healthy agents available",
                error_code="NO_AGENTS_AVAILABLE",
            )

        # Apply load balancing strategy
        if strategy == "least-loaded":
            selected = min(
                healthy_candidates,
                key=lambda a: self._endpoints[a].current_load
            )
        elif strategy == "weighted":
            # Weight by available capacity
            selected = max(
                healthy_candidates,
                key=lambda a: (self._endpoints[a].max_load - self._endpoints[a].current_load) * self._endpoints[a].weight
            )
        else:  # round-robin
            selected = healthy_candidates[0]
            # Rotate for next request
            self._capability_index[capability] = healthy_candidates[1:] + [healthy_candidates[0]]

        endpoint = self._endpoints[selected]
        return AgentResponse.success_response({
            "agent_id": selected,
            "load": endpoint.current_load,
            "max_load": endpoint.max_load,
            "strategy": strategy,
        })

    async def _handle_capability_matching(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle capability matching requests."""
        payload = message.payload
        capabilities = payload.get("capabilities", [])
        match_mode = payload.get("match_mode", "all")

        matching_agents = []

        for agent_id, endpoint in self._endpoints.items():
            agent_caps = set(endpoint.capabilities)
            required_caps = set(capabilities)

            if match_mode == "all":
                if required_caps <= agent_caps:
                    matching_agents.append({
                        "agent_id": agent_id,
                        "matched_capabilities": list(required_caps),
                        "additional_capabilities": list(agent_caps - required_caps),
                    })
            else:  # any
                matched = agent_caps & required_caps
                if matched:
                    matching_agents.append({
                        "agent_id": agent_id,
                        "matched_capabilities": list(matched),
                        "match_ratio": len(matched) / len(required_caps),
                    })

        # Sort by match quality
        if match_mode == "any":
            matching_agents.sort(key=lambda x: -x.get("match_ratio", 0))

        return AgentResponse.success_response({
            "agents": matching_agents,
            "total": len(matching_agents),
            "match_mode": match_mode,
        })

    def _select_best_agent(self, candidates: List[str]) -> Optional[str]:
        """Select the best agent from candidates based on health and load."""
        healthy = [
            c for c in candidates
            if c in self._endpoints and self._endpoints[c].healthy
        ]

        if not healthy:
            return None

        # Return least loaded healthy agent
        return min(healthy, key=lambda a: self._endpoints[a].current_load)

    # Public API

    def register_endpoint(
        self,
        agent_id: str,
        capabilities: List[str],
        weight: float = 1.0,
        max_load: int = 100,
    ) -> None:
        """Register an agent endpoint for routing."""
        self._endpoints[agent_id] = AgentEndpoint(
            agent_id=agent_id,
            capabilities=capabilities,
            weight=weight,
            max_load=max_load,
        )

        # Update capability index
        for cap in capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if agent_id not in self._capability_index[cap]:
                self._capability_index[cap].append(agent_id)

    def add_route(
        self,
        pattern: str,
        agent_id: str,
        capability: str,
        priority: int = 0,
    ) -> None:
        """Add a routing rule."""
        self._routing_table.append(RouteEntry(
            pattern=pattern,
            agent_id=agent_id,
            capability=capability,
            priority=priority,
        ))

    def update_load(self, agent_id: str, load: int) -> None:
        """Update an agent's current load."""
        if agent_id in self._endpoints:
            self._endpoints[agent_id].current_load = load

    def set_health(self, agent_id: str, healthy: bool) -> None:
        """Set an agent's health status."""
        if agent_id in self._endpoints:
            self._endpoints[agent_id].healthy = healthy

    def get_routes(self) -> List[Dict[str, Any]]:
        """Get all routing rules."""
        return [
            {
                "pattern": r.pattern,
                "agent_id": r.agent_id,
                "capability": r.capability,
                "priority": r.priority,
            }
            for r in self._routing_table
        ]
