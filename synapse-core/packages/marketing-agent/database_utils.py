"""
Database Utilities for Synapse Core
Handles PostgreSQL connections, queries, and health checks.
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://synapse:synapse@localhost:5432/synapse_core",
)


class DatabaseConnection:
    """Manages database connections for Synapse Core."""

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or DATABASE_URL
        self._connection = None

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            import psycopg2

            conn = psycopg2.connect(self.connection_string)
            yield conn
            conn.commit()
        except ImportError:
            logger.warning("psycopg2 not installed, using mock connection")
            yield MockConnection()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and not isinstance(conn, MockConnection):
                conn.close()


class MockConnection:
    """Mock connection for development without PostgreSQL."""

    def cursor(self):
        return MockCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class MockCursor:
    """Mock cursor for development."""

    def execute(self, query: str, params: tuple = None):
        logger.debug(f"Mock execute: {query[:50]}...")

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def close(self):
        pass


# Global database instance
db = DatabaseConnection()


def check_database_health() -> dict:
    """
    Check database connectivity and health.

    Returns:
        Dict with health status information
    """
    try:
        import psycopg2  # noqa: F401 - needed for ImportError check
        from time import time

        start = time()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()

        latency = round((time() - start) * 1000, 2)

        return {
            "connected": True,
            "latency_ms": latency,
            "database": "postgresql",
        }
    except ImportError:
        return {
            "connected": False,
            "error": "psycopg2 not installed",
            "database": "none",
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "database": "postgresql",
        }


# --- Brand DNA Operations ---
def get_brand_dna(user_id: str) -> Optional[dict]:
    """
    Retrieve brand DNA for a user.

    Args:
        user_id: The user's unique identifier

    Returns:
        Brand DNA dictionary or None
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT voice_tone, visual_style, keywords, avoid_phrases, brand_values
                FROM brand_dna
                WHERE user_id = %s
                """,
                (user_id,),
            )
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "voice_tone": result[0],
                    "visual_style": result[1],
                    "keywords": result[2],
                    "avoid_phrases": result[3],
                    "brand_values": result[4],
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching brand DNA: {e}")
        return None


def save_brand_dna(user_id: str, brand_dna: dict) -> bool:
    """
    Save or update brand DNA for a user.

    Args:
        user_id: The user's unique identifier
        brand_dna: Brand DNA dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO brand_dna
                    (user_id, voice_tone, visual_style, keywords,
                     avoid_phrases, brand_values)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    voice_tone = EXCLUDED.voice_tone,
                    visual_style = EXCLUDED.visual_style,
                    keywords = EXCLUDED.keywords,
                    avoid_phrases = EXCLUDED.avoid_phrases,
                    brand_values = EXCLUDED.brand_values,
                    updated_at = NOW()
                """,
                (
                    user_id,
                    brand_dna.get("voice_tone"),
                    brand_dna.get("visual_style"),
                    brand_dna.get("keywords"),
                    brand_dna.get("avoid_phrases"),
                    brand_dna.get("brand_values"),
                ),
            )
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"Error saving brand DNA: {e}")
        return False


# --- Context Lake Operations ---
def store_context(user_id: str, context_type: str, content: dict, embedding: list = None) -> bool:
    """
    Store context in the context lake for semantic memory.

    Args:
        user_id: The user's unique identifier
        context_type: Type of context (e.g., 'conversation', 'content', 'feedback')
        content: Context content as dictionary
        embedding: Optional vector embedding

    Returns:
        True if successful, False otherwise
    """
    try:
        import json

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO context_lake (user_id, context_type, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, context_type, json.dumps(content), embedding),
            )
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"Error storing context: {e}")
        return False


def search_context(user_id: str, query_embedding: list, limit: int = 5) -> list[dict]:
    """
    Search context lake using vector similarity.

    Args:
        user_id: The user's unique identifier
        query_embedding: Query vector for similarity search
        limit: Maximum number of results

    Returns:
        List of matching context entries
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT content, context_type, created_at,
                       1 - (embedding <=> %s::vector) as similarity
                FROM context_lake
                WHERE user_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (query_embedding, user_id, query_embedding, limit),
            )
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "content": row[0],
                    "context_type": row[1],
                    "created_at": row[2],
                    "similarity": row[3],
                }
                for row in results
            ]
    except Exception as e:
        logger.error(f"Error searching context: {e}")
        return []


# --- Audit Log Operations ---
def log_audit_event(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str = None,
    details: dict = None,
) -> bool:
    """
    Log an audit event for compliance and debugging.

    Args:
        user_id: The user's unique identifier
        action: The action performed
        resource_type: Type of resource affected
        resource_id: Optional resource identifier
        details: Optional additional details

    Returns:
        True if successful, False otherwise
    """
    try:
        import json

        with db.get_connection() as conn:
            cursor = conn.cursor()
            details_json = json.dumps(details) if details else None
            cursor.execute(
                """
                INSERT INTO audit_log
                    (user_id, action, resource_type, resource_id, details)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, action, resource_type, resource_id, details_json),
            )
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"Error logging audit event: {e}")
        return False
