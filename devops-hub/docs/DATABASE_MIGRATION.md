# Database Migration Guide

> **Last Updated:** 2026-01-12
> **Status:** Production Ready

This guide covers database schema migrations using Alembic and migrating from SQLite to PostgreSQL for production deployments.

---

## Table of Contents

1. [Overview](#overview)
2. [Alembic Setup](#alembic-setup)
3. [Running Migrations](#running-migrations)
4. [SQLite to PostgreSQL Migration](#sqlite-to-postgresql-migration)
5. [Environment Configuration](#environment-configuration)
6. [Troubleshooting](#troubleshooting)

---

## Overview

DevOps Hub uses SQLite by default for simplicity. For production deployments with high concurrency requirements, PostgreSQL is recommended.

### Current Schema

| Table | Purpose |
|-------|---------|
| `agents` | Agent registry metadata |
| `workflows` | Workflow definitions |
| `workflow_executions` | Execution history and state |
| `events` | Event log for pub/sub |
| `api_keys` | Authentication keys |
| `documentation_guides` | User guides |
| `documentation_examples` | Code examples |

---

## Alembic Setup

### Prerequisites

```bash
pip install alembic sqlalchemy psycopg2-binary
```

### Initialize Alembic (Already Done)

The project includes pre-configured Alembic setup in `migrations/`:

```
migrations/
├── alembic.ini          # Alembic configuration
├── env.py               # Migration environment
├── script.py.mako       # Migration template
└── versions/            # Migration scripts
    └── 001_initial_schema.py
```

### Configuration

Alembic reads the database URL from the `DATABASE_URL` environment variable:

```bash
# SQLite (default)
export DATABASE_URL="sqlite:///./data/devops_hub.db"

# PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/devops_hub"
```

---

## Running Migrations

### Check Current Version

```bash
alembic current
```

### Upgrade to Latest

```bash
alembic upgrade head
```

### Downgrade One Version

```bash
alembic downgrade -1
```

### View Migration History

```bash
alembic history
```

### Create New Migration

When you modify the schema in `core/database.py`, create a new migration:

```bash
alembic revision -m "description_of_change"
```

Then edit the generated file in `migrations/versions/` to add your upgrade/downgrade logic.

---

## SQLite to PostgreSQL Migration

### Step 1: Export Data from SQLite

```bash
# Create a data export
python -c "
from core.database import get_database
import json

db = get_database()
tables = ['agents', 'workflows', 'workflow_executions', 'events', 'api_keys',
          'documentation_guides', 'documentation_examples']

export = {}
for table in tables:
    rows = db.fetch_all(f'SELECT * FROM {table}')
    export[table] = rows

with open('data_export.json', 'w') as f:
    json.dump(export, f, indent=2)

print(f'Exported {sum(len(v) for v in export.values())} total rows')
"
```

### Step 2: Set Up PostgreSQL

```bash
# Create database
createdb devops_hub

# Or using psql
psql -c "CREATE DATABASE devops_hub;"
```

### Step 3: Configure Environment

```bash
# Update .env or export
export DATABASE_URL="postgresql://user:password@localhost:5432/devops_hub"
```

### Step 4: Run Migrations on PostgreSQL

```bash
alembic upgrade head
```

### Step 5: Import Data

```bash
python -c "
import json
import os

# Set PostgreSQL connection
os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost:5432/devops_hub'

from core.database_pg import get_database  # Use PostgreSQL adapter

db = get_database()

with open('data_export.json', 'r') as f:
    export = json.load(f)

for table, rows in export.items():
    for row in rows:
        # Insert logic here (table-specific)
        pass

print('Import complete')
"
```

### Step 6: Verify Migration

```bash
# Check row counts match
psql devops_hub -c \"
SELECT
    'agents' as table_name, COUNT(*) FROM agents
UNION ALL SELECT 'workflows', COUNT(*) FROM workflows
UNION ALL SELECT 'api_keys', COUNT(*) FROM api_keys;
\"
```

---

## Environment Configuration

### Development (SQLite)

```env
DATABASE_URL=sqlite:///./data/devops_hub.db
```

### Production (PostgreSQL)

```env
DATABASE_URL=postgresql://devops:secure_password@db.example.com:5432/devops_hub
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
```

### Docker Compose PostgreSQL

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: devops
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: devops_hub
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devops -d devops_hub"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    environment:
      DATABASE_URL: postgresql://devops:${DB_PASSWORD}@db:5432/devops_hub
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

---

## Schema Differences

### SQLite vs PostgreSQL Syntax

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Auto-increment | `INTEGER PRIMARY KEY` | `SERIAL` or `GENERATED` |
| Boolean | `INTEGER (0/1)` | `BOOLEAN` |
| JSON | `TEXT` | `JSONB` |
| Datetime | `TEXT` | `TIMESTAMP WITH TIME ZONE` |
| Case sensitivity | Case-insensitive by default | Case-sensitive |

### Migration Considerations

1. **JSON columns**: SQLite stores as TEXT, PostgreSQL uses native JSONB for better indexing
2. **Timestamps**: Use ISO format strings for SQLite, native timestamps for PostgreSQL
3. **Boolean**: SQLite uses 0/1, PostgreSQL uses true/false
4. **Indexes**: GIN indexes on JSONB columns improve query performance

---

## Troubleshooting

### Common Issues

#### "alembic: command not found"

```bash
pip install alembic
# Or ensure virtual environment is activated
```

#### "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
# For production, use: pip install psycopg2
```

#### Migration conflicts

```bash
# Check for multiple heads
alembic heads

# Merge if needed
alembic merge heads -m "merge_migrations"
```

#### Connection refused to PostgreSQL

1. Verify PostgreSQL is running: `pg_isready`
2. Check connection string format
3. Verify user permissions: `GRANT ALL ON DATABASE devops_hub TO user;`

### Backup Before Migration

Always backup before migrating:

```bash
# SQLite
cp data/devops_hub.db data/devops_hub.db.backup

# PostgreSQL
pg_dump devops_hub > backup.sql
```

---

## Best Practices

1. **Test migrations** on a copy of production data first
2. **Version control** all migration scripts
3. **Document** any manual steps required
4. **Backup** before running migrations
5. **Use transactions** - Alembic wraps migrations in transactions by default
6. **Review generated SQL** before applying: `alembic upgrade head --sql`

---

## Next Steps

- See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- See [../PRODUCTION_ROADMAP.md](../PRODUCTION_ROADMAP.md) for project status
