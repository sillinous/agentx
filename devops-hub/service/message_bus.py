"""
Message Bus - Inter-agent communication and event system.

Enables agents to communicate asynchronously through events and messages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4
from enum import Enum
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types."""
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_ERROR = "agent.error"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    CUSTOM = "custom"


@dataclass
class Event:
    """An event in the message bus."""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


@dataclass
class Subscription:
    """A subscription to events."""
    id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "*"  # "*" means all events
    handler: Callable[[Event], Awaitable[None]] = None
    filter_source: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class MessageBus:
    """
    Central message bus for inter-agent communication.

    Features:
    - Publish/subscribe pattern
    - Event filtering by type and source
    - Event history for replay
    - Async event handling
    """

    def __init__(self, history_size: int = 1000):
        self._subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._history_size = history_size
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        async with self._lock:
            # Store in history
            self._event_history.append(event)
            if len(self._event_history) > self._history_size:
                self._event_history = self._event_history[-self._history_size:]

        # Get matching subscribers
        handlers = []

        # Exact type match
        for sub in self._subscriptions.get(event.type, []):
            if sub.filter_source is None or sub.filter_source == event.source:
                handlers.append(sub.handler)

        # Wildcard subscribers
        for sub in self._subscriptions.get("*", []):
            if sub.filter_source is None or sub.filter_source == event.source:
                handlers.append(sub.handler)

        # Execute handlers
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Awaitable[None]],
        filter_source: Optional[str] = None,
    ) -> str:
        """Subscribe to events. Returns subscription ID."""
        sub = Subscription(
            event_type=event_type,
            handler=handler,
            filter_source=filter_source,
        )
        self._subscriptions[event_type].append(sub)
        return sub.id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        for event_type, subs in self._subscriptions.items():
            for sub in subs:
                if sub.id == subscription_id:
                    subs.remove(sub)
                    return True
        return False

    def get_history(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get event history with optional filters."""
        events = self._event_history

        if event_type:
            events = [e for e in events if e.type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]

    def get_subscriptions(self) -> Dict[str, int]:
        """Get subscription counts by event type."""
        return {k: len(v) for k, v in self._subscriptions.items()}

    # Convenience methods for common events

    async def emit_agent_started(self, agent_id: str, **kwargs):
        await self.publish(Event(
            type=EventType.AGENT_STARTED,
            source=agent_id,
            data={"agent_id": agent_id, **kwargs},
        ))

    async def emit_agent_stopped(self, agent_id: str, **kwargs):
        await self.publish(Event(
            type=EventType.AGENT_STOPPED,
            source=agent_id,
            data={"agent_id": agent_id, **kwargs},
        ))

    async def emit_task_started(self, agent_id: str, task_id: str, capability: str, **kwargs):
        await self.publish(Event(
            type=EventType.TASK_STARTED,
            source=agent_id,
            data={"agent_id": agent_id, "task_id": task_id, "capability": capability, **kwargs},
            correlation_id=task_id,
        ))

    async def emit_task_completed(self, agent_id: str, task_id: str, result: Any, **kwargs):
        await self.publish(Event(
            type=EventType.TASK_COMPLETED,
            source=agent_id,
            data={"agent_id": agent_id, "task_id": task_id, "result": result, **kwargs},
            correlation_id=task_id,
        ))

    async def emit_task_failed(self, agent_id: str, task_id: str, error: str, **kwargs):
        await self.publish(Event(
            type=EventType.TASK_FAILED,
            source=agent_id,
            data={"agent_id": agent_id, "task_id": task_id, "error": error, **kwargs},
            correlation_id=task_id,
        ))

    async def emit_workflow_started(self, workflow_id: str, execution_id: str, **kwargs):
        await self.publish(Event(
            type=EventType.WORKFLOW_STARTED,
            source="workflow-engine",
            data={"workflow_id": workflow_id, "execution_id": execution_id, **kwargs},
            correlation_id=execution_id,
        ))

    async def emit_workflow_completed(self, workflow_id: str, execution_id: str, **kwargs):
        await self.publish(Event(
            type=EventType.WORKFLOW_COMPLETED,
            source="workflow-engine",
            data={"workflow_id": workflow_id, "execution_id": execution_id, **kwargs},
            correlation_id=execution_id,
        ))

    async def emit_custom(self, event_type: str, source: str, data: Dict[str, Any], **kwargs):
        await self.publish(Event(
            type=event_type,
            source=source,
            data=data,
            **kwargs,
        ))


# Global message bus instance
_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get the global message bus instance."""
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus
