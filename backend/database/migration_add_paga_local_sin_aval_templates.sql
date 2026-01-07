/*
 * Migration: Add Paga Local Colombia "Sin Aval" Contract Templates
 * Created: 2024-12-03
 * Author: SDLC Agent
 *
 * Purpose:
 * Adds two new contract template records for the Paga Local Colombia module
 * to enable document generation for contracts without guarantees ("Sin Aval").
 *
 * Contract Types:
 * 1. K° Crédito (No Aval) - Credit contract without personal or corporate guarantee
 * 2. K° Mandato (No Aval) - Mandate contract without guarantee
 *
 * These templates are part of the "Contratos Cuenta Cliente - Sin Aval" section
 * in the Paga Local Colombia workflow.
 */

-- Insert template record for K° Crédito (No Aval)
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_credito_no_aval',
    '1.0.0',
    'FK COL paga local - Fin. COP - K° Crédito (No Aval).docx',
    true,
    NOW()
) ON CONFLICT (contract_type, version) DO NOTHING;

-- Insert template record for K° Mandato (No Aval)
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_mandato_no_aval',
    '1.0.0',
    'FK COL paga local - Fin. COP - K° Mandato.docx',
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
WHERE contract_type IN ('pl_co_credito_no_aval', 'pl_co_mandato_no_aval')
ORDER BY contract_type;
