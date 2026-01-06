"""
Database Initialization Script for Synapse Core
Creates tables, indexes, and initial data for the application.
"""

import os
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://synapse:synapse@localhost:5432/synapse_core",
)

# SQL Schema
SCHEMA_SQL = """
-- Enable pgvector extension for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'standard',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Brand DNA table for storing brand voice and identity
CREATE TABLE IF NOT EXISTS brand_dna (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    voice_tone TEXT,
    visual_style TEXT,
    keywords TEXT[],
    avoid_phrases TEXT[],
    brand_values TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Agents table for agent configurations
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Context Lake for semantic memory with vector embeddings
CREATE TABLE IF NOT EXISTS context_lake (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    context_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task Queue for agent tasks
CREATE TABLE IF NOT EXISTS task_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    task_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Audit Log for compliance and debugging
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generated Content table for storing agent outputs
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id),
    content_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table for chat history
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    thread_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    messages JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, thread_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_brand_dna_user_id ON brand_dna(user_id);
CREATE INDEX IF NOT EXISTS idx_context_lake_user_id ON context_lake(user_id);
CREATE INDEX IF NOT EXISTS idx_context_lake_type ON context_lake(context_type);
CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status);
CREATE INDEX IF NOT EXISTS idx_task_queue_user_id ON task_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_generated_content_user_id ON generated_content(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_thread_id ON conversations(thread_id);

-- Vector similarity index for semantic search
CREATE INDEX IF NOT EXISTS idx_context_lake_embedding ON context_lake
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_generated_content_embedding ON generated_content
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""

# Initial seed data
SEED_SQL = """
-- Insert default agents
INSERT INTO agents (name, type, description, config) VALUES
    ('The Scribe', 'marketing', 'Marketing content generation and brand voice consistency',
     '{"model": "gpt-4-turbo-preview", "temperature": 0.7}'),
    ('The Architect', 'builder', 'React/Next.js UI component generation',
     '{"model": "gpt-4-turbo-preview", "temperature": 0.3}'),
    ('The Sentry', 'analytics', 'Performance monitoring and analytics',
     '{"model": "gpt-4-turbo-preview", "temperature": 0.2}')
ON CONFLICT DO NOTHING;

-- Insert a demo user for development
INSERT INTO users (email, name, subscription_tier) VALUES
    ('dev@synapse.local', 'Development User', 'enterprise')
ON CONFLICT (email) DO NOTHING;

-- Insert sample brand DNA for demo user
INSERT INTO brand_dna (user_id, voice_tone, visual_style, keywords, avoid_phrases, brand_values)
SELECT id,
    'Professional yet approachable, confident but not arrogant',
    'Modern, clean, with subtle gradients and glass effects',
    ARRAY['innovative', 'reliable', 'expert', 'trusted'],
    ARRAY['jargon', 'passive voice', 'clichés', 'buzzwords'],
    ARRAY['excellence', 'integrity', 'innovation', 'customer-first']
FROM users WHERE email = 'dev@synapse.local'
ON CONFLICT (user_id) DO NOTHING;
"""


def init_database():
    """Initialize the database with schema and seed data."""
    try:
        import psycopg2

        logger.info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        logger.info("Creating schema...")
        cursor.execute(SCHEMA_SQL)
        conn.commit()
        logger.info("Schema created successfully")

        logger.info("Inserting seed data...")
        cursor.execute(SEED_SQL)
        conn.commit()
        logger.info("Seed data inserted successfully")

        # Verify tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[t[0] for t in tables]}")

        cursor.close()
        conn.close()

        logger.info("Database initialization complete!")
        return True

    except ImportError:
        logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def check_database():
    """Check database connection and status."""
    try:
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"PostgreSQL version: {version}")

        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [t[0] for t in cursor.fetchall()]
        logger.info(f"Existing tables: {tables}")

        # Check for pgvector
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        has_vector = cursor.fetchone() is not None
        logger.info(f"pgvector extension: {'installed' if has_vector else 'not installed'}")

        cursor.close()
        conn.close()

        return True

    except ImportError:
        logger.error("psycopg2 not installed")
        return False
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False


def drop_all_tables():
    """Drop all tables (use with caution!)."""
    try:
        import psycopg2

        logger.warning("Dropping all tables...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            DROP TABLE IF EXISTS
                audit_log,
                generated_content,
                conversations,
                task_queue,
                context_lake,
                brand_dna,
                agents,
                users
            CASCADE;
        """)
        conn.commit()

        cursor.close()
        conn.close()

        logger.info("All tables dropped")
        return True

    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            check_database()
        elif command == "reset":
            drop_all_tables()
            init_database()
        elif command == "drop":
            drop_all_tables()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python init_db.py [check|reset|drop]")
    else:
        init_database()
