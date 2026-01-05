-- ENABLE VECTOR EXTENSION (For AI Long-term Memory)
create extension if not exists vector;

-- 1. THE USERS (The Humans)
create table users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  full_name text,
  subscription_tier text default 'standard', -- 'standard' or 'enterprise'
  created_at timestamp with time zone default now()
);

-- 2. THE BRAND DNA (The "Soul" of the business)
-- This stores the JSON blob we generated in the "Genesis" interview.
create table brand_dna (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade,
  parameters jsonb not null, -- { "voice": "witty", "colors": ["#00f0ff"] }
  updated_at timestamp with time zone default now()
);

-- 3. THE AGENT REGISTRY (The Employees)
-- Defines which agents are active for which user.
create table agents (
  id uuid primary key default uuid_generate_v4(),
  system_key text not null, -- e.g., 'sys_scribe_v1'
  name text not null, -- e.g., 'The Scribe'
  capabilities jsonb, -- ["write_email", "check_grammar"]
  user_id uuid references users(id) on delete cascade,
  is_active boolean default true
);

-- 4. THE CONTEXT LAKE (Long Term Memory)
-- Every email sent, every page built, is stored here as a vector.
create table context_lake (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade,
  agent_id uuid references agents(id),
  content text not null, -- "Drafted email regarding Black Friday"
  metadata jsonb, -- { "type": "email", "performance_score": 0.9 }
  embedding vector(1536), -- The AI "Brain" representation
  created_at timestamp with time zone default now()
);

-- 5. THE TASK QUEUE (The Agent To-Do List)
-- This powers the "Activity Feed" in the UI.
create table task_queue (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id),
  assigned_agent_id uuid references agents(id),
  task_type text not null, -- 'GENERATE_LANDING_PAGE'
  status text default 'PENDING', -- 'PENDING', 'IN_PROGRESS', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED'
  payload jsonb, -- The input data
  result jsonb, -- The output data
  confidence_score float, -- 0.0 to 1.0
  created_at timestamp with time zone default now()
);

-- 6. AUDIT LOG (The Security Trace)
create table audit_log (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id),
  action text not null,
  details jsonb,
  timestamp timestamp with time zone default now()
);
