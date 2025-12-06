/*
 * Migration: Add Paga Local Colombia Mandato PJ and PN Contract Templates
 * Created: 2025-12-06
 * Author: SDLC Agent
 *
 * Purpose:
 * Adds contract template records for Mandato contracts with Persona Juridica (PJ)
 * and Persona Natural (PN) guarantees. These templates use the same document
 * as the existing Mandato No Aval template.
 *
 * Contract Types:
 * 1. pl_co_mandato_pj - Mandato with Persona Juridica (corporate) guarantee
 * 2. pl_co_mandato_pn - Mandato with Persona Natural (individual) guarantee
 *
 * Note: All three Mandato contract types (PJ, PN, No Aval) use the same
 * template file: "FK COL paga local - Fin. COP - K° Mandato.docx"
 */

-- Insert template record for K° Mandato (Aval PJ)
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_mandato_pj',
    '1.0.0',
    'FK COL paga local - Fin. COP - K° Mandato.docx',
    true,
    NOW()
) ON CONFLICT (contract_type, version) DO NOTHING;

-- Insert template record for K° Mandato (Aval PN)
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_mandato_pn',
    '1.0.0',
    'FK COL paga local - Fin. COP - K° Mandato.docx',
    true,
    NOW()
) ON CONFLICT (contract_type, version) DO NOTHING;

-- Verify all Mandato templates are properly configured
SELECT
    id,
    contract_type,
    version,
    template_content,
    active,
    created_at
FROM contract_templates
WHERE contract_type IN ('pl_co_mandato_pj', 'pl_co_mandato_pn', 'pl_co_mandato_no_aval')
ORDER BY contract_type;
