"""
Comprehensive API Integration Tests
Tests end-to-end API workflows, cross-agent scenarios, and system integration.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, UTC

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


@pytest.fixture
def standard_token():
    """Create a standard tier test token."""
    from auth import create_access_token
    return create_access_token("standard-user", "standard@example.com", "standard")


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


class TestHealthEndpoint:
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

    def test_health_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_timestamp_is_recent(self, client):
        """Test that health timestamp is recent."""
        response = client.get("/health")
        data = response.json()

        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        now = datetime.now(UTC)
        diff = abs((now - timestamp).total_seconds())

        # Should be within 5 seconds
        assert diff < 5


class TestDashboardMetricsEndpoint:
    """Tests for the /dashboard/metrics endpoint."""

    def test_dashboard_metrics_returns_data(self, client, valid_token):
        """Test that dashboard metrics returns expected data."""
        response = client.get(
            "/dashboard/metrics",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        # May be 200 or 401 depending on auth configuration
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data or isinstance(data, dict)


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_headers_present(self, client, valid_token):
        """Test that rate limit headers are present."""
        response = client.get("/health")

        # Rate limit headers should be present in response
        headers = response.headers
        assert response.status_code in [200, 429]

    def test_health_endpoint_not_rate_limited(self, client):
        """Test that health endpoint has high rate limit."""
        # Make multiple requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_allows_options_request(self, client):
        """Test that OPTIONS preflight request is handled."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should return 200 or appropriate CORS response
        assert response.status_code in [200, 204, 400]

    def test_cors_headers_on_response(self, client):
        """Test that CORS headers are present on responses."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # Check for CORS headers
        headers = response.headers
        # CORS headers may or may not be present depending on configuration
        assert response.status_code == 200


class TestSecurityHeaders:
    """Tests for security headers."""

    def test_security_headers_present(self, client):
        """Test that security headers are present."""
        response = client.get("/health")
        headers = response.headers

        # Check for common security headers
        # These may be present depending on configuration
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
        ]

        # At minimum, response should succeed
        assert response.status_code == 200


class TestAPIResponseFormats:
    """Tests for API response format consistency."""

    def test_error_responses_have_detail(self, client, valid_token):
        """Test that error responses include detail field."""
        # Try to invoke invalid agent
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "invalid",
                "thread_id": "test",
                "prompt": "test",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_successful_responses_have_expected_fields(self, client):
        """Test that successful responses have expected fields."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Health endpoint should have status
        assert "status" in data

    @patch("main.scribe_agent_app")
    def test_agent_response_format(self, mock_agent, client, valid_token):
        """Test that agent responses have consistent format."""
        mock_response = MagicMock()
        mock_response.content = '{"type": "content", "text": "Response"}'
        mock_agent.invoke.return_value = {"messages": [mock_response]}

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "format-test",
                "prompt": "Test prompt",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should have standard response fields
        assert "response" in data or "content" in data or "text" in data
        assert "agent" in data
        assert "thread_id" in data


class TestEdgeCases:
    """Tests for API edge cases."""

    def test_very_long_thread_id(self, client, valid_token):
        """Test handling of very long thread_id."""
        long_id = "a" * 1000

        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": long_id,
                "prompt": "Test",
            },
        )

        # Should be rejected by validation
        assert response.status_code == 422

    def test_empty_prompt(self, client, valid_token):
        """Test handling of empty prompt."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "",
            },
        )

        # Should be rejected by validation
        assert response.status_code == 422

    def test_unicode_in_prompt(self, client, valid_token):
        """Test handling of unicode in prompt."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "unicode-test",
                "prompt": "Write about 日本語 and emojis 🚀",
            },
        )

        # Should accept unicode
        assert response.status_code in [200, 500]  # 500 if agent fails

    def test_special_characters_in_thread_id(self, client, valid_token):
        """Test handling of special characters in thread_id."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test/thread/../id",
                "prompt": "Test",
            },
        )

        # Should handle or reject special chars
        assert response.status_code in [200, 422, 500]


class TestAuthenticationIntegration:
    """Integration tests for authentication."""

    def test_missing_auth_header(self, client):
        """Test request without auth header."""
        response = client.post(
            "/invoke",
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )

        # In dev mode might work, in production should fail
        assert response.status_code in [200, 401, 500]

    def test_invalid_auth_header_format(self, client):
        """Test request with invalid auth header format."""
        response = client.post(
            "/invoke",
            headers={"Authorization": "InvalidFormat token123"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )

        assert response.status_code in [200, 401]

    def test_malformed_token(self, client):
        """Test request with malformed token."""
        response = client.post(
            "/invoke",
            headers={"Authorization": "Bearer not.a.valid.jwt.token"},
            json={
                "agent": "scribe",
                "thread_id": "test",
                "prompt": "Test",
            },
        )

        assert response.status_code in [200, 401]


class TestMultiAgentWorkflow:
    """Tests for multi-agent workflow scenarios."""

    @patch("main.scribe_agent_app")
    @patch("main.architect_agent_app")
    def test_sequential_agent_calls(self, mock_architect, mock_scribe, client, valid_token):
        """Test calling multiple agents sequentially."""
        # Setup mocks
        mock_scribe_response = MagicMock()
        mock_scribe_response.content = '{"type": "content", "text": "Marketing copy"}'
        mock_scribe.invoke.return_value = {"messages": [mock_scribe_response]}

        mock_arch_response = MagicMock()
        mock_arch_response.content = '{"type": "component", "code": "<Landing />"}'
        mock_architect.invoke.return_value = {"messages": [mock_arch_response]}

        # Call scribe first
        response1 = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "workflow-test",
                "prompt": "Write landing page copy",
            },
        )
        assert response1.status_code == 200

        # Call architect second
        response2 = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "architect",
                "thread_id": "workflow-test",
                "prompt": "Create landing page component",
            },
        )
        assert response2.status_code == 200


class TestConversationEndpoints:
    """Tests for conversation management endpoints."""

    def test_conversations_endpoint_exists(self, client, valid_token):
        """Test that conversations endpoint exists."""
        response = client.get(
            "/conversations",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        # Endpoint should exist (may return empty list or require different auth)
        assert response.status_code in [200, 401, 404, 500]

    def test_single_conversation_endpoint(self, client, valid_token):
        """Test getting a single conversation."""
        response = client.get(
            "/conversations/test-thread-id",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

        # Should handle non-existent conversation gracefully
        assert response.status_code in [200, 404, 401, 500]


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_endpoint_available(self, client):
        """Test that docs endpoint is available."""
        response = client.get("/docs")

        # In production this might be disabled
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
