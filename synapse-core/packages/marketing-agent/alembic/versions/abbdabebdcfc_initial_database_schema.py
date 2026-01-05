"""Initial database schema

Revision ID: abbdabebdcfc
Revises:
Create Date: 2025-12-28 20:12:44.402542

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "abbdabebdcfc"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("create extension if not exists vector;")

    op.execute(
        """
        create table users (
          id uuid primary key default uuid_generate_v4(),
          email text unique not null,
          full_name text,
          subscription_tier text default 'standard',
          created_at timestamp with time zone default now()
        );
    """
    )

    op.execute(
        """
        create table brand_dna (
          id uuid primary key default uuid_generate_v4(),
          user_id uuid references users(id) on delete cascade,
          parameters jsonb not null,
          updated_at timestamp with time zone default now()
        );
    """
    )

    op.execute(
        """
        create table agents (
          id uuid primary key default uuid_generate_v4(),
          system_key text not null,
          name text not null,
          capabilities jsonb,
          user_id uuid references users(id) on delete cascade,
          is_active boolean default true
        );
    """
    )

    op.execute(
        """
        create table context_lake (
          id uuid primary key default uuid_generate_v4(),
          user_id uuid references users(id) on delete cascade,
          agent_id uuid references agents(id),
          content text not null,
          metadata jsonb,
          embedding vector(1536),
          created_at timestamp with time zone default now()
        );
    """
    )

    op.execute(
        """
        create table task_queue (
          id uuid primary key default uuid_generate_v4(),
          user_id uuid references users(id),
          assigned_agent_id uuid references agents(id),
          task_type text not null,
          status text default 'PENDING',
          payload jsonb,
          result jsonb,
          confidence_score float,
          created_at timestamp with time zone default now()
        );
    """
    )

    op.execute(
        """
        create table audit_log (
          id uuid primary key default uuid_generate_v4(),
          user_id uuid references users(id),
          action text not null,
          details jsonb,
          timestamp timestamp with time zone default now()
        );
    """
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("task_queue")
    op.drop_table("context_lake")
    op.drop_table("agents")
    op.drop_table("brand_dna")
    op.drop_table("users")
    op.execute("drop extension if exists vector;")
