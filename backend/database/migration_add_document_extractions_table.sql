-- Migration: Add Document Extractions and Cross-Validation Tables
-- Feature: AI-Powered Document Cross-Validation for Fraud Detection
-- Date: 2025-12-22

-- Table for storing extracted data from uploaded documents
CREATE TABLE IF NOT EXISTS risk_document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES risk_assessments(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    document_filename VARCHAR(255),
    document_storage_path TEXT,
    extracted_data JSONB,
    extraction_status VARCHAR(20) DEFAULT 'pending',
    extraction_method VARCHAR(20) DEFAULT 'landingai',
    extraction_confidence DECIMAL(3,2),
    extraction_errors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_document_type CHECK (
        document_type IN (
            'financial_statement_current',
            'financial_statement_prior',
            'cedula',
            'composicion_accionaria',
            'rut',
            'certificado_existencia'
        )
    ),
    CONSTRAINT valid_extraction_status CHECK (
        extraction_status IN ('pending', 'processing', 'completed', 'failed')
    )
);

-- Table for storing cross-validation results
CREATE TABLE IF NOT EXISTS risk_cross_validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES risk_assessments(id) ON DELETE CASCADE,
    validation_type VARCHAR(50) NOT NULL,
    documents_compared TEXT[] NOT NULL,
    field_compared VARCHAR(100),
    values_found JSONB,
    is_discrepancy BOOLEAN DEFAULT false,
    severity VARCHAR(20),
    description TEXT,
    score_impact DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_severity CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_doc_extractions_assessment
    ON risk_document_extractions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_doc_extractions_status
    ON risk_document_extractions(extraction_status);
CREATE INDEX IF NOT EXISTS idx_doc_extractions_type
    ON risk_document_extractions(document_type);

CREATE INDEX IF NOT EXISTS idx_cross_validation_assessment
    ON risk_cross_validation_results(assessment_id);
CREATE INDEX IF NOT EXISTS idx_cross_validation_discrepancy
    ON risk_cross_validation_results(is_discrepancy) WHERE is_discrepancy = true;

-- Add has_documents column to risk_assessments if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'risk_assessments'
        AND column_name = 'has_document_validation'
    ) THEN
        ALTER TABLE risk_assessments
        ADD COLUMN has_document_validation BOOLEAN DEFAULT false;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'risk_assessments'
        AND column_name = 'document_validation_status'
    ) THEN
        ALTER TABLE risk_assessments
        ADD COLUMN document_validation_status VARCHAR(20) DEFAULT NULL;
    END IF;
END $$;

-- Row Level Security for document extractions
ALTER TABLE risk_document_extractions ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read document extractions
CREATE POLICY "Authenticated users can read document extractions"
ON risk_document_extractions FOR SELECT
TO authenticated
USING (true);

-- Policy: Risk roles can insert document extractions
CREATE POLICY "Risk roles can insert document extractions"
ON risk_document_extractions FOR INSERT
TO authenticated
WITH CHECK (true);

-- Policy: Risk roles can update document extractions
CREATE POLICY "Risk roles can update document extractions"
ON risk_document_extractions FOR UPDATE
TO authenticated
USING (true);

-- Row Level Security for cross-validation results
ALTER TABLE risk_cross_validation_results ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read cross-validation results
CREATE POLICY "Authenticated users can read cross validation results"
ON risk_cross_validation_results FOR SELECT
TO authenticated
USING (true);

-- Policy: Risk roles can insert cross-validation results
CREATE POLICY "Risk roles can insert cross validation results"
ON risk_cross_validation_results FOR INSERT
TO authenticated
WITH CHECK (true);

-- Grant permissions to service role (backend)
GRANT ALL ON risk_document_extractions TO service_role;
GRANT ALL ON risk_cross_validation_results TO service_role;

-- Comment tables for documentation
COMMENT ON TABLE risk_document_extractions IS 'Stores AI-extracted data from uploaded documents for fraud detection cross-validation';
COMMENT ON TABLE risk_cross_validation_results IS 'Stores results of cross-document validation checks identifying discrepancies';

COMMENT ON COLUMN risk_document_extractions.document_type IS 'Type of document: financial_statement_current, financial_statement_prior, cedula, composicion_accionaria, rut, certificado_existencia';
COMMENT ON COLUMN risk_document_extractions.extraction_status IS 'Status of AI extraction: pending, processing, completed, failed';
COMMENT ON COLUMN risk_document_extractions.extraction_confidence IS 'AI confidence score for extraction (0.00-1.00)';
COMMENT ON COLUMN risk_cross_validation_results.validation_type IS 'Type of validation performed: company_name, nit, legal_representative, shareholders, financial_continuity, email_domain';
COMMENT ON COLUMN risk_cross_validation_results.severity IS 'Severity of discrepancy: low, medium, high, critical';
