/*
 * Migration: Add Paga Local Colombia "Aval PN" Contract Template
 * Created: 2025-12-05
 * Author: SDLC Agent
 *
 * Purpose:
 * Adds contract template record for the Paga Local Colombia module
 * to enable document generation for credit contracts with personal guarantee ("Aval PN").
 *
 * Contract Type:
 * K° Crédito (Aval PN) - Credit contract with personal (Persona Natural) guarantee
 *
 * This template is part of the "Contratos Cuenta Cliente - Aval Persona Natural" section
 * in the Paga Local Colombia workflow.
 *
 * Note: The contract ID prefix (PLCR) was already configured in
 * migration_add_paga_local_contract_id_prefixes.sql
 */

-- Insert template record for K° Crédito (Aval PN)
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_credito_aval_pn',
    '1.0.0',
    'FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx',
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
WHERE contract_type = 'pl_co_credito_aval_pn'
ORDER BY created_at DESC;
