-- Database Initialization Script for Docker
-- This file is executed automatically when the PostgreSQL container starts for the first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Note: The full schema will be created by Alembic migrations
-- This file only ensures required extensions are available

-- Create a health check table
CREATE TABLE IF NOT EXISTS _db_health (
    initialized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO _db_health DEFAULT VALUES;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully with pgvector extension';
END $$;
