-- Migration: Allow NULL for audit fields until auth is implemented
-- Run this in Supabase SQL Editor

-- Make imported_by nullable in clients table
ALTER TABLE clients
ALTER COLUMN imported_by DROP NOT NULL;

-- Make generated_by nullable in contract_generations table
ALTER TABLE contract_generations
ALTER COLUMN generated_by DROP NOT NULL;

-- Make created_by nullable in contract_templates table
ALTER TABLE contract_templates
ALTER COLUMN created_by DROP NOT NULL;

-- Make imported_by nullable in data_imports table
ALTER TABLE data_imports
ALTER COLUMN imported_by DROP NOT NULL;

COMMENT ON COLUMN clients.imported_by IS 'User who imported this record (nullable until auth is implemented)';
COMMENT ON COLUMN contract_generations.generated_by IS 'User who generated this contract (nullable until auth is implemented)';
COMMENT ON COLUMN contract_templates.created_by IS 'User who created this template (nullable until auth is implemented)';
COMMENT ON COLUMN data_imports.imported_by IS 'User who imported this data (nullable until auth is implemented)';
