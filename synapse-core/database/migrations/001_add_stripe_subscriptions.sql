-- Migration: Add Stripe subscription and payment tables
-- Date: 2026-01-21
-- Description: Adds tables for Stripe subscription management

-- =============================================================================
-- 1. MODIFY USERS TABLE - Add Stripe-related columns
-- =============================================================================

-- Add Stripe customer ID to users
ALTER TABLE users
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT UNIQUE;

-- Add billing email (can differ from account email)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS billing_email TEXT;

-- Add updated_at timestamp
ALTER TABLE users
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create index for Stripe customer lookups
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);


-- =============================================================================
-- 2. SUBSCRIPTIONS TABLE - Track active subscriptions
-- =============================================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Stripe identifiers
    stripe_subscription_id TEXT UNIQUE NOT NULL,
    stripe_customer_id TEXT NOT NULL,
    stripe_price_id TEXT,

    -- Subscription details
    tier TEXT NOT NULL DEFAULT 'standard', -- 'standard' or 'enterprise'
    status TEXT NOT NULL DEFAULT 'active', -- 'active', 'canceled', 'past_due', 'trialing', 'incomplete'
    billing_period TEXT DEFAULT 'monthly', -- 'monthly' or 'yearly'

    -- Period tracking
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,

    -- Trial tracking (optional)
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT subscriptions_tier_check CHECK (tier IN ('standard', 'enterprise')),
    CONSTRAINT subscriptions_status_check CHECK (
        status IN ('active', 'canceled', 'past_due', 'trialing', 'incomplete', 'incomplete_expired')
    ),
    CONSTRAINT subscriptions_billing_period_check CHECK (billing_period IN ('monthly', 'yearly'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_current_period_end ON subscriptions(current_period_end);


-- =============================================================================
-- 3. PAYMENT TRANSACTIONS TABLE - Track all payments
-- =============================================================================

CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,

    -- Stripe identifiers
    stripe_payment_intent_id TEXT UNIQUE,
    stripe_invoice_id TEXT,
    stripe_charge_id TEXT,

    -- Payment details
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'usd',
    status TEXT NOT NULL, -- 'succeeded', 'pending', 'failed', 'refunded'

    -- Invoice details
    invoice_pdf_url TEXT,
    receipt_url TEXT,

    -- Period this payment covers
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,

    -- Failure tracking
    failure_code TEXT,
    failure_message TEXT,

    -- Metadata
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT payment_transactions_status_check CHECK (
        status IN ('succeeded', 'pending', 'failed', 'refunded', 'canceled')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_subscription_id ON payment_transactions(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_stripe_invoice_id ON payment_transactions(stripe_invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_created_at ON payment_transactions(created_at DESC);


-- =============================================================================
-- 4. STRIPE WEBHOOK EVENTS TABLE - Track processed webhooks (idempotency)
-- =============================================================================

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stripe_event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,

    -- Processing status
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,

    -- Related entities
    customer_id TEXT,
    subscription_id TEXT,

    -- Raw event data (for debugging)
    event_data JSONB,

    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_stripe_event_id ON stripe_webhook_events(stripe_event_id);
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_event_type ON stripe_webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_processed ON stripe_webhook_events(processed) WHERE NOT processed;


-- =============================================================================
-- 5. SUBSCRIPTION TIER FEATURES TABLE - Define tier capabilities
-- =============================================================================

CREATE TABLE IF NOT EXISTS subscription_tier_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier TEXT NOT NULL,
    feature_key TEXT NOT NULL,
    feature_value JSONB NOT NULL, -- Can be boolean, number, or string
    description TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint per tier/feature
    CONSTRAINT subscription_tier_features_unique UNIQUE (tier, feature_key)
);

-- Seed default tier features
INSERT INTO subscription_tier_features (tier, feature_key, feature_value, description) VALUES
    -- Standard tier features
    ('standard', 'rate_limit_per_minute', '60', 'API rate limit per minute'),
    ('standard', 'context_storage_gb', '10', 'Context lake storage in GB'),
    ('standard', 'agents_available', '["scribe", "architect", "sentry"]', 'Available agents'),
    ('standard', 'support_level', '"email"', 'Support tier'),
    ('standard', 'custom_integrations', 'false', 'Custom integrations available'),

    -- Enterprise tier features
    ('enterprise', 'rate_limit_per_minute', '600', 'API rate limit per minute'),
    ('enterprise', 'context_storage_gb', '100', 'Context lake storage in GB'),
    ('enterprise', 'agents_available', '["scribe", "architect", "sentry"]', 'Available agents'),
    ('enterprise', 'support_level', '"priority"', 'Support tier'),
    ('enterprise', 'custom_integrations', 'true', 'Custom integrations available'),
    ('enterprise', 'team_collaboration', 'true', 'Team features enabled'),
    ('enterprise', 'advanced_analytics', 'true', 'Advanced analytics enabled')
ON CONFLICT (tier, feature_key) DO UPDATE SET
    feature_value = EXCLUDED.feature_value,
    updated_at = NOW();


-- =============================================================================
-- 6. HELPER FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for subscriptions table
DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for subscription_tier_features table
DROP TRIGGER IF EXISTS update_subscription_tier_features_updated_at ON subscription_tier_features;
CREATE TRIGGER update_subscription_tier_features_updated_at
    BEFORE UPDATE ON subscription_tier_features
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- 7. FUNCTION: Get user's current subscription tier
-- =============================================================================

CREATE OR REPLACE FUNCTION get_user_subscription_tier(p_user_id UUID)
RETURNS TEXT AS $$
DECLARE
    v_tier TEXT;
BEGIN
    SELECT tier INTO v_tier
    FROM subscriptions
    WHERE user_id = p_user_id
      AND status IN ('active', 'trialing')
    ORDER BY created_at DESC
    LIMIT 1;

    RETURN COALESCE(v_tier, 'free');
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- 8. FUNCTION: Check if user has active subscription
-- =============================================================================

CREATE OR REPLACE FUNCTION has_active_subscription(p_user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM subscriptions
        WHERE user_id = p_user_id
          AND status IN ('active', 'trialing')
          AND (current_period_end IS NULL OR current_period_end > NOW())
    );
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

COMMENT ON TABLE subscriptions IS 'Stores Stripe subscription data for users';
COMMENT ON TABLE payment_transactions IS 'Tracks all payment transactions from Stripe';
COMMENT ON TABLE stripe_webhook_events IS 'Tracks processed Stripe webhook events for idempotency';
COMMENT ON TABLE subscription_tier_features IS 'Defines features available per subscription tier';
