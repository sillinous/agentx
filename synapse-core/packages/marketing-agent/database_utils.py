"""
Database Utilities for Synapse Core
Handles PostgreSQL connections, queries, and health checks.
"""

import os
import json
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
def store_context(
    user_id: str, context_type: str, content: dict, embedding: list = None
) -> bool:
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


# --- User Operations ---
def get_user_by_email(email: str) -> Optional[dict]:
    """
    Retrieve user information by email.

    Args:
        email: The user's email address

    Returns:
        User dictionary or None
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, name, subscription_tier, created_at
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "id": str(result[0]),
                    "email": result[1],
                    "name": result[2],
                    "subscription_tier": result[3],
                    "created_at": result[4].isoformat() if result[4] else None,
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Retrieve user information by ID.

    Args:
        user_id: The user's unique identifier

    Returns:
        User dictionary or None
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, name, subscription_tier, created_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "id": str(result[0]),
                    "email": result[1],
                    "name": result[2],
                    "subscription_tier": result[3],
                    "created_at": result[4].isoformat() if result[4] else None,
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None


# --- Conversation Operations ---
def save_conversation(
    user_id: str,
    thread_id: str,
    agent_type: str,
    messages: list,
) -> bool:
    """
    Save or update a conversation thread.

    Args:
        user_id: The user's unique identifier
        thread_id: The conversation thread ID
        agent_type: Type of agent (scribe, architect, sentry)
        messages: List of messages in the conversation

    Returns:
        True if successful, False otherwise
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (user_id, thread_id, agent_type, messages)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, thread_id) DO UPDATE SET
                    messages = %s,
                    updated_at = NOW()
                """,
                (
                    user_id,
                    thread_id,
                    agent_type,
                    json.dumps(messages),
                    json.dumps(messages),
                ),
            )
            cursor.close()
            return True
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        return False


def get_conversation(user_id: str, thread_id: str) -> Optional[dict]:
    """
    Retrieve a conversation by thread ID.

    Args:
        user_id: The user's unique identifier
        thread_id: The conversation thread ID

    Returns:
        Conversation dictionary or None
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, agent_type, messages, created_at, updated_at
                FROM conversations
                WHERE user_id = %s AND thread_id = %s
                """,
                (user_id, thread_id),
            )
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "id": str(result[0]),
                    "thread_id": thread_id,
                    "agent_type": result[1],
                    "messages": (
                        result[2]
                        if isinstance(result[2], list)
                        else json.loads(result[2] or "[]")
                    ),
                    "created_at": result[3].isoformat() if result[3] else None,
                    "updated_at": result[4].isoformat() if result[4] else None,
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        return None


def get_user_conversations(
    user_id: str, agent_type: str = None, limit: int = 20
) -> list[dict]:
    """
    Retrieve recent conversations for a user.

    Args:
        user_id: The user's unique identifier
        agent_type: Optional filter by agent type
        limit: Maximum number of conversations to return

    Returns:
        List of conversation dictionaries
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if agent_type:
                cursor.execute(
                    """
                    SELECT id, thread_id, agent_type, messages, created_at, updated_at
                    FROM conversations
                    WHERE user_id = %s AND agent_type = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (user_id, agent_type, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, thread_id, agent_type, messages, created_at, updated_at
                    FROM conversations
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit),
                )
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": str(row[0]),
                    "thread_id": row[1],
                    "agent_type": row[2],
                    "messages": (
                        row[3]
                        if isinstance(row[3], list)
                        else json.loads(row[3] or "[]")
                    ),
                    "created_at": row[4].isoformat() if row[4] else None,
                    "updated_at": row[5].isoformat() if row[5] else None,
                }
                for row in results
            ]
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        return []


# --- Generated Content Operations ---
def save_generated_content(
    user_id: str,
    content_type: str,
    content: str,
    metadata: dict = None,
    agent_type: str = None,
    embedding: list = None,
) -> Optional[str]:
    """
    Save generated content to the database.

    Args:
        user_id: The user's unique identifier
        content_type: Type of content (blog_post, social_media, component, etc.)
        content: The generated content
        metadata: Optional metadata dictionary
        agent_type: Optional agent type that generated the content
        embedding: Optional vector embedding

    Returns:
        Content ID if successful, None otherwise
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Get agent_id if agent_type provided
            agent_id = None
            if agent_type:
                cursor.execute(
                    "SELECT id FROM agents WHERE type = %s LIMIT 1",
                    (agent_type,),
                )
                agent_result = cursor.fetchone()
                if agent_result:
                    agent_id = agent_result[0]

            cursor.execute(
                """
                INSERT INTO generated_content
                    (user_id, agent_id, content_type, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user_id,
                    agent_id,
                    content_type,
                    content,
                    json.dumps(metadata) if metadata else None,
                    embedding,
                ),
            )
            result = cursor.fetchone()
            cursor.close()

            return str(result[0]) if result else None
    except Exception as e:
        logger.error(f"Error saving generated content: {e}")
        return None


def get_generated_content(content_id: str) -> Optional[dict]:
    """
    Retrieve generated content by ID.

    Args:
        content_id: The content's unique identifier

    Returns:
        Content dictionary or None
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT gc.id, gc.user_id, gc.content_type, gc.content,
                       gc.metadata, gc.created_at, a.type as agent_type
                FROM generated_content gc
                LEFT JOIN agents a ON gc.agent_id = a.id
                WHERE gc.id = %s
                """,
                (content_id,),
            )
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "id": str(result[0]),
                    "user_id": str(result[1]),
                    "content_type": result[2],
                    "content": result[3],
                    "metadata": (
                        result[4]
                        if isinstance(result[4], dict)
                        else json.loads(result[4] or "{}")
                    ),
                    "created_at": result[5].isoformat() if result[5] else None,
                    "agent_type": result[6],
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching content: {e}")
        return None


def get_user_content(
    user_id: str,
    content_type: str = None,
    limit: int = 20,
) -> list[dict]:
    """
    Retrieve recent generated content for a user.

    Args:
        user_id: The user's unique identifier
        content_type: Optional filter by content type
        limit: Maximum number of items to return

    Returns:
        List of content dictionaries
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if content_type:
                cursor.execute(
                    """
                    SELECT gc.id, gc.content_type, gc.content, gc.metadata,
                           gc.created_at, a.type as agent_type
                    FROM generated_content gc
                    LEFT JOIN agents a ON gc.agent_id = a.id
                    WHERE gc.user_id = %s AND gc.content_type = %s
                    ORDER BY gc.created_at DESC
                    LIMIT %s
                    """,
                    (user_id, content_type, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT gc.id, gc.content_type, gc.content, gc.metadata,
                           gc.created_at, a.type as agent_type
                    FROM generated_content gc
                    LEFT JOIN agents a ON gc.agent_id = a.id
                    WHERE gc.user_id = %s
                    ORDER BY gc.created_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit),
                )
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": str(row[0]),
                    "content_type": row[1],
                    "content": row[2],
                    "metadata": (
                        row[3]
                        if isinstance(row[3], dict)
                        else json.loads(row[3] or "{}")
                    ),
                    "created_at": row[4].isoformat() if row[4] else None,
                    "agent_type": row[5],
                }
                for row in results
            ]
    except Exception as e:
        logger.error(f"Error fetching user content: {e}")
        return []


