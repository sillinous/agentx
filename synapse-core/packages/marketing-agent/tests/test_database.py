"""
Tests for database utilities.
Tests use mock database connections when PostgreSQL is not available.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Test environment is set in conftest.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_utils import (
    DatabaseConnection,
    MockConnection,
    MockCursor,
    check_database_health,
    get_brand_dna,
    save_brand_dna,
    store_context,
    search_context,
    log_audit_event,
    get_user_by_email,
    get_user_by_id,
    save_conversation,
    get_conversation,
    get_user_conversations,
    save_generated_content,
    get_generated_content,
    get_user_content,
    search_similar_content,
    generate_embedding,
    get_agent_config,
    db,
)


class TestMockConnection:
    """Tests for MockConnection class."""

    def test_mock_cursor(self):
        """Test MockConnection returns MockCursor."""
        conn = MockConnection()
        cursor = conn.cursor()
        assert isinstance(cursor, MockCursor)

    def test_mock_cursor_execute(self):
        """Test MockCursor execute doesn't raise."""
        cursor = MockCursor()
        cursor.execute("SELECT * FROM users")
        cursor.execute("INSERT INTO users VALUES (%s, %s)", ("test", "value"))

    def test_mock_cursor_fetchone(self):
        """Test MockCursor fetchone returns None."""
        cursor = MockCursor()
        result = cursor.fetchone()
        assert result is None

    def test_mock_cursor_fetchall(self):
        """Test MockCursor fetchall returns empty list."""
        cursor = MockCursor()
        result = cursor.fetchall()
        assert result == []


class TestDatabaseConnection:
    """Tests for DatabaseConnection class."""

    def test_default_connection_string(self):
        """Test default connection string is used."""
        conn = DatabaseConnection()
        assert "postgresql" in conn.connection_string

    def test_custom_connection_string(self):
        """Test custom connection string is used."""
        custom_url = "postgresql://custom:custom@localhost:5432/custom"
        conn = DatabaseConnection(custom_url)
        assert conn.connection_string == custom_url


class TestHealthCheck:
    """Tests for database health check."""

    def test_health_check_without_postgres(self):
        """Test health check when psycopg2 not available."""
        health = check_database_health()
        # Should return a dict with connected status
        assert isinstance(health, dict)
        assert "connected" in health


class TestBrandDNA:
    """Tests for brand DNA operations."""

    def test_get_brand_dna_no_data(self):
        """Test get_brand_dna returns None when no data."""
        result = get_brand_dna("nonexistent-user")
        assert result is None

    @patch("database_utils.db.get_connection")
    def test_get_brand_dna_with_data(self, mock_get_conn):
        """Test get_brand_dna returns data when found."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            "professional",
            "modern",
            ["innovative"],
            ["jargon"],
            ["quality"],
        )
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = get_brand_dna("test-user")
        assert result is not None
        assert result["voice_tone"] == "professional"
        assert result["visual_style"] == "modern"


class TestConversations:
    """Tests for conversation operations."""

    def test_get_conversation_no_data(self):
        """Test get_conversation returns None when no data."""
        result = get_conversation("nonexistent-user", "nonexistent-thread")
        assert result is None

    def test_get_user_conversations_empty(self):
        """Test get_user_conversations returns empty list."""
        result = get_user_conversations("nonexistent-user")
        assert result == []

    @patch("database_utils.db.get_connection")
    def test_save_conversation(self, mock_get_conn):
        """Test save_conversation with mock connection."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        messages = [{"role": "user", "content": "Hello"}]
        result = save_conversation("user-1", "thread-1", "scribe", messages)
        assert result is True
        mock_cursor.execute.assert_called_once()


class TestGeneratedContent:
    """Tests for generated content operations."""

    def test_get_generated_content_no_data(self):
        """Test get_generated_content returns None when no data."""
        result = get_generated_content("nonexistent-id")
        assert result is None

    def test_get_user_content_empty(self):
        """Test get_user_content returns empty list."""
        result = get_user_content("nonexistent-user")
        assert result == []

    def test_search_similar_content_empty(self):
        """Test search_similar_content returns empty list."""
        result = search_similar_content("user-1", [0.1] * 1536)
        assert result == []

    @patch("database_utils.db.get_connection")
    def test_save_generated_content(self, mock_get_conn):
        """Test save_generated_content with mock connection."""
        mock_cursor = MagicMock()
        # When agent_type is None, only one fetchone call happens (INSERT RETURNING)
        mock_cursor.fetchone.return_value = ("content-id-123",)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = save_generated_content(
            user_id="user-1",
            content_type="blog_post",
            content="Test content",
            metadata={"key": "value"},
        )
        # With mock, should return the ID
        assert result == "content-id-123"


class TestAuditLog:
    """Tests for audit log operations."""

    @patch("database_utils.db.get_connection")
    def test_log_audit_event(self, mock_get_conn):
        """Test log_audit_event with mock connection."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = log_audit_event(
            user_id="user-1",
            action="create_content",
            resource_type="content",
            details={"content_type": "blog"},
        )
        assert result is True


class TestEmbedding:
    """Tests for embedding generation."""

    def test_generate_embedding_no_api_key(self):
        """Test generate_embedding returns None without API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            # Clear the env var
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            result = generate_embedding("test text")
            # Without API key, should return None
            assert result is None


class TestAgentConfig:
    """Tests for agent configuration."""

    def test_get_agent_config_no_data(self):
        """Test get_agent_config returns None when no data."""
        result = get_agent_config("nonexistent-agent")
        assert result is None


class TestUserOperations:
    """Tests for user operations."""

    def test_get_user_by_email_no_data(self):
        """Test get_user_by_email returns None when no data."""
        result = get_user_by_email("nonexistent@example.com")
        assert result is None

    def test_get_user_by_id_no_data(self):
        """Test get_user_by_id returns None when no data."""
        result = get_user_by_id("nonexistent-id")
        assert result is None

    @patch("database_utils.db.get_connection")
    def test_get_user_by_email_found(self, mock_get_conn):
        """Test get_user_by_email returns user when found."""
        from datetime import datetime, UTC

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            "user-id-123",
            "test@example.com",
            "Test User",
            "enterprise",
            datetime.now(UTC),
        )
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = get_user_by_email("test@example.com")
        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["subscription_tier"] == "enterprise"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
