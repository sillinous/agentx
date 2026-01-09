# Base Agent Framework
# Core abstractions for all agent implementations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class Protocol(str, Enum):
    """Supported agent communication protocols."""
    A2A = "a2a/1.0"    # Agent-to-Agent
    ACP = "acp/1.0"    # Agent Communication Protocol
    ANP = "anp/1.0"    # Agent Network Protocol
    MCP = "mcp/1.0"    # Model Context Protocol


class MessageType(str, Enum):
    """Types of agent messages."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    COMMAND = "command"
    QUERY = "query"
    NOTIFICATION = "notification"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentCapability:
    """Describes a capability an agent provides."""
    name: str
    description: str
    version: str = "1.0.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    returns: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": self.parameters,
            "returns": self.returns,
        }


@dataclass
class AgentMessage:
    """Standard message format for agent communication."""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.REQUEST
    sender: str = ""
    recipient: str = ""
    capability: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    protocol: Protocol = Protocol.A2A

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "capability": self.capability,
            "payload": self.payload,
            "metadata": self.metadata,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "protocol": self.protocol.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls(
            id=data.get("id", str(uuid4())),
            type=MessageType(data.get("type", "request")),
            sender=data.get("sender", ""),
            recipient=data.get("recipient", ""),
            capability=data.get("capability", ""),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            priority=MessagePriority(data.get("priority", "normal")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            correlation_id=data.get("correlation_id"),
            protocol=Protocol(data.get("protocol", "a2a/1.0")),
        )


@dataclass
class AgentResponse:
    """Standard response format from agents."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    message_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
        }

    @classmethod
    def success_response(cls, data: Any, correlation_id: Optional[str] = None, **kwargs) -> "AgentResponse":
        return cls(success=True, data=data, correlation_id=correlation_id, **kwargs)

    @classmethod
    def error_response(cls, error: str, error_code: str = "UNKNOWN_ERROR",
                       correlation_id: Optional[str] = None, **kwargs) -> "AgentResponse":
        return cls(success=False, error=error, error_code=error_code,
                   correlation_id=correlation_id, **kwargs)


@dataclass
class AgentContext:
    """Execution context for agent operations."""
    request_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    environment: str = "production"
    timeout_ms: int = 30000
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "environment": self.environment,
            "timeout_ms": self.timeout_ms,
            "metadata": self.metadata,
        }


class AgentState(str, Enum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class AgentHealth:
    """Agent health status."""
    status: str = "healthy"
    state: AgentState = AgentState.READY
    uptime_seconds: float = 0.0
    requests_processed: int = 0
    errors_count: int = 0
    last_activity: Optional[datetime] = None
    memory_usage_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "state": self.state.value,
            "uptime_seconds": self.uptime_seconds,
            "requests_processed": self.requests_processed,
            "errors_count": self.errors_count,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "memory_usage_mb": self.memory_usage_mb,
        }