def search_similar_content(
    user_id: str,
    query_embedding: list,
    content_type: str = None,
    limit: int = 5,
) -> list[dict]:
    """
    Search for similar content using vector similarity.

    Args:
        user_id: The user's unique identifier
        query_embedding: Query vector for similarity search
        content_type: Optional filter by content type
        limit: Maximum number of results

    Returns:
        List of similar content entries with similarity scores
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if content_type:
                cursor.execute(
                    """
                    SELECT gc.id, gc.content_type, gc.content, gc.metadata,
                           1 - (gc.embedding <=> %s::vector) as similarity
                    FROM generated_content gc
                    WHERE gc.user_id = %s AND gc.content_type = %s
                        AND gc.embedding IS NOT NULL
                    ORDER BY gc.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding, user_id, content_type, query_embedding, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT gc.id, gc.content_type, gc.content, gc.metadata,
                           1 - (gc.embedding <=> %s::vector) as similarity
                    FROM generated_content gc
                    WHERE gc.user_id = %s AND gc.embedding IS NOT NULL
                    ORDER BY gc.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding, user_id, query_embedding, limit),
                )
            results = cursor.fetchall()
            cursor.close()

            return [
                {
                    "id": str(row[0]),
                    "content_type": row[1],
                    "content": row[2],
                    "metadata": (
                        row[3]
                        if isinstance(row[3], dict)
                        else json.loads(row[3] or "{}")
                    ),
                    "similarity": row[4],
                }
                for row in results
            ]
    except Exception as e:
        logger.error(f"Error searching similar content: {e}")
        return []


# --- Embedding Generation ---
def generate_embedding(text: str) -> Optional[list]:
    """
    Generate an embedding vector for text using OpenAI.

    Args:
        text: The text to embed

    Returns:
        Embedding vector as a list of floats, or None on error
    """
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, cannot generate embeddings")
            return None

        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],  # Truncate to model limit
        )
        return response.data[0].embedding
    except ImportError:
        logger.warning("openai package not installed")
        return None
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


# --- Agent Configuration ---
def get_agent_config(agent_type: str) -> Optional[dict]:
    """
    Retrieve agent configuration from the database.

    Args:
        agent_type: Type of agent (marketing, builder, analytics)

    Returns:
        Agent configuration dictionary or None
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, description, config, is_active
                FROM agents
                WHERE type = %s AND is_active = true
                """,
                (agent_type,),
            )
            result = cursor.fetchone()
            cursor.close()

            if result:
                return {
                    "id": str(result[0]),
                    "name": result[1],
                    "description": result[2],
                    "config": (
                        result[3]
                        if isinstance(result[3], dict)
                        else json.loads(result[3] or "{}")
                    ),
                    "is_active": result[4],
                }
            return None
    except Exception as e:
        logger.error(f"Error fetching agent config: {e}")
        return None
