-- Migration: Add 'pending_documents' status to risk_assessments table
-- Date: 2025-12-23
-- Description: Updates the CHECK constraint on risk_assessments.status to include
--              the 'pending_documents' value required for the document upload workflow.
--
-- Background: The AssessmentStatus enum in risk_dtos.py includes PENDING_DOCUMENTS,
--             but the original migration did not include this value in the CHECK constraint.
--             This caused database constraint violations when creating new evaluations,
--             which manifested as CORS errors in the frontend.

-- ==================== UPDATE CHECK CONSTRAINT ====================

-- Step 1: Find and drop the existing check constraint on status column
-- PostgreSQL auto-generates constraint names, so we need to find it dynamically
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    -- Find the check constraint on the status column
    SELECT conname INTO constraint_name
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
    WHERE c.conrelid = 'risk_assessments'::regclass
    AND c.contype = 'c'
    AND a.attname = 'status';

    -- Drop the constraint if it exists
    IF constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE risk_assessments DROP CONSTRAINT ' || quote_ident(constraint_name);
        RAISE NOTICE 'Dropped constraint: %', constraint_name;
    ELSE
        RAISE NOTICE 'No check constraint found on status column';
    END IF;
END $$;

-- Step 2: Add new check constraint with all valid status values
-- Values match AssessmentStatus enum in backend/src/interface/risk_dtos.py
ALTER TABLE risk_assessments
ADD CONSTRAINT risk_assessments_status_check
CHECK (status IN (
    'pending',           -- Initial status
    'pending_documents', -- Awaiting document upload for cross-validation
    'in_progress',       -- Evaluation in progress
    'completed',         -- Evaluation completed (auto for low risk)
    'escalated',         -- Escalated for review (auto for critical risk)
    'approved',          -- Approved by risk manager
    'rejected'           -- Rejected by risk manager
));

-- ==================== VERIFICATION ====================

-- Verify the new constraint exists and has correct definition
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'risk_assessments'::regclass
AND contype = 'c'
AND conname = 'risk_assessments_status_check';

-- Show all check constraints on risk_assessments for verification
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'risk_assessments'::regclass
AND contype = 'c';