class BaseAgent(ABC):
    """
    Base class for all agent implementations.

    Provides:
    - Lifecycle management (start, stop, pause, resume)
    - Message handling with protocol support
    - Capability registration and discovery
    - Health monitoring
    - Event hooks
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str = "1.0.0",
        protocols: Optional[List[Protocol]] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.protocols = protocols or [Protocol.A2A, Protocol.ACP]

        self._state = AgentState.INITIALIZING
        self._capabilities: Dict[str, AgentCapability] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._event_hooks: Dict[str, List[Callable]] = {}
        self._health = AgentHealth()
        self._start_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

        # Register default capabilities
        self._register_default_capabilities()

    @abstractmethod
    def _register_default_capabilities(self) -> None:
        """Register agent-specific capabilities. Override in subclasses."""
        pass

    @abstractmethod
    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Process an incoming message. Override in subclasses."""
        pass

    # Lifecycle Management

    async def start(self) -> None:
        """Start the agent."""
        async with self._lock:
            if self._state != AgentState.INITIALIZING:
                raise RuntimeError(f"Cannot start agent in state: {self._state}")

            await self._on_start()
            self._state = AgentState.READY
            self._start_time = datetime.utcnow()
            self._health.status = "healthy"
            await self._emit_event("agent_started", {"agent_id": self.agent_id})
            logger.info(f"Agent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent."""
        async with self._lock:
            self._state = AgentState.SHUTTING_DOWN
            await self._on_stop()
            self._state = AgentState.STOPPED
            await self._emit_event("agent_stopped", {"agent_id": self.agent_id})
            logger.info(f"Agent {self.agent_id} stopped")

    async def pause(self) -> None:
        """Pause the agent."""
        async with self._lock:
            if self._state == AgentState.READY:
                self._state = AgentState.PAUSED
                await self._emit_event("agent_paused", {"agent_id": self.agent_id})

    async def resume(self) -> None:
        """Resume the agent."""
        async with self._lock:
            if self._state == AgentState.PAUSED:
                self._state = AgentState.READY
                await self._emit_event("agent_resumed", {"agent_id": self.agent_id})

    async def _on_start(self) -> None:
        """Hook called during agent startup. Override for custom initialization."""
        pass

    async def _on_stop(self) -> None:
        """Hook called during agent shutdown. Override for custom cleanup."""
        pass

    # Capability Management

    def register_capability(self, capability: AgentCapability) -> None:
        """Register a capability this agent provides."""
        self._capabilities[capability.name] = capability

    def get_capabilities(self) -> List[AgentCapability]:
        """Get all registered capabilities."""
        return list(self._capabilities.values())

    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability."""
        return capability_name in self._capabilities

    # Message Handling

    def register_handler(self, capability: str, handler: Callable) -> None:
        """Register a handler for a specific capability."""
        self._message_handlers[capability] = handler

    async def handle_message(self, message: AgentMessage, context: Optional[AgentContext] = None) -> AgentResponse:
        """Main entry point for handling messages."""
        if self._state != AgentState.READY:
            return AgentResponse.error_response(
                f"Agent not ready. Current state: {self._state.value}",
                error_code="AGENT_NOT_READY",
                correlation_id=message.id,
            )

        context = context or AgentContext()
        start_time = datetime.utcnow()

        try:
            async with self._lock:
                self._state = AgentState.BUSY

            # Check if we have a specific handler
            if message.capability in self._message_handlers:
                handler = self._message_handlers[message.capability]
                if asyncio.iscoroutinefunction(handler):
                    response = await handler(message, context)
                else:
                    response = handler(message, context)
            else:
                # Fall back to general message processing
                response = await self.process_message(message, context)

            # Update health metrics
            self._health.requests_processed += 1
            self._health.last_activity = datetime.utcnow()

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response.execution_time_ms = execution_time
            response.correlation_id = message.id

            return response

        except Exception as e:
            self._health.errors_count += 1
            logger.exception(f"Error handling message in agent {self.agent_id}")
            return AgentResponse.error_response(
                str(e),
                error_code="PROCESSING_ERROR",
                correlation_id=message.id,
            )
        finally:
            async with self._lock:
                if self._state == AgentState.BUSY:
                    self._state = AgentState.READY

    # Event System

    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        if event not in self._event_hooks:
            self._event_hooks[event] = []
        self._event_hooks[event].append(handler)

    async def _emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit an event to all registered handlers."""
        if event in self._event_hooks:
            for handler in self._event_hooks[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event}: {e}")

    # Health & Monitoring

    def get_health(self) -> AgentHealth:
        """Get agent health status."""
        if self._start_time:
            self._health.uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
        self._health.state = self._state
        return self._health

    # Protocol Support

    def supports_protocol(self, protocol: Protocol) -> bool:
        """Check if agent supports a protocol."""
        return protocol in self.protocols

    # Agent Card (ANP Discovery)

    def get_agent_card(self) -> Dict[str, Any]:
        """Get agent card for ANP discovery."""
        return {
            "id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "protocols": [p.value for p in self.protocols],
            "capabilities": [c.to_dict() for c in self.get_capabilities()],
            "state": self._state.value,
            "health": self.get_health().to_dict(),
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, state={self._state.value})>"
