-- ================================================================
-- Migration: Differentiate Paga Local Contract ID Prefixes
-- Description: Updates generate_contract_id() function to use unique
--              prefixes for each K° Crédito and Mandato contract type
--              to prevent duplicate contract ID generation errors.
-- Date: 2025-12-06
-- ================================================================
--
-- PROBLEM:
-- The Paga Local Colombia contract types share the same prefix within
-- their categories (PLCR for Crédito, PLCM for Mandato), causing
-- duplicate contract ID errors when contracts of different aval types
-- are created.
--
-- SOLUTION:
-- Assign unique prefixes to each contract type:
--
-- K° Crédito contracts:
--   - pl_co_credito_aval_pj  → PLCRJ (Paga Local CRédito Jurídica)
--   - pl_co_credito_aval_pn  → PLCRN (Paga Local CRédito Natural)
--   - pl_co_credito_no_aval  → PLCRS (Paga Local CRédito Sin aval)
--
-- Mandato contracts:
--   - pl_co_mandato_pj       → PLCMJ (Paga Local Cuenta Mandato Jurídica)
--   - pl_co_mandato_pn       → PLCMN (Paga Local Cuenta Mandato Natural)
--   - pl_co_mandato_no_aval  → PLCMS (Paga Local Cuenta Mandato Sin aval)
--
-- ================================================================

-- ================================================================
-- STEP 1: Drop and recreate the generate_contract_id function
-- ================================================================

-- Drop existing function
DROP FUNCTION IF EXISTS generate_contract_id(VARCHAR);
DROP FUNCTION IF EXISTS generate_contract_id();

-- Create updated function with differentiated prefixes
CREATE OR REPLACE FUNCTION generate_contract_id(p_contract_type VARCHAR DEFAULT 'activos')
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    prefix VARCHAR(10);
BEGIN
    -- Get current year
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Determine prefix based on contract type
    CASE p_contract_type
        -- Existing contract types
        WHEN 'activos' THEN prefix := 'ACT';
        WHEN 'otrosi' THEN prefix := 'OTRO';
        WHEN 'inventario_bodega' THEN prefix := 'INV';

        -- Paga Local Colombia - Credito contracts (Account-Level)
        -- Each aval type now has a unique prefix to prevent duplicate IDs
        -- PLCRJ = Paga Local CRédito Jurídica (Aval Persona Jurídica)
        WHEN 'pl_co_credito_aval_pj' THEN prefix := 'PLCRJ';
        -- PLCRN = Paga Local CRédito Natural (Aval Persona Natural)
        WHEN 'pl_co_credito_aval_pn' THEN prefix := 'PLCRN';
        -- PLCRS = Paga Local CRédito Sin aval (No Aval)
        WHEN 'pl_co_credito_no_aval' THEN prefix := 'PLCRS';

        -- Paga Local Colombia - Mandato contracts (Account-Level)
        -- Each aval type has a unique prefix to prevent duplicate IDs
        -- PLCMJ = Paga Local Cuenta Mandato Jurídica (Aval Persona Jurídica)
        WHEN 'pl_co_mandato_pj' THEN prefix := 'PLCMJ';
        -- PLCMN = Paga Local Cuenta Mandato Natural (Aval Persona Natural)
        WHEN 'pl_co_mandato_pn' THEN prefix := 'PLCMN';
        -- PLCMS = Paga Local Cuenta Mandato Sin aval (No Aval)
        WHEN 'pl_co_mandato_no_aval' THEN prefix := 'PLCMS';

        -- Paga Local Colombia - Documentos Operacion (Operation-Level)
        -- PLMI = Paga Local Mandato Importacion
        WHEN 'pl_co_mandato_im' THEN prefix := 'PLMI';
        -- PLSD = Paga Local Solicitud Desembolso
        WHEN 'pl_co_solicitud_desembolso' THEN prefix := 'PLSD';
        -- PLDI = Paga Local DIAN
        WHEN 'pl_co_dian_mandato_im' THEN prefix := 'PLDI';

        -- Default fallback for backward compatibility
        ELSE prefix := 'ACT';
    END CASE;

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
-- STEP 2: Verification queries (run these to confirm migration worked)
-- ================================================================

-- Test differentiated K° Crédito prefixes:
-- SELECT generate_contract_id('pl_co_credito_aval_pj');  -- Should return PLCRJ-2025-XXX
-- SELECT generate_contract_id('pl_co_credito_aval_pn');  -- Should return PLCRN-2025-XXX
-- SELECT generate_contract_id('pl_co_credito_no_aval');  -- Should return PLCRS-2025-XXX

-- Test differentiated Mandato prefixes:
-- SELECT generate_contract_id('pl_co_mandato_pj');      -- Should return PLCMJ-2025-XXX
-- SELECT generate_contract_id('pl_co_mandato_pn');      -- Should return PLCMN-2025-XXX
-- SELECT generate_contract_id('pl_co_mandato_no_aval'); -- Should return PLCMS-2025-XXX

-- Verify existing types still work correctly:
-- SELECT generate_contract_id('activos');           -- Should return ACT-2025-XXX
-- SELECT generate_contract_id('otrosi');            -- Should return OTRO-2025-XXX
-- SELECT generate_contract_id('inventario_bodega'); -- Should return INV-2025-XXX

-- Verify operation-level documents still work:
-- SELECT generate_contract_id('pl_co_mandato_im');           -- Should return PLMI-2025-XXX
-- SELECT generate_contract_id('pl_co_solicitud_desembolso'); -- Should return PLSD-2025-XXX
-- SELECT generate_contract_id('pl_co_dian_mandato_im');      -- Should return PLDI-2025-XXX

-- ================================================================
-- END OF MIGRATION
-- ================================================================
