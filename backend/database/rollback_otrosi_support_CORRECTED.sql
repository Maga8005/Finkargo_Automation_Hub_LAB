-- Rollback: Remove Otrosí Contract Type Support
-- Description: Reverts the Otrosí migration back to original state
-- Date: 2025-11-06
-- CAUTION: This will remove Otrosí data and revert to single contract type

-- ================================================================
-- STEP 1: Drop the updated function
-- ================================================================

DROP FUNCTION IF EXISTS generate_contract_id(VARCHAR);

-- ================================================================
-- STEP 2: Restore original function (single contract type)
-- ================================================================

CREATE OR REPLACE FUNCTION generate_contract_id()
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    new_contract_id VARCHAR(50);
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Insert or update sequence for current year
    INSERT INTO contract_id_sequence (year, last_sequence)
    VALUES (current_year, 1)
    ON CONFLICT (year)
    DO UPDATE SET last_sequence = contract_id_sequence.last_sequence + 1
    RETURNING last_sequence INTO next_sequence;

    -- Format: ACT-YYYY-NNN
    new_contract_id := 'ACT-' || current_year || '-' || LPAD(next_sequence::TEXT, 3, '0');

    RETURN new_contract_id;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- STEP 3: Remove contract_type column from contract_generations
-- ================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contract_generations' AND column_name = 'contract_type'
    ) THEN
        -- First check if there are any otrosi contracts
        IF EXISTS (SELECT 1 FROM contract_generations WHERE contract_type = 'otrosi') THEN
            RAISE WARNING 'WARNING: Found Otrosí contracts in database. Consider backing up before removing column.';
        END IF;

        ALTER TABLE contract_generations DROP COLUMN IF EXISTS contract_type;
    END IF;
END $$;

-- ================================================================
-- STEP 4: Remove approved_document_url column
-- ================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contract_generations' AND column_name = 'approved_document_url'
    ) THEN
        ALTER TABLE contract_generations DROP COLUMN IF EXISTS approved_document_url;
    END IF;
END $$;

-- ================================================================
-- STEP 5: Restore contract_id_sequence to original structure
-- ================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'contract_id_sequence' AND column_name = 'contract_type'
    ) THEN
        -- Drop composite primary key
        ALTER TABLE contract_id_sequence DROP CONSTRAINT IF EXISTS contract_id_sequence_pkey;

        -- Drop index
        DROP INDEX IF EXISTS idx_contract_id_sequence_type;

        -- Remove contract_type column
        ALTER TABLE contract_id_sequence DROP COLUMN IF EXISTS contract_type;

        -- Restore original UNIQUE constraint
        ALTER TABLE contract_id_sequence ADD CONSTRAINT contract_id_sequence_year_key UNIQUE (year);
    END IF;
END $$;

-- ================================================================
-- STEP 6: Deactivate or remove Otrosí template
-- ================================================================

UPDATE contract_templates
SET active = FALSE
WHERE contract_type = 'otrosi';

-- OR completely remove it (uncomment if you want to delete):
-- DELETE FROM contract_templates WHERE contract_type = 'otrosi';

-- ================================================================
-- VERIFICATION
-- ================================================================

-- Verify rollback
SELECT 'contract_id_sequence structure:' AS verification;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'contract_id_sequence'
ORDER BY ordinal_position;

SELECT 'Otrosí template status:' AS verification;
SELECT contract_type, version, active
FROM contract_templates
WHERE contract_type = 'otrosi';

-- ================================================================
-- SUCCESS MESSAGE
-- ================================================================
DO $$
BEGIN
    RAISE NOTICE '✓ Rollback completed successfully!';
    RAISE NOTICE '✓ Original generate_contract_id() function restored';
    RAISE NOTICE '✓ contract_type columns removed';
    RAISE NOTICE '✓ contract_id_sequence restored to original structure';
    RAISE NOTICE '✓ Otrosí template deactivated';
END $$;
