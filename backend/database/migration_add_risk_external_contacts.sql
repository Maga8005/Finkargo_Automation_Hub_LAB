-- Migration: Add risk_external_contacts table for email/contact validation
-- Feature: Email/Contact Information Correlation Tab
-- Description: Stores external contact information (emails received via commercial channels)
--              for validation against document data to detect typosquatting fraud attempts

-- Create the risk_external_contacts table
CREATE TABLE IF NOT EXISTS risk_external_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES risk_assessments(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    source VARCHAR(100) NOT NULL DEFAULT 'comercial_team',
    validation_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    validation_result JSONB,
    validated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_risk_external_contacts_assessment_id
    ON risk_external_contacts(assessment_id);

CREATE INDEX IF NOT EXISTS idx_risk_external_contacts_email
    ON risk_external_contacts(email);

CREATE INDEX IF NOT EXISTS idx_risk_external_contacts_validation_status
    ON risk_external_contacts(validation_status);

CREATE INDEX IF NOT EXISTS idx_risk_external_contacts_is_active
    ON risk_external_contacts(is_active);

-- Add comment for documentation
COMMENT ON TABLE risk_external_contacts IS 'Stores external contact emails received via commercial channels for fraud validation';
COMMENT ON COLUMN risk_external_contacts.email IS 'Email address provided by user for validation';
COMMENT ON COLUMN risk_external_contacts.sender_name IS 'Optional name of the sender';
COMMENT ON COLUMN risk_external_contacts.source IS 'Where the email was received (e.g., comercial_team, whatsapp, email)';
COMMENT ON COLUMN risk_external_contacts.validation_status IS 'Status: pending, validated, suspicious, critical';
COMMENT ON COLUMN risk_external_contacts.validation_result IS 'JSON containing typosquatting analysis result';
COMMENT ON COLUMN risk_external_contacts.validated_at IS 'Timestamp when validation was performed';
COMMENT ON COLUMN risk_external_contacts.is_active IS 'Soft delete flag';

-- Enable Row Level Security
ALTER TABLE risk_external_contacts ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Authenticated users can read external contacts
CREATE POLICY "Authenticated users can read external contacts"
    ON risk_external_contacts
    FOR SELECT
    TO authenticated
    USING (true);

-- RLS Policy: Authenticated users can insert external contacts
CREATE POLICY "Authenticated users can insert external contacts"
    ON risk_external_contacts
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- RLS Policy: Authenticated users can update external contacts
CREATE POLICY "Authenticated users can update external contacts"
    ON risk_external_contacts
    FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- RLS Policy: Authenticated users can delete external contacts
CREATE POLICY "Authenticated users can delete external contacts"
    ON risk_external_contacts
    FOR DELETE
    TO authenticated
    USING (true);

-- Grant permissions to service role (bypasses RLS)
GRANT ALL ON risk_external_contacts TO service_role;
GRANT ALL ON risk_external_contacts TO authenticated;
