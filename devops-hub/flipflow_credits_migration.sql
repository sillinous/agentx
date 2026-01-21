-- ============================================================================
-- FlipFlow Credits System - Unified Migration
-- ============================================================================
-- Purpose: Unify credit tracking from dual systems to single source of truth
-- Run in: Supabase SQL Editor for FlipFlow project
-- Time: ~2 minutes
-- ============================================================================

-- PROBLEM:
-- - Original schema uses: analysis_credits
-- - New code uses: credits + used_credits
-- - This creates inconsistency and NULL errors

-- SOLUTION:
-- Standardize on: credits (total available) + used_credits (consumed this period)
-- Keep analysis_credits for backward compatibility (deprecated)

-- ============================================================================
-- STEP 1: Add new credit tracking columns (safe - IF NOT EXISTS)
-- ============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 3;
ALTER TABLE users ADD COLUMN IF NOT EXISTS used_credits INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_id TEXT DEFAULT 'free';

-- ============================================================================
-- STEP 2: Migrate data from old system to new system
-- ============================================================================

-- For users who have data in analysis_credits but not in credits
UPDATE users 
SET credits = COALESCE(analysis_credits, 3)
WHERE credits IS NULL OR credits = 0;

-- Ensure used_credits is never NULL
UPDATE users 
SET used_credits = 0
WHERE used_credits IS NULL;

-- Ensure plan_id is set
UPDATE users 
SET plan_id = COALESCE(subscription_tier, 'free')
WHERE plan_id IS NULL OR plan_id = '';

-- ============================================================================
-- STEP 3: Add Stripe-related columns (if not already present)
-- ============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_period_start TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS cancel_at_period_end BOOLEAN DEFAULT false;

-- ============================================================================
-- STEP 4: Create performance indexes
-- ============================================================================

-- Index for credit lookups (most common query)
CREATE INDEX IF NOT EXISTS idx_users_credits 
    ON users(credits) 
    WHERE credits IS NOT NULL;

-- Index for subscription status queries
CREATE INDEX IF NOT EXISTS idx_users_subscription_status 
    ON users(subscription_status) 
    WHERE subscription_status IS NOT NULL;

-- Index for Stripe customer lookups
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id 
    ON users(stripe_customer_id) 
    WHERE stripe_customer_id IS NOT NULL;

-- Index for plan-based queries
CREATE INDEX IF NOT EXISTS idx_users_plan_id 
    ON users(plan_id);

-- Composite index for subscription queries (plan + status)
CREATE INDEX IF NOT EXISTS idx_users_subscription_lookup 
    ON users(plan_id, subscription_status);

-- ============================================================================
-- STEP 5: Add constraints for data integrity
-- ============================================================================

-- Ensure credits is never negative (except -1 for unlimited)
ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS chk_credits_valid 
    CHECK (credits >= -1);

-- Ensure used_credits is never negative
ALTER TABLE users ADD CONSTRAINT IF NOT EXISTS chk_used_credits_valid 
    CHECK (used_credits >= 0);

-- ============================================================================
-- STEP 6: Create helper function for remaining credits
-- ============================================================================

-- Drop if exists (to allow re-running this migration)
DROP FUNCTION IF EXISTS get_remaining_credits(UUID);

-- Function to calculate remaining credits (handles unlimited -1 case)
CREATE OR REPLACE FUNCTION get_remaining_credits(user_id_param UUID)
RETURNS INTEGER AS $$
DECLARE
    total_credits INTEGER;
    used_credits_val INTEGER;
BEGIN
    SELECT credits, used_credits 
    INTO total_credits, used_credits_val
    FROM users 
    WHERE id = user_id_param;
    
    -- Unlimited plan
    IF total_credits = -1 THEN
        RETURN -1;
    END IF;
    
    -- Calculate remaining
    RETURN total_credits - COALESCE(used_credits_val, 0);
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify migration succeeded:

-- 1. Check that all users have credits
SELECT 
    COUNT(*) as total_users,
    COUNT(credits) as users_with_credits,
    COUNT(used_credits) as users_with_used_credits,
    AVG(credits) as avg_credits,
    AVG(used_credits) as avg_used_credits
FROM users;

-- 2. View sample data to verify
SELECT 
    id,
    email,
    credits,
    used_credits,
    get_remaining_credits(id) as remaining,
    analysis_credits,
    subscription_tier,
    plan_id,
    subscription_status
FROM users
ORDER BY created_at DESC
LIMIT 10;

-- 3. Check for any NULL credits (should be 0)
SELECT COUNT(*) as users_with_null_credits
FROM users
WHERE credits IS NULL OR used_credits IS NULL;

-- 4. Check data distribution
SELECT 
    plan_id,
    COUNT(*) as user_count,
    AVG(credits) as avg_credits,
    SUM(CASE WHEN credits = -1 THEN 1 ELSE 0 END) as unlimited_users
FROM users
GROUP BY plan_id
ORDER BY user_count DESC;

-- Migration complete! 🎉
