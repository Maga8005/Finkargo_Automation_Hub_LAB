/*
 * Migration: Add Paga Local Colombia "Aval PJ" Contract Template
 * Created: 2025-12-05
 * Author: SDLC Agent
 *
 * Purpose:
 * Adds contract template record for the Paga Local Colombia module
 * to enable document generation for credit contracts with corporate guarantee ("Aval PJ").
 *
 * Contract Type:
 * K° Crédito (Aval PJ) - Credit contract with corporate (Persona Jurídica) guarantee
 *
 * This template is part of the "Contratos Cuenta Cliente - Aval Persona Jurídica" section
 * in the Paga Local Colombia workflow.
 *
 * Note: The contract ID prefix (PLCR) was already configured in
 * migration_add_paga_local_contract_id_prefixes.sql
 */

-- Insert template record for K° Crédito (Aval PJ)
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_credito_aval_pj',
    '1.0.0',
    'FK COL paga local - Fin. COP - K° Crédito (Aval PJ).docx',
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
WHERE contract_type = 'pl_co_credito_aval_pj'
ORDER BY created_at DESC;
