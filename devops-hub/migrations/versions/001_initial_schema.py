"""Initial schema - baseline for DevOps Hub

Revision ID: 001
Revises: None
Create Date: 2026-01-12

This migration creates the initial database schema.
Supports both SQLite and PostgreSQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table already exists."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create initial schema."""

    # Agents table
    if not table_exists("agents"):
        op.create_table(
            "agents",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
            sa.Column("status", sa.String(50), nullable=False, server_default="production"),
            sa.Column("domain", sa.String(100), nullable=False, server_default="utility"),
            sa.Column("agent_type", sa.String(50), nullable=False, server_default="worker"),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("capabilities", sa.Text, nullable=False, server_default="[]"),
            sa.Column("protocols", sa.Text, nullable=False, server_default="[]"),
            sa.Column("implementations", sa.Text, nullable=False, server_default="{}"),
            sa.Column("documentation", sa.Text, nullable=True),
            sa.Column("performance", sa.Text, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(50), nullable=False),
            sa.Column("updated_at", sa.String(50), nullable=False),
        )

    # Workflows table
    if not table_exists("workflows"):
        op.create_table(
            "workflows",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
            sa.Column("steps", sa.Text, nullable=False, server_default="[]"),
            sa.Column("input_schema", sa.Text, nullable=False, server_default="{}"),
            sa.Column("output_schema", sa.Text, nullable=False, server_default="{}"),
            sa.Column("metadata", sa.Text, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(50), nullable=False),
            sa.Column("updated_at", sa.String(50), nullable=False),
        )

    # Workflow executions table
    if not table_exists("workflow_executions"):
        op.create_table(
            "workflow_executions",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("workflow_id", sa.String(255), nullable=False),
            sa.Column("workflow_name", sa.String(255), nullable=False),
            sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
            sa.Column("current_step", sa.Integer, nullable=False, server_default="0"),
            sa.Column("context", sa.Text, nullable=False, server_default="{}"),
            sa.Column("results", sa.Text, nullable=False, server_default="{}"),
            sa.Column("errors", sa.Text, nullable=False, server_default="[]"),
            sa.Column("started_at", sa.String(50), nullable=True),
            sa.Column("completed_at", sa.String(50), nullable=True),
            sa.Column("created_at", sa.String(50), nullable=False),
        )

    # Events table
    if not table_exists("events"):
        op.create_table(
            "events",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("type", sa.String(100), nullable=False),
            sa.Column("source", sa.String(255), nullable=False),
            sa.Column("data", sa.Text, nullable=False, server_default="{}"),
            sa.Column("correlation_id", sa.String(255), nullable=True),
            sa.Column("metadata", sa.Text, nullable=False, server_default="{}"),
            sa.Column("timestamp", sa.String(50), nullable=False),
        )
        # Create indexes
        op.create_index("idx_events_type", "events", ["type"])
        op.create_index("idx_events_source", "events", ["source"])
        op.create_index("idx_events_timestamp", "events", ["timestamp"])

    # API keys table
    if not table_exists("api_keys"):
        op.create_table(
            "api_keys",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("scopes", sa.Text, nullable=False, server_default='["read"]'),
            sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
            sa.Column("created_at", sa.String(50), nullable=False),
            sa.Column("last_used_at", sa.String(50), nullable=True),
            sa.Column("expires_at", sa.String(50), nullable=True),
        )
        op.create_index("idx_api_keys_hash", "api_keys", ["key_hash"])

    # Documentation guides table
    if not table_exists("documentation_guides"):
        op.create_table(
            "documentation_guides",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("slug", sa.String(255), nullable=False, unique=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("category", sa.String(100), nullable=False, server_default="general"),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
            sa.Column("parent_id", sa.String(255), nullable=True),
            sa.Column("metadata", sa.Text, nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(50), nullable=False),
            sa.Column("updated_at", sa.String(50), nullable=False),
            sa.ForeignKeyConstraint(["parent_id"], ["documentation_guides.id"]),
        )
        op.create_index("idx_docs_category", "documentation_guides", ["category"])
        op.create_index("idx_docs_slug", "documentation_guides", ["slug"])

    # Documentation examples table
    if not table_exists("documentation_examples"):
        op.create_table(
            "documentation_examples",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("category", sa.String(100), nullable=False, server_default="general"),
            sa.Column("agent_ids", sa.Text, nullable=False, server_default="[]"),
            sa.Column("workflow_id", sa.String(255), nullable=True),
            sa.Column("code_snippet", sa.Text, nullable=True),
            sa.Column("input_example", sa.Text, nullable=False, server_default="{}"),
            sa.Column("expected_output", sa.Text, nullable=True),
            sa.Column("tags", sa.Text, nullable=False, server_default="[]"),
            sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
            sa.Column("created_at", sa.String(50), nullable=False),
            sa.Column("updated_at", sa.String(50), nullable=False),
        )
        op.create_index("idx_examples_category", "documentation_examples", ["category"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("documentation_examples")
    op.drop_table("documentation_guides")
    op.drop_table("api_keys")
    op.drop_table("events")
    op.drop_table("workflow_executions")
    op.drop_table("workflows")
    op.drop_table("agents")
