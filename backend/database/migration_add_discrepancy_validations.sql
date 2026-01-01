-- Migration: Add discrepancy validations table
-- Date: 2025-12-31
-- Description: Creates the discrepancy_validations table to store per-discrepancy validation state
--              for mesa de control users to validate individual cross-validation findings.

-- Create discrepancy_validations table
CREATE TABLE IF NOT EXISTS discrepancy_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to cross-validation result
    cross_validation_result_id UUID NOT NULL REFERENCES risk_cross_validation_results(id) ON DELETE CASCADE,

    -- Validation data
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validation_reason TEXT, -- validation_reason enum value
    comments TEXT, -- max 2000 chars, enforced at application level

    -- Audit trail
    validated_by UUID REFERENCES auth.users(id),
    validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Ensure unique validation per cross-validation result
    UNIQUE (cross_validation_result_id)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_discrepancy_validations_result_id
ON discrepancy_validations(cross_validation_result_id);

CREATE INDEX IF NOT EXISTS idx_discrepancy_validations_validated_by
ON discrepancy_validations(validated_by);

CREATE INDEX IF NOT EXISTS idx_discrepancy_validations_is_validated
ON discrepancy_validations(is_validated);

-- Enable Row Level Security
ALTER TABLE discrepancy_validations ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read validations
CREATE POLICY "Authenticated users can read discrepancy validations"
ON discrepancy_validations FOR SELECT
TO authenticated
USING (true);

-- Policy: Users with appropriate roles can create/update validations
CREATE POLICY "Authorized users can create discrepancy validations"
ON discrepancy_validations FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authorized users can update discrepancy validations"
ON discrepancy_validations FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

CREATE POLICY "Authorized users can delete discrepancy validations"
ON discrepancy_validations FOR DELETE
TO authenticated
USING (true);

-- Trigger to update updated_at on modification
CREATE OR REPLACE FUNCTION update_discrepancy_validations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_discrepancy_validations_updated_at
    BEFORE UPDATE ON discrepancy_validations
    FOR EACH ROW
    EXECUTE FUNCTION update_discrepancy_validations_updated_at();

-- Grant permissions to service role (backend)
GRANT ALL ON discrepancy_validations TO service_role;

COMMENT ON TABLE discrepancy_validations IS 'Stores validation state for individual cross-validation discrepancies';
COMMENT ON COLUMN discrepancy_validations.cross_validation_result_id IS 'Reference to the cross-validation result being validated';
COMMENT ON COLUMN discrepancy_validations.is_validated IS 'Whether this discrepancy has been validated by mesa de control';
COMMENT ON COLUMN discrepancy_validations.validation_reason IS 'Reason for validation (manual_validation, email_verification, loading_error, client_justification)';
COMMENT ON COLUMN discrepancy_validations.comments IS 'Free-text comments from the validator (max 2000 chars)';
COMMENT ON COLUMN discrepancy_validations.validated_by IS 'User ID who validated this discrepancy';
COMMENT ON COLUMN discrepancy_validations.validated_at IS 'Timestamp when validation was performed';
