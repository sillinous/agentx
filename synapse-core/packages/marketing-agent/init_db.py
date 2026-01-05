import sqlite3
import os
import json
import uuid
from datetime import datetime

DATABASE_FILE = "synapse.db"

# Adapted schema for SQLite
SQLITE_SCHEMA = """
-- 1. THE USERS (The Humans)
create table users (
  id TEXT primary key,
  email text unique not null,
  full_name text,
  subscription_tier text default 'standard', -- 'standard' or 'enterprise'
  created_at TEXT default (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 2. THE BRAND DNA (The "Soul" of the business)
-- This stores the JSON blob we generated in the "Genesis" interview.
create table brand_dna (
  id TEXT primary key,
  user_id TEXT references users(id) on delete cascade,
  parameters TEXT not null, -- { "voice": "witty", "colors": ["#00f0ff"] }
  updated_at TEXT default (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 3. THE AGENT REGISTRY (The Employees)
-- Defines which agents are active for which user.
create table agents (
  id TEXT primary key,
  system_key text not null, -- e.g., 'sys_scribe_v1'
  name text not null, -- e.g., 'The Scribe'
  capabilities TEXT, -- ["write_email", "check_grammar"]
  user_id TEXT references users(id) on delete cascade,
  is_active boolean default true
);

-- 4. THE CONTEXT LAKE (Long Term Memory)
-- Every email sent, every page built, is stored here as a vector.
create table context_lake (
  id TEXT primary key,
  user_id TEXT references users(id) on delete cascade,
  agent_id TEXT references agents(id),
  content text not null, -- "Drafted email regarding Black Friday"
  metadata TEXT, -- { "type": "email", "performance_score": 0.9 }
  embedding TEXT, -- The AI "Brain" representation
  created_at TEXT default (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 5. THE TASK QUEUE (The Agent To-Do List)
-- This powers the "Activity Feed" in the UI.
create table task_queue (
  id TEXT primary key,
  user_id TEXT references users(id),
  assigned_agent_id TEXT references agents(id),
  task_type text not null, -- 'GENERATE_LANDING_PAGE'
  status text default 'PENDING', -- 'PENDING', 'IN_PROGRESS', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED'
  payload TEXT, -- The input data
  result TEXT, -- The output data
  confidence_score float, -- 0.0 to 1.0
  created_at TEXT default (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);

-- 6. AUDIT LOG (The Security Trace)
create table audit_log (
  id TEXT primary key,
  user_id TEXT references users(id),
  action text not null,
  details TEXT,
  timestamp TEXT default (strftime('%Y-%m-%d %H:%M:%S', 'now'))
);
"""


def initialize_sqlite_db():
    """
    Initializes the SQLite database with the adapted schema and seeds initial data.
    """
    conn = None
    try:
        db_path = os.path.join(os.path.dirname(__file__), DATABASE_FILE)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the adapted schema
        cursor.executescript(SQLITE_SCHEMA)
        conn.commit()
        print(
            f"SQLite database '{DATABASE_FILE}' initialized successfully with adapted schema."
        )

        # --- Seed initial data ---
        # 1. Insert a sample user
        sample_user_id = str(uuid.uuid4())
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, email, full_name, created_at) VALUES (?, ?, ?, ?)",
            (sample_user_id, "test@example.com", "Test User", current_time),
        )
        print(f"Inserted sample user with ID: {sample_user_id}")

        # 2. Insert sample brand_dna for the user
        sample_brand_dna = {
            "voice": "witty and professional",
            "tone": "friendly and informative",
            "keywords": ["AI", "marketing", "automation", "synapse"],
            "target_audience": "small business owners",
            "style_guide": "Use clear, concise language. Avoid jargon where possible. Maintain a positive outlook.",
        }
        cursor.execute(
            "INSERT OR IGNORE INTO brand_dna (id, user_id, parameters, updated_at) VALUES (?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                sample_user_id,
                json.dumps(sample_brand_dna),
                current_time,
            ),
        )
        print(f"Inserted sample brand_dna for user ID: {sample_user_id}")

        conn.commit()
        print("Initial data seeded successfully.")

    except sqlite3.Error as e:
        print(f"Error initializing SQLite database or seeding data: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    initialize_sqlite_db()
