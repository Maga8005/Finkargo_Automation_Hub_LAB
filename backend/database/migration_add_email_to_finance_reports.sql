-- Migration: Add generated_by_email column to finance_reports table
-- Date: 2024-11-28
-- Description: Adds email column for tracking who generated the report

-- Add the email column if it doesn't exist
ALTER TABLE finance_reports
ADD COLUMN IF NOT EXISTS generated_by_email VARCHAR(255);

-- Add comment
COMMENT ON COLUMN finance_reports.generated_by_email IS 'Email of the user who generated the report';
