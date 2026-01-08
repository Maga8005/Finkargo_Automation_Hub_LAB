/*
 * Migration: Add Instrucción de Mandato Contract Template
 * Created: 2025-12-07
 * Author: SDLC Agent
 *
 * Purpose:
 * Adds the contract template record for Instrucción de Mandato (PLMI) documents
 * in the Paga Local Colombia module.
 *
 * This fixes the bug where document generation fails with:
 * "No active contract template found for type: pl_co_mandato_im"
 *
 * The Word template file already exists at:
 * backend/templates/FK COL - Fin. COP - Mandato (IM).docx
 */

-- Insert template record for Instrucción de Mandato
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_mandato_im',
    '1.0.0',
    'FK COL - Fin. COP - Mandato (IM).docx',
    true,
    NOW()
) ON CONFLICT (contract_type, version) DO NOTHING;

-- Verify insertion
SELECT
    id,
    contract_type,
    version,
    template_content,
    active,
    created_at
FROM contract_templates
WHERE contract_type = 'pl_co_mandato_im';
