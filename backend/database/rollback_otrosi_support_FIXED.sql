-- ================================================================
-- ROLLBACK SCRIPT: Remove Otrosí No. 1 Support (FIXED VERSION)
-- ================================================================
-- Run this script if you need to revert the Otrosí migration
-- This will restore the system to only support Activos contracts
-- ================================================================

-- STEP 1: Remove Otrosí contracts (if any were created)
-- WARNING: This will delete all Otrosí contract records!
-- Uncomment this line if you want to delete Otrosí contracts:
-- DELETE FROM contract_generations WHERE contract_type = 'otrosi';

-- STEP 2: Remove Otrosí template from contract_templates
DELETE FROM contract_templates WHERE contract_type = 'otrosi';

-- STEP 3: Remove Otrosí sequences
DELETE FROM contract_id_sequence WHERE contract_type = 'otrosi';

-- STEP 4: Drop the new function that supports contract_type parameter
DROP FUNCTION IF EXISTS generate_contract_id(VARCHAR);

-- STEP 5: Recreate the original generate_contract_id function (Activos only)
CREATE OR REPLACE FUNCTION generate_contract_id()
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    new_contract_id VARCHAR(50);
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Insert or update sequence for current year
    INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
    VALUES (current_year, 'activos', 1)
    ON CONFLICT (year, contract_type)
    DO UPDATE SET last_sequence = contract_id_sequence.last_sequence + 1
    RETURNING last_sequence INTO next_sequence;

    -- Format: ACT-YYYY-NNN
    new_contract_id := 'ACT-' || current_year || '-' || LPAD(next_sequence::TEXT, 3, '0');

    RETURN new_contract_id;
END;
$$ LANGUAGE plpgsql;

-- STEP 6: (Optional) Remove contract_type columns if desired
-- WARNING: Only run these if you want to completely remove multi-type support
-- This will fail if you have any Otrosí contracts in the database

-- Remove contract_type from contract_generations
-- ALTER TABLE contract_generations DROP COLUMN IF EXISTS contract_type;

-- Remove contract_type from contract_id_sequence and restore single primary key
-- NOTE: This requires manual intervention if you have both activos and otrosi sequences
-- ALTER TABLE contract_id_sequence DROP CONSTRAINT contract_id_sequence_pkey;
-- ALTER TABLE contract_id_sequence DROP COLUMN IF EXISTS contract_type;
-- ALTER TABLE contract_id_sequence ADD PRIMARY KEY (year);

-- Remove approved_document_url column
-- ALTER TABLE contract_generations DROP COLUMN IF EXISTS approved_document_url;

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Verify Otrosí template was removed
-- SELECT * FROM contract_templates WHERE contract_type = 'otrosi';
-- (Should return no rows)

-- Verify function works for Activos
-- SELECT generate_contract_id();
-- (Should return ACT-2025-XXX)

-- Verify sequence table
-- SELECT * FROM contract_id_sequence ORDER BY year DESC, contract_type;

-- Verify contract_generations structure
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'contract_generations';

-- ================================================================
-- NOTES
-- ================================================================
-- 1. This rollback is SAFE - it only removes Otrosí support
-- 2. Existing Activos contracts are NOT affected
-- 3. The contract_type columns remain by default for compatibility
-- 4. Uncomment STEP 6 only if you want to fully remove multi-type support
-- 5. If you created Otrosí contracts, they remain unless you uncomment STEP 1
