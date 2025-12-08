/*
 * Migration: Add DIAN Mandato (IM) Contract Template
 * Created: 2025-12-07
 * Author: SDLC Agent
 *
 * Purpose:
 * Adds the contract template record for DIAN Mandato (IM) (PLDI) documents
 * in the Paga Local Colombia module.
 *
 * The Word template file already exists at:
 * backend/templates/FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx
 *
 * IMPORTANT: Run this migration manually in Supabase SQL Editor before
 * using the DIAN Mandato (IM) document generation feature.
 */

-- Insert template record for DIAN Mandato (IM)
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_dian_mandato_im',
    '1.0.0',
    'FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx',
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
WHERE contract_type = 'pl_co_dian_mandato_im';
