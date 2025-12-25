-- Migration: Add Finalization Workflow Support
-- Description: Adds finalization columns to risk_assessments and creates evaluation requirements config table
-- Feature: Defer fraud checks until finalization
-- Date: 2024-12-24

-- ==================== Step 1: Add finalization columns to risk_assessments ====================

-- Add finalized_by column (references user who finalized the evaluation)
ALTER TABLE risk_assessments
ADD COLUMN IF NOT EXISTS finalized_by UUID REFERENCES user_profiles(id);

-- Add finalized_at column (timestamp when evaluation was finalized)
ALTER TABLE risk_assessments
ADD COLUMN IF NOT EXISTS finalized_at TIMESTAMP WITH TIME ZONE;

-- Add comment for documentation
COMMENT ON COLUMN risk_assessments.finalized_by IS 'UUID of user who finalized the evaluation';
COMMENT ON COLUMN risk_assessments.finalized_at IS 'Timestamp when the evaluation was finalized';

-- ==================== Step 2: Update status constraint to include pending_finalization ====================

-- First, drop existing constraint if it exists
ALTER TABLE risk_assessments
DROP CONSTRAINT IF EXISTS risk_assessments_status_check;

-- Create new constraint with pending_finalization status
ALTER TABLE risk_assessments
ADD CONSTRAINT risk_assessments_status_check
CHECK (status IN (
    'pending',
    'pending_documents',
    'pending_finalization',
    'in_progress',
    'completed',
    'escalated',
    'approved',
    'rejected'
));

-- ==================== Step 3: Create evaluation_requirements_config table ====================

CREATE TABLE IF NOT EXISTS evaluation_requirements_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    require_cross_validation BOOLEAN NOT NULL DEFAULT true,
    require_email_chain_validation BOOLEAN NOT NULL DEFAULT false,
    require_external_contact_validation BOOLEAN NOT NULL DEFAULT false,
    min_documents_required INTEGER NOT NULL DEFAULT 2,
    allow_force_complete BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES user_profiles(id)
);

-- Add comments for documentation
COMMENT ON TABLE evaluation_requirements_config IS 'Configuration table for evaluation finalization requirements';
COMMENT ON COLUMN evaluation_requirements_config.require_cross_validation IS 'Whether cross-validation must be completed before finalization';
COMMENT ON COLUMN evaluation_requirements_config.require_email_chain_validation IS 'Whether email chain validation must be completed before finalization';
COMMENT ON COLUMN evaluation_requirements_config.require_external_contact_validation IS 'Whether external contact validation must be completed before finalization';
COMMENT ON COLUMN evaluation_requirements_config.min_documents_required IS 'Minimum number of documents that must be uploaded before finalization';
COMMENT ON COLUMN evaluation_requirements_config.allow_force_complete IS 'Whether users can force complete without meeting all optional requirements';

-- ==================== Step 4: Insert default configuration ====================

INSERT INTO evaluation_requirements_config (
    require_cross_validation,
    require_email_chain_validation,
    require_external_contact_validation,
    min_documents_required,
    allow_force_complete
)
SELECT true, false, false, 2, true
WHERE NOT EXISTS (SELECT 1 FROM evaluation_requirements_config);

-- ==================== Step 5: Create indexes for performance ====================

-- Index for finding finalized evaluations
CREATE INDEX IF NOT EXISTS idx_risk_assessments_finalized_at
ON risk_assessments(finalized_at)
WHERE finalized_at IS NOT NULL;

-- Index for finding evaluations by finalized_by user
CREATE INDEX IF NOT EXISTS idx_risk_assessments_finalized_by
ON risk_assessments(finalized_by)
WHERE finalized_by IS NOT NULL;

-- ==================== Step 6: Enable RLS on config table ====================

ALTER TABLE evaluation_requirements_config ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read configuration
CREATE POLICY "Authenticated users can read config"
ON evaluation_requirements_config FOR SELECT
TO authenticated
USING (true);

-- Only risk managers can update configuration
CREATE POLICY "Risk managers can update config"
ON evaluation_requirements_config FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.id = auth.uid()
        AND user_profiles.role IN ('risk_manager', 'admin')
    )
);

-- ==================== Step 7: Update existing assessments with cross-validation ====================
-- Migrate existing pending_documents assessments that have cross-validation results to pending_finalization

UPDATE risk_assessments
SET status = 'pending_finalization'
WHERE status = 'pending_documents'
AND EXISTS (
    SELECT 1 FROM risk_cross_validation_results
    WHERE risk_cross_validation_results.assessment_id = risk_assessments.id
);

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: Added finalization workflow support to risk_assessments';
    RAISE NOTICE 'New columns: finalized_by, finalized_at';
    RAISE NOTICE 'New status: pending_finalization';
    RAISE NOTICE 'New table: evaluation_requirements_config';
END
$$;
