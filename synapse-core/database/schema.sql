-- ENABLE EXTENSIONS
create extension if not exists vector;
create extension if not exists "uuid-ossp";

-- 1. THE USERS (The Humans)
create table users (
  id uuid primary key default uuid_generate_v4(),
  email text unique not null,
  full_name text,
  name text, -- Alias for full_name
  subscription_tier text default 'standard', -- 'standard' or 'enterprise'
  created_at timestamp with time zone default now()
);

-- 2. THE BRAND DNA (The "Soul" of the business)
-- Stores brand voice and identity parameters
create table brand_dna (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade unique,
  parameters jsonb not null default '{}'::jsonb, -- Legacy JSON blob
  voice_tone text, -- e.g., 'professional', 'witty', 'casual'
  visual_style text, -- e.g., 'modern', 'classic', 'minimalist'
  keywords text[], -- Brand-associated keywords
  avoid_phrases text[], -- Phrases to avoid in content
  brand_values text[], -- Core brand values
  updated_at timestamp with time zone default now()
);

-- 3. THE AGENT REGISTRY (The Employees)
-- Defines which agents are active for which user.
create table agents (
  id uuid primary key default uuid_generate_v4(),
  system_key text not null, -- e.g., 'sys_scribe_v1'
  name text not null, -- e.g., 'The Scribe'
  type text, -- 'scribe', 'architect', 'sentry'
  description text, -- Agent description
  capabilities jsonb, -- ["write_email", "check_grammar"]
  config jsonb, -- Agent configuration
  user_id uuid references users(id) on delete cascade,
  is_active boolean default true
);

-- 4. THE CONTEXT LAKE (Long Term Memory)
-- Every email sent, every page built, is stored here as a vector.
create table context_lake (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade,
  agent_id uuid references agents(id),
  context_type text, -- 'conversation', 'content', 'feedback'
  content text not null, -- "Drafted email regarding Black Friday"
  metadata jsonb, -- { "type": "email", "performance_score": 0.9 }
  embedding vector(1536), -- The AI "Brain" representation
  created_at timestamp with time zone default now()
);

create index idx_context_lake_user_id on context_lake(user_id);

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
  resource_type text, -- 'agent', 'content', 'conversation'
  resource_id text, -- ID of the affected resource
  details jsonb,
  timestamp timestamp with time zone default now()
);

-- 7. CONVERSATIONS (Chat History)
-- Stores conversation threads for persistence and retrieval
create table conversations (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade,
  thread_id text not null,
  agent_type text not null, -- 'scribe', 'architect', 'sentry'
  messages jsonb not null default '[]'::jsonb,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  unique(user_id, thread_id)
);

create index idx_conversations_user_id on conversations(user_id);
create index idx_conversations_updated_at on conversations(updated_at desc);

-- 8. GENERATED CONTENT (Agent Outputs)
-- Stores generated content with embeddings for semantic search
create table generated_content (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references users(id) on delete cascade,
  agent_id uuid references agents(id) on delete set null,
  content_type text not null, -- 'blog_post', 'social_media', 'component', etc.
  content text not null,
  metadata jsonb,
  embedding vector(1536),
  created_at timestamp with time zone default now()
);

create index idx_generated_content_user_id on generated_content(user_id);
create index idx_generated_content_type on generated_content(content_type);
create index idx_generated_content_created_at on generated_content(created_at desc);
