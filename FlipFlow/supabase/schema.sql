-- FlipFlow Phase 2: Scout Agent Database Schema
-- Supabase PostgreSQL Schema

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS & SUBSCRIPTIONS
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  subscription_tier TEXT DEFAULT 'free',
  subscription_status TEXT DEFAULT 'active',
  analysis_credits INT DEFAULT 3,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- FLIPPA LISTINGS
CREATE TABLE IF NOT EXISTS listings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  flippa_id TEXT UNIQUE NOT NULL,
  url TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  asking_price DECIMAL(12, 2),
  monthly_revenue DECIMAL(12, 2),
  monthly_profit DECIMAL(12, 2),
  category TEXT,
  listing_status TEXT DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI ANALYSES
CREATE TABLE IF NOT EXISTS analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  listing_id UUID REFERENCES listings(id),
  score INT NOT NULL,
  deal_quality TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  summary TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- USER ALERTS
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  min_score INT,
  max_price DECIMAL(12, 2),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- PERFORMANCE INDEXES

-- Users: Email lookups for authentication
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Listings: Status and creation date for filtering/sorting
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(listing_status);
CREATE INDEX IF NOT EXISTS idx_listings_created ON listings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_listings_category ON listings(category);
CREATE INDEX IF NOT EXISTS idx_listings_asking_price ON listings(asking_price);

-- Analyses: Optimize queries by listing, score, and creation date
CREATE INDEX IF NOT EXISTS idx_analyses_listing ON analyses(listing_id);
CREATE INDEX IF NOT EXISTS idx_analyses_score ON analyses(score DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at DESC);

-- Alerts: Find active alerts for users
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(user_id, is_active) WHERE is_active = true;
