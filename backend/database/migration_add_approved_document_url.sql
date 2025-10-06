-- Migration: Add approved_document_url to contract_generations table
-- Run this in Supabase SQL Editor AFTER setting up the Storage bucket

-- Add column to store Supabase Storage URL for approved contracts
ALTER TABLE contract_generations
ADD COLUMN approved_document_url TEXT;

-- Add comment explaining the column
COMMENT ON COLUMN contract_generations.approved_document_url
IS 'Supabase Storage URL for approved contract PDF. Populated when contract is approved by Legal.';

-- Add index for faster queries on approved contracts with documents
CREATE INDEX idx_contract_generations_approved_url
ON contract_generations(approved_document_url)
WHERE approved_document_url IS NOT NULL;

-- Verify the change
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'contract_generations'
  AND column_name = 'approved_document_url';
