-- ============================================================================
-- FlipFlow Database Migration - Fix Credits Field
-- ============================================================================
-- Purpose: Align database schema with code expectations
-- Run in: Supabase SQL Editor for FlipFlow project
-- Time: ~2 minutes
-- ============================================================================

-- Step 1: Add missing columns (safe - uses IF NOT EXISTS)
-- ============================================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 3;
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_id TEXT DEFAULT 'free';

-- Step 2: Migrate data from old field to new field
-- ============================================================================
-- This ensures existing users don't lose their credits
UPDATE users 
SET credits = COALESCE(analysis_credits, 3)
WHERE credits IS NULL OR credits = 0;

-- Step 3: Create performance indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_users_credits 
    ON users(credits);

CREATE INDEX IF NOT EXISTS idx_users_subscription_tier 
    ON users(subscription_tier);

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id 
    ON users(stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_users_plan_id 
    ON users(plan_id);

-- Step 4: Verification queries
-- ============================================================================
-- Run these to verify migration succeeded:

-- Check that credits column exists and has data
SELECT 
    COUNT(*) as total_users,
    COUNT(credits) as users_with_credits,
    AVG(credits) as avg_credits
FROM users;

-- View sample data to verify
SELECT 
    id,
    email,
    credits,
    analysis_credits,
    used_credits,
    subscription_tier,
    plan_id
FROM users
ORDER BY created_at DESC
LIMIT 10;

-- Check for any NULL credits (should be 0)
SELECT COUNT(*) as users_with_null_credits
FROM users
WHERE credits IS NULL;

-- ============================================================================
-- Expected Results:
-- ============================================================================
-- ✅ All users should have credits ≥ 3 (or their analysis_credits value)
-- ✅ New columns should exist: credits, plan_id
-- ✅ Indexes should be created
-- ✅ Zero NULL values in credits column
-- ============================================================================

-- ============================================================================
-- Rollback (if needed):
-- ============================================================================
-- Uncomment and run ONLY if you need to undo this migration:
-- 
-- DROP INDEX IF EXISTS idx_users_credits;
-- DROP INDEX IF EXISTS idx_users_subscription_tier;  
-- DROP INDEX IF EXISTS idx_users_stripe_customer_id;
-- DROP INDEX IF EXISTS idx_users_plan_id;
-- ALTER TABLE users DROP COLUMN IF EXISTS credits;
-- ALTER TABLE users DROP COLUMN IF EXISTS plan_id;
-- ============================================================================
