-- Migration: Add email_chains table for email chain/thread cross-validation
-- Date: 2024-12-23
-- Description: Creates table to store uploaded email chains for fraud detection cross-validation

-- Create email_chains table
CREATE TABLE IF NOT EXISTS email_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES risk_assessments(id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    raw_content TEXT,
    parsed_data JSONB DEFAULT '{}',  -- Stores extracted messages array and metadata
    validation_status VARCHAR(50) DEFAULT 'pending',  -- pending, validated, suspicious, critical
    validation_result JSONB,  -- Stores full validation results
    validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT TRUE
);

-- Add index on assessment_id for query performance
CREATE INDEX IF NOT EXISTS idx_email_chains_assessment_id ON email_chains(assessment_id);

-- Add index on validation_status for filtering
CREATE INDEX IF NOT EXISTS idx_email_chains_validation_status ON email_chains(validation_status);

-- Add index on is_active for filtering
CREATE INDEX IF NOT EXISTS idx_email_chains_is_active ON email_chains(is_active);

-- Enable Row Level Security
ALTER TABLE email_chains ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Authenticated users can read email chains
CREATE POLICY "Authenticated users can read email chains"
ON email_chains FOR SELECT
TO authenticated
USING (is_active = TRUE);

-- RLS Policy: Authenticated users can insert email chains
CREATE POLICY "Authenticated users can insert email chains"
ON email_chains FOR INSERT
TO authenticated
WITH CHECK (TRUE);

-- RLS Policy: Authenticated users can update email chains
CREATE POLICY "Authenticated users can update email chains"
ON email_chains FOR UPDATE
TO authenticated
USING (is_active = TRUE);

-- RLS Policy: Service role can do anything
CREATE POLICY "Service role has full access to email chains"
ON email_chains FOR ALL
TO service_role
USING (TRUE)
WITH CHECK (TRUE);

-- Comment on table
COMMENT ON TABLE email_chains IS 'Stores uploaded email chains for cross-validation in fraud detection';

-- Comments on columns
COMMENT ON COLUMN email_chains.assessment_id IS 'Foreign key to risk_assessments table';
COMMENT ON COLUMN email_chains.original_filename IS 'Original filename if uploaded as .eml or .msg file';
COMMENT ON COLUMN email_chains.raw_content IS 'Raw text content of the email chain';
COMMENT ON COLUMN email_chains.parsed_data IS 'JSON object containing parsed email data: messages array, sender info, extracted mentions';
COMMENT ON COLUMN email_chains.validation_status IS 'Status: pending, validated, suspicious, critical';
COMMENT ON COLUMN email_chains.validation_result IS 'JSON object containing cross-validation results and discrepancies';
COMMENT ON COLUMN email_chains.validated_at IS 'Timestamp when validation was performed';
