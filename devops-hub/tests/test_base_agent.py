"""
Unit tests for the base agent framework.
"""

import pytest
from datetime import datetime

from built_in_agents.base import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentMessage,
    AgentResponse,
    AgentState,
    AgentHealth,
    MessageType,
    MessagePriority,
    Protocol,
)


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    def __init__(self):
        super().__init__(
            agent_id="test-agent",
            name="Test Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP],
        )

    def _register_default_capabilities(self) -> None:
        self.register_capability(AgentCapability(
            name="test-action",
            description="A test action",
            parameters={"input": {"type": "string"}},
            returns={"type": "object"},
        ))
        self.register_handler("test-action", self._handle_test_action)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return AgentResponse.success_response({"processed": True})

    async def _handle_test_action(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return AgentResponse.success_response({
            "action": "test-action",
            "input": message.payload.get("input"),
            "result": "success",
        })


class TestAgentCapability:
    """Tests for AgentCapability."""

    def test_capability_creation(self):
        cap = AgentCapability(
            name="test-cap",
            description="Test capability",
            version="1.0.0",
            parameters={"x": {"type": "int"}},
            returns={"type": "string"},
        )
        assert cap.name == "test-cap"
        assert cap.version == "1.0.0"

    def test_capability_to_dict(self):
        cap = AgentCapability(name="test", description="Test")
        d = cap.to_dict()
        assert "name" in d
        assert "description" in d
        assert d["name"] == "test"


class TestAgentMessage:
    """Tests for AgentMessage."""

    def test_message_creation(self):
        msg = AgentMessage(
            type=MessageType.REQUEST,
            sender="sender-agent",
            recipient="recipient-agent",
            capability="do-something",
            payload={"key": "value"},
        )
        assert msg.sender == "sender-agent"
        assert msg.type == MessageType.REQUEST
        assert msg.priority == MessagePriority.NORMAL

    def test_message_to_dict(self):
        msg = AgentMessage(capability="test")
        d = msg.to_dict()
        assert "id" in d
        assert "type" in d
        assert "capability" in d

    def test_message_from_dict(self):
        original = AgentMessage(
            sender="test",
            capability="action",
            payload={"data": 123},
        )
        d = original.to_dict()
        restored = AgentMessage.from_dict(d)
        assert restored.sender == original.sender
        assert restored.capability == original.capability


class TestAgentResponse:
    """Tests for AgentResponse."""

    def test_success_response(self):
        resp = AgentResponse.success_response({"result": "ok"})
        assert resp.success is True
        assert resp.data == {"result": "ok"}
        assert resp.error is None

    def test_error_response(self):
        resp = AgentResponse.error_response("Something failed", error_code="TEST_ERROR")
        assert resp.success is False
        assert resp.error == "Something failed"
        assert resp.error_code == "TEST_ERROR"

    def test_response_to_dict(self):
        resp = AgentResponse.success_response({"x": 1})
        d = resp.to_dict()
        assert "success" in d
        assert "data" in d
        assert d["success"] is True


class TestAgentContext:
    """Tests for AgentContext."""

    def test_context_creation(self):
        ctx = AgentContext(
            user_id="user-123",
            session_id="session-456",
            timeout_ms=5000,
        )
        assert ctx.user_id == "user-123"
        assert ctx.timeout_ms == 5000

    def test_context_to_dict(self):
        ctx = AgentContext()
        d = ctx.to_dict()
        assert "request_id" in d
        assert "environment" in d


class TestBaseAgent:
    """Tests for BaseAgent."""

    @pytest.fixture
    def agent(self):
        return ConcreteTestAgent()

    def test_agent_initialization(self, agent):
        assert agent.agent_id == "test-agent"
        assert agent.name == "Test Agent"
        assert agent._state == AgentState.INITIALIZING

    def test_agent_capabilities(self, agent):
        caps = agent.get_capabilities()
        assert len(caps) == 1
        assert caps[0].name == "test-action"

    def test_has_capability(self, agent):
        assert agent.has_capability("test-action") is True
        assert agent.has_capability("non-existent") is False

    def test_supports_protocol(self, agent):
        assert agent.supports_protocol(Protocol.A2A) is True
        assert agent.supports_protocol(Protocol.ANP) is False

    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, agent):
        # Start
        await agent.start()
        assert agent._state == AgentState.READY

        # Pause
        await agent.pause()
        assert agent._state == AgentState.PAUSED

        # Resume
        await agent.resume()
        assert agent._state == AgentState.READY

        # Stop
        await agent.stop()
        assert agent._state == AgentState.STOPPED

    @pytest.mark.asyncio
    async def test_agent_cannot_start_twice(self, agent):
        await agent.start()
        with pytest.raises(RuntimeError):
            await agent.start()

    @pytest.mark.asyncio
    async def test_handle_message(self, agent):
        await agent.start()

        msg = AgentMessage(
            type=MessageType.REQUEST,
            sender="test-sender",
            recipient="test-agent",
            capability="test-action",
            payload={"input": "hello"},
        )

        response = await agent.handle_message(msg)
        assert response.success is True
        assert response.data["action"] == "test-action"
        assert response.data["input"] == "hello"

    @pytest.mark.asyncio
    async def test_handle_message_not_ready(self, agent):
        # Agent not started
        msg = AgentMessage(capability="test-action")
        response = await agent.handle_message(msg)
        assert response.success is False
        assert response.error_code == "AGENT_NOT_READY"

    def test_get_health(self, agent):
        health = agent.get_health()
        assert isinstance(health, AgentHealth)
        assert health.state == AgentState.INITIALIZING

    @pytest.mark.asyncio
    async def test_health_after_requests(self, agent):
        await agent.start()

        msg = AgentMessage(capability="test-action")
        await agent.handle_message(msg)
        await agent.handle_message(msg)

        health = agent.get_health()
        assert health.requests_processed == 2
        assert health.state == AgentState.READY

    def test_get_agent_card(self, agent):
        card = agent.get_agent_card()
        assert card["id"] == "test-agent"
        assert "capabilities" in card
        assert "protocols" in card
        assert "health" in card

    def test_register_capability(self, agent):
        new_cap = AgentCapability(name="new-cap", description="New capability")
        agent.register_capability(new_cap)
        assert agent.has_capability("new-cap")

    @pytest.mark.asyncio
    async def test_event_hooks(self, agent):
        events_received = []

        def on_started(data):
            events_received.append(("started", data))

        agent.on("agent_started", on_started)
        await agent.start()

        assert len(events_received) == 1
        assert events_received[0][0] == "started"
