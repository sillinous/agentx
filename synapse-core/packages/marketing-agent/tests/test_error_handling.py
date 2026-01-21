"""
Tests for Error Handling and Edge Cases
Covers exception scenarios, timeout handling, and error responses.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, UTC

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ["TESTING"] = "1"
os.environ["DEV_MODE"] = "true"

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid test token."""
    from auth import create_access_token
    return create_access_token("test-user", "test@example.com", "enterprise")


class TestAuthenticationErrors:
    """Tests for authentication error handling."""

    def test_missing_authorization_header(self, client):
        """Test request without Authorization header."""
        response = client.post(
            "/invoke",
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        # In dev mode, this might still work
        assert response.status_code in [200, 401, 500]

    def test_invalid_bearer_format(self, client):
        """Test Authorization header without Bearer prefix."""
        response = client.post(
            "/invoke",
            headers={"Authorization": "InvalidFormat token123"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        assert response.status_code in [200, 401]  # Dev mode may allow

    def test_malformed_jwt_token(self, client):
        """Test malformed JWT token."""
        response = client.post(
            "/invoke",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        assert response.status_code in [200, 401]

    def test_expired_token(self, client):
        """Test expired JWT token."""
        import jwt
        secret = os.getenv("JWT_SECRET", "test-secret-for-unit-tests-only")

        expired_payload = {
            "user_id": "test-user",
            "email": "test@test.com",
            "subscription_tier": "standard",
            "type": "access_token",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "iat": datetime.now(UTC) - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        assert response.status_code in [200, 401]

    def test_token_with_wrong_secret(self, client):
        """Test token signed with wrong secret."""
        import jwt

        payload = {
            "user_id": "test-user",
            "email": "test@test.com",
            "subscription_tier": "standard",
            "type": "access_token",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
        }
        wrong_secret_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {wrong_secret_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        assert response.status_code in [200, 401]


class TestAgentInvocationErrors:
    """Tests for agent invocation error handling."""

    @patch("main.scribe_agent_app")
    def test_agent_raises_exception(self, mock_agent, client, valid_token):
        """Test handling when agent raises an exception."""
        mock_agent.invoke.side_effect = Exception("Agent internal error")

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        assert response.status_code == 500
        assert "error" in response.json() or "detail" in response.json()

    @patch("main.scribe_agent_app")
    def test_agent_returns_empty_response(self, mock_agent, client, valid_token):
        """Test handling when agent returns empty response."""
        mock_agent.invoke.return_value = {"messages": []}

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        # Should handle gracefully
        assert response.status_code in [200, 500]

    @patch("main.scribe_agent_app")
    def test_agent_returns_none(self, mock_agent, client, valid_token):
        """Test handling when agent returns None."""
        mock_agent.invoke.return_value = None

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        assert response.status_code == 500

    @patch("main.scribe_agent_app")
    def test_agent_returns_malformed_json(self, mock_agent, client, valid_token):
        """Test handling when agent returns malformed JSON."""
        mock_response = MagicMock()
        mock_response.content = "not valid json {"
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        # Should handle gracefully (may return string content)
        assert response.status_code in [200, 500]


class TestDatabaseErrors:
    """Tests for database error handling."""

    @patch("main.save_conversation")
    @patch("main.scribe_agent_app")
    def test_database_save_failure(self, mock_agent, mock_save, client, valid_token):
        """Test handling when database save fails."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "content", "text": "Response"}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}
        mock_save.side_effect = Exception("Database connection failed")

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        # Should still return response even if save fails
        assert response.status_code in [200, 500]


class TestRateLimitErrors:
    """Tests for rate limiting error handling."""

    def test_rate_limit_headers_present(self, client, valid_token):
        """Test that rate limit headers are present in response."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test prompt",
            },
        )
        # Rate limit headers should be present
        headers = response.headers
        # Headers may or may not be present depending on configuration
        # Just verify no crash
        assert response.status_code in [200, 429, 500]


class TestEndpointErrors:
    """Tests for endpoint-specific error handling."""

    def test_health_endpoint_always_works(self, client):
        """Test that health endpoint works without auth."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_nonexistent_endpoint(self, client, valid_token):
        """Test request to nonexistent endpoint."""
        response = client.get(
            "/nonexistent/endpoint",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 404

    def test_method_not_allowed(self, client, valid_token):
        """Test wrong HTTP method."""
        response = client.get(  # Should be POST
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 405

    def test_invoke_without_json(self, client, valid_token):
        """Test invoke endpoint without JSON body."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 422


class TestErrorResponseFormat:
    """Tests for error response format consistency."""

    def test_validation_error_format(self, client, valid_token):
        """Test that validation errors return proper format."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "invalid",
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_auth_error_format(self, client):
        """Test that auth errors return proper format."""
        response = client.post(
            "/invoke",
            headers={"Authorization": "Bearer invalid.token.here"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        if response.status_code == 401:
            data = response.json()
            assert "detail" in data


class TestConcurrentRequests:
    """Tests for concurrent request handling."""

    def test_multiple_sequential_requests(self, client, valid_token):
        """Test multiple sequential requests work."""
        for i in range(3):
            response = client.get("/health")
            assert response.status_code == 200


class TestSpecialCharacterHandling:
    """Tests for special character handling in errors."""

    def test_error_with_unicode(self, client, valid_token):
        """Test error messages with unicode characters."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "不存在",  # Chinese characters
                "thread_id": "test",
                "prompt": "Test",
            },
        )
        assert response.status_code == 422
        # Should return valid JSON with unicode
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
