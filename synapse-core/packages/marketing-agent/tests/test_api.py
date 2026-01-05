"""
Integration Tests for Synapse API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from auth import create_access_token


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing"""
    return create_access_token(
        user_id="test-user-123",
        email="test@synapse.test",
        subscription_tier="enterprise",
    )


@pytest.fixture
def auth_headers(valid_token):
    """Create authorization headers with valid token"""
    return {"Authorization": f"Bearer {valid_token}"}


class TestHealthEndpoints:
    def test_root_endpoint(self, client):
        """Test the root endpoint returns correct information"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "agents" in data
        assert "scribe" in data["agents"]
        assert "architect" in data["agents"]
        assert "sentry" in data["agents"]


class TestAuthEndpoints:
    def test_dev_token_generation(self, client):
        """Test development token generation"""
        response = client.post("/auth/dev-token")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_token_verification_with_valid_token(self, client, auth_headers):
        """Test token verification with valid token"""
        response = client.get("/auth/verify", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data
        assert "email" in data
        assert "subscription_tier" in data

    def test_token_verification_without_token(self, client):
        """Test token verification without token (should fail)"""
        response = client.get("/auth/verify")

        assert response.status_code == 422  # Missing required header

    def test_token_verification_with_invalid_token(self, client):
        """Test token verification with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/auth/verify", headers=headers)

        assert response.status_code == 401


class TestScribeAgent:
    @patch('main.scribe_agent_app')
    def test_invoke_scribe_agent(self, mock_scribe, client, auth_headers):
        """Test invoking the Scribe agent"""
        # Mock the agent response
        mock_response = MagicMock()
        mock_response.content = '{"type": "headline", "content": "Test Headline"}'
        mock_scribe.invoke.return_value = {
            "messages": [mock_response]
        }

        payload = {
            "thread_id": "test-thread-1",
            "prompt": "Write a headline for a yoga app"
        }

        response = client.post("/invoke/scribe", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"]["type"] == "headline"
        assert "content" in data["response"]

    def test_invoke_scribe_without_auth(self, client):
        """Test invoking Scribe without authentication (should fail)"""
        payload = {
            "thread_id": "test-thread-1",
            "prompt": "Write a headline"
        }

        response = client.post("/invoke/scribe", json=payload)

        assert response.status_code == 422  # Missing required header

    @patch('main.scribe_agent_app')
    def test_invoke_scribe_with_invalid_token(self, mock_scribe, client):
        """Test invoking Scribe with invalid token"""
        headers = {"Authorization": "Bearer invalid.token"}
        payload = {
            "thread_id": "test-thread-1",
            "prompt": "Write a headline"
        }

        response = client.post("/invoke/scribe", json=payload, headers=headers)

        assert response.status_code == 401


class TestArchitectAgent:
    @patch('main.architect_agent_app')
    def test_invoke_architect_agent(self, mock_architect, client, auth_headers):
        """Test invoking the Architect agent"""
        # Mock the agent response
        mock_response = MagicMock()
        mock_response.content = '{"type": "component", "code": "export default function Button() { return <button>Click</button> }"}'
        mock_architect.invoke.return_value = {
            "messages": [mock_response]
        }

        payload = {
            "thread_id": "test-thread-2",
            "prompt": "Create a simple button component"
        }

        response = client.post("/invoke/architect", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"]["type"] == "component"
        assert "code" in data["response"]

    def test_invoke_architect_without_auth(self, client):
        """Test invoking Architect without authentication (should fail)"""
        payload = {
            "thread_id": "test-thread-2",
            "prompt": "Create a button"
        }

        response = client.post("/invoke/architect", json=payload)

        assert response.status_code == 422


class TestSentryAgent:
    @patch('main.sentry_agent_app')
    def test_invoke_sentry_agent(self, mock_sentry, client, auth_headers):
        """Test invoking the Sentry agent"""
        # Mock the agent response
        mock_response = MagicMock()
        mock_response.content = '{"type": "analytics_report", "insights": "Traffic up 20%", "recommendations": "Increase ad spend"}'
        mock_sentry.invoke.return_value = {
            "messages": [mock_response]
        }

        payload = {
            "thread_id": "test-thread-3",
            "prompt": "Analyze my website performance for the last 7 days"
        }

        response = client.post("/invoke/sentry", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"]["type"] == "analytics_report"

    def test_invoke_sentry_without_auth(self, client):
        """Test invoking Sentry without authentication (should fail)"""
        payload = {
            "thread_id": "test-thread-3",
            "prompt": "Analyze performance"
        }

        response = client.post("/invoke/sentry", json=payload)

        assert response.status_code == 422


class TestErrorHandling:
    @patch('main.scribe_agent_app')
    def test_agent_returns_non_json_content(self, mock_scribe, client, auth_headers):
        """Test handling of non-JSON responses from agents"""
        # Mock agent returning plain text
        mock_response = MagicMock()
        mock_response.content = "This is just plain text, not JSON"
        mock_scribe.invoke.return_value = {
            "messages": [mock_response]
        }

        payload = {
            "thread_id": "test-thread-error",
            "prompt": "Write something"
        }

        response = client.post("/invoke/scribe", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Should wrap in default structure
        assert data["response"]["type"] == "text"
        assert "content" in data["response"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
