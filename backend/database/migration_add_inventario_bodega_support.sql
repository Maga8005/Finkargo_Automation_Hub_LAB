-- Migration: Add Inventario Bodega de 3ro Contract Type Support
-- Description: Add Inventario Bodega template and update contract_id generation to support warehouse inventory contract type
-- Date: 2025-11-10
-- Pattern: Based on migration_add_otrosi_support_CORRECTED.sql

-- ================================================================
-- STEP 1: Add Inventario Bodega template to contract_templates table
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
    'inventario_bodega',
    '1.0.0',
    'FK COL - GM - Inventario Bodega de 3ro.docx',
    true,
    'Template for Inventario Bodega de 3ro (Third-Party Warehouse Inventory) contracts. File stored in backend/templates/',
    NOW()
)
ON CONFLICT (contract_type, version) DO UPDATE
SET
    template_content = EXCLUDED.template_content,
    active = EXCLUDED.active,
    notes = EXCLUDED.notes;

-- ================================================================
-- STEP 2: Update generate_contract_id() function to support inventario_bodega type
-- ================================================================

-- Drop existing function
DROP FUNCTION IF EXISTS generate_contract_id(VARCHAR);

-- Create updated function with inventario_bodega support
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
    ELSIF p_contract_type = 'inventario_bodega' THEN
        prefix := 'INV';
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
-- STEP 3: Initialize Inventario Bodega sequence for current year
-- ================================================================

-- Insert initial sequence record for Inventario Bodega contracts
INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
VALUES (
    EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER,
    'inventario_bodega',
    0
)
ON CONFLICT (year, contract_type) DO NOTHING;

-- ================================================================
-- VERIFICATION QUERIES
-- ================================================================

-- Verify Inventario Bodega template was added
SELECT contract_type, version, active, notes
FROM contract_templates
WHERE contract_type = 'inventario_bodega';

-- Verify function works for all three contract types
SELECT generate_contract_id('activos') AS activos_id;
SELECT generate_contract_id('otrosi') AS otrosi_id;
SELECT generate_contract_id('inventario_bodega') AS inventario_bodega_id;

-- Verify sequence table structure includes all types
SELECT year, contract_type, last_sequence
FROM contract_id_sequence
ORDER BY year DESC, contract_type;

-- ================================================================
-- SUCCESS MESSAGE
-- ================================================================
DO $$
BEGIN
    RAISE NOTICE '✓ Migration completed successfully!';
    RAISE NOTICE '✓ Inventario Bodega template added';
    RAISE NOTICE '✓ generate_contract_id() function updated to support inventario_bodega type';
    RAISE NOTICE '✓ Sequence initialized for Inventario Bodega contracts';
    RAISE NOTICE '✓ Contract ID format: INV-YYYY-NNN';
END $$;
