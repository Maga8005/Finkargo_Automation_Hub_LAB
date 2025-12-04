-- ================================================================
-- Migration: Add Paga Local Colombia Contract ID Prefixes
-- Description: Extends generate_contract_id() function to support
--              unique prefixes for Paga Local Colombia contracts
-- Date: 2025-12-03
-- ================================================================

-- ================================================================
-- STEP 1: Drop and recreate the generate_contract_id function
-- ================================================================

-- Drop existing function
DROP FUNCTION IF EXISTS generate_contract_id(VARCHAR);
DROP FUNCTION IF EXISTS generate_contract_id();

-- Create updated function with Paga Local prefixes
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
        -- PLCR = Paga Local CRedito
        WHEN 'pl_co_credito_no_aval' THEN prefix := 'PLCR';
        WHEN 'pl_co_credito_aval_pj' THEN prefix := 'PLCR';
        WHEN 'pl_co_credito_aval_pn' THEN prefix := 'PLCR';

        -- Paga Local Colombia - Mandato contracts (Account-Level)
        -- PLCM = Paga Local Cuenta Mandato
        WHEN 'pl_co_mandato_no_aval' THEN prefix := 'PLCM';
        WHEN 'pl_co_mandato_pj' THEN prefix := 'PLCM';
        WHEN 'pl_co_mandato_pn' THEN prefix := 'PLCM';

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
-- STEP 2: Initialize sequences for Paga Local contract types
-- ================================================================

-- Initialize sequences for all new Paga Local contract types
-- Uses ON CONFLICT to avoid errors if sequences already exist
INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
VALUES
    -- Account-Level Contracts (Contratos Cuenta Cliente)
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_credito_no_aval', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_no_aval', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_credito_aval_pj', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_pj', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_credito_aval_pn', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_pn', 0),
    -- Operation-Level Documents (Documentos Operacion)
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_im', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_solicitud_desembolso', 0),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_dian_mandato_im', 0)
ON CONFLICT (year, contract_type) DO NOTHING;

-- ================================================================
-- STEP 3: Verification queries (run these to confirm migration worked)
-- ================================================================

-- Verify function works for Paga Local contract types:

-- Account-Level Contracts (Contratos Cuenta Cliente)
-- SELECT generate_contract_id('pl_co_credito_no_aval');  -- Should return PLCR-2025-001
-- SELECT generate_contract_id('pl_co_mandato_no_aval');  -- Should return PLCM-2025-001
-- SELECT generate_contract_id('pl_co_credito_aval_pj');  -- Should return PLCR-2025-002
-- SELECT generate_contract_id('pl_co_mandato_pj');       -- Should return PLCM-2025-002

-- Operation-Level Documents (Documentos Operacion)
-- SELECT generate_contract_id('pl_co_mandato_im');           -- Should return PLMI-2025-001
-- SELECT generate_contract_id('pl_co_solicitud_desembolso'); -- Should return PLSD-2025-001
-- SELECT generate_contract_id('pl_co_dian_mandato_im');      -- Should return PLDI-2025-001

-- Existing types (should still work with no changes)
-- SELECT generate_contract_id('activos');           -- Should return ACT-2025-XXX
-- SELECT generate_contract_id('otrosi');            -- Should return OTRO-2025-XXX
-- SELECT generate_contract_id('inventario_bodega'); -- Should return INV-2025-XXX

-- Verify sequence table has all Paga Local types
-- SELECT * FROM contract_id_sequence
-- WHERE contract_type LIKE 'pl_co_%'
-- ORDER BY contract_type;

-- ================================================================
-- END OF MIGRATION
-- ================================================================
