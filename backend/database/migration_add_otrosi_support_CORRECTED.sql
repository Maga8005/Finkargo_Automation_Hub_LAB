-- Migration: Add Otrosí Contract Type Support (CORRECTED VERSION)
-- Description: Add Otrosí template and update contract_id generation to support multiple contract types
-- Date: 2025-11-06
-- Fixed: Removed created_at references that don't exist in contract_id_sequence table

-- ================================================================
-- STEP 1: Add Otrosí template to contract_templates table
-- ================================================================

INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    notes,
    created_at
)
VALUES (
    'otrosi',
    '1.0.0',
    'FK COL - K Marco - Otrosí No. 1.docx',
    true,
    'Template for Otrosí No. 1 contract amendments. File stored in backend/templates/',
    NOW()
)
ON CONFLICT (contract_type, version) DO UPDATE
SET
    template_content = EXCLUDED.template_content,
    active = EXCLUDED.active,
    notes = EXCLUDED.notes;

-- ================================================================
-- STEP 2: Add contract_type column to contract_id_sequence if needed
-- ================================================================

DO $$
BEGIN
    -- Add contract_type column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contract_id_sequence' AND column_name = 'contract_type'
    ) THEN
        ALTER TABLE contract_id_sequence ADD COLUMN contract_type VARCHAR(50) DEFAULT 'activos';

        -- Update existing records to have 'activos' as contract_type
        UPDATE contract_id_sequence SET contract_type = 'activos' WHERE contract_type IS NULL;

        -- Make contract_type NOT NULL
        ALTER TABLE contract_id_sequence ALTER COLUMN contract_type SET NOT NULL;

        -- Drop old primary key constraint (if exists)
        ALTER TABLE contract_id_sequence DROP CONSTRAINT IF EXISTS contract_id_sequence_year_key;

        -- Drop old unique constraint (if exists)
        ALTER TABLE contract_id_sequence DROP CONSTRAINT IF EXISTS contract_id_sequence_pkey;

        -- Add new composite primary key
        ALTER TABLE contract_id_sequence ADD CONSTRAINT contract_id_sequence_pkey PRIMARY KEY (year, contract_type);

        -- Add index for faster lookups
        CREATE INDEX IF NOT EXISTS idx_contract_id_sequence_type ON contract_id_sequence(contract_type, year);
    END IF;
END $$;

-- ================================================================
-- STEP 3: Add contract_type column to contract_generations if needed
-- ================================================================

DO $$
BEGIN
    -- Add contract_type column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contract_generations' AND column_name = 'contract_type'
    ) THEN
        ALTER TABLE contract_generations ADD COLUMN contract_type VARCHAR(50) DEFAULT 'activos';

        -- Update existing records
        UPDATE contract_generations SET contract_type = 'activos' WHERE contract_type IS NULL;

        -- Make contract_type NOT NULL
        ALTER TABLE contract_generations ALTER COLUMN contract_type SET NOT NULL;

        -- Add index for filtering
        CREATE INDEX IF NOT EXISTS idx_contract_gen_type ON contract_generations(contract_type);
    END IF;
END $$;

-- ================================================================
-- STEP 4: Drop old function and create new one with contract_type parameter
-- ================================================================

-- Drop existing function if it exists (both versions)
DROP FUNCTION IF EXISTS generate_contract_id(VARCHAR);
DROP FUNCTION IF EXISTS generate_contract_id();

-- Create new polymorphic function that accepts contract_type parameter
CREATE OR REPLACE FUNCTION generate_contract_id(p_contract_type VARCHAR DEFAULT 'activos')
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    prefix VARCHAR(10);
    sequence_key VARCHAR(50);
BEGIN
    -- Get current year
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Determine prefix based on contract type
    IF p_contract_type = 'otrosi' THEN
        prefix := 'OTRO';
    ELSE
        prefix := 'ACT';  -- Default to Activos for backward compatibility
    END IF;

    -- Create composite key for sequence tracking (year + contract_type)
    sequence_key := current_year::TEXT || '-' || p_contract_type;

    -- Try to get existing sequence for this year and contract type
    SELECT last_sequence INTO next_sequence
    FROM contract_id_sequence
    WHERE year = current_year AND contract_type = p_contract_type
    FOR UPDATE;

    -- If sequence exists, increment it
    IF FOUND THEN
        next_sequence := next_sequence + 1;

        UPDATE contract_id_sequence
        SET last_sequence = next_sequence
        WHERE year = current_year AND contract_type = p_contract_type;
    ELSE
        -- Initialize new sequence for this year and contract type
        next_sequence := 1;

        INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
        VALUES (current_year, p_contract_type, next_sequence);
    END IF;

    -- Return formatted contract ID: PREFIX-YYYY-NNN
    RETURN prefix || '-' || current_year || '-' || LPAD(next_sequence::TEXT, 3, '0');
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- STEP 5: Initialize Otrosí sequence for current year
-- ================================================================

-- Insert initial sequence record for Otrosí contracts (removed created_at)
INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
VALUES (
    EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER,
    'otrosi',
    0
)
ON CONFLICT (year, contract_type) DO NOTHING;

-- ================================================================
-- STEP 6: Add approved_document_url column to contract_generations if needed
-- ================================================================

DO $$
BEGIN
    -- Add approved_document_url column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contract_generations' AND column_name = 'approved_document_url'
    ) THEN
        ALTER TABLE contract_generations ADD COLUMN approved_document_url TEXT;
    END IF;
END $$;

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Verify Otrosí template was added
SELECT contract_type, version, active, notes
FROM contract_templates
WHERE contract_type = 'otrosi';

-- Verify function works for both contract types
SELECT generate_contract_id('activos') AS activos_id;
SELECT generate_contract_id('otrosi') AS otrosi_id;

-- Verify sequence table structure
SELECT year, contract_type, last_sequence
FROM contract_id_sequence
ORDER BY year DESC, contract_type;

-- Verify contract_generations has new columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'contract_generations'
AND column_name IN ('contract_type', 'approved_document_url');

-- ================================================================
-- SUCCESS MESSAGE
-- ================================================================
DO $$
BEGIN
    RAISE NOTICE '✓ Migration completed successfully!';
    RAISE NOTICE '✓ Otrosí template added';
    RAISE NOTICE '✓ contract_type column added to tables';
    RAISE NOTICE '✓ generate_contract_id() function updated';
    RAISE NOTICE '✓ Sequence initialized for Otrosí contracts';
END $$;
