-- Migration: Add Verification Status Columns to risk_assessments
-- Description: Adds missing columns for verification status, discrepancy flag, and discrepancy count
-- Bug Fix: Resolves 500 error when calling finalize_evaluation_complete()
-- Date: 2024-12-24

-- ==================== Step 1: Add verification_status column ====================

-- Add verification_status column to store binary pass/fail status
-- Values: 'pass' or 'requires_manual_verification'
ALTER TABLE risk_assessments
ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50);

-- Add comment for documentation
COMMENT ON COLUMN risk_assessments.verification_status IS 'Binary verification status: pass or requires_manual_verification';

-- ==================== Step 2: Add has_discrepancies column ====================

-- Add has_discrepancies boolean column
-- Default to FALSE for existing records (no discrepancies known)
ALTER TABLE risk_assessments
ADD COLUMN IF NOT EXISTS has_discrepancies BOOLEAN DEFAULT FALSE;

-- Add comment for documentation
COMMENT ON COLUMN risk_assessments.has_discrepancies IS 'Boolean flag indicating whether any cross-validation discrepancies were found';

-- ==================== Step 3: Add discrepancy_count column ====================

-- Add discrepancy_count integer column
-- Default to 0 for existing records
ALTER TABLE risk_assessments
ADD COLUMN IF NOT EXISTS discrepancy_count INTEGER DEFAULT 0;

-- Add comment for documentation
COMMENT ON COLUMN risk_assessments.discrepancy_count IS 'Count of triggered fraud indicators and discrepancies found during finalization';

-- ==================== Step 4: Create indexes for query performance ====================

-- Index for filtering by verification_status
CREATE INDEX IF NOT EXISTS idx_risk_assessments_verification_status
ON risk_assessments(verification_status)
WHERE verification_status IS NOT NULL;

-- Index for filtering assessments with discrepancies
CREATE INDEX IF NOT EXISTS idx_risk_assessments_has_discrepancies
ON risk_assessments(has_discrepancies)
WHERE has_discrepancies = TRUE;

-- ==================== Step 5: Verification queries ====================

-- Verify columns were added successfully
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'risk_assessments'
    AND column_name IN ('verification_status', 'has_discrepancies', 'discrepancy_count');

    IF col_count = 3 THEN
        RAISE NOTICE 'Migration successful: All 3 columns added to risk_assessments table';
    ELSE
        RAISE EXCEPTION 'Migration failed: Expected 3 columns, found %', col_count;
    END IF;
END
$$;

-- Display current column info for verification
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'risk_assessments'
AND column_name IN ('verification_status', 'has_discrepancies', 'discrepancy_count')
ORDER BY column_name;
