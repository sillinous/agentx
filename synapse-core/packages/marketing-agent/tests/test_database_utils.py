import pytest
from unittest.mock import patch, MagicMock
import os
from database_utils import (
    get_db_connection,
    retrieve_brand_dna,
)


# Mock the DATABASE_URL environment variable for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://test_user:test_password@test_host:5432/test_db"},
    ):
        yield


@patch("database_utils.psycopg2.connect")
def test_get_db_connection_success(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    conn = get_db_connection()

    mock_connect.assert_called_once_with(os.environ["DATABASE_URL"])
    assert conn == mock_conn
    conn.close.assert_not_called()  # Connection should not be closed by get_db_connection


@patch("database_utils.psycopg2.connect")
def test_get_db_connection_failure(mock_connect):
    mock_connect.side_effect = Exception("Connection failed")

    conn = get_db_connection()

    mock_connect.assert_called_once_with(os.environ["DATABASE_URL"])
    assert conn is None


@patch("database_utils.psycopg2.connect")
def test_retrieve_brand_dna_found(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    test_brand_dna = {"voice": "witty", "colors": ["#00f0ff"]}
    mock_cursor.fetchone.return_value = {"parameters": test_brand_dna}

    result = retrieve_brand_dna(test_user_id)

    mock_connect.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "SELECT parameters FROM brand_dna WHERE user_id = %s::uuid", (test_user_id,)
    )
    assert result == test_brand_dna
    mock_conn.close.assert_called_once()


@patch("database_utils.psycopg2.connect")
def test_retrieve_brand_dna_not_found(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    mock_cursor.fetchone.return_value = None

    result = retrieve_brand_dna(test_user_id)

    mock_connect.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "SELECT parameters FROM brand_dna WHERE user_id = %s::uuid", (test_user_id,)
    )
    assert result == {}
    mock_conn.close.assert_called_once()


@patch("database_utils.psycopg2.connect")
def test_retrieve_brand_dna_db_error(mock_connect):
    mock_connect.side_effect = Exception("DB connection error")

    test_user_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

    result = retrieve_brand_dna(test_user_id)

    mock_connect.assert_called_once()
    assert result == {}
    # No connection to close if connect failed
    mock_connect.return_value.close.assert_not_called()
