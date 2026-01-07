-- Synapse Core Seed Data
-- Default system agents

-- Insert default agents (system-wide, no user_id)
INSERT INTO agents (system_key, name, type, description, capabilities, is_active)
VALUES
  (
    'sys_scribe_v1',
    'The Scribe',
    'scribe',
    'Marketing content generation agent - handles brand voice consistency, copywriting, and SEO optimization',
    '["content_generation", "brand_voice", "seo_optimization", "sentiment_analysis"]'::jsonb,
    true
  ),
  (
    'sys_architect_v1',
    'The Architect',
    'architect',
    'UI/UX builder agent - generates React/Next.js components with best practices',
    '["component_generation", "react_syntax", "ui_testing", "accessibility"]'::jsonb,
    true
  ),
  (
    'sys_sentry_v1',
    'The Sentry',
    'sentry',
    'Analytics and monitoring agent - tracks performance, detects anomalies, provides insights',
    '["performance_metrics", "anomaly_detection", "traffic_analysis", "alerting"]'::jsonb,
    true
  )
ON CONFLICT DO NOTHING;

-- Create a demo user for development
INSERT INTO users (email, full_name, name, subscription_tier)
VALUES ('demo@synapse.local', 'Demo User', 'Demo User', 'enterprise')
ON CONFLICT (email) DO NOTHING;
