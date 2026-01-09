

class TestUnifiedInvokeEndpoint:
    """Tests for the unified /invoke endpoint."""

    def test_unified_invoke_requires_agent_field(self, client, valid_token):
        """Test that the unified invoke requires agent field."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        assert response.status_code == 422

    def test_unified_invoke_validates_agent_type(self, client, valid_token):
        """Test that the unified invoke validates agent type."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "invalid_agent",
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        assert response.status_code == 422

    @patch("main.scribe_agent_app")
    def test_unified_invoke_routes_to_scribe(self, mock_agent, client, valid_token):
        """Test that unified invoke routes to scribe agent."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "content", "text": "Test response"}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "unified-test-thread",
                "prompt": "Write a tagline",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "scribe"
        assert data["thread_id"] == "unified-test-thread"

    @patch("main.architect_agent_app")
    def test_unified_invoke_routes_to_architect(self, mock_agent, client, valid_token):
        """Test that unified invoke routes to architect agent."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "component", "code": "<Button />"}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "architect",
                "thread_id": "unified-arch-thread",
                "prompt": "Create a button",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "architect"

    @patch("main.sentry_agent_app")
    def test_unified_invoke_routes_to_sentry(self, mock_agent, client, valid_token):
        """Test that unified invoke routes to sentry agent."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "analytics_report", "insights": []}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "sentry",
                "thread_id": "unified-sentry-thread",
                "prompt": "Get analytics",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "sentry"


class TestEnhancedHealthEndpoint:
    """Tests for the enhanced /health endpoint."""

    def test_health_returns_detailed_status(self, client):
        """Test that health endpoint returns detailed status."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "agents" in data
        assert "memory_usage_mb" in data
        assert "timestamp" in data

    def test_health_shows_agent_types(self, client):
        """Test that health shows agent types (mock vs live)."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        agents = data.get("agents", {})

        for agent_name in ["scribe", "architect", "sentry"]:
            assert agent_name in agents
            assert "status" in agents[agent_name]
            assert "type" in agents[agent_name]
