"""
Database layer for DevOps Hub - SQLite persistence.

Provides persistent storage for:
- Agent registry metadata
- Workflow definitions and executions
- Event history
- API keys for authentication
"""

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import threading
import logging

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "devops_hub.db"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: Path = DEFAULT_DB_PATH
    echo: bool = False


class Database:
    """
    SQLite database manager with connection pooling.

    Thread-safe implementation using thread-local connections.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._local = threading.local()
        self._ensure_directory()
        self._init_schema()

    def _ensure_directory(self):
        """Ensure the database directory exists."""
        self.config.path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.config.path),
                check_same_thread=False,
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    @contextmanager
    def connection(self):
        """Context manager for database connections."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    @contextmanager
    def cursor(self):
        """Context manager for database cursors."""
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def _init_schema(self):
        """Initialize database schema."""
        with self.cursor() as cur:
            # Agents table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    status TEXT NOT NULL DEFAULT 'production',
                    domain TEXT NOT NULL DEFAULT 'utility',
                    agent_type TEXT NOT NULL DEFAULT 'worker',
                    description TEXT,
                    capabilities TEXT NOT NULL DEFAULT '[]',
                    protocols TEXT NOT NULL DEFAULT '[]',
                    implementations TEXT NOT NULL DEFAULT '{}',
                    documentation TEXT,
                    performance TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Workflows table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    steps TEXT NOT NULL DEFAULT '[]',
                    input_schema TEXT NOT NULL DEFAULT '{}',
                    output_schema TEXT NOT NULL DEFAULT '{}',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Workflow executions table (no FK constraint for flexibility with dynamic workflows)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    current_step INTEGER NOT NULL DEFAULT 0,
                    context TEXT NOT NULL DEFAULT '{}',
                    results TEXT NOT NULL DEFAULT '{}',
                    errors TEXT NOT NULL DEFAULT '[]',
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Events table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    data TEXT NOT NULL DEFAULT '{}',
                    correlation_id TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    timestamp TEXT NOT NULL
                )
            """)

            # Create index for event queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)
            """)

            # API keys table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    scopes TEXT NOT NULL DEFAULT '["read"]',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    expires_at TEXT
                )
            """)

            # Create index for API key lookup
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)
            """)

            # Documentation guides table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documentation_guides (
                    id TEXT PRIMARY KEY,
                    slug TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    content TEXT NOT NULL,
                    order_index INTEGER NOT NULL DEFAULT 0,
                    parent_id TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (parent_id) REFERENCES documentation_guides(id)
                )
            """)

            # Documentation examples table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documentation_examples (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL DEFAULT 'general',
                    agent_ids TEXT NOT NULL DEFAULT '[]',
                    workflow_id TEXT,
                    code_snippet TEXT,
                    input_example TEXT NOT NULL DEFAULT '{}',
                    expected_output TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    order_index INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create indexes for documentation
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_category ON documentation_guides(category)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_slug ON documentation_guides(slug)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_examples_category ON documentation_examples(category)
            """)

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query."""
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
        with self.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        with self.cursor() as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# Repository classes for each entity

class AgentRepository:
    """Repository for agent data."""

    def __init__(self, db: Database):
        self.db = db

    def save(self, agent: Dict[str, Any]) -> str:
        """Save or update an agent."""
        now = datetime.utcnow().isoformat()
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO agents (id, name, version, status, domain, agent_type,
                    description, capabilities, protocols, implementations,
                    documentation, performance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name, version=excluded.version,
                    status=excluded.status, domain=excluded.domain,
                    agent_type=excluded.agent_type, description=excluded.description,
                    capabilities=excluded.capabilities, protocols=excluded.protocols,
                    implementations=excluded.implementations, documentation=excluded.documentation,
                    performance=excluded.performance, updated_at=excluded.updated_at
            """, (
                agent["id"],
                agent["name"],
                agent.get("version", "1.0.0"),
                agent.get("status", "production"),
                agent.get("domain", "utility"),
                agent.get("type", "worker"),
                agent.get("description", ""),
                json.dumps(agent.get("capabilities", [])),
                json.dumps(agent.get("protocols", [])),
                json.dumps(agent.get("implementations", {})),
                agent.get("documentation", ""),
                json.dumps(agent.get("performance", {})),
                agent.get("created_at", now),
                now,
            ))
        return agent["id"]

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM agents WHERE id = ?",
            (agent_id,)
        )
        return self._row_to_dict(row) if row else None

    def list_all(self) -> List[Dict[str, Any]]:
        """List all agents."""
        rows = self.db.fetch_all("SELECT * FROM agents ORDER BY name")
        return [self._row_to_dict(row) for row in rows]

    def find(
        self,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        capability: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find agents matching criteria."""
        query = "SELECT * FROM agents WHERE 1=1"
        params = []

        if domain:
            query += " AND domain = ?"
            params.append(domain)
        if status:
            query += " AND status = ?"
            params.append(status)
        if agent_type:
            query += " AND agent_type = ?"
            params.append(agent_type)
        if capability:
            query += " AND capabilities LIKE ?"
            params.append(f'%"{capability}"%')

        rows = self.db.fetch_all(query, tuple(params))
        return [self._row_to_dict(row) for row in rows]

    def delete(self, agent_id: str) -> bool:
        """Delete an agent."""
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            return cur.rowcount > 0

    def count(self) -> int:
        """Count total agents."""
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM agents")
        return row["count"] if row else 0

    def _row_to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "name": row["name"],
            "version": row["version"],
            "status": row["status"],
            "domain": row["domain"],
            "type": row["agent_type"],
            "description": row["description"],
            "capabilities": json.loads(row["capabilities"]),
            "protocols": json.loads(row["protocols"]),
            "implementations": json.loads(row["implementations"]),
            "documentation": row["documentation"],
            "performance": json.loads(row["performance"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


class WorkflowRepository:
    """Repository for workflow data."""

    def __init__(self, db: Database):
        self.db = db

    def save(self, workflow: Dict[str, Any]) -> str:
        """Save or update a workflow."""
        now = datetime.utcnow().isoformat()
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO workflows (id, name, description, version, steps,
                    input_schema, output_schema, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name, description=excluded.description,
                    version=excluded.version, steps=excluded.steps,
                    input_schema=excluded.input_schema, output_schema=excluded.output_schema,
                    metadata=excluded.metadata, updated_at=excluded.updated_at
            """, (
                workflow["id"],
                workflow["name"],
                workflow.get("description", ""),
                workflow.get("version", "1.0.0"),
                json.dumps(workflow.get("steps", [])),
                json.dumps(workflow.get("input_schema", {})),
                json.dumps(workflow.get("output_schema", {})),
                json.dumps(workflow.get("metadata", {})),
                workflow.get("created_at", now),
                now,
            ))
        return workflow["id"]

    def get(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM workflows WHERE id = ?",
            (workflow_id,)
        )
        return self._row_to_dict(row) if row else None

    def list_all(self) -> List[Dict[str, Any]]:
        """List all workflows."""
        rows = self.db.fetch_all("SELECT * FROM workflows ORDER BY name")
        return [self._row_to_dict(row) for row in rows]

    def delete(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
            return cur.rowcount > 0

    def _row_to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "version": row["version"],
            "steps": json.loads(row["steps"]),
            "input_schema": json.loads(row["input_schema"]),
            "output_schema": json.loads(row["output_schema"]),
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


class ExecutionRepository:
    """Repository for workflow execution data."""

    def __init__(self, db: Database):
        self.db = db

    def save(self, execution: Dict[str, Any]) -> str:
        """Save or update an execution."""
        now = datetime.utcnow().isoformat()
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO workflow_executions (id, workflow_id, workflow_name,
                    status, current_step, context, results, errors,
                    started_at, completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status, current_step=excluded.current_step,
                    context=excluded.context, results=excluded.results,
                    errors=excluded.errors, started_at=excluded.started_at,
                    completed_at=excluded.completed_at
            """, (
                execution["id"],
                execution["workflow_id"],
                execution["workflow_name"],
                execution.get("status", "pending"),
                execution.get("current_step", 0),
                json.dumps(execution.get("context", {})),
                json.dumps(execution.get("results", {})),
                json.dumps(execution.get("errors", [])),
                execution.get("started_at"),
                execution.get("completed_at"),
                execution.get("created_at", now),
            ))
        return execution["id"]

    def get(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get an execution by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM workflow_executions WHERE id = ?",
            (execution_id,)
        )
        return self._row_to_dict(row) if row else None

    def find(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Find executions matching criteria."""
        query = "SELECT * FROM workflow_executions WHERE 1=1"
        params = []

        if workflow_id:
            query += " AND workflow_id = ?"
            params.append(workflow_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = self.db.fetch_all(query, tuple(params))
        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "workflow_name": row["workflow_name"],
            "status": row["status"],
            "current_step": row["current_step"],
            "context": json.loads(row["context"]),
            "results": json.loads(row["results"]),
            "errors": json.loads(row["errors"]),
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "created_at": row["created_at"],
        }


class EventRepository:
    """Repository for event data."""

    def __init__(self, db: Database, max_events: int = 10000):
        self.db = db
        self.max_events = max_events

    def save(self, event: Dict[str, Any]) -> str:
        """Save an event."""
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO events (id, type, source, data, correlation_id, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event["id"],
                event["type"],
                event["source"],
                json.dumps(event.get("data", {})),
                event.get("correlation_id"),
                json.dumps(event.get("metadata", {})),
                event["timestamp"],
            ))

            # Cleanup old events if needed
            cur.execute("""
                DELETE FROM events WHERE id IN (
                    SELECT id FROM events ORDER BY timestamp DESC LIMIT -1 OFFSET ?
                )
            """, (self.max_events,))

        return event["id"]

    def find(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Find events matching criteria."""
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if event_type:
            query += " AND type = ?"
            params.append(event_type)
        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self.db.fetch_all(query, tuple(params))
        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "type": row["type"],
            "source": row["source"],
            "data": json.loads(row["data"]),
            "correlation_id": row["correlation_id"],
            "metadata": json.loads(row["metadata"]),
            "timestamp": row["timestamp"],
        }


# Global database instance
_db: Optional[Database] = None


def get_database(config: Optional[DatabaseConfig] = None) -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database(config)
    return _db


def get_agent_repository() -> AgentRepository:
    """Get an agent repository."""
    return AgentRepository(get_database())


def get_workflow_repository() -> WorkflowRepository:
    """Get a workflow repository."""
    return WorkflowRepository(get_database())


def get_execution_repository() -> ExecutionRepository:
    """Get an execution repository."""
    return ExecutionRepository(get_database())


def get_event_repository() -> EventRepository:
    """Get an event repository."""
    return EventRepository(get_database())


class DocumentationRepository:
    """Repository for documentation guides."""

    def __init__(self, db: Database):
        self.db = db

    def save(self, guide: Dict[str, Any]) -> str:
        """Save or update a documentation guide."""
        now = datetime.utcnow().isoformat()
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO documentation_guides (id, slug, title, category, content,
                    order_index, parent_id, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    slug=excluded.slug, title=excluded.title, category=excluded.category,
                    content=excluded.content, order_index=excluded.order_index,
                    parent_id=excluded.parent_id, metadata=excluded.metadata,
                    updated_at=excluded.updated_at
            """, (
                guide["id"],
                guide["slug"],
                guide["title"],
                guide.get("category", "general"),
                guide["content"],
                guide.get("order_index", 0),
                guide.get("parent_id"),
                json.dumps(guide.get("metadata", {})),
                guide.get("created_at", now),
                now,
            ))
        return guide["id"]

    def get(self, guide_id: str) -> Optional[Dict[str, Any]]:
        """Get a guide by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM documentation_guides WHERE id = ?",
            (guide_id,)
        )
        return self._row_to_dict(row) if row else None

    def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a guide by slug."""
        row = self.db.fetch_one(
            "SELECT * FROM documentation_guides WHERE slug = ?",
            (slug,)
        )
        return self._row_to_dict(row) if row else None

    def list_all(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all guides, optionally filtered by category."""
        if category:
            rows = self.db.fetch_all(
                "SELECT * FROM documentation_guides WHERE category = ? ORDER BY order_index, title",
                (category,)
            )
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM documentation_guides ORDER BY category, order_index, title"
            )
        return [self._row_to_dict(row) for row in rows]

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        rows = self.db.fetch_all(
            "SELECT DISTINCT category FROM documentation_guides ORDER BY category"
        )
        return [row["category"] for row in rows]

    def get_table_of_contents(self) -> List[Dict[str, Any]]:
        """Get hierarchical table of contents."""
        rows = self.db.fetch_all("""
            SELECT id, slug, title, category, order_index, parent_id
            FROM documentation_guides
            ORDER BY category, order_index, title
        """)
        return [dict(row) for row in rows]

    def delete(self, guide_id: str) -> bool:
        """Delete a guide."""
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM documentation_guides WHERE id = ?", (guide_id,))
            return cur.rowcount > 0

    def _row_to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "slug": row["slug"],
            "title": row["title"],
            "category": row["category"],
            "content": row["content"],
            "order_index": row["order_index"],
            "parent_id": row["parent_id"],
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


class ExampleRepository:
    """Repository for documentation examples."""

    def __init__(self, db: Database):
        self.db = db

    def save(self, example: Dict[str, Any]) -> str:
        """Save or update an example."""
        now = datetime.utcnow().isoformat()
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO documentation_examples (id, title, description, category,
                    agent_ids, workflow_id, code_snippet, input_example, expected_output,
                    tags, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, description=excluded.description,
                    category=excluded.category, agent_ids=excluded.agent_ids,
                    workflow_id=excluded.workflow_id, code_snippet=excluded.code_snippet,
                    input_example=excluded.input_example, expected_output=excluded.expected_output,
                    tags=excluded.tags, order_index=excluded.order_index,
                    updated_at=excluded.updated_at
            """, (
                example["id"],
                example["title"],
                example.get("description", ""),
                example.get("category", "general"),
                json.dumps(example.get("agent_ids", [])),
                example.get("workflow_id"),
                example.get("code_snippet", ""),
                json.dumps(example.get("input_example", {})),
                example.get("expected_output", ""),
                json.dumps(example.get("tags", [])),
                example.get("order_index", 0),
                example.get("created_at", now),
                now,
            ))
        return example["id"]

    def get(self, example_id: str) -> Optional[Dict[str, Any]]:
        """Get an example by ID."""
        row = self.db.fetch_one(
            "SELECT * FROM documentation_examples WHERE id = ?",
            (example_id,)
        )
        return self._row_to_dict(row) if row else None

    def list_all(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all examples, optionally filtered by category."""
        if category:
            rows = self.db.fetch_all(
                "SELECT * FROM documentation_examples WHERE category = ? ORDER BY order_index, title",
                (category,)
            )
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM documentation_examples ORDER BY category, order_index, title"
            )
        return [self._row_to_dict(row) for row in rows]

    def find_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Find examples that use a specific agent."""
        rows = self.db.fetch_all(
            "SELECT * FROM documentation_examples WHERE agent_ids LIKE ? ORDER BY order_index",
            (f'%"{agent_id}"%',)
        )
        return [self._row_to_dict(row) for row in rows]

    def find_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Find examples with a specific tag."""
        rows = self.db.fetch_all(
            "SELECT * FROM documentation_examples WHERE tags LIKE ? ORDER BY order_index",
            (f'%"{tag}"%',)
        )
        return [self._row_to_dict(row) for row in rows]

    def delete(self, example_id: str) -> bool:
        """Delete an example."""
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM documentation_examples WHERE id = ?", (example_id,))
            return cur.rowcount > 0

    def _row_to_dict(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "category": row["category"],
            "agent_ids": json.loads(row["agent_ids"]),
            "workflow_id": row["workflow_id"],
            "code_snippet": row["code_snippet"],
            "input_example": json.loads(row["input_example"]),
            "expected_output": row["expected_output"],
            "tags": json.loads(row["tags"]),
            "order_index": row["order_index"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def get_documentation_repository() -> DocumentationRepository:
    """Get a documentation repository."""
    return DocumentationRepository(get_database())


def get_example_repository() -> ExampleRepository:
    """Get an example repository."""
    return ExampleRepository(get_database())
