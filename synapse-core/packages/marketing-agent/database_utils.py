"""
Database utilities for Synapse Core.
Supports PostgreSQL (production) with SQLite fallback (testing).
"""

import os
import json
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None and DATABASE_URL.startswith("postgresql")

# SQLite fallback for testing
SQLITE_DATABASE_FILE = os.getenv("SQLITE_DATABASE_FILE", "synapse_test.db")


def _get_postgres_connection():
    """
    Establishes a connection to PostgreSQL database.
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except ImportError:
        logger.warning("psycopg2 not installed, falling back to SQLite")
        return None
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return None


def _get_sqlite_connection():
    """
    Establishes a connection to SQLite database (for testing).
    """
    try:
        import sqlite3

        conn = sqlite3.connect(SQLITE_DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error connecting to SQLite database: {e}")
        return None


def get_db_connection():
    """
    Establishes a database connection.
    Uses PostgreSQL if DATABASE_URL is set, otherwise SQLite.
    """
    if USE_POSTGRES:
        conn = _get_postgres_connection()
        if conn:
            return conn

    # Fallback to SQLite
    return _get_sqlite_connection()


@contextmanager
def db_connection():
    """
    Context manager for database connections.
    Ensures proper cleanup.
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        if conn:
            conn.close()


def retrieve_brand_dna(user_id: str) -> dict:
    """
    Retrieves the brand_dna parameters for a given user from the database.

    Args:
        user_id: The UUID of the user

    Returns:
        Dictionary containing brand DNA parameters, or empty dict if not found
    """
    with db_connection() as conn:
        if conn is None:
            logger.warning("No database connection available")
            return _get_default_brand_dna()

        try:
            cursor = conn.cursor()

            if USE_POSTGRES:
                # PostgreSQL uses $1 placeholders and returns jsonb directly
                cursor.execute(
                    "SELECT parameters FROM brand_dna WHERE user_id = %s", (user_id,)
                )
            else:
                # SQLite uses ? placeholders and stores JSON as TEXT
                cursor.execute(
                    "SELECT parameters FROM brand_dna WHERE user_id = ?", (user_id,)
                )

            result = cursor.fetchone()

            if result:
                parameters = result["parameters"] if USE_POSTGRES else result[0]
                if isinstance(parameters, str):
                    return json.loads(parameters)
                return parameters if parameters else {}
            else:
                logger.info(f"No brand_dna found for user_id: {user_id}")
                return _get_default_brand_dna()

        except Exception as e:
            logger.error(f"Error retrieving brand DNA: {e}")
            return _get_default_brand_dna()


def _get_default_brand_dna() -> dict:
    """
    Returns default brand DNA parameters when none found in database.
    """
    return {
        "voice": "professional",
        "tone": "friendly",
        "industry": "general",
        "target_audience": "general audience",
        "key_values": ["quality", "innovation", "reliability"],
    }


def save_brand_dna(user_id: str, parameters: dict) -> bool:
    """
    Saves or updates brand DNA parameters for a user.

    Args:
        user_id: The UUID of the user
        parameters: Dictionary of brand DNA parameters

    Returns:
        True if saved successfully, False otherwise
    """
    with db_connection() as conn:
        if conn is None:
            logger.error("No database connection available")
            return False

        try:
            cursor = conn.cursor()

            if USE_POSTGRES:
                # Upsert for PostgreSQL
                cursor.execute(
                    """
                    INSERT INTO brand_dna (user_id, parameters, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        parameters = EXCLUDED.parameters,
                        updated_at = NOW()
                    """,
                    (user_id, json.dumps(parameters)),
                )
            else:
                # SQLite upsert
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO brand_dna (user_id, parameters, updated_at)
                    VALUES (?, ?, datetime('now'))
                    """,
                    (user_id, json.dumps(parameters)),
                )

            conn.commit()
            logger.info(f"Brand DNA saved for user_id: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving brand DNA: {e}")
            conn.rollback()
            return False


def check_database_health() -> dict:
    """
    Checks database connectivity and returns health status.
    """
    status = {
        "connected": False,
        "database_type": "postgresql" if USE_POSTGRES else "sqlite",
        "error": None,
    }

    with db_connection() as conn:
        if conn is None:
            status["error"] = "Failed to establish connection"
            return status

        try:
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute("SELECT 1")
            else:
                cursor.execute("SELECT 1")
            status["connected"] = True
        except Exception as e:
            status["error"] = str(e)

    return status
