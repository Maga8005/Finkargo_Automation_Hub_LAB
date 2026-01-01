-- Migration: Add external communication validations tables
-- Date: 2026-01-01
-- Description: Creates tables for storing per-alert validation state for email chain discrepancies
--              and external contact alerts. Follows the same pattern as discrepancy_validations.

-- ==================== EMAIL CHAIN DISCREPANCY VALIDATIONS ====================

-- Create email_chain_discrepancy_validations table
-- Stores validation state for individual discrepancies within an email chain's validation_result.discrepancies array
CREATE TABLE IF NOT EXISTS email_chain_discrepancy_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to email chain
    email_chain_id UUID NOT NULL REFERENCES email_chains(id) ON DELETE CASCADE,

    -- Discrepancy identifier (index in the validation_result.discrepancies array)
    discrepancy_index INTEGER NOT NULL CHECK (discrepancy_index >= 0),

    -- Validation data
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validation_reason TEXT, -- validation_reason enum value
    comments TEXT, -- max 2000 chars, enforced at application level

    -- Audit trail
    validated_by UUID REFERENCES auth.users(id),
    validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Ensure unique validation per discrepancy within an email chain
    UNIQUE (email_chain_id, discrepancy_index)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_email_chain_discrepancy_validations_chain_id
ON email_chain_discrepancy_validations(email_chain_id);

CREATE INDEX IF NOT EXISTS idx_email_chain_discrepancy_validations_validated_by
ON email_chain_discrepancy_validations(validated_by);

CREATE INDEX IF NOT EXISTS idx_email_chain_discrepancy_validations_is_validated
ON email_chain_discrepancy_validations(is_validated);

-- Enable Row Level Security
ALTER TABLE email_chain_discrepancy_validations ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read validations
CREATE POLICY "Authenticated users can read email chain discrepancy validations"
ON email_chain_discrepancy_validations FOR SELECT
TO authenticated
USING (true);

-- Policy: Users with appropriate roles can create/update validations
CREATE POLICY "Authorized users can create email chain discrepancy validations"
ON email_chain_discrepancy_validations FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authorized users can update email chain discrepancy validations"
ON email_chain_discrepancy_validations FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authorized users can delete email chain discrepancy validations"
ON email_chain_discrepancy_validations FOR DELETE
TO authenticated
USING (true);

-- Trigger to update updated_at on modification
CREATE OR REPLACE FUNCTION update_email_chain_discrepancy_validations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_email_chain_discrepancy_validations_updated_at
    BEFORE UPDATE ON email_chain_discrepancy_validations
    FOR EACH ROW
    EXECUTE FUNCTION update_email_chain_discrepancy_validations_updated_at();

-- Grant permissions to service role (backend)
GRANT ALL ON email_chain_discrepancy_validations TO service_role;

COMMENT ON TABLE email_chain_discrepancy_validations IS 'Stores validation state for individual email chain discrepancies';
COMMENT ON COLUMN email_chain_discrepancy_validations.email_chain_id IS 'Reference to the email chain containing the discrepancy';
COMMENT ON COLUMN email_chain_discrepancy_validations.discrepancy_index IS 'Index of the discrepancy in validation_result.discrepancies array';
COMMENT ON COLUMN email_chain_discrepancy_validations.is_validated IS 'Whether this discrepancy has been validated by mesa de control';
COMMENT ON COLUMN email_chain_discrepancy_validations.validation_reason IS 'Reason for validation (manual_validation, email_verification, loading_error, client_justification)';
COMMENT ON COLUMN email_chain_discrepancy_validations.comments IS 'Free-text comments from the validator (max 2000 chars)';
COMMENT ON COLUMN email_chain_discrepancy_validations.validated_by IS 'User ID who validated this discrepancy';
COMMENT ON COLUMN email_chain_discrepancy_validations.validated_at IS 'Timestamp when validation was performed';

-- ==================== EXTERNAL CONTACT VALIDATIONS ====================

-- Create external_contact_validations table
-- Stores validation state for external contacts that have suspicious/critical validation results
CREATE TABLE IF NOT EXISTS external_contact_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to external contact
    external_contact_id UUID NOT NULL REFERENCES risk_external_contacts(id) ON DELETE CASCADE,

    -- Validation data
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validation_reason TEXT, -- validation_reason enum value
    comments TEXT, -- max 2000 chars, enforced at application level

    -- Audit trail
    validated_by UUID REFERENCES auth.users(id),
    validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Ensure unique validation per external contact
    UNIQUE (external_contact_id)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_external_contact_validations_contact_id
ON external_contact_validations(external_contact_id);

CREATE INDEX IF NOT EXISTS idx_external_contact_validations_validated_by
ON external_contact_validations(validated_by);

CREATE INDEX IF NOT EXISTS idx_external_contact_validations_is_validated
ON external_contact_validations(is_validated);

-- Enable Row Level Security
ALTER TABLE external_contact_validations ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read validations
CREATE POLICY "Authenticated users can read external contact validations"
ON external_contact_validations FOR SELECT
TO authenticated
USING (true);

-- Policy: Users with appropriate roles can create/update validations
CREATE POLICY "Authorized users can create external contact validations"
ON external_contact_validations FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authorized users can update external contact validations"
ON external_contact_validations FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authorized users can delete external contact validations"
ON external_contact_validations FOR DELETE
TO authenticated
USING (true);

-- Trigger to update updated_at on modification
CREATE OR REPLACE FUNCTION update_external_contact_validations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_external_contact_validations_updated_at
    BEFORE UPDATE ON external_contact_validations
    FOR EACH ROW
    EXECUTE FUNCTION update_external_contact_validations_updated_at();

-- Grant permissions to service role (backend)
GRANT ALL ON external_contact_validations TO service_role;

COMMENT ON TABLE external_contact_validations IS 'Stores validation state for external contact alerts';
COMMENT ON COLUMN external_contact_validations.external_contact_id IS 'Reference to the external contact being validated';
COMMENT ON COLUMN external_contact_validations.is_validated IS 'Whether this contact alert has been validated by mesa de control';
COMMENT ON COLUMN external_contact_validations.validation_reason IS 'Reason for validation (manual_validation, email_verification, loading_error, client_justification)';
COMMENT ON COLUMN external_contact_validations.comments IS 'Free-text comments from the validator (max 2000 chars)';
COMMENT ON COLUMN external_contact_validations.validated_by IS 'User ID who validated this alert';
COMMENT ON COLUMN external_contact_validations.validated_at IS 'Timestamp when validation was performed';
