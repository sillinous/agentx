"""
Tests for the FastAPI endpoints in main.py
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, UTC
import jwt

# Import the app and auth utilities
from main import app
from auth import JWT_SECRET, JWT_ALGORITHM


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for testing."""
    payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "subscription_tier": "standard",
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
        "type": "access_token",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest.fixture
def expired_token():
    """Generate an expired JWT token for testing."""
    payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "subscription_tier": "standard",
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "iat": datetime.now(UTC) - timedelta(hours=2),
        "type": "access_token",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_server_info(self, client):
        """Test that root endpoint returns server information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "Synapse Agent Server is running" in data["message"]
        assert data["version"] == "1.0.0"

    def test_root_lists_available_agents(self, client):
        """Test that root endpoint lists all available agents."""
        response = client.get("/")
        data = response.json()

        assert "agents" in data
        agents = data["agents"]

        assert "scribe" in agents
        assert agents["scribe"]["name"] == "The Scribe"
        assert agents["scribe"]["endpoint"] == "/invoke/scribe"

        assert "architect" in agents
        assert agents["architect"]["name"] == "The Architect"
        assert agents["architect"]["endpoint"] == "/invoke/architect"

        assert "sentry" in agents
        assert agents["sentry"]["name"] == "The Sentry"
        assert agents["sentry"]["endpoint"] == "/invoke/sentry"


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @patch("main.check_database_health")
    def test_health_returns_healthy_when_db_connected(self, mock_db_health, client):
        """Test health endpoint returns healthy when database is connected."""
        mock_db_health.return_value = {"connected": True, "latency_ms": 5}

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["database"]["connected"] is True

    @patch("main.check_database_health")
    def test_health_returns_degraded_when_db_disconnected(self, mock_db_health, client):
        """Test health endpoint returns degraded when database is disconnected."""
        mock_db_health.return_value = {
            "connected": False,
            "error": "Connection refused",
        }

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"]["connected"] is False

    @patch("main.check_database_health")
    def test_health_shows_agent_status(self, mock_db_health, client):
        """Test health endpoint shows status of all agents."""
        mock_db_health.return_value = {"connected": True}

        response = client.get("/health")
        data = response.json()

        assert "agents" in data
        assert data["agents"]["scribe"] == "ready"
        assert data["agents"]["architect"] == "ready"
        assert data["agents"]["sentry"] == "ready"


class TestAuthDevToken:
    """Tests for the development token endpoint."""

    def test_dev_token_creates_token_in_non_production(self, client):
        """Test that dev token endpoint creates a token in non-production."""
        with patch.dict("os.environ", {"NODE_ENV": "development"}):
            response = client.post("/auth/dev-token")
            assert response.status_code == 200

            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert len(data["access_token"]) > 0

    def test_dev_token_forbidden_in_production(self, client):
        """Test that dev token endpoint is forbidden in production."""
        with patch.dict("os.environ", {"NODE_ENV": "production"}):
            response = client.post("/auth/dev-token")
            assert response.status_code == 403


class TestAuthVerify:
    """Tests for the token verification endpoint."""

    def test_verify_valid_token(self, client, valid_token):
        """Test that a valid token is verified successfully."""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"
        assert data["subscription_tier"] == "standard"

    def test_verify_expired_token(self, client, expired_token):
        """Test that an expired token is rejected."""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    def test_verify_missing_token(self, client):
        """Test that missing authorization header returns error."""
        response = client.get("/auth/verify")
        assert response.status_code == 422  # Validation error - missing header

    def test_verify_invalid_token_format(self, client):
        """Test that invalid token format is rejected."""
        response = client.get(
            "/auth/verify",
            headers={"Authorization": "InvalidFormat token123"},
        )
        assert response.status_code == 401


class TestInvokeScribe:
    """Tests for The Scribe agent invocation endpoint."""

    @patch("main.scribe_agent_app")
    def test_invoke_scribe_success(self, mock_agent, client, valid_token):
        """Test successful invocation of The Scribe agent."""
        mock_response = MagicMock()
        mock_response.content = (
            '{"type": "content", "text": "Generated marketing copy"}'
        )
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke/scribe",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "thread_id": "test-thread-123",
                "prompt": "Write a tagline for my product",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert data["response"]["type"] == "content"

    def test_invoke_scribe_no_auth(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.post(
            "/invoke/scribe",
            json={
                "thread_id": "test-thread-123",
                "prompt": "Write a tagline",
            },
        )
        assert response.status_code == 422  # Missing auth header

    def test_invoke_scribe_expired_token(self, client, expired_token):
        """Test that requests with expired tokens are rejected."""
        response = client.post(
            "/invoke/scribe",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={
                "thread_id": "test-thread-123",
                "prompt": "Write a tagline",
            },
        )
        assert response.status_code == 401

    @patch("main.scribe_agent_app")
    def test_invoke_scribe_with_custom_user_id(self, mock_agent, client, valid_token):
        """Test that custom user_id is used when provided."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "content", "text": "Generated content"}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke/scribe",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "thread_id": "test-thread-123",
                "user_id": "custom-user-456",
                "prompt": "Write content",
            },
        )
        assert response.status_code == 200

        # Verify the custom user_id was passed to the agent
        call_args = mock_agent.invoke.call_args
        assert call_args[1]["config"]["configurable"]["user_id"] == "custom-user-456"


