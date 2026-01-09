"""
Tests for the SDK client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from sdk.client import (
    AgentServiceClient,
    AsyncAgentServiceClient,
    Agent,
    ExecutionResult,
    WorkflowExecution,
    AgentServiceError,
)


class TestAgent:
    """Tests for Agent dataclass."""

    def test_agent_from_dict(self):
        data = {
            "id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "status": "production",
            "domain": "utility",
            "type": "worker",
            "description": "A test agent",
            "capabilities": ["cap1", "cap2"],
        }
        agent = Agent.from_dict(data)
        assert agent.id == "test-agent"
        assert agent.capabilities == ["cap1", "cap2"]


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_from_dict(self):
        data = {
            "agent_id": "test-agent",
            "status": "success",
            "output": {"result": "ok"},
            "error": None,
            "execution_time_ms": 150.5,
            "timestamp": "2024-01-01T00:00:00",
        }
        result = ExecutionResult.from_dict(data)
        assert result.agent_id == "test-agent"
        assert result.success is True

    def test_execution_result_error(self):
        data = {
            "agent_id": "test-agent",
            "status": "error",
            "output": None,
            "error": "Something failed",
            "execution_time_ms": 50.0,
            "timestamp": "2024-01-01T00:00:00",
        }
        result = ExecutionResult.from_dict(data)
        assert result.success is False
        assert result.error == "Something failed"


class TestWorkflowExecution:
    """Tests for WorkflowExecution dataclass."""

    def test_workflow_execution_from_dict(self):
        data = {
            "id": "exec-123",
            "workflow_id": "wf-1",
            "workflow_name": "Test Workflow",
            "status": "completed",
            "current_step": 2,
            "context": {"input": {"x": 1}},
            "results": {"step1": "done"},
            "errors": [],
            "started_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-01T00:01:00",
        }
        execution = WorkflowExecution.from_dict(data)
        assert execution.id == "exec-123"
        assert execution.success is True


class TestAgentServiceError:
    """Tests for AgentServiceError."""

    def test_error_creation(self):
        error = AgentServiceError("Test error", status_code=404, detail="Not found")
        assert str(error) == "Test error"
        assert error.status_code == 404
        assert error.detail == "Not found"


@pytest.mark.skip(reason="Integration tests require async transport - run with live server")
class TestAgentServiceClientIntegration:
    """Integration tests using actual test server.

    These tests are skipped by default because they require a live server.
    To run them, start the server and use:
        pytest tests/test_sdk_client.py -k Integration --no-skip
    """

    @pytest.fixture
    def client(self):
        """Create a client pointing to live test server."""
        return AgentServiceClient("http://localhost:8100")

    def test_health(self, client):
        result = client.health()
        assert result["status"] == "healthy"

    def test_statistics(self, client):
        result = client.statistics()
        assert "total_agents" in result

    def test_list_agents(self, client):
        agents = client.list_agents()
        assert len(agents) >= 1
        assert all(isinstance(a, Agent) for a in agents)

    def test_get_agent(self, client):
        agent = client.get_agent("supervisor-agent")
        assert agent.id == "supervisor-agent"
        assert isinstance(agent, Agent)

    def test_discover_agents(self, client):
        agents = client.discover_agents(domain="system")
        assert len(agents) >= 1
        for agent in agents:
            assert agent.domain == "system"

    def test_get_capabilities(self, client):
        caps = client.get_capabilities()
        assert isinstance(caps, list)
        assert len(caps) >= 1

    def test_execute_agent(self, client):
        result = client.execute_agent(
            "research-analyzer",
            "market-analysis",
            {"market": "AI"},
        )
        assert isinstance(result, ExecutionResult)
        assert result.agent_id == "research-analyzer"

    def test_list_workflows(self, client):
        workflows = client.list_workflows()
        assert len(workflows) >= 1

    def test_execute_workflow(self, client):
        result = client.execute_workflow(
            "research-report",
            {"market": "Technology"},
        )
        assert isinstance(result, WorkflowExecution)
        assert result.workflow_id == "research-report"


class TestAgentServiceClientUnit:
    """Unit tests with mocked HTTP client."""

    @pytest.fixture
    def mock_client(self):
        client = AgentServiceClient("http://localhost:8100")
        client._client = Mock(spec=httpx.Client)
        return client

    def test_health_success(self, mock_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_client._client.request.return_value = mock_response

        result = mock_client.health()
        assert result["status"] == "healthy"

    def test_request_error_handling(self, mock_client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_client._client.request.return_value = mock_response

        with pytest.raises(AgentServiceError) as exc_info:
            mock_client.get_agent("nonexistent")

        assert exc_info.value.status_code == 404

    def test_context_manager(self):
        with AgentServiceClient("http://localhost:8100") as client:
            assert client is not None


class TestAsyncAgentServiceClient:
    """Tests for async client."""

    @pytest.fixture
    def mock_async_client(self):
        client = AsyncAgentServiceClient("http://localhost:8100")
        client._client = AsyncMock(spec=httpx.AsyncClient)
        return client

    @pytest.mark.asyncio
    async def test_health_async(self, mock_async_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_async_client._client.request = AsyncMock(return_value=mock_response)

        result = await mock_async_client.health()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_list_agents_async(self, mock_async_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "test-agent",
                "name": "Test",
                "version": "1.0.0",
                "status": "production",
                "domain": "utility",
                "type": "worker",
                "description": "Test",
                "capabilities": [],
            }
        ]
        mock_async_client._client.request = AsyncMock(return_value=mock_response)

        agents = await mock_async_client.list_agents()
        assert len(agents) == 1
        assert isinstance(agents[0], Agent)

    @pytest.mark.asyncio
    async def test_execute_agent_async(self, mock_async_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "agent_id": "test-agent",
            "status": "success",
            "output": {"result": "ok"},
            "error": None,
            "execution_time_ms": 100.0,
            "timestamp": "2024-01-01T00:00:00",
        }
        mock_async_client._client.request = AsyncMock(return_value=mock_response)

        result = await mock_async_client.execute_agent("test-agent", "test-cap", {})
        assert result.success is True

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with AsyncAgentServiceClient("http://localhost:8100") as client:
            assert client is not None
