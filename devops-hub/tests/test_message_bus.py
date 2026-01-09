"""
Tests for the message bus.
"""

import pytest

from service.message_bus import (
    MessageBus,
    Event,
    EventType,
    get_message_bus,
)


class TestEvent:
    """Tests for Event."""

    def test_event_creation(self):
        event = Event(
            type="test.event",
            source="test-source",
            data={"key": "value"},
        )
        assert event.type == "test.event"
        assert event.source == "test-source"
        assert event.data["key"] == "value"
        assert event.id is not None

    def test_event_with_correlation_id(self):
        event = Event(
            type="test.event",
            source="test",
            correlation_id="corr-123",
        )
        assert event.correlation_id == "corr-123"

    def test_event_to_dict(self):
        event = Event(type="test", source="src", data={"x": 1})
        d = event.to_dict()
        assert "id" in d
        assert "type" in d
        assert "source" in d
        assert "data" in d
        assert "timestamp" in d


class TestEventType:
    """Tests for EventType enum."""

    def test_event_types(self):
        assert EventType.AGENT_STARTED == "agent.started"
        assert EventType.TASK_COMPLETED == "task.completed"
        assert EventType.WORKFLOW_STARTED == "workflow.started"


class TestMessageBus:
    """Tests for MessageBus."""

    @pytest.fixture
    def bus(self):
        return MessageBus()

    @pytest.mark.asyncio
    async def test_publish_event(self, bus):
        event = Event(type="test.event", source="test", data={"msg": "hello"})
        await bus.publish(event)

        history = bus.get_history()
        assert len(history) == 1
        assert history[0].type == "test.event"

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self, bus):
        received_events = []

        async def handler(event):
            received_events.append(event)

        bus.subscribe("test.event", handler)

        event = Event(type="test.event", source="test")
        await bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].type == "test.event"

    @pytest.mark.asyncio
    async def test_subscribe_wildcard(self, bus):
        received_events = []

        async def handler(event):
            received_events.append(event)

        bus.subscribe("*", handler)

        await bus.publish(Event(type="event1", source="test"))
        await bus.publish(Event(type="event2", source="test"))

        assert len(received_events) == 2

    @pytest.mark.asyncio
    async def test_subscribe_with_source_filter(self, bus):
        received_events = []

        async def handler(event):
            received_events.append(event)

        bus.subscribe("test.event", handler, filter_source="specific-source")

        await bus.publish(Event(type="test.event", source="specific-source"))
        await bus.publish(Event(type="test.event", source="other-source"))

        assert len(received_events) == 1
        assert received_events[0].source == "specific-source"

    def test_unsubscribe(self, bus):
        async def handler(event):
            pass

        sub_id = bus.subscribe("test.event", handler)
        result = bus.unsubscribe(sub_id)
        assert result is True

        result = bus.unsubscribe("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_history(self, bus):
        await bus.publish(Event(type="event1", source="src1"))
        await bus.publish(Event(type="event2", source="src2"))
        await bus.publish(Event(type="event1", source="src1"))

        all_history = bus.get_history()
        assert len(all_history) == 3

        filtered = bus.get_history(event_type="event1")
        assert len(filtered) == 2

        filtered = bus.get_history(source="src2")
        assert len(filtered) == 1

    @pytest.mark.asyncio
    async def test_history_limit(self, bus):
        for i in range(10):
            await bus.publish(Event(type="test", source="test", data={"i": i}))

        history = bus.get_history(limit=5)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_history_size_limit(self):
        bus = MessageBus(history_size=5)

        for i in range(10):
            await bus.publish(Event(type="test", source="test", data={"i": i}))

        history = bus.get_history()
        assert len(history) == 5
        # Should have the last 5 events
        assert history[0].data["i"] == 5

    def test_get_subscriptions(self, bus):
        async def handler(event):
            pass

        bus.subscribe("event1", handler)
        bus.subscribe("event1", handler)
        bus.subscribe("event2", handler)

        subs = bus.get_subscriptions()
        assert subs["event1"] == 2
        assert subs["event2"] == 1

    @pytest.mark.asyncio
    async def test_emit_agent_started(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.AGENT_STARTED, handler)
        await bus.emit_agent_started("agent-123", extra="data")

        assert len(received) == 1
        assert received[0].data["agent_id"] == "agent-123"

    @pytest.mark.asyncio
    async def test_emit_task_started(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.TASK_STARTED, handler)
        await bus.emit_task_started("agent-1", "task-1", "capability-1")

        assert len(received) == 1
        assert received[0].data["task_id"] == "task-1"
        assert received[0].correlation_id == "task-1"

    @pytest.mark.asyncio
    async def test_emit_workflow_completed(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.WORKFLOW_COMPLETED, handler)
        await bus.emit_workflow_completed("wf-1", "exec-1")

        assert len(received) == 1
        assert received[0].data["workflow_id"] == "wf-1"

    @pytest.mark.asyncio
    async def test_handler_error_does_not_break_bus(self, bus):
        async def bad_handler(event):
            raise ValueError("Handler error")

        async def good_handler(event):
            pass

        bus.subscribe("test", bad_handler)
        bus.subscribe("test", good_handler)

        # Should not raise
        await bus.publish(Event(type="test", source="test"))


class TestMessageBusGlobal:
    """Tests for global message bus."""

    def test_get_message_bus_singleton(self):
        bus1 = get_message_bus()
        bus2 = get_message_bus()
        assert bus1 is bus2
