/*
 * Migration: Fix Paga Local Sequence Synchronization Issue
 * Created: 2025-12-06
 * Author: SDLC Agent
 *
 * Problem:
 * Multiple contract types share the same prefix (PLCR for all credit contracts),
 * but each has its own sequence counter. This causes duplicate contract IDs:
 * - pl_co_credito_aval_pj generates PLCR-2025-001
 * - pl_co_credito_aval_pn tries to generate PLCR-2025-001 (CONFLICT!)
 *
 * Solution:
 * Update all sequences that share a prefix to use the maximum existing value.
 */

-- Step 1: Find the maximum sequence number for each prefix
-- by looking at existing contracts in contract_generations

-- Get max sequence for PLCR prefix (all credit contracts)
DO $$
DECLARE
    max_plcr_seq INTEGER;
    max_plcm_seq INTEGER;
    current_yr INTEGER;
BEGIN
    current_yr := EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER;

    -- Find max sequence for PLCR prefix
    SELECT COALESCE(
        MAX(
            SUBSTRING(contract_id FROM 'PLCR-\d{4}-(\d+)')::INTEGER
        ), 0
    ) INTO max_plcr_seq
    FROM contract_generations
    WHERE contract_id LIKE 'PLCR-' || current_yr || '-%';

    RAISE NOTICE 'Max PLCR sequence for %: %', current_yr, max_plcr_seq;

    -- Update all credit contract type sequences to max value
    UPDATE contract_id_sequence
    SET last_sequence = max_plcr_seq
    WHERE year = current_yr
    AND contract_type IN (
        'pl_co_credito_no_aval',
        'pl_co_credito_aval_pj',
        'pl_co_credito_aval_pn'
    );

    -- Find max sequence for PLCM prefix
    SELECT COALESCE(
        MAX(
            SUBSTRING(contract_id FROM 'PLCM-\d{4}-(\d+)')::INTEGER
        ), 0
    ) INTO max_plcm_seq
    FROM contract_generations
    WHERE contract_id LIKE 'PLCM-' || current_yr || '-%';

    RAISE NOTICE 'Max PLCM sequence for %: %', current_yr, max_plcm_seq;

    -- Update all mandato contract type sequences to max value
    UPDATE contract_id_sequence
    SET last_sequence = max_plcm_seq
    WHERE year = current_yr
    AND contract_type IN (
        'pl_co_mandato_no_aval',
        'pl_co_mandato_pj',
        'pl_co_mandato_pn'
    );
END $$;

-- Step 2: Verify the fix
SELECT
    contract_type,
    year,
    last_sequence,
    CASE
        WHEN contract_type LIKE 'pl_co_credito%' THEN 'PLCR'
        WHEN contract_type LIKE 'pl_co_mandato%' THEN 'PLCM'
        ELSE 'OTHER'
    END as prefix
FROM contract_id_sequence
WHERE contract_type LIKE 'pl_co_%'
ORDER BY prefix, contract_type;

-- Step 3: Show existing PLCR contracts for reference
SELECT contract_id, contract_type, created_at
FROM contract_generations
WHERE contract_id LIKE 'PLCR-%'
ORDER BY contract_id;