class TestInvokeArchitect:
    """Tests for The Architect agent invocation endpoint."""

    @patch("main.architect_agent_app")
    def test_invoke_architect_success(self, mock_agent, client, valid_token):
        """Test successful invocation of The Architect agent."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "component", "code": "const Button = () => <button>Click</button>"}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke/architect",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "thread_id": "test-thread-123",
                "prompt": "Create a button component",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert data["response"]["type"] == "component"

    def test_invoke_architect_no_auth(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.post(
            "/invoke/architect",
            json={
                "thread_id": "test-thread-123",
                "prompt": "Create a button",
            },
        )
        assert response.status_code == 422

    @patch("main.architect_agent_app")
    def test_invoke_architect_text_response(self, mock_agent, client, valid_token):
        """Test that non-JSON responses are wrapped properly."""
        mock_response = MagicMock()
        mock_response.content = "I need more details about the component."
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke/architect",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "thread_id": "test-thread-123",
                "prompt": "Create something",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["response"]["type"] == "text"
        assert "more details" in data["response"]["content"]


class TestInvokeSentry:
    """Tests for The Sentry agent invocation endpoint."""

    @patch("main.sentry_agent_app")
    def test_invoke_sentry_success(self, mock_agent, client, valid_token):
        """Test successful invocation of The Sentry agent."""
        mock_response = MagicMock()
        mock_response.content = (
            '{"type": "analytics_report", "insights": "Traffic increased 15%"}'
        )
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke/sentry",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "thread_id": "test-thread-123",
                "prompt": "Analyze my traffic patterns",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert data["response"]["type"] == "analytics_report"

    def test_invoke_sentry_no_auth(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.post(
            "/invoke/sentry",
            json={
                "thread_id": "test-thread-123",
                "prompt": "Analyze traffic",
            },
        )
        assert response.status_code == 422

    @patch("main.sentry_agent_app")
    def test_invoke_sentry_passes_user_context(self, mock_agent, client, valid_token):
        """Test that user context is passed to the agent."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "analytics_report", "insights": "Report"}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke/sentry",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "thread_id": "analytics-thread",
                "prompt": "Get metrics",
            },
        )
        assert response.status_code == 200

        # Verify user_id from token was passed
        call_args = mock_agent.invoke.call_args
        assert call_args[1]["config"]["configurable"]["user_id"] == "test-user-123"
        assert call_args[1]["config"]["configurable"]["thread_id"] == "analytics-thread"


class TestParseAgentResponse:
    """Tests for the response parsing helper."""

    def test_parse_json_response(self, client):
        """Test that valid JSON is parsed correctly."""
        from main import parse_agent_response

        result = parse_agent_response('{"type": "content", "text": "Hello"}')
        assert result["type"] == "content"
        assert result["text"] == "Hello"

    def test_parse_text_response(self, client):
        """Test that plain text is wrapped in text structure."""
        from main import parse_agent_response

        result = parse_agent_response("This is plain text")
        assert result["type"] == "text"
        assert result["content"] == "This is plain text"

    def test_parse_invalid_json(self, client):
        """Test that invalid JSON is treated as text."""
        from main import parse_agent_response

        result = parse_agent_response("{invalid json")
        assert result["type"] == "text"
        assert "{invalid json" in result["content"]
