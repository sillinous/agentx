# Registry Agent
# Manages ANP discovery and agent registration across the network

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import json
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
class AgentCard:
    """ANP Agent Card for discovery."""
    agent_id: str
    name: str
    version: str
    description: str
    capabilities: List[str]
    protocols: List[str]
    endpoint: str
    domain: str = "general"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 300


@dataclass
class NetworkNode:
    """Represents a node in the agent network topology."""
    node_id: str
    endpoint: str
    agents: List[str] = field(default_factory=list)
    connected_nodes: List[str] = field(default_factory=list)
    status: str = "active"


class RegistryAgent(BaseAgent):
    """
    Registry Agent - Central registry for agent discovery and registration.

    Capabilities:
    - agent-registration: Register agents with the network
    - agent-discovery: Discover agents by various criteria
    - capability-indexing: Index and search agent capabilities
    - network-topology-management: Manage agent network topology
    """

    def __init__(self):
        super().__init__(
            agent_id="registry-agent",
            name="Registry Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP],
        )

        self._agent_cards: Dict[str, AgentCard] = {}
        self._capability_index: Dict[str, Set[str]] = {}
        self._domain_index: Dict[str, Set[str]] = {}
        self._tag_index: Dict[str, Set[str]] = {}
        self._network_nodes: Dict[str, NetworkNode] = {}

    def _register_default_capabilities(self) -> None:
        """Register registry capabilities."""
        self.register_capability(AgentCapability(
            name="agent-registration",
            description="Register an agent with the network registry",
            parameters={
                "agent_card": {"type": "object", "description": "Agent card data"},
            },
            returns={"type": "object", "properties": {"registered": "boolean", "agent_id": "string"}},
        ))

        self.register_capability(AgentCapability(
            name="agent-discovery",
            description="Discover agents matching search criteria",
            parameters={
                "capability": {"type": "string", "description": "Required capability"},
                "domain": {"type": "string", "description": "Domain filter"},
                "tags": {"type": "array", "description": "Tag filters"},
            },
            returns={"type": "array", "items": {"type": "object"}},
        ))

        self.register_capability(AgentCapability(
            name="capability-indexing",
            description="Index and query agent capabilities",
            parameters={
                "action": {"type": "string", "enum": ["index", "query", "list"]},
                "capability": {"type": "string", "description": "Capability to query"},
            },
            returns={"type": "object"},
        ))

        self.register_capability(AgentCapability(
            name="network-topology-management",
            description="Manage the agent network topology",
            parameters={
                "action": {"type": "string", "enum": ["add-node", "remove-node", "connect", "status"]},
                "node": {"type": "object", "description": "Node data"},
            },
            returns={"type": "object"},
        ))

        # Register handlers
        self.register_handler("agent-registration", self._handle_registration)
        self.register_handler("agent-discovery", self._handle_discovery)
        self.register_handler("capability-indexing", self._handle_capability_indexing)
        self.register_handler("network-topology-management", self._handle_topology)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Process incoming messages."""
        if message.capability in self._message_handlers:
            return await self._message_handlers[message.capability](message, context)

        return AgentResponse.error_response(
            f"Unknown capability: {message.capability}",
            error_code="UNKNOWN_CAPABILITY",
        )

    async def _handle_registration(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle agent registration."""
        payload = message.payload
        action = payload.get("action", "register")

        if action == "register":
            card_data = payload.get("agent_card", {})

            agent_card = AgentCard(
                agent_id=card_data.get("agent_id", ""),
                name=card_data.get("name", ""),
                version=card_data.get("version", "1.0.0"),
                description=card_data.get("description", ""),
                capabilities=card_data.get("capabilities", []),
                protocols=card_data.get("protocols", []),
                endpoint=card_data.get("endpoint", ""),
                domain=card_data.get("domain", "general"),
                tags=card_data.get("tags", []),
                metadata=card_data.get("metadata", {}),
                ttl_seconds=card_data.get("ttl_seconds", 300),
            )

            self._register_agent(agent_card)

            return AgentResponse.success_response({
                "registered": True,
                "agent_id": agent_card.agent_id,
                "expires_at": (
                    datetime.utcnow().timestamp() + agent_card.ttl_seconds
                ),
            })

        elif action == "unregister":
            agent_id = payload.get("agent_id")
            if agent_id and agent_id in self._agent_cards:
                self._unregister_agent(agent_id)
                return AgentResponse.success_response({
                    "unregistered": True,
                    "agent_id": agent_id,
                })
            return AgentResponse.error_response(
                f"Agent not found: {agent_id}",
                error_code="AGENT_NOT_FOUND",
            )

        elif action == "refresh":
            agent_id = payload.get("agent_id")
            if agent_id and agent_id in self._agent_cards:
                self._agent_cards[agent_id].last_seen = datetime.utcnow()
                return AgentResponse.success_response({
                    "refreshed": True,
                    "agent_id": agent_id,
                })
            return AgentResponse.error_response(
                f"Agent not found: {agent_id}",
                error_code="AGENT_NOT_FOUND",
            )

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    async def _handle_discovery(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle agent discovery."""
        payload = message.payload
        capability = payload.get("capability")
        domain = payload.get("domain")
        tags = payload.get("tags", [])
        protocol = payload.get("protocol")

        # Start with all agents
        candidates = set(self._agent_cards.keys())

        # Filter by capability
        if capability:
            if capability in self._capability_index:
                candidates &= self._capability_index[capability]
            else:
                candidates = set()

        # Filter by domain
        if domain:
            if domain in self._domain_index:
                candidates &= self._domain_index[domain]
            else:
                candidates = set()

        # Filter by tags
        for tag in tags:
            if tag in self._tag_index:
                candidates &= self._tag_index[tag]
            else:
                candidates = set()
                break

        # Filter by protocol
        if protocol:
            candidates = {
                c for c in candidates
                if protocol in self._agent_cards[c].protocols
            }

        # Build results
        results = []
        for agent_id in candidates:
            card = self._agent_cards[agent_id]
            results.append({
                "agent_id": card.agent_id,
                "name": card.name,
                "version": card.version,
                "description": card.description,
                "capabilities": card.capabilities,
                "protocols": card.protocols,
                "endpoint": card.endpoint,
                "domain": card.domain,
                "tags": card.tags,
                "last_seen": card.last_seen.isoformat(),
            })

        return AgentResponse.success_response({
            "agents": results,
            "total": len(results),
            "filters": {
                "capability": capability,
                "domain": domain,
                "tags": tags,
                "protocol": protocol,
            },
        })

    async def _handle_capability_indexing(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle capability indexing operations."""
        payload = message.payload
        action = payload.get("action", "list")

        if action == "list":
            capabilities = {}
            for cap, agents in self._capability_index.items():
                capabilities[cap] = list(agents)

            return AgentResponse.success_response({
                "capabilities": capabilities,
                "total": len(capabilities),
            })

        elif action == "query":
            capability = payload.get("capability")
            if capability in self._capability_index:
                agents = [
                    {
                        "agent_id": aid,
                        "name": self._agent_cards[aid].name,
                        "endpoint": self._agent_cards[aid].endpoint,
                    }
                    for aid in self._capability_index[capability]
                    if aid in self._agent_cards
                ]
                return AgentResponse.success_response({
                    "capability": capability,
                    "agents": agents,
                    "count": len(agents),
                })
            return AgentResponse.success_response({
                "capability": capability,
                "agents": [],
                "count": 0,
            })

        elif action == "stats":
            stats = {
                "total_capabilities": len(self._capability_index),
                "total_agents": len(self._agent_cards),
                "total_domains": len(self._domain_index),
                "capabilities_per_agent": sum(
                    len(c.capabilities) for c in self._agent_cards.values()
                ) / max(len(self._agent_cards), 1),
            }
            return AgentResponse.success_response(stats)

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    async def _handle_topology(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle network topology management."""
        payload = message.payload
        action = payload.get("action", "status")

        if action == "status":
            nodes = [
                {
                    "node_id": n.node_id,
                    "endpoint": n.endpoint,
                    "agents": n.agents,
                    "connected_nodes": n.connected_nodes,
                    "status": n.status,
                }
                for n in self._network_nodes.values()
            ]
            return AgentResponse.success_response({
                "nodes": nodes,
                "total_nodes": len(nodes),
                "total_agents": len(self._agent_cards),
            })

        elif action == "add-node":
            node_data = payload.get("node", {})
            node = NetworkNode(
                node_id=node_data.get("node_id", ""),
                endpoint=node_data.get("endpoint", ""),
                agents=node_data.get("agents", []),
            )
            self._network_nodes[node.node_id] = node
            return AgentResponse.success_response({
                "added": True,
                "node_id": node.node_id,
            })

        elif action == "remove-node":
            node_id = payload.get("node_id")
            if node_id in self._network_nodes:
                del self._network_nodes[node_id]
                return AgentResponse.success_response({
                    "removed": True,
                    "node_id": node_id,
                })
            return AgentResponse.error_response(
                f"Node not found: {node_id}",
                error_code="NODE_NOT_FOUND",
            )

        elif action == "connect":
            source = payload.get("source")
            target = payload.get("target")
            if source in self._network_nodes and target in self._network_nodes:
                if target not in self._network_nodes[source].connected_nodes:
                    self._network_nodes[source].connected_nodes.append(target)
                if source not in self._network_nodes[target].connected_nodes:
                    self._network_nodes[target].connected_nodes.append(source)
                return AgentResponse.success_response({
                    "connected": True,
                    "source": source,
                    "target": target,
                })
            return AgentResponse.error_response(
                "One or both nodes not found",
                error_code="NODE_NOT_FOUND",
            )

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    def _register_agent(self, card: AgentCard) -> None:
        """Register an agent and update indices."""
        self._agent_cards[card.agent_id] = card

        # Update capability index
        for cap in card.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = set()
            self._capability_index[cap].add(card.agent_id)

        # Update domain index
        if card.domain not in self._domain_index:
            self._domain_index[card.domain] = set()
        self._domain_index[card.domain].add(card.agent_id)

        # Update tag index
        for tag in card.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(card.agent_id)

    def _unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent and update indices."""
        if agent_id not in self._agent_cards:
            return

        card = self._agent_cards[agent_id]

        # Remove from capability index
        for cap in card.capabilities:
            if cap in self._capability_index:
                self._capability_index[cap].discard(agent_id)

        # Remove from domain index
        if card.domain in self._domain_index:
            self._domain_index[card.domain].discard(agent_id)

        # Remove from tag index
        for tag in card.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(agent_id)

        del self._agent_cards[agent_id]

    # Public API

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all registered agents."""
        return [
            {
                "agent_id": c.agent_id,
                "name": c.name,
                "capabilities": c.capabilities,
                "domain": c.domain,
            }
            for c in self._agent_cards.values()
        ]

    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get capability to agents mapping."""
        return {k: list(v) for k, v in self._capability_index.items()}

    def get_domains(self) -> List[str]:
        """Get all domains."""
        return list(self._domain_index.keys())
