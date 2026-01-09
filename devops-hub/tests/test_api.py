"""
Integration tests for the REST API endpoints.
"""

import pytest
import httpx

from service.api import app, get_factory


@pytest.fixture
async def client():
    """Create an async test client using httpx with ASGI transport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestHealthEndpoint:
    """Tests for health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestAgentEndpoints:
    """Tests for agent-related endpoints."""

    @pytest.mark.asyncio
    async def test_list_agents(self, client):
        response = await client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_agents_with_status_filter(self, client):
        response = await client.get("/agents?status=production")
        assert response.status_code == 200
        data = response.json()
        for agent in data:
            assert agent["status"] == "production"

    @pytest.mark.asyncio
    async def test_get_agent_details(self, client):
        response = await client.get("/agents/supervisor-agent")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "supervisor-agent"
        assert "capabilities" in data
        assert "protocols" in data

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, client):
        response = await client.get("/agents/nonexistent-agent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_agent_capabilities(self, client):
        response = await client.get("/agents/supervisor-agent/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "supervisor-agent"
        assert "capabilities" in data

    @pytest.mark.asyncio
    async def test_discover_agents(self, client):
        response = await client.get("/agents/discover")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert "filters_applied" in data

    @pytest.mark.asyncio
    async def test_discover_agents_by_domain(self, client):
        response = await client.get("/agents/discover?domain=system")
        assert response.status_code == 200
        data = response.json()
        for agent in data["agents"]:
            assert agent["domain"] == "system"

    @pytest.mark.asyncio
    async def test_discover_agents_by_capability(self, client):
        response = await client.get("/agents/discover?capability=orchestration")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_validate_agent(self, client):
        response = await client.post("/agents/supervisor-agent/validate")
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "score" in data
        assert data["agent_id"] == "supervisor-agent"


class TestExecutionEndpoint:
    """Tests for agent execution endpoint."""

    @pytest.mark.asyncio
    async def test_execute_agent(self, client):
        response = await client.post(
            "/agents/research-analyzer/execute",
            json={
                "capability": "market-analysis",
                "input_data": {"market": "technology", "region": "global"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "research-analyzer"
        assert data["status"] == "success"
        assert "output" in data
        assert "execution_time_ms" in data

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, client):
        response = await client.post(
            "/agents/nonexistent/execute",
            json={"capability": "test", "input_data": {}},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_agent_invalid_capability(self, client):
        response = await client.post(
            "/agents/research-analyzer/execute",
            json={"capability": "nonexistent-capability", "input_data": {}},
        )
        assert response.status_code == 400


class TestStatisticsEndpoint:
    """Tests for statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_statistics(self, client):
        response = await client.get("/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_agents" in data
        assert "by_status" in data
        assert "by_domain" in data
        assert "by_type" in data
        assert "capabilities_count" in data


class TestDiscoveryEndpoints:
    """Tests for discovery endpoints."""

    @pytest.mark.asyncio
    async def test_list_capabilities(self, client):
        response = await client.get("/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert "capabilities" in data
        assert isinstance(data["capabilities"], list)

    @pytest.mark.asyncio
    async def test_list_domains(self, client):
        response = await client.get("/domains")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)


class TestWorkflowEndpoints:
    """Tests for workflow endpoints."""

    @pytest.mark.asyncio
    async def test_list_workflows(self, client):
        response = await client.get("/workflows")
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert len(data["workflows"]) >= 1

    @pytest.mark.asyncio
    async def test_get_workflow(self, client):
        response = await client.get("/workflows/research-report")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "research-report"
        assert "steps" in data

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, client):
        response = await client.get("/workflows/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_workflow(self, client):
        response = await client.post(
            "/workflows/research-report/execute",
            json={"market": "AI", "region": "US"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert data["workflow_id"] == "research-report"

    @pytest.mark.asyncio
    async def test_create_workflow(self, client):
        response = await client.post(
            "/workflows",
            json={
                "name": "Custom Test Workflow",
                "description": "A test workflow",
                "steps": [
                    {
                        "name": "Step 1",
                        "type": "agent",
                        "agent_id": "research-analyzer",
                        "capability": "market-analysis",
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert data["name"] == "Custom Test Workflow"

    @pytest.mark.asyncio
    async def test_list_executions(self, client):
        response = await client.get("/workflow-executions")
        assert response.status_code == 200
        data = response.json()
        assert "executions" in data


class TestEventEndpoints:
    """Tests for event endpoints."""

    @pytest.mark.asyncio
    async def test_get_events(self, client):
        response = await client.get("/events")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_publish_event(self, client):
        response = await client.post(
            "/events",
            json={
                "type": "test.event",
                "source": "test-client",
                "data": {"message": "Hello"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["published"] is True
        assert "event_id" in data

    @pytest.mark.asyncio
    async def test_get_subscriptions(self, client):
        response = await client.get("/events/subscriptions")
        assert response.status_code == 200
        data = response.json()
        assert "subscriptions" in data
