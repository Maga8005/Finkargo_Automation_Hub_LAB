-- Migration: Add Risk Settings Table
-- Date: 2025-12-28
-- Description: Creates risk_settings table for configurable AI extraction and other risk module settings

-- ==================== RISK SETTINGS TABLE ====================

CREATE TABLE IF NOT EXISTS risk_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL DEFAULT 'false',
    value_type VARCHAR(20) NOT NULL DEFAULT 'boolean' CHECK (value_type IN ('boolean', 'number', 'text', 'json')),
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES user_profiles(id)
);

-- Index for fast lookups by setting_key
CREATE INDEX IF NOT EXISTS idx_risk_settings_key ON risk_settings(setting_key);

-- ==================== INSERT DEFAULT SETTINGS ====================

INSERT INTO risk_settings (setting_key, setting_value, value_type, description) VALUES
    ('ai_email_extraction_enabled', 'false', 'boolean', 'Enable AI-powered (OpenAI GPT-4o) entity extraction from email chains. When disabled, uses regex-based extraction.')
ON CONFLICT (setting_key) DO NOTHING;

-- ==================== ROW LEVEL SECURITY ====================

-- Enable RLS on risk_settings table
ALTER TABLE risk_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies for risk_settings
CREATE POLICY "Authenticated users can view risk settings"
ON risk_settings FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Risk managers can update risk settings"
ON risk_settings FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Risk managers can insert risk settings"
ON risk_settings FOR INSERT
TO authenticated
WITH CHECK (true);

-- ==================== TRIGGER FOR UPDATED_AT ====================

-- Trigger for risk_settings (reuses update_updated_at_column function from risk_tables migration)
DROP TRIGGER IF EXISTS update_risk_settings_updated_at ON risk_settings;
CREATE TRIGGER update_risk_settings_updated_at
    BEFORE UPDATE ON risk_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================== VERIFICATION ====================

-- Verify table was created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name = 'risk_settings';

-- Verify default setting was inserted
SELECT setting_key, setting_value, value_type, description
FROM risk_settings
ORDER BY setting_key;
