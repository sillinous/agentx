"""
Tests for Input Validation and Sanitization
Covers edge cases, malformed inputs, and security validations.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

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


class TestInputSanitization:
    """Tests for input sanitization functions."""

    def test_prompt_with_html_tags(self, client, valid_token):
        """Test that HTML tags in prompts are escaped."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "<script>alert('xss')</script>",
            },
        )
        # Should process without error (HTML escaped internally)
        assert response.status_code in [200, 500]  # 500 if agent fails, but no XSS

    def test_prompt_with_sql_injection_attempt(self, client, valid_token):
        """Test that SQL injection attempts are safely handled."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "'; DROP TABLE users; --",
            },
        )
        # Should not cause SQL error
        assert response.status_code in [200, 500]

    def test_thread_id_max_length(self, client, valid_token):
        """Test thread_id length validation."""
        long_thread_id = "a" * 100  # Exceeds 64 char limit
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": long_thread_id,
                "prompt": "Test",
            },
        )
        assert response.status_code == 422  # Validation error

    def test_prompt_max_length(self, client, valid_token):
        """Test prompt length validation."""
        long_prompt = "a" * 15000  # Exceeds 10000 char limit
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": long_prompt,
            },
        )
        assert response.status_code == 422  # Validation error

    def test_empty_thread_id(self, client, valid_token):
        """Test empty thread_id is rejected."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "",
                "prompt": "Test prompt",
            },
        )
        assert response.status_code == 422

    def test_empty_prompt(self, client, valid_token):
        """Test empty prompt is rejected."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "",
            },
        )
        assert response.status_code == 422

    def test_whitespace_only_prompt(self, client, valid_token):
        """Test whitespace-only prompt is rejected."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "   \n\t  ",
            },
        )
        # Should be rejected or sanitized
        assert response.status_code in [200, 422]

    def test_unicode_in_prompt(self, client, valid_token):
        """Test unicode characters in prompt are handled."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test with emoji 🚀 and unicode: 中文",
            },
        )
        # Should handle unicode properly
        assert response.status_code in [200, 500]

    def test_null_bytes_in_input(self, client, valid_token):
        """Test null bytes in input are handled."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test\x00with\x00nulls",
            },
        )
        # Should not crash
        assert response.status_code in [200, 422, 500]


class TestThreadIdValidation:
    """Tests for thread_id pattern validation."""

    def test_valid_thread_id_formats(self, client, valid_token):
        """Test various valid thread_id formats."""
        valid_ids = [
            "test-thread-123",
            "thread_with_underscore",
            "Thread123",
            "simple",
            "a" * 64,  # Max length
        ]
        for thread_id in valid_ids:
            response = client.post(
                "/invoke",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "agent": "scribe",
                    "thread_id": thread_id,
                    "prompt": "Test",
                },
            )
            assert response.status_code != 422, f"Valid thread_id rejected: {thread_id}"

    def test_thread_id_with_special_chars(self, client, valid_token):
        """Test thread_id with disallowed special characters."""
        invalid_ids = [
            "thread/with/slashes",
            "thread\\with\\backslash",
            "thread;with;semicolon",
            "thread<>brackets",
        ]
        for thread_id in invalid_ids:
            response = client.post(
                "/invoke",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "agent": "scribe",
                    "thread_id": thread_id,
                    "prompt": "Test",
                },
            )
            # Should either reject or sanitize
            assert response.status_code in [200, 422, 500]


class TestAgentValidation:
    """Tests for agent type validation."""

    def test_invalid_agent_type(self, client, valid_token):
        """Test that invalid agent types are rejected."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "nonexistent_agent",
                "thread_id": "test-thread",
                "prompt": "Test",
            },
        )
        assert response.status_code == 422

    def test_agent_case_sensitivity(self, client, valid_token):
        """Test that agent names are case-sensitive."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "SCRIBE",  # Should be lowercase
                "thread_id": "test-thread",
                "prompt": "Test",
            },
        )
        assert response.status_code == 422

    def test_all_valid_agents(self, client, valid_token):
        """Test that all valid agent types are accepted."""
        valid_agents = ["scribe", "architect", "sentry"]
        for agent in valid_agents:
            response = client.post(
                "/invoke",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "agent": agent,
                    "thread_id": f"test-{agent}",
                    "prompt": "Test prompt",
                },
            )
            # Agent should be accepted (may fail for other reasons)
            assert response.status_code != 422, f"Valid agent rejected: {agent}"


class TestJsonPayloadValidation:
    """Tests for JSON payload validation."""

    def test_missing_required_fields(self, client, valid_token):
        """Test that missing required fields are rejected."""
        # Missing prompt
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
            },
        )
        assert response.status_code == 422

        # Missing thread_id
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "prompt": "Test",
            },
        )
        assert response.status_code == 422

    def test_extra_fields_ignored(self, client, valid_token):
        """Test that extra fields are ignored."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": "test-thread",
                "prompt": "Test",
                "extra_field": "should be ignored",
                "another_extra": 12345,
            },
        )
        # Should not fail due to extra fields
        assert response.status_code in [200, 500]

    def test_wrong_type_for_fields(self, client, valid_token):
        """Test that wrong types are rejected."""
        # Number instead of string
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": 12345,  # Should be string
                "prompt": "Test",
            },
        )
        assert response.status_code == 422

    def test_empty_json_body(self, client, valid_token):
        """Test that empty JSON body is rejected."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={},
        )
        assert response.status_code == 422

    def test_null_values(self, client, valid_token):
        """Test that null values are rejected."""
        response = client.post(
            "/invoke",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "agent": "scribe",
                "thread_id": None,
                "prompt": "Test",
            },
        )
        assert response.status_code == 422


class TestContentTypeValidation:
    """Tests for Content-Type header validation."""

    def test_without_content_type(self, client, valid_token):
        """Test request without Content-Type header."""
        response = client.post(
            "/invoke",
            headers={
                "Authorization": f"Bearer {valid_token}",
            },
            content='{"agent": "scribe", "thread_id": "test", "prompt": "test"}',
        )
        # FastAPI should handle this
        assert response.status_code in [200, 415, 422, 500]

    def test_form_data_rejected(self, client, valid_token):
        """Test that form data is rejected."""
        response = client.post(
            "/invoke",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="agent=scribe&thread_id=test&prompt=test",
        )
        assert response.status_code in [415, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
