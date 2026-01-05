"""
Tests for database_utils module.
Tests PostgreSQL and SQLite database operations.
"""

import pytest
from unittest.mock import patch, MagicMock
import os


# We need to patch before import due to module-level DATABASE_URL check
@pytest.fixture(autouse=True)
def reset_database_module():
    """Reset database module state between tests."""
    import importlib

    # Clear DATABASE_URL to test SQLite fallback by default
    with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
        import database_utils

        importlib.reload(database_utils)
        yield database_utils


class TestGetDbConnection:
    """Tests for database connection functions."""

    @patch("database_utils._get_sqlite_connection")
    def test_get_db_connection_sqlite_fallback(
        self, mock_sqlite, reset_database_module
    ):
        """Test that SQLite is used when DATABASE_URL is not set."""
        mock_conn = MagicMock()
        mock_sqlite.return_value = mock_conn

        conn = reset_database_module.get_db_connection()

        mock_sqlite.assert_called_once()
        assert conn == mock_conn

    @patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://user:pass@host:5432/db"},
    )
    def test_get_db_connection_postgres(self):
        """Test PostgreSQL connection when DATABASE_URL is set."""
        import importlib
        import database_utils

        importlib.reload(database_utils)

        with patch("database_utils._get_postgres_connection") as mock_pg:
            mock_conn = MagicMock()
            mock_pg.return_value = mock_conn

            conn = database_utils.get_db_connection()

            mock_pg.assert_called_once()
            assert conn == mock_conn


class TestRetrieveBrandDna:
    """Tests for brand DNA retrieval."""

    def test_retrieve_brand_dna_found(self, reset_database_module):
        """Test successful brand DNA retrieval."""
        test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        test_brand_dna = '{"voice": "witty", "colors": ["#00f0ff"]}'

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (test_brand_dna,)

        with patch.object(
            reset_database_module, "get_db_connection", return_value=mock_conn
        ):
            result = reset_database_module.retrieve_brand_dna(test_user_id)

        assert result == {"voice": "witty", "colors": ["#00f0ff"]}
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_retrieve_brand_dna_not_found(self, reset_database_module):
        """Test brand DNA retrieval when user not found - returns defaults."""
        test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        with patch.object(
            reset_database_module, "get_db_connection", return_value=mock_conn
        ):
            result = reset_database_module.retrieve_brand_dna(test_user_id)

        # Should return default brand DNA
        assert "voice" in result
        assert "tone" in result
        mock_conn.close.assert_called_once()

    def test_retrieve_brand_dna_no_connection(self, reset_database_module):
        """Test brand DNA retrieval when no database connection."""
        test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

        with patch.object(
            reset_database_module, "get_db_connection", return_value=None
        ):
            result = reset_database_module.retrieve_brand_dna(test_user_id)

        # Should return default brand DNA
        assert "voice" in result
        assert result["voice"] == "professional"

    def test_retrieve_brand_dna_query_error(self, reset_database_module):
        """Test brand DNA retrieval when query fails."""
        test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Query failed")

        with patch.object(
            reset_database_module, "get_db_connection", return_value=mock_conn
        ):
            result = reset_database_module.retrieve_brand_dna(test_user_id)

        # Should return default brand DNA on error
        assert "voice" in result
        mock_conn.close.assert_called_once()


class TestSaveBrandDna:
    """Tests for brand DNA saving."""

    def test_save_brand_dna_success(self, reset_database_module):
        """Test successful brand DNA save."""
        test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        test_params = {"voice": "friendly", "tone": "casual"}

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(
            reset_database_module, "get_db_connection", return_value=mock_conn
        ):
            result = reset_database_module.save_brand_dna(test_user_id, test_params)

        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_save_brand_dna_no_connection(self, reset_database_module):
        """Test save fails gracefully when no connection."""
        test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        test_params = {"voice": "friendly"}

        with patch.object(
            reset_database_module, "get_db_connection", return_value=None
        ):
            result = reset_database_module.save_brand_dna(test_user_id, test_params)

        assert result is False

    def test_save_brand_dna_query_error(self, reset_database_module):
        """Test save handles query errors."""
        test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        test_params = {"voice": "friendly"}

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Insert failed")

        with patch.object(
            reset_database_module, "get_db_connection", return_value=mock_conn
        ):
            result = reset_database_module.save_brand_dna(test_user_id, test_params)

        assert result is False
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()


class TestDatabaseHealth:
    """Tests for database health check."""

    def test_check_database_health_connected(self, reset_database_module):
        """Test health check when database is connected."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(
            reset_database_module, "get_db_connection", return_value=mock_conn
        ):
            result = reset_database_module.check_database_health()

        assert result["connected"] is True
        assert result["error"] is None
        mock_conn.close.assert_called_once()

    def test_check_database_health_disconnected(self, reset_database_module):
        """Test health check when database is not connected."""
        with patch.object(
            reset_database_module, "get_db_connection", return_value=None
        ):
            result = reset_database_module.check_database_health()

        assert result["connected"] is False
        assert result["error"] == "Failed to establish connection"
