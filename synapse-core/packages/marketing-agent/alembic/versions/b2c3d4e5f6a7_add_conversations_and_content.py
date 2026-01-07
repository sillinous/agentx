"""Add conversations and generated content tables

Revision ID: b2c3d4e5f6a7
Revises: abbdabebdcfc
Create Date: 2025-01-07

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "abbdabebdcfc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add type column to agents table for agent type lookup
    op.execute(
        """
        ALTER TABLE agents
        ADD COLUMN IF NOT EXISTS type text,
        ADD COLUMN IF NOT EXISTS description text,
        ADD COLUMN IF NOT EXISTS config jsonb;
        """
    )

    # Update existing agents with type based on system_key
    op.execute(
        """
        UPDATE agents
        SET type = CASE
            WHEN system_key LIKE '%scribe%' THEN 'scribe'
            WHEN system_key LIKE '%architect%' THEN 'architect'
            WHEN system_key LIKE '%sentry%' THEN 'sentry'
            ELSE 'unknown'
        END
        WHERE type IS NULL;
        """
    )

    # Add additional columns to brand_dna for structured brand voice
    op.execute(
        """
        ALTER TABLE brand_dna
        ADD COLUMN IF NOT EXISTS voice_tone text,
        ADD COLUMN IF NOT EXISTS visual_style text,
        ADD COLUMN IF NOT EXISTS keywords text[],
        ADD COLUMN IF NOT EXISTS avoid_phrases text[],
        ADD COLUMN IF NOT EXISTS brand_values text[];
        """
    )

    # Add unique constraint on user_id for brand_dna upserts
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'brand_dna_user_id_key'
            ) THEN
                ALTER TABLE brand_dna
                ADD CONSTRAINT brand_dna_user_id_key UNIQUE (user_id);
            END IF;
        END $$;
        """
    )

    # Add context_type column to context_lake
    op.execute(
        """
        ALTER TABLE context_lake
        ADD COLUMN IF NOT EXISTS context_type text;
        """
    )

    # Create conversations table for chat history persistence
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id uuid REFERENCES users(id) ON DELETE CASCADE,
            thread_id text NOT NULL,
            agent_type text NOT NULL,
            messages jsonb NOT NULL DEFAULT '[]'::jsonb,
            created_at timestamp with time zone DEFAULT now(),
            updated_at timestamp with time zone DEFAULT now(),
            UNIQUE(user_id, thread_id)
        );
        """
    )

    # Create index on conversations for efficient querying
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id
        ON conversations(user_id);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
        ON conversations(updated_at DESC);
        """
    )

    # Create generated_content table for storing agent outputs
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_content (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id uuid REFERENCES users(id) ON DELETE CASCADE,
            agent_id uuid REFERENCES agents(id) ON DELETE SET NULL,
            content_type text NOT NULL,
            content text NOT NULL,
            metadata jsonb,
            embedding vector(1536),
            created_at timestamp with time zone DEFAULT now()
        );
        """
    )

    # Create indexes for generated_content
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_generated_content_user_id
        ON generated_content(user_id);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_generated_content_type
        ON generated_content(content_type);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_generated_content_created_at
        ON generated_content(created_at DESC);
        """
    )

    # Add additional columns to audit_log for resource tracking
    op.execute(
        """
        ALTER TABLE audit_log
        ADD COLUMN IF NOT EXISTS resource_type text,
        ADD COLUMN IF NOT EXISTS resource_id text;
        """
    )

    # Create indexes on context_lake for vector search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_context_lake_user_id
        ON context_lake(user_id);
        """
    )

    # Add name column to users table if it doesn't exist
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS name text;
        """
    )

    # Update full_name to name if name is null but full_name exists
    op.execute(
        """
        UPDATE users
        SET name = full_name
        WHERE name IS NULL AND full_name IS NOT NULL;
        """
    )


def downgrade() -> None:
    # Drop generated_content table
    op.execute("DROP TABLE IF EXISTS generated_content;")

    # Drop conversations table
    op.execute("DROP TABLE IF EXISTS conversations;")

    # Remove columns added to audit_log
    op.execute(
        """
        ALTER TABLE audit_log
        DROP COLUMN IF EXISTS resource_type,
        DROP COLUMN IF EXISTS resource_id;
        """
    )

    # Remove columns added to context_lake
    op.execute(
        """
        ALTER TABLE context_lake
        DROP COLUMN IF EXISTS context_type;
        """
    )

    # Remove columns added to brand_dna
    op.execute(
        """
        ALTER TABLE brand_dna
        DROP CONSTRAINT IF EXISTS brand_dna_user_id_key,
        DROP COLUMN IF EXISTS voice_tone,
        DROP COLUMN IF EXISTS visual_style,
        DROP COLUMN IF EXISTS keywords,
        DROP COLUMN IF EXISTS avoid_phrases,
        DROP COLUMN IF EXISTS brand_values;
        """
    )

    # Remove columns added to agents
    op.execute(
        """
        ALTER TABLE agents
        DROP COLUMN IF EXISTS type,
        DROP COLUMN IF EXISTS description,
        DROP COLUMN IF EXISTS config;
        """
    )

    # Remove name column from users
    op.execute(
        """
        ALTER TABLE users
        DROP COLUMN IF EXISTS name;
        """
    )
